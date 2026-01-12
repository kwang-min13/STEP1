"""
Candidate Generation Module

추천 후보군 생성을 위한 모듈
- Popularity 기반 후보군
- Item-based Collaborative Filtering (최적화)
- 후보군 병합
"""

import duckdb
from pathlib import Path
from typing import List, Optional, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CandidateGenerator:
    """후보군 생성 클래스 (최적화 버전)"""
    
    def __init__(self, db_path: str = 'local_helix.db'):
        """
        초기화
        
        Args:
            db_path: DuckDB 데이터베이스 경로
        """
        self.db_path = db_path
        self.con: Optional[duckdb.DuckDBPyConnection] = None
    
    def connect(self):
        """DuckDB 연결"""
        if self.con is None:
            self.con = duckdb.connect(self.db_path)
            self.con.execute("SET memory_limit='8GB'")
            self.con.execute("SET threads TO 4")
        return self.con
    
    def generate_popularity_candidates(self, top_k: int = 50) -> List[str]:
        """
        인기 상품 기반 후보군 생성
        
        Args:
            top_k: 추출할 인기 상품 수
            
        Returns:
            상품 ID 리스트
        """
        con = self.connect()
        
        query = f"""
            SELECT article_id
            FROM read_parquet('data/features/item_features.parquet')
            ORDER BY popularity_rank
            LIMIT {top_k}
        """
        
        result = con.execute(query).fetchall()
        return [row[0] for row in result]
    
    def generate_cf_candidates(self, 
                               user_id: str,
                               top_k: int = 50,
                               recent_items: int = 5) -> List[str]:
        """
        Collaborative Filtering 기반 후보군 생성 (최적화 버전)
        최근 데이터만 사용하여 성능 향상
        
        Args:
            user_id: 유저 ID
            top_k: 추출할 후보 상품 수
            recent_items: 참고할 최근 구매 상품 수
            
        Returns:
            상품 ID 리스트
        """
        con = self.connect()
        
        # 최적화: 최근 28일 데이터만 사용
        cf_query = f"""
            WITH recent_transactions AS (
                SELECT customer_id, article_id, t_dat
                FROM read_csv_auto('data/raw/transactions_train.csv')
                WHERE t_dat >= (SELECT MAX(t_dat) - INTERVAL '28 days' FROM read_csv_auto('data/raw/transactions_train.csv'))
            ),
            user_items AS (
                SELECT article_id
                FROM recent_transactions
                WHERE customer_id = '{user_id}'
                ORDER BY t_dat DESC
                LIMIT {recent_items}
            ),
            user_purchased AS (
                SELECT DISTINCT article_id
                FROM recent_transactions
                WHERE customer_id = '{user_id}'
            ),
            similar_users AS (
                -- 같은 상품을 구매한 유저들
                SELECT DISTINCT rt.customer_id
                FROM recent_transactions rt
                INNER JOIN user_items ui ON rt.article_id = ui.article_id
                WHERE rt.customer_id != '{user_id}'
                LIMIT 1000
            ),
            candidate_items AS (
                -- 유사 유저들이 구매한 다른 상품들
                SELECT 
                    rt.article_id,
                    COUNT(*) as purchase_count
                FROM recent_transactions rt
                INNER JOIN similar_users su ON rt.customer_id = su.customer_id
                WHERE rt.article_id NOT IN (SELECT article_id FROM user_purchased)
                GROUP BY rt.article_id
                ORDER BY purchase_count DESC
                LIMIT {top_k}
            )
            SELECT article_id
            FROM candidate_items
        """
        
        result = con.execute(cf_query).fetchall()
        return [row[0] for row in result]
    
    def merge_candidates(self,
                        user_id: str,
                        popularity_ratio: float = 0.5,
                        total_k: int = 100) -> List[str]:
        """
        Popularity와 CF 후보군 병합
        
        Args:
            user_id: 유저 ID
            popularity_ratio: Popularity 후보군 비율 (0.0 ~ 1.0)
            total_k: 최종 후보군 크기
            
        Returns:
            병합된 상품 ID 리스트
        """
        # Popularity 후보군 크기 계산
        pop_k = int(total_k * popularity_ratio)
        cf_k = total_k - pop_k
        
        # 1. Popularity 후보군
        popularity_items = self.generate_popularity_candidates(top_k=pop_k)
        
        # 2. CF 후보군
        cf_items = self.generate_cf_candidates(user_id, top_k=cf_k)
        
        # 3. 중복 제거 및 병합
        all_candidates: Set[str] = set(popularity_items)
        all_candidates.update(cf_items)
        
        # 4. CF 후보가 부족하면 Popularity로 채우기
        if len(all_candidates) < total_k:
            additional_pop = self.generate_popularity_candidates(top_k=total_k * 2)
            for item in additional_pop:
                if len(all_candidates) >= total_k:
                    break
                all_candidates.add(item)
        
        # 리스트로 변환 (최대 total_k개)
        return list(all_candidates)[:total_k]
    
    def close(self):
        """연결 종료"""
        if self.con is not None:
            self.con.close()
            self.con = None


def main():
    """테스트 실행"""
    import time
    
    generator = CandidateGenerator()
    
    try:
        # Popularity 후보군 테스트
        logger.info("=" * 60)
        logger.info("Popularity 후보군 생성 테스트")
        start = time.time()
        pop_candidates = generator.generate_popularity_candidates(top_k=50)
        logger.info(f"생성된 후보 수: {len(pop_candidates)}")
        logger.info(f"처리 시간: {(time.time() - start)*1000:.2f}ms")
        logger.info(f"샘플 상품 ID: {pop_candidates[:5]}")
        
        # 샘플 유저로 CF 후보군 테스트
        logger.info("\n" + "=" * 60)
        logger.info("CF 후보군 생성 테스트 (최적화)")
        
        # 첫 번째 유저 ID 가져오기
        con = generator.connect()
        sample_user = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
        """).fetchone()[0]
        
        logger.info(f"샘플 유저 ID: {sample_user}")
        start = time.time()
        cf_candidates = generator.generate_cf_candidates(sample_user, top_k=50)
        logger.info(f"생성된 CF 후보 수: {len(cf_candidates)}")
        logger.info(f"처리 시간: {(time.time() - start)*1000:.2f}ms")
        
        # 병합 후보군 테스트
        logger.info("\n" + "=" * 60)
        logger.info("후보군 병합 테스트")
        start = time.time()
        merged = generator.merge_candidates(sample_user, total_k=100)
        logger.info(f"최종 후보 수: {len(merged)}")
        logger.info(f"처리 시간: {(time.time() - start)*1000:.2f}ms")
        logger.info("=" * 60)
        
    finally:
        generator.close()


if __name__ == "__main__":
    main()
