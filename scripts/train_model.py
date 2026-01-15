"""
Model Training Script

LightGBM LambdaRank 모델 학습 및 평가
"""

from __future__ import annotations

import sys
from pathlib import Path
import logging
import argparse
import time
from typing import Tuple, List
import numpy as np

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.dataset import create_ranking_dataset
from src.models.ranker import PurchaseRanker
import polars as pl

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def split_dataset_by_user(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    group: List[int],
    val_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[pl.DataFrame, pl.DataFrame, List[int], pl.DataFrame, pl.DataFrame, List[int]]:
    """
    유저 단위로 train/val split (group 구조 유지)
    
    Args:
        features: Feature DataFrame
        labels: Label DataFrame
        group: 유저별 row 수 리스트
        val_ratio: Validation 비율
        seed: Random seed
        
    Returns:
        (X_train, y_train, group_train, X_val, y_val, group_val)
    """
    np.random.seed(seed)
    
    n_users = len(group)
    n_val_users = int(n_users * val_ratio)
    
    # 유저 인덱스 shuffle
    user_indices = np.random.permutation(n_users)
    val_user_idx = set(user_indices[:n_val_users])
    train_user_idx = set(user_indices[n_val_users:])
    
    # row 인덱스로 변환
    cumsum = np.cumsum([0] + group)
    train_rows = []
    val_rows = []
    group_train = []
    group_val = []
    
    for i in range(n_users):
        row_start = cumsum[i]
        row_end = cumsum[i + 1]
        rows = list(range(row_start, row_end))
        
        if i in train_user_idx:
            train_rows.extend(rows)
            group_train.append(group[i])
        elif i in val_user_idx:
            val_rows.extend(rows)
            group_val.append(group[i])
    
    # Polars indexing
    X_train = features[train_rows]
    y_train = labels[train_rows]
    X_val = features[val_rows]
    y_val = labels[val_rows]
    
    logger.info(f"Train: {len(X_train)} rows, {len(group_train)} users")
    logger.info(f"Val: {len(X_val)} rows, {len(group_val)} users")
    
    return X_train, y_train, group_train, X_val, y_val, group_val


def train_model(
    sample_users: int = 20000,
    negative_per_user: int = 50,
    window_days: int = 28,
    val_ratio: float = 0.2,
    num_boost_round: int = 2000,
    early_stopping_rounds: int = 50,
    learning_rate: float = 0.05,
    num_leaves: int = 127,
    seed: int = 42,
    output_dir: str = "models/artifacts"
):
    """
    전체 학습 파이프라인
    """
    logger.info("=" * 70)
    logger.info("LightGBM LambdaRank 모델 학습 시작")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    # 1. 데이터셋 생성
    logger.info("\n[1/5] 데이터셋 생성 중...")
    X, y, group = create_ranking_dataset(
        sample_users=sample_users,
        negative_per_user=negative_per_user,
        window_days=window_days,
        popularity_pool=2000,
        seed=seed
    )
    
    logger.info(f"총 샘플 수: {len(X):,}")
    logger.info(f"총 유저 수: {len(group):,}")
    logger.info(f"Positive 비율: {(y.filter(pl.col('label')==1).height / len(y)):.2%}")
    
    # 2. Train/Val Split
    logger.info("\n[2/5] Train/Val Split 중...")
    X_train, y_train, group_train, X_val, y_val, group_val = split_dataset_by_user(
        X, y, group, val_ratio=val_ratio, seed=seed
    )
    
    # 3. 모델 학습
    logger.info("\n[3/5] LightGBM 모델 학습 중...")
    
    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "eval_at": [5, 10, 20],
        "boosting_type": "gbdt",
        "learning_rate": learning_rate,
        "num_leaves": num_leaves,
        "min_data_in_leaf": 50,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "lambda_l1": 0.0,
        "lambda_l2": 1.0,
        "max_depth": -1,
        "verbosity": -1,
        "seed": seed,
    }
    
    ranker = PurchaseRanker()
    
    try:
        metrics = ranker.train(
            X_train=X_train,
            y_train=y_train,
            group_train=group_train,
            X_val=X_val,
            y_val=y_val,
            group_val=group_val,
            params=params,
            num_boost_round=num_boost_round,
            early_stopping_rounds=early_stopping_rounds,
            eval_at=[5, 10, 20]
        )
    except Exception as e:
        logger.error(f"학습 중 오류 발생: {e}")
        raise
    
    # 4. 결과 출력
    logger.info("\n[4/5] 학습 결과:")
    logger.info("=" * 70)
    for key, value in metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.6f}")
        else:
            logger.info(f"  {key}: {value}")
    logger.info("=" * 70)
    
    # 5. Feature Importance
    logger.info("\n[5/5] Feature Importance:")
    importance = ranker.get_feature_importance()
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for feat, imp in sorted_importance:
        logger.info(f"  {feat:20s}: {imp:10.2f}")
    
    # 6. 모델 저장
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model_file = output_path / "purchase_ranker.pkl"
    ranker.save(str(model_file))
    
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 70)
    logger.info(f"학습 완료! 총 소요 시간: {elapsed/60:.1f}분")
    logger.info(f"모델 저장 위치: {model_file}")
    logger.info("=" * 70)
    
    return ranker, metrics


def main():
    parser = argparse.ArgumentParser(description="LightGBM LambdaRank 모델 학습")
    
    # 데이터셋 파라미터
    parser.add_argument("--sample-users", type=int, default=20000,
                        help="샘플링할 유저 수 (default: 20000)")
    parser.add_argument("--negative-per-user", type=int, default=50,
                        help="유저당 negative 샘플 수 (default: 50)")
    parser.add_argument("--window-days", type=int, default=28,
                        help="최근 거래 window (default: 28)")
    parser.add_argument("--val-ratio", type=float, default=0.2,
                        help="Validation 비율 (default: 0.2)")
    
    # 모델 파라미터
    parser.add_argument("--num-boost-round", type=int, default=2000,
                        help="Boosting rounds (default: 2000)")
    parser.add_argument("--early-stopping", type=int, default=50,
                        help="Early stopping rounds (default: 50)")
    parser.add_argument("--learning-rate", type=float, default=0.05,
                        help="Learning rate (default: 0.05)")
    parser.add_argument("--num-leaves", type=int, default=127,
                        help="Number of leaves (default: 127)")
    
    # 기타
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default="models/artifacts",
                        help="모델 저장 디렉토리 (default: models/artifacts)")
    
    args = parser.parse_args()
    
    # 학습 실행
    train_model(
        sample_users=args.sample_users,
        negative_per_user=args.negative_per_user,
        window_days=args.window_days,
        val_ratio=args.val_ratio,
        num_boost_round=args.num_boost_round,
        early_stopping_rounds=args.early_stopping,
        learning_rate=args.learning_rate,
        num_leaves=args.num_leaves,
        seed=args.seed,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
