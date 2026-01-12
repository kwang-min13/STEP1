"""
Model Training Pipeline

전체 모델 학습 파이프라인 실행
"""

import sys
from pathlib import Path
import time
import logging

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.dataset import create_training_dataset
from src.models.ranker import PurchaseRanker
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """모델 학습 파이프라인"""
    logger.info("=" * 70)
    logger.info("LightGBM 랭킹 모델 학습 파이프라인 시작")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    # 1. 데이터셋 생성
    logger.info("\n[1/4] 학습 데이터셋 생성 중...")
    features, labels = create_training_dataset(sample_size=5000, negative_ratio=4)
    
    # 2. Train/Validation Split
    logger.info("\n[2/4] Train/Validation Split...")
    X_train, X_val, y_train, y_val = train_test_split(
        features, labels, 
        test_size=0.2, 
        random_state=42,
        stratify=labels
    )
    
    logger.info(f"Train 샘플: {len(X_train):,}")
    logger.info(f"Validation 샘플: {len(X_val):,}")
    
    # 3. 모델 학습
    logger.info("\n[3/4] LightGBM 모델 학습 중...")
    ranker = PurchaseRanker()
    
    params = {
        'objective': 'binary',
        'metric': ['auc', 'binary_logloss'],
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }
    
    metrics = ranker.train(X_train, y_train, X_val, y_val, params)
    
    # 4. 모델 저장
    logger.info("\n[4/4] 모델 저장 중...")
    model_path = 'models/artifacts/purchase_ranker.pkl'
    ranker.save(model_path)
    
    # 결과 출력
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 70)
    logger.info("학습 완료!")
    logger.info("=" * 70)
    logger.info(f"총 소요 시간: {elapsed:.2f}초")
    logger.info(f"\n학습 메트릭:")
    logger.info(f"  Train AUC: {metrics['train_auc']:.4f}")
    logger.info(f"  Valid AUC: {metrics['valid_auc']:.4f}")
    logger.info(f"  Train LogLoss: {metrics['train_logloss']:.4f}")
    logger.info(f"  Valid LogLoss: {metrics['valid_logloss']:.4f}")
    logger.info(f"  Best Iteration: {metrics['best_iteration']}")
    
    # Feature Importance
    logger.info(f"\nFeature Importance (Top 5):")
    importance = ranker.get_feature_importance()
    for i, (feat, imp) in enumerate(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5], 1):
        logger.info(f"  {i}. {feat}: {imp:.2f}")
    
    logger.info(f"\n모델 저장 위치: {model_path}")
    logger.info("=" * 70)
    
    # 성능 검증
    if metrics['valid_auc'] >= 0.65:
        logger.info("✓ 모델 성능 목표 달성 (AUC >= 0.65)")
    else:
        logger.warning(f"⚠ 모델 성능 개선 필요 (AUC: {metrics['valid_auc']:.4f})")


if __name__ == "__main__":
    main()
