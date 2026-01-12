"""
LightGBM Ranker Module

구매 확률 예측을 위한 LightGBM 모델
"""

import lightgbm as lgb
import polars as pl
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PurchaseRanker:
    """구매 확률 예측 Ranker"""
    
    def __init__(self):
        self.model: Optional[lgb.Booster] = None
        self.feature_names: Optional[list] = None
    
    def train(self,
              X_train: pl.DataFrame,
              y_train: pl.DataFrame,
              X_val: pl.DataFrame,
              y_val: pl.DataFrame,
              params: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        모델 학습
        
        Args:
            X_train: 학습 Features
            y_train: 학습 Labels
            X_val: 검증 Features
            y_val: 검증 Labels
            params: LightGBM 파라미터
            
        Returns:
            학습 메트릭
        """
        logger.info("모델 학습 시작...")
        
        # 기본 파라미터
        if params is None:
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
        
        # Feature 이름 저장
        self.feature_names = X_train.columns
        
        # Polars to numpy
        X_train_np = X_train.to_numpy()
        y_train_np = y_train.to_numpy().ravel()
        X_val_np = X_val.to_numpy()
        y_val_np = y_val.to_numpy().ravel()
        
        # LightGBM Dataset 생성
        train_data = lgb.Dataset(X_train_np, label=y_train_np, feature_name=self.feature_names)
        val_data = lgb.Dataset(X_val_np, label=y_val_np, reference=train_data, feature_name=self.feature_names)
        
        # 학습
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'valid'],
            callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=True)]
        )
        
        # 최종 메트릭
        metrics = {
            'train_auc': self.model.best_score['train']['auc'],
            'valid_auc': self.model.best_score['valid']['auc'],
            'train_logloss': self.model.best_score['train']['binary_logloss'],
            'valid_logloss': self.model.best_score['valid']['binary_logloss'],
            'best_iteration': self.model.best_iteration
        }
        
        logger.info(f"학습 완료 - Valid AUC: {metrics['valid_auc']:.4f}")
        
        return metrics
    
    def predict(self, X: pl.DataFrame) -> np.ndarray:
        """
        예측
        
        Args:
            X: Features
            
        Returns:
            예측 확률
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        X_np = X.to_numpy()
        return self.model.predict(X_np)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Feature Importance 조회"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        importance = self.model.feature_importance(importance_type='gain')
        return dict(zip(self.feature_names, importance))
    
    def save(self, path: str):
        """모델 저장"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # LightGBM 모델 저장
        model_path = path.replace('.pkl', '.txt')
        self.model.save_model(model_path)
        
        # Feature 이름 저장
        metadata = {
            'feature_names': self.feature_names,
            'model_path': model_path
        }
        joblib.dump(metadata, path)
        
        logger.info(f"모델 저장 완료: {path}")
    
    @classmethod
    def load(cls, path: str) -> 'PurchaseRanker':
        """모델 로드"""
        ranker = cls()
        
        # 메타데이터 로드
        metadata = joblib.load(path)
        ranker.feature_names = metadata['feature_names']
        
        # LightGBM 모델 로드
        ranker.model = lgb.Booster(model_file=metadata['model_path'])
        
        logger.info(f"모델 로드 완료: {path}")
        return ranker


if __name__ == "__main__":
    from dataset import create_training_dataset
    from sklearn.model_selection import train_test_split
    
    # 데이터셋 생성
    logger.info("데이터셋 생성 중...")
    features, labels = create_training_dataset(sample_size=5000)
    
    # Train/Val Split
    X_train, X_val, y_train, y_val = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}")
    
    # 모델 학습
    ranker = PurchaseRanker()
    metrics = ranker.train(X_train, y_train, X_val, y_val)
    
    logger.info("=" * 60)
    logger.info("학습 결과:")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 60)
    
    # Feature Importance
    importance = ranker.get_feature_importance()
    logger.info("\nFeature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {feat}: {imp:.2f}")
