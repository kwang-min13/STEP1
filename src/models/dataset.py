"""
Dataset Creation Module

학습 데이터셋 생성 - User/Item Features + Label
"""

import duckdb
import polars as pl
from pathlib import Path
from typing import Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_training_dataset(
    db_path: str = ':memory:',  # 메모리 DB 사용
    sample_size: int = 10000,
    negative_ratio: int = 4
) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """
    학습 데이터셋 생성 (간소화 버전 - 빠른 실행)
    
    Args:
        db_path: DuckDB 경로 (기본값: 메모리)
        sample_size: 샘플링할 유저 수
        negative_ratio: Negative 샘플 비율 (1:N)
        
    Returns:
        (features_df, labels_df) 튜플
    """
    logger.info("학습 데이터셋 생성 시작...")
    
    con = duckdb.connect(db_path)
    con.execute("SET memory_limit='8GB'")
    
    # 최근 7일 데이터만 사용 (빠른 처리)
    query = f"""
    WITH recent_transactions AS (
        SELECT customer_id, article_id, t_dat
        FROM read_csv_auto('data/raw/transactions_train.csv')
        WHERE t_dat >= (SELECT MAX(t_dat) - INTERVAL '7 days' FROM read_csv_auto('data/raw/transactions_train.csv'))
    ),
    sampled_users AS (
        SELECT DISTINCT customer_id
        FROM recent_transactions
        ORDER BY RANDOM()
        LIMIT {sample_size}
    ),
    positive_samples AS (
        SELECT 
            rt.customer_id,
            rt.article_id,
            1 as label
        FROM recent_transactions rt
        INNER JOIN sampled_users su ON rt.customer_id = su.customer_id
    ),
    negative_samples AS (
        SELECT 
            su.customer_id,
            if_.article_id,
            0 as label
        FROM sampled_users su
        CROSS JOIN (
            SELECT article_id 
            FROM read_parquet('data/features/item_features.parquet')
            ORDER BY popularity_rank
            LIMIT 100
        ) if_
        WHERE NOT EXISTS (
            SELECT 1 FROM positive_samples ps 
            WHERE ps.customer_id = su.customer_id 
            AND ps.article_id = if_.article_id
        )
        ORDER BY RANDOM()
        LIMIT (SELECT COUNT(*) * {negative_ratio} FROM positive_samples)
    ),
    all_samples AS (
        SELECT * FROM positive_samples
        UNION ALL
        SELECT * FROM negative_samples
    )
    SELECT 
        s.customer_id,
        s.article_id,
        s.label,
        uf.avg_purchase_hour,
        uf.purchase_count,
        uf.recency,
        uf.unique_items,
        if_.popularity_rank,
        if_.sales_count,
        if_.peak_hour
    FROM all_samples s
    LEFT JOIN read_parquet('data/features/user_features.parquet') uf 
        ON s.customer_id = uf.customer_id
    LEFT JOIN read_parquet('data/features/item_features.parquet') if_ 
        ON s.article_id = if_.article_id
    WHERE uf.customer_id IS NOT NULL 
        AND if_.article_id IS NOT NULL
    """
    
    logger.info("SQL 쿼리 실행 중...")
    result = con.execute(query).fetch_df()
    con.close()
    
    # Polars DataFrame으로 변환
    df = pl.from_pandas(result)
    
    # Features와 Labels 분리
    feature_cols = [
        'avg_purchase_hour', 'purchase_count', 'recency', 'unique_items',
        'popularity_rank', 'sales_count', 'peak_hour'
    ]
    
    features = df.select(feature_cols)
    labels = df.select('label')
    
    logger.info(f"데이터셋 생성 완료: {len(df):,}개 샘플")
    logger.info(f"Positive: {labels.filter(pl.col('label') == 1).height:,}")
    logger.info(f"Negative: {labels.filter(pl.col('label') == 0).height:,}")
    
    return features, labels


if __name__ == "__main__":
    features, labels = create_training_dataset(sample_size=5000)
    logger.info(f"Features shape: {features.shape}")
    logger.info(f"Labels shape: {labels.shape}")
    logger.info(f"Feature columns: {features.columns}")
