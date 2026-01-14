"""
Recommendation Serving Module

학습된 모델을 활용한 추천 서비스
"""

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
    
    def __init__(self, model_path: str = 'models/artifacts/purchase_ranker.pkl'):
        """
        초기화
        
        Args:
            model_path: 학습된 모델 경로
        """
        self.model_path: str = model_path
        self.ranker: Optional[PurchaseRanker] = None
        self.candidate_gen: CandidateGenerator = CandidateGenerator()
        self.feature_store: FeatureStore = FeatureStore()
        
        # 모델 로드
        self._load_model()
    
    def _load_model(self):
        """모델 로드"""
        if Path(self.model_path).exists():
            self.ranker = PurchaseRanker.load(self.model_path)
            logger.info(f"모델 로드 완료: {self.model_path}")
        else:
            logger.warning(f"모델 파일이 없습니다: {self.model_path}")
    
    def recommend(self, user_id: str, top_k: int = 10) -> Dict[str, Any]:
        """
        유저별 Top K 추천 생성
        
        Args:
            user_id: 유저 ID
            top_k: 추천할 상품 수
            
        Returns:
            추천 결과 딕셔너리
        """
        # 1. 후보군 생성
        candidates = self.candidate_gen.merge_candidates(user_id, total_k=100)
        
        if not candidates:
            logger.warning(f"유저 {user_id}에 대한 후보군이 없습니다.")
            return {
                'user_id': user_id,
                'recommendations': [],
                'optimal_send_time': None
            }
        
        # 2. User Features 조회
        user_features = self.feature_store.get_user_features([user_id])
        
        if user_features.height == 0:
            logger.warning(f"유저 {user_id}의 Feature가 없습니다.")
            return {
                'user_id': user_id,
                'recommendations': [],
                'optimal_send_time': None
            }
        
        # 3. Item Features 조회
        item_features = self.feature_store.get_item_features(candidates)
        
        # 4. Features 병합 (Cross Join)
        user_row = user_features.select([
            'avg_purchase_hour', 'purchase_count', 'recency', 'unique_items'
        ]).row(0)
        
        # 각 후보 상품에 대해 Feature 생성
        features_list = []
        for item_row in item_features.iter_rows(named=True):
            features_list.append({
                'avg_purchase_hour': user_row[0],
                'purchase_count': user_row[1],
                'recency': user_row[2],
                'unique_items': user_row[3],
                'popularity_rank': item_row['popularity_rank'],
                'sales_count': item_row['sales_count'],
                'peak_hour': item_row['peak_hour']
            })
        
        features_df = pl.DataFrame(features_list)
        
        # 5. 예측
        if self.ranker is None:
            logger.error("모델이 로드되지 않았습니다.")
            return {
                'user_id': user_id,
                'recommendations': candidates[:top_k],
                'optimal_send_time': int(user_row[0]) if user_row[0] else 12
            }
        
        try:
            scores = self.ranker.predict(features_df)
            
            # 6. Top K 추출
            top_indices = np.argsort(scores)[-top_k:][::-1]
            top_items = [item_features.row(int(idx), named=True)['article_id'] for idx in top_indices]
            top_scores = [float(scores[idx]) for idx in top_indices]
        except Exception as e:
            logger.error(f"예측 중 오류 발생: {e}")
            return {
                'user_id': user_id,
                'recommendations': candidates[:top_k],
                'optimal_send_time': int(user_row[0]) if user_row[0] else 12
            }
        
        # 7. 최적 발송 시간 (유저의 평균 구매 시간)
        optimal_hour = int(user_row[0]) if user_row[0] else 12
        
        return {
            'user_id': user_id,
            'recommendations': top_items,
            'scores': top_scores,
            'optimal_send_time': optimal_hour
        }
    
    def close(self):
        """리소스 정리"""
        self.candidate_gen.close()
        self.feature_store.close()


if __name__ == "__main__":
    # 테스트
    import sys
    from pathlib import Path
    
    # 프로젝트 루트를 Python 경로에 추가
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    service = RecommendationService()
    
    try:
        # 샘플 유저로 테스트
        import duckdb
        con = duckdb.connect(':memory:')
        sample_user = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
        """).fetchone()[0]
        con.close()
        
        logger.info(f"샘플 유저: {sample_user}")
        
        # 추천 생성
        result = service.recommend(sample_user, top_k=10)
        
        logger.info("=" * 60)
        logger.info(f"추천 결과:")
        logger.info(f"  유저 ID: {result['user_id']}")
        logger.info(f"  추천 상품 수: {len(result['recommendations'])}")
        logger.info(f"  최적 발송 시간: {result['optimal_send_time']}시")
        logger.info(f"  Top 3 상품: {result['recommendations'][:3]}")
        if 'scores' in result:
            logger.info(f"  Top 3 점수: {[f'{s:.4f}' for s in result['scores'][:3]]}")
        logger.info("=" * 60)
        
    finally:
        service.close()
