"""
Data Processing Pipeline

전체 데이터 처리 워크플로우를 실행하는 메인 스크립트
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.user_features import UserFeatureGenerator
from src.data.item_features import ItemFeatureGenerator
from src.data.feature_store import FeatureStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_data_files():
    """원본 데이터 파일 존재 확인"""
    logger.info("데이터 파일 검증 중...")
    
    required_files = [
        'data/raw/transactions_train.csv',
        'data/raw/customers.csv',
        'data/raw/articles.csv'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"필수 데이터 파일이 없습니다: {missing_files}")
        logger.error("data/DATA_DOWNLOAD_GUIDE.md를 참조하여 데이터를 다운로드하세요.")
        return False
    
    logger.info("✓ 모든 데이터 파일 확인 완료")
    return True


def main():
    """메인 실행 함수"""
    start_time = datetime.now()
    
    logger.info("=" * 70)
    logger.info("Local-Helix 데이터 처리 파이프라인 시작")
    logger.info("=" * 70)
    
    # 1. 데이터 파일 검증
    if not validate_data_files():
        sys.exit(1)
    
    # 2. User Features 생성
    logger.info("\n[1/2] User Features 생성 중...")
    user_gen = UserFeatureGenerator()
    try:
        user_features_path = user_gen.create_user_features()
        logger.info(f"✓ User Features 저장 완료: {user_features_path}")
    except Exception as e:
        logger.error(f"✗ User Features 생성 실패: {str(e)}")
        raise
    finally:
        user_gen.close()
    
    # 3. Item Features 생성
    logger.info("\n[2/2] Item Features 생성 중...")
    item_gen = ItemFeatureGenerator()
    try:
        item_features_path = item_gen.create_item_features()
        logger.info(f"✓ Item Features 저장 완료: {item_features_path}")
    except Exception as e:
        logger.error(f"✗ Item Features 생성 실패: {str(e)}")
        raise
    finally:
        item_gen.close()
    
    # 4. Feature Store 통계 출력
    logger.info("\n[통계] Feature Store 요약")
    store = FeatureStore()
    try:
        stats = store.get_feature_stats()
        
        logger.info("-" * 70)
        if 'users' in stats:
            logger.info(f"User Features:")
            logger.info(f"  - 총 유저 수: {stats['users']['total']:,}")
            logger.info(f"  - 평균 구매 횟수: {stats['users']['avg_purchases']}")
            logger.info(f"  - 평균 구매 시간대: {stats['users']['avg_hour']}시")
        
        if 'items' in stats:
            logger.info(f"Item Features:")
            logger.info(f"  - 총 상품 수: {stats['items']['total']:,}")
            logger.info(f"  - 평균 판매량: {stats['items']['avg_sales']}")
            logger.info(f"  - 최대 판매량: {stats['items']['max_sales']:,}")
        logger.info("-" * 70)
    finally:
        store.close()
    
    # 완료
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ 데이터 처리 파이프라인 완료!")
    logger.info(f"총 소요 시간: {duration:.2f}초")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
