"""
Simulation Runner

가상 유저 시뮬레이션 실행
"""

import sys
from pathlib import Path
import time
import logging
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.simulation.virtual_user import VirtualUser
from src.simulation.ollama_client import OllamaClient
from src.models.serving import RecommendationService
import duckdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_simulation(num_users: int = 5):
    """
    가상 유저 시뮬레이션 실행
    
    Args:
        num_users: 생성할 가상 유저 수
    """
    logger.info("=" * 70)
    logger.info("가상 유저 시뮬레이션 시작")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    # 1. Ollama 연결 확인
    logger.info("\n[1/4] Ollama 연결 확인 중...")
    ollama_client = OllamaClient()
    
    if ollama_client.check_connection():
        logger.info("✓ Ollama 서버 연결 성공")
        use_llm = True
    else:
        logger.warning("✗ Ollama 서버에 연결할 수 없습니다.")
        logger.info("랜덤 페르소나로 시뮬레이션을 진행합니다.")
        use_llm = False
    
    # 2. Recommendation Service 초기화
    logger.info("\n[2/4] Recommendation Service 초기화 중...")
    rec_service = RecommendationService()
    
    # 3. 실제 유저 샘플 추출
    logger.info(f"\n[3/4] 실제 유저 {num_users}명 샘플링 중...")
    con = duckdb.connect(':memory:')
    real_users = con.execute(f"""
        SELECT customer_id 
        FROM read_parquet('data/features/user_features.parquet')
        ORDER BY RANDOM()
        LIMIT {num_users}
    """).fetchall()
    con.close()
    
    logger.info(f"샘플링된 유저 수: {len(real_users)}")
    
    # 4. 시뮬레이션 실행
    logger.info(f"\n[4/4] 시뮬레이션 실행 중...")
    
    results = []
    
    for i, user_row in enumerate(real_users, 1):
        real_user_id = user_row[0]
        
        logger.info(f"\n--- 시뮬레이션 {i}/{num_users} ---")
        
        # 가상 유저 생성
        virtual_user = VirtualUser(ollama_client if use_llm else None)
        persona = virtual_user.generate_persona()
        
        logger.info(f"페르소나: {persona['age']}세 {persona['gender']}, "
                   f"스타일: {persona.get('style', 'N/A')}")
        
        # 추천 생성 (실제 유저 ID 사용)
        try:
            recommendations = rec_service.recommend(real_user_id, top_k=10)
            
            if recommendations['recommendations']:
                # 가상 유저가 추천 평가
                evaluation = virtual_user.evaluate_recommendations(
                    recommendations['recommendations']
                )
                
                logger.info(f"추천 수: {len(recommendations['recommendations'])}")
                logger.info(f"구매 예상: {evaluation['purchase_count']}")
                logger.info(f"만족도: {evaluation['satisfaction']}/5")
                
                results.append({
                    'persona': persona,
                    'recommendations_count': len(recommendations['recommendations']),
                    'purchase_count': evaluation['purchase_count'],
                    'satisfaction': evaluation['satisfaction'],
                    'acceptance_rate': evaluation['acceptance_rate']
                })
            else:
                logger.warning("추천 생성 실패")
                
        except Exception as e:
            logger.error(f"시뮬레이션 오류: {str(e)}")
    
    # 5. 결과 요약
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 70)
    logger.info("시뮬레이션 완료!")
    logger.info("=" * 70)
    logger.info(f"총 소요 시간: {elapsed:.2f}초")
    logger.info(f"성공한 시뮬레이션: {len(results)}/{num_users}")
    
    if results:
        avg_purchase = sum(r['purchase_count'] for r in results) / len(results)
        avg_satisfaction = sum(r['satisfaction'] for r in results) / len(results)
        avg_acceptance = sum(r['acceptance_rate'] for r in results) / len(results)
        
        logger.info(f"\n평균 지표:")
        logger.info(f"  구매 예상: {avg_purchase:.2f}개")
        logger.info(f"  만족도: {avg_satisfaction:.2f}/5")
        logger.info(f"  수용률: {avg_acceptance:.1%}")
    
    logger.info("=" * 70)
    
    # 정리
    rec_service.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='가상 유저 시뮬레이션 실행')
    parser.add_argument('--users', type=int, default=5, help='생성할 가상 유저 수')
    args = parser.parse_args()
    
    run_simulation(num_users=args.users)
