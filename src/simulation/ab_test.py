"""
A/B Test Simulator Module

A/B 테스트 시뮬레이션을 위한 모듈
- Group A (Control): 인기 상품 + 랜덤 시간
- Group B (Test): ML 추천 + 최적 시간
"""

import random
from typing import Dict, Any, Optional
import logging

from .virtual_user import VirtualUser
from .ollama_client import OllamaClient
from ..models.serving import RecommendationService
from ..models.candidate_generation import CandidateGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABTestSimulator:
    """A/B 테스트 시뮬레이터"""
    
    def __init__(self, 
                 ollama_client: Optional[OllamaClient],
                 rec_service: RecommendationService,
                 candidate_gen: CandidateGenerator):
        """
        초기화
        
        Args:
            ollama_client: Ollama 클라이언트 (None이면 LLM 미사용)
            rec_service: 추천 서비스
            candidate_gen: 후보군 생성기
        """
        self.ollama_client = ollama_client
        self.rec_service = rec_service
        self.candidate_gen = candidate_gen
    
    def simulate_group_a(self, user_id: str, virtual_user: VirtualUser) -> Dict[str, Any]:
        """
        Group A (Control) 시뮬레이션: 인기 상품 + 랜덤 시간
        
        Args:
            user_id: 유저 ID
            virtual_user: 가상 유저 인스턴스
            
        Returns:
            시뮬레이션 결과 딕셔너리
        """
        # 1. 인기 상품 Top 5 추출
        popular_items = self.candidate_gen.generate_popularity_candidates(top_k=5)
        
        # 2. 랜덤 발송 시간 (9시~21시)
        send_time = random.randint(9, 21)
        
        # 3. 가상 유저 평가
        evaluation = virtual_user.evaluate_recommendations(popular_items)
        
        # 클릭 여부: 구매 예상이 1개 이상이면 클릭
        clicked = evaluation.get('purchase_count', 0) > 0
        
        return {
            'clicked': clicked,
            'items': popular_items,
            'send_time': send_time,
            'num_items': len(popular_items),
            'purchase_count': evaluation.get('purchase_count', 0),
            'satisfaction': evaluation.get('satisfaction', 0)
        }
    
    def simulate_group_b(self, user_id: str, virtual_user: VirtualUser) -> Dict[str, Any]:
        """
        Group B (Test) 시뮬레이션: ML 추천 + 최적 시간
        
        Args:
            user_id: 유저 ID
            virtual_user: 가상 유저 인스턴스
            
        Returns:
            시뮬레이션 결과 딕셔너리
        """
        # 1. ML 모델 추천 생성
        recommendations = self.rec_service.recommend(user_id, top_k=5)
        
        rec_items = recommendations.get('recommendations', [])
        optimal_time = recommendations.get('optimal_send_time', 12)
        
        # 2. 가상 유저 평가
        if rec_items:
            evaluation = virtual_user.evaluate_recommendations(rec_items)
        else:
            # 추천이 없으면 기본값
            evaluation = {'purchase_count': 0, 'satisfaction': 0}
        
        # 클릭 여부: 구매 예상이 1개 이상이면 클릭
        clicked = evaluation.get('purchase_count', 0) > 0
        
        return {
            'clicked': clicked,
            'items': rec_items,
            'send_time': optimal_time,
            'num_items': len(rec_items),
            'purchase_count': evaluation.get('purchase_count', 0),
            'satisfaction': evaluation.get('satisfaction', 0)
        }
    
    def close(self):
        """리소스 정리"""
        if self.rec_service:
            self.rec_service.close()
        if self.candidate_gen:
            self.candidate_gen.close()


if __name__ == "__main__":
    # 테스트
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.simulation.ab_test import ABTestSimulator
    from src.simulation.virtual_user import VirtualUser
    from src.models.serving import RecommendationService
    from src.models.candidate_generation import CandidateGenerator
    
    # LLM 없이 테스트
    simulator = ABTestSimulator(
        ollama_client=None,
        rec_service=RecommendationService(),
        candidate_gen=CandidateGenerator()
    )
    
    virtual_user = VirtualUser(ollama_client=None)
    
    # 샘플 유저로 테스트
    import duckdb
    con = duckdb.connect(':memory:')
    sample_user = con.execute("""
        SELECT customer_id 
        FROM read_parquet('data/features/user_features.parquet')
        LIMIT 1
    """).fetchone()[0]
    con.close()
    
    logger.info("=" * 60)
    logger.info("A/B Test Simulator 테스트")
    logger.info("=" * 60)
    
    # Group A 테스트
    logger.info("\n[Group A Test]")
    result_a = simulator.simulate_group_a(sample_user, virtual_user)
    logger.info(f"Clicked: {result_a['clicked']}")
    logger.info(f"Send Time: {result_a['send_time']}시")
    logger.info(f"Items: {len(result_a['items'])}개")
    
    # Group B 테스트
    logger.info("\n[Group B Test]")
    result_b = simulator.simulate_group_b(sample_user, virtual_user)
    logger.info(f"Clicked: {result_b['clicked']}")
    logger.info(f"Send Time: {result_b['send_time']}시")
    logger.info(f"Items: {len(result_b['items'])}개")
    
    logger.info("=" * 60)
    
    simulator.close()
