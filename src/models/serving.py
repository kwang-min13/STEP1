"""
Recommendation Serving Module (Improved)

개선 포인트
1) 점수-아이템 매핑 정합성 보장: candidates 순서를 기준으로 정렬
2) Feature 생성 벡터화: Python loop 제거
3) 결측/타입 안전화: None/NaN 처리, dtype 정리
4) fallback 정책 통일: 모델 없거나 오류 시 deterministic fallback
"""

from __future__ import annotations

import polars as pl
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import numpy as np

from .candidate_generation import CandidateGenerator
from .ranker import PurchaseRanker
from ..data.feature_store import FeatureStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationService:
    """추천 서비스 클래스"""

    def __init__(
        self,
        model_path: str = "models/artifacts/purchase_ranker.pkl",
        candidate_k: int = 300,   # 후보군 크기(성능에 직접 영향)
        top_k_default: int = 10,
        fallback_hour: int = 12,
    ):
        self.model_path = model_path
        self.candidate_k = int(candidate_k)
        self.top_k_default = int(top_k_default)
        self.fallback_hour = int(fallback_hour)

        self.ranker: Optional[PurchaseRanker] = None
        self.candidate_gen = CandidateGenerator()
        self.feature_store = FeatureStore()

        self._load_model()

    def _load_model(self) -> None:
        if Path(self.model_path).exists():
            self.ranker = PurchaseRanker.load(self.model_path)
            logger.info(f"모델 로드 완료: {self.model_path}")
        else:
            self.ranker = None
            logger.warning(f"모델 파일이 없습니다: {self.model_path}")

    def _safe_int_hour(self, x: Any) -> int:
        try:
            if x is None:
                return self.fallback_hour
            # float NaN 대응
            if isinstance(x, float) and np.isnan(x):
                return self.fallback_hour
            h = int(round(float(x)))
            # 0~23 범위 클램프
            return max(0, min(23, h))
        except Exception:
            return self.fallback_hour

    def _fallback(self, user_id: str, candidates: List[str], user_avg_hour: Any, top_k: int) -> Dict[str, Any]:
        # fallback은 항상 popularity/merge 순서 그대로
        return {
            "user_id": user_id,
            "recommendations": candidates[:top_k],
            "scores": None,
            "optimal_send_time": self._safe_int_hour(user_avg_hour),
            "fallback": True,
        }

    def recommend(self, user_id: str, top_k: int = 10) -> Dict[str, Any]:
        top_k = int(top_k) if top_k else self.top_k_default

        # 1) 후보군 생성 (결정적 리스트)
        candidates = self.candidate_gen.merge_candidates(user_id, total_k=self.candidate_k)
        if not candidates:
            logger.warning(f"유저 {user_id}: 후보군이 없습니다.")
            return {"user_id": user_id, "recommendations": [], "scores": None, "optimal_send_time": None, "fallback": True}

        # 2) user features
        uf = self.feature_store.get_user_features([user_id])
        if uf.height == 0:
            logger.warning(f"유저 {user_id}: user feature 없음")
            return self._fallback(user_id, candidates, None, top_k)

        # 필요한 user feature만
        uf1 = uf.select(["avg_purchase_hour", "purchase_count", "recency", "unique_items"]).head(1)
        user_avg_hour = uf1["avg_purchase_hour"][0] if uf1.height else None

        # 3) item features (후보들)
        it = self.feature_store.get_item_features(candidates)

        if it.height == 0:
            logger.warning(f"유저 {user_id}: item feature 없음")
            return self._fallback(user_id, candidates, user_avg_hour, top_k)

        # 3-1) candidates 순서 보장: (candidate_idx join)
        cand_df = pl.DataFrame(
            {"article_id": candidates, "candidate_idx": list(range(len(candidates)))}
        )

        # item_features에 article_id 컬럼이 있어야 함 (없으면 FeatureStore 버그)
        if "article_id" not in it.columns:
            logger.error("item_features에 article_id 컬럼이 없습니다.")
            return self._fallback(user_id, candidates, user_avg_hour, top_k)

        # join 후 후보 순서대로 정렬
        it2 = (
            cand_df.join(it, on="article_id", how="left")
                  .sort("candidate_idx")
        )

        # feature 결측 제거(필요 시)
        needed_item_cols = ["popularity_rank", "sales_count", "peak_hour"]
        missing_cols = [c for c in needed_item_cols if c not in it2.columns]
        if missing_cols:
            logger.error(f"item_features에 필요한 컬럼 누락: {missing_cols}")
            return self._fallback(user_id, candidates, user_avg_hour, top_k)

        # join 결과에서 item feature가 NULL인 후보 제거(모델 입력 불가)
        it2 = it2.filter(
            pl.all_horizontal([pl.col(c).is_not_null() for c in needed_item_cols])
        )
        if it2.height == 0:
            logger.warning(f"유저 {user_id}: 유효한 item feature가 있는 후보가 없습니다.")
            return self._fallback(user_id, candidates, user_avg_hour, top_k)

        # 4) 최종 feature matrix (벡터화)
        # user feature를 상수 컬럼으로 붙임
        features_df = it2.select(
            [
                pl.lit(float(uf1["avg_purchase_hour"][0])).alias("avg_purchase_hour"),
                pl.lit(float(uf1["purchase_count"][0])).alias("purchase_count"),
                pl.lit(float(uf1["recency"][0])).alias("recency"),
                pl.lit(float(uf1["unique_items"][0])).alias("unique_items"),
                pl.col("popularity_rank").cast(pl.Float64),
                pl.col("sales_count").cast(pl.Float64),
                pl.col("peak_hour").cast(pl.Float64),
            ]
        )

        # 5) 모델 없으면 fallback
        if self.ranker is None:
            return self._fallback(user_id, it2["article_id"].to_list(), user_avg_hour, top_k)

        # 6) 예측 + TopK (정합성: it2.article_id와 scores는 같은 순서)
        try:
            scores = self.ranker.predict(features_df)
            scores = np.asarray(scores, dtype=float)

            k = min(top_k, len(scores))
            # argpartition이 빠름(정렬 full cost 감소)
            top_idx = np.argpartition(scores, -k)[-k:]
            top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

            top_items = it2["article_id"].to_list()
            recs = [top_items[int(i)] for i in top_idx]
            rec_scores = [float(scores[int(i)]) for i in top_idx]

        except Exception as e:
            logger.error(f"예측 중 오류: {e}")
            return self._fallback(user_id, it2["article_id"].to_list(), user_avg_hour, top_k)

        # 7) optimal send time (현재는 avg_purchase_hour 기반)
        optimal_hour = self._safe_int_hour(user_avg_hour)

        return {
            "user_id": user_id,
            "recommendations": recs,
            "scores": rec_scores,
            "optimal_send_time": optimal_hour,
            "fallback": False,
        }

    def close(self) -> None:
        self.candidate_gen.close()
        self.feature_store.close()


if __name__ == "__main__":
    import duckdb

    service = RecommendationService(candidate_k=300)

    try:
        con = duckdb.connect(":memory:")
        sample_user = con.execute("""
            SELECT customer_id
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
        """).fetchone()[0]
        con.close()

        res = service.recommend(sample_user, top_k=10)

        logger.info("=" * 60)
        logger.info("추천 결과")
        logger.info(f"  user_id: {res['user_id']}")
        logger.info(f"  #recs: {len(res['recommendations'])}")
        logger.info(f"  optimal_send_time: {res['optimal_send_time']}")
        logger.info(f"  fallback: {res['fallback']}")
        logger.info(f"  top3: {res['recommendations'][:3]}")
        if res["scores"] is not None:
            logger.info(f"  top3 scores: {[f'{s:.4f}' for s in res['scores'][:3]]}")
        logger.info("=" * 60)

    finally:
        service.close()
