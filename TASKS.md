# Implementation Guide: Local-Helix (Commerce Edition)

이 문서는 Local-Helix 프로젝트의 전체 구현 과정을 단계별로 세분화하여 정리한 실행 가이드입니다.

---

## 📋 Overview

**난이도**: 중상  
**필수 선행 지식**: Python, SQL, 기본 ML 개념

---

## Phase 0: 프로젝트 기획 및 준비 ✅

### 완료된 작업
- [x] PRD.md 작성
- [x] TASKS.md 작성
- [x] TECH_STACK.md 작성
- [x] README.md 작성
- [x] GitHub 이슈 생성 스크립트 개발

### 다음 단계
- [ ] GitHub Issues 생성 실행
- [ ] 프로젝트 디렉토리 구조 생성

---

## Phase 1: 환경 설정

### 목표
로컬 개발 환경을 구축하고 모든 필수 도구를 설치합니다.

### 세부 작업

#### 1.1 Python 환경 설정
```bash
# Python 버전 확인
python --version  # 3.10 이상 필요

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 1.2 핵심 라이브러리 설치
```bash
# requirements.txt 생성
cat > requirements.txt << EOF
duckdb>=0.9.0
polars>=0.20.0
lightgbm>=4.0.0
mlflow>=2.10.0
scipy>=1.11.0
statsmodels>=0.14.0
streamlit>=1.30.0
matplotlib>=3.7.0
seaborn>=0.12.0
jupyter>=1.0.0
requests>=2.31.0
kaggle>=1.5.0
EOF

# 설치
pip install -r requirements.txt
```

#### 1.3 Ollama 설치 및 모델 다운로드
```bash
# Ollama 설치 (https://ollama.ai)
# Windows: 설치 프로그램 다운로드
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Llama 3 모델 다운로드
ollama pull llama3
```

#### 1.4 Kaggle 데이터셋 다운로드
```bash
# Kaggle API 설정
mkdir -p ~/.kaggle
# kaggle.json 파일을 ~/.kaggle/에 복사

# H&M 데이터셋 다운로드
kaggle competitions download -c h-and-m-personalized-fashion-recommendations
unzip h-and-m-personalized-fashion-recommendations.zip -d data/raw/
```

#### 1.5 프로젝트 디렉토리 구조 생성
```bash
mkdir -p data/{raw,processed,features}
mkdir -p notebooks
mkdir -p src/{data,models,simulation,utils}
mkdir -p models/artifacts
mkdir -p logs
mkdir -p reports
```

**체크포인트**: DuckDB 연결 테스트 성공

---

## Phase 2: 데이터 엔지니어링

### 목표
3천만 건의 트랜잭션 데이터를 분석하고 User/Item Feature를 생성합니다.

### 세부 작업

#### 2.1 데이터 탐색 (EDA)
**파일**: `notebooks/01_eda.ipynb`

```python
import duckdb
import polars as pl

# DuckDB 연결
con = duckdb.connect('local_helix.db')

# 데이터 로드 및 기본 통계
con.execute("""
    SELECT COUNT(*) as total_transactions
    FROM 'data/raw/transactions_train.csv'
""").fetchall()

# 유저 수, 상품 수 확인
# 시계열 분포 확인
# 카테고리 분포 확인
```

**체크리스트**:
- [ ] 전체 트랜잭션 수 확인
- [ ] 유니크 유저 수 확인
- [ ] 유니크 상품 수 확인
- [ ] 시계열 범위 확인
- [ ] 결측치 분석
- [ ] 이상치 탐지

#### 2.2 User Feature 생성
**파일**: `src/data/user_features.py`

```python
def create_user_features(con):
    """
    유저별 Feature 생성:
    - avg_purchase_hour: 최근 4주 평균 구매 시간대
    - preferred_category: 선호 카테고리
    - recency: 마지막 구매로부터 경과일
    - purchase_frequency: 구매 빈도
    """
    query = """
    CREATE OR REPLACE TABLE user_features AS
    SELECT 
        customer_id,
        AVG(EXTRACT(HOUR FROM t_dat)) as avg_purchase_hour,
        MODE(product_type_no) as preferred_category,
        DATEDIFF('day', MAX(t_dat), CURRENT_DATE) as recency,
        COUNT(*) as purchase_count
    FROM 'data/raw/transactions_train.csv'
    WHERE t_dat >= CURRENT_DATE - INTERVAL '28 days'
    GROUP BY customer_id
    """
    con.execute(query)
    
    # Parquet로 저장
    con.execute("""
        COPY user_features TO 'data/features/user_features.parquet'
        (FORMAT PARQUET)
    """)
```

**체크리스트**:
- [ ] avg_purchase_hour 계산
- [ ] preferred_category 추출
- [ ] recency 계산
- [ ] purchase_frequency 계산
- [ ] Feature 검증 (NULL 체크)
- [ ] Parquet 저장 확인

#### 2.3 Item Feature 생성
**파일**: `src/data/item_features.py`

```python
def create_item_features(con):
    """
    상품별 Feature 생성:
    - popularity_rank: 최근 1주 판매량 순위
    - peak_hour: 주 판매 시간대
    - avg_price: 평균 가격
    """
    query = """
    CREATE OR REPLACE TABLE item_features AS
    SELECT 
        article_id,
        RANK() OVER (ORDER BY COUNT(*) DESC) as popularity_rank,
        MODE(EXTRACT(HOUR FROM t_dat)) as peak_hour,
        COUNT(*) as sales_count
    FROM 'data/raw/transactions_train.csv'
    WHERE t_dat >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY article_id
    """
    con.execute(query)
```

**체크리스트**:
- [ ] popularity_rank 계산
- [ ] peak_hour 추출
- [ ] sales_count 집계
- [ ] Feature 검증
- [ ] Parquet 저장

#### 2.4 Feature Store 구축
**파일**: `src/data/feature_store.py`

```python
class FeatureStore:
    def __init__(self, db_path='local_helix.db'):
        self.con = duckdb.connect(db_path)
    
    def get_user_features(self, user_ids):
        """유저 Feature 조회"""
        pass
    
    def get_item_features(self, item_ids):
        """상품 Feature 조회"""
        pass
    
    def refresh_features(self):
        """Feature 재생성"""
        pass
```

**체크포인트**: Feature Parquet 파일 생성 완료

---

## Phase 3: 후보군 생성

### 목표
전체 상품 중 유저별로 추천 가능한 후보군을 생성합니다.

### 세부 작업

#### 3.1 Popularity 기반 후보군
**파일**: `src/models/candidate_generation.py`

```python
def generate_popularity_candidates(con, top_k=50):
    """
    전체 유저 대상 인기 상품 Top K 추출
    """
    query = """
    SELECT article_id, sales_count
    FROM item_features
    ORDER BY popularity_rank
    LIMIT ?
    """
    return con.execute(query, [top_k]).fetchall()
```

#### 3.2 Item-based Collaborative Filtering
**파일**: `src/models/candidate_generation.py`

```python
def generate_cf_candidates(con, user_id, top_k=50):
    """
    유저의 최근 구매 상품과 유사한 상품 추천
    Co-visitation 기반
    """
    # 1. 유저의 최근 N개 구매 상품 조회
    query_user_items = """
    SELECT DISTINCT article_id
    FROM 'data/raw/transactions_train.csv'
    WHERE customer_id = ?
    ORDER BY t_dat DESC
    LIMIT 10
    """
    user_items = con.execute(query_user_items, [user_id]).fetchall()
    
    # 2. Co-visitation 행렬 계산
    query_similar = """
    SELECT 
        t2.article_id,
        COUNT(DISTINCT t2.customer_id) as covisit_count
    FROM 'data/raw/transactions_train.csv' t1
    JOIN 'data/raw/transactions_train.csv' t2
        ON t1.customer_id = t2.customer_id
        AND t1.article_id != t2.article_id
    WHERE t1.article_id IN (?)
    GROUP BY t2.article_id
    ORDER BY covisit_count DESC
    LIMIT ?
    """
    return con.execute(query_similar, [user_items, top_k]).fetchall()
```

**체크리스트**:
- [ ] 유저의 최근 N개 구매 상품 조회 (N=10 권장)
- [ ] Co-visitation 행렬 계산 (상품 A와 B를 함께 구매한 유저 수)
- [ ] 유사도 점수 정규화 (선택 사항)
- [ ] Top K 유사 상품 추출
- [ ] 이미 구매한 상품 제외
- [ ] 결과 캐싱 구현 (성능 최적화)

#### 3.3 후보군 병합
**파일**: `src/models/candidate_generation.py`

```python
def merge_candidates(con, user_id, total_k=100):
    """
    Popularity + CF 후보군 병합
    최종 50~100개 후보군 생성
    """
    # 1. Popularity 후보군 (50%)
    popularity_items = generate_popularity_candidates(con, top_k=50)
    
    # 2. CF 후보군 (50%)
    cf_items = generate_cf_candidates(con, user_id, top_k=50)
    
    # 3. 중복 제거
    all_candidates = set([item[0] for item in popularity_items])
    all_candidates.update([item[0] for item in cf_items])
    
    # 4. 다양성 확보 (카테고리 분산)
    # 필요시 카테고리별 쿼터 적용
    
    return list(all_candidates)[:total_k]
```

**체크리스트**:
- [ ] Popularity와 CF 후보군 비율 결정 (50:50 권장)
- [ ] 중복 상품 제거
- [ ] 카테고리 다양성 확보
- [ ] 최종 후보군 크기 검증 (50~100개)
- [ ] 후보군 품질 검증 (NULL 체크)

**체크포인트**: 유저별 후보군 생성 완료

---

## Phase 4: 랭킹 모델

### 목표
LightGBM을 활용하여 구매 확률 예측 모델을 학습합니다.

### 세부 작업

#### 4.1 학습 데이터셋 구성
**파일**: `src/models/dataset.py`

```python
def create_training_dataset(con):
    """
    (User, Item, Time) Feature + Label 병합
    Positive: 실제 구매 (1)
    Negative: 후보군 중 미구매 (0)
    """
    query = """
    SELECT 
        u.customer_id,
        i.article_id,
        u.avg_purchase_hour,
        u.preferred_category,
        u.recency,
        i.popularity_rank,
        i.peak_hour,
        CASE WHEN t.article_id IS NOT NULL THEN 1 ELSE 0 END as label
    FROM user_features u
    CROSS JOIN item_features i
    LEFT JOIN transactions t 
        ON u.customer_id = t.customer_id 
        AND i.article_id = t.article_id
    """
    return con.execute(query).fetch_df()
```

#### 4.2 Train/Validation Split
```python
from sklearn.model_selection import TimeSeriesSplit

# 시계열 기반 분할
tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

#### 4.3 LightGBM 학습
**파일**: `src/models/ranker.py`

```python
import lightgbm as lgb
import mlflow

def train_ranker(X_train, y_train, X_val, y_val):
    """
    LightGBM Ranker 학습
    """
    mlflow.start_run()
    
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9
    }
    
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(10)]
    )
    
    # MLflow 로깅
    mlflow.log_params(params)
    mlflow.log_metric('ndcg', model.best_score['valid_0']['ndcg'])
    mlflow.lightgbm.log_model(model, 'model')
    
    return model
```

#### 4.4 모델 평가
**파일**: `src/models/evaluation.py`

```python
import numpy as np
from sklearn.metrics import ndcg_score

def evaluate_model(model, X_val, y_val, user_groups, k_values=[10, 20, 50]):
    """
    다양한 메트릭으로 모델 평가
    """
    predictions = model.predict(X_val)
    
    metrics = {}
    for k in k_values:
        # Hit Rate@K
        hit_rate = calculate_hit_rate(predictions, y_val, user_groups, k)
        metrics[f'hit_rate@{k}'] = hit_rate
        
        # NDCG@K
        ndcg = calculate_ndcg(predictions, y_val, user_groups, k)
        metrics[f'ndcg@{k}'] = ndcg
        
        # Precision@K
        precision = calculate_precision(predictions, y_val, user_groups, k)
        metrics[f'precision@{k}'] = precision
    
    return metrics

def calculate_hit_rate(predictions, y_true, user_groups, k):
    """
    Hit Rate@K: 추천 K개 중 실제 구매가 포함된 비율
    """
    hits = 0
    total_users = len(user_groups)
    
    for user_id, indices in user_groups.items():
        user_preds = predictions[indices]
        user_labels = y_true[indices]
        
        # Top K 추출
        top_k_idx = np.argsort(user_preds)[-k:]
        top_k_labels = user_labels[top_k_idx]
        
        # 실제 구매가 하나라도 포함되면 hit
        if np.sum(top_k_labels) > 0:
            hits += 1
    
    return hits / total_users
```

**체크리스트**:
- [ ] 검증 데이터셋에 대한 예측 수행
- [ ] Top K 추천 리스트 생성 (K=10, 20, 50)
- [ ] Hit Rate@K 계산
- [ ] NDCG@K 계산
- [ ] Precision@K, Recall@K 계산
- [ ] 평가 결과 시각화 (matplotlib)
- [ ] MLflow에 모든 메트릭 로깅
- [ ] Feature Importance 분석 및 저장

**체크포인트**: MLflow에 모델 저장 완료

---

## Phase 5: 로컬 서빙

### 목표
학습된 모델을 활용하여 실시간 추천 API를 구현합니다.

### 세부 작업

#### 5.1 Serving 함수 구현
**파일**: `src/models/serving.py`

```python
import polars as pl

def merge_features(user_features, item_features):
    """
    User와 Item Feature를 병합하여 모델 입력 생성
    """
    # Polars DataFrame으로 변환
    user_df = pl.DataFrame(user_features)
    item_df = pl.DataFrame(item_features)
    
    # Cross join으로 모든 조합 생성
    merged = user_df.join(item_df, how='cross')
    
    # 필요한 컬럼만 선택
    feature_cols = [
        'avg_purchase_hour', 'preferred_category', 'recency',
        'popularity_rank', 'peak_hour', 'sales_count'
    ]
    
    return merged.select(feature_cols).to_numpy()

class RecommendationService:
    def __init__(self, model_path):
        self.model = lgb.Booster(model_file=model_path)
        self.feature_store = FeatureStore()
    
    def predict(self, user_id, top_k=10):
        """
        유저별 Top K 추천 상품 및 최적 발송 시간 반환
        """
        # 1. 후보군 생성
        candidates = merge_candidates(user_id)
        
        # 2. Feature 조회
        user_features = self.feature_store.get_user_features([user_id])
        item_features = self.feature_store.get_item_features(candidates)
        
        # 3. 예측
        X = merge_features(user_features, item_features)
        scores = self.model.predict(X)
        
        # 4. Top K 추출
        top_items = candidates[scores.argsort()[-top_k:]]
        
        # 5. 최적 발송 시간 계산
        optimal_hour = user_features['avg_purchase_hour']
        
        return {
            'user_id': user_id,
            'recommendations': top_items,
            'optimal_send_time': optimal_hour
        }
```

#### 5.2 배치 추론
**파일**: `scripts/batch_inference.py`

```python
import pandas as pd
from tqdm import tqdm
import logging

def batch_inference(user_ids, output_path='data/recommendations.csv', batch_size=100):
    """
    전체 타겟 유저에 대한 추천 생성
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    service = RecommendationService('models/artifacts/model.txt')
    
    results = []
    failed_users = []
    
    # 배치 단위로 처리
    for i in tqdm(range(0, len(user_ids), batch_size)):
        batch = user_ids[i:i+batch_size]
        
        for user_id in batch:
            try:
                result = service.predict(user_id)
                
                # 결과 검증
                if result and result['recommendations']:
                    results.append(result)
                else:
                    logger.warning(f"Empty result for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Failed for user {user_id}: {str(e)}")
                failed_users.append(user_id)
    
    # 결과 저장
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    
    # 실패한 유저 로깅
    if failed_users:
        with open('logs/failed_users.txt', 'w') as f:
            f.write('\n'.join(map(str, failed_users)))
    
    logger.info(f"Completed: {len(results)} success, {len(failed_users)} failed")
```

**체크리스트**:
- [ ] 타겟 유저 리스트 로드
- [ ] 배치 크기 설정 (메모리 관리, 100~1000 권장)
- [ ] 진행률 표시 (tqdm)
- [ ] 에러 핸들링 및 실패 유저 로깅
- [ ] 결과 검증 (NULL, 빈 리스트 체크)
- [ ] CSV 저장 및 백업
- [ ] 처리 시간 측정 및 로깅

**체크포인트**: 배치 추론 결과 파일 생성

---

## Phase 6: 가상 유저 시뮬레이션

### 목표
Ollama를 활용하여 A/B 테스트 시뮬레이션을 수행합니다.

### 세부 작업

#### 6.1 Ollama API 연동
**파일**: `src/simulation/llm_client.py`

```python
import requests

class OllamaClient:
    def __init__(self, base_url='http://localhost:11434'):
        self.base_url = base_url
    
    def generate(self, prompt, model='llama3'):
        response = requests.post(
            f'{self.base_url}/api/generate',
            json={'model': model, 'prompt': prompt}
        )
        return response.json()
```

#### 6.2 페르소나 생성
**파일**: `src/simulation/persona.py`

```python
from dataclasses import dataclass
from typing import List

@dataclass
class UserMetadata:
    """유저 메타데이터 스키마"""
    user_id: str
    age_group: str  # '20s', '30s', '40s', etc.
    preferred_category: str
    avg_purchase_hour: int
    recent_purchases: List[str]
    purchase_frequency: str  # 'high', 'medium', 'low'

def create_persona(user_metadata: UserMetadata) -> str:
    """
    유저 메타데이터 기반 페르소나 프롬프트 생성
    """
    # 나이대별 페르소나 특성
    age_traits = {
        '20s': '트렌디하고 새로운 스타일을 추구하는',
        '30s': '실용적이면서도 품질을 중시하는',
        '40s': '클래식하고 안정적인 스타일을 선호하는',
    }
    
    # 구매 빈도별 특성
    frequency_traits = {
        'high': '패션에 관심이 많아 자주 쇼핑하는',
        'medium': '필요할 때 계획적으로 구매하는',
        'low': '신중하게 선택하여 가끔 구매하는',
    }
    
    template = f"""
    당신은 다음과 같은 특성을 가진 H&M 고객입니다:
    
    **기본 정보**:
    - 연령대: {user_metadata.age_group}
    - 쇼핑 성향: {age_traits.get(user_metadata.age_group, '일반적인')} {frequency_traits.get(user_metadata.purchase_frequency, '고객')}
    
    **선호도**:
    - 주로 구매하는 카테고리: {user_metadata.preferred_category}
    - 선호 쇼핑 시간대: {user_metadata.avg_purchase_hour}시경
    - 최근 구매 상품: {', '.join(user_metadata.recent_purchases[:3])}
    
    당신의 쇼핑 성향과 선호도를 바탕으로 솔직하게 행동해주세요.
    """
    
    return template

def load_user_metadata(con, user_id):
    """DuckDB에서 유저 메타데이터 로드"""
    query = """
    SELECT 
        customer_id,
        CASE 
            WHEN age < 30 THEN '20s'
            WHEN age < 40 THEN '30s'
            ELSE '40s'
        END as age_group,
        preferred_category,
        avg_purchase_hour,
        recent_purchases,
        CASE
            WHEN purchase_count > 10 THEN 'high'
            WHEN purchase_count > 5 THEN 'medium'
            ELSE 'low'
        END as purchase_frequency
    FROM user_features
    WHERE customer_id = ?
    """
    result = con.execute(query, [user_id]).fetchone()
    return UserMetadata(*result) if result else None
```

**체크리스트**:
- [ ] 유저 메타데이터 스키마 정의 (UserMetadata dataclass)
- [ ] 나이대별 페르소나 특성 정의
- [ ] 구매 빈도별 특성 정의
- [ ] 카테고리별 선호도 프롬프트 작성
- [ ] 페르소나 템플릿 검증 (다양한 유저 타입)
- [ ] LLM 응답 품질 테스트
- [ ] 페르소나 라이브러리 구축 (재사용)

#### 6.3 A/B 테스트 시뮬레이터
**파일**: `src/simulation/ab_test.py`

```python
class ABTestSimulator:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def simulate_group_a(self, user_id):
        """Control: 인기 상품 + 랜덤 시간"""
        popular_items = generate_popularity_candidates(top_k=5)
        send_time = random.randint(9, 21)
        
        prompt = f"""
        {create_persona(user_id)}
        
        오늘 {send_time}시에 다음 상품 추천 푸시를 받았습니다:
        {popular_items}
        
        이 푸시를 클릭하시겠습니까? (Yes/No로만 답변)
        """
        
        response = self.llm.generate(prompt)
        return 'yes' in response.lower()
    
    def simulate_group_b(self, user_id):
        """Test: 모델 추천 + 최적 시간"""
        service = RecommendationService('models/artifacts/model.txt')
        result = service.predict(user_id)
        
        prompt = f"""
        {create_persona(user_id)}
        
        오늘 {result['optimal_send_time']}시에 다음 상품 추천 푸시를 받았습니다:
        {result['recommendations']}
        
        이 푸시를 클릭하시겠습니까? (Yes/No로만 답변)
        """
        
        response = self.llm.generate(prompt)
        return 'yes' in response.lower()
```

#### 6.4 시뮬레이션 실행
**파일**: `scripts/run_simulation.py`

```python
import random
import pandas as pd
from tqdm import tqdm
import logging

def sample_users(con, n_users=1000, sampling_method='random'):
    """
    시뮬레이션 대상 유저 샘플링
    """
    if sampling_method == 'random':
        query = """
        SELECT customer_id
        FROM user_features
        ORDER BY RANDOM()
        LIMIT ?
        """
    elif sampling_method == 'stratified':
        # 구매 빈도별 계층 샘플링
        query = """
        WITH stratified AS (
            SELECT 
                customer_id,
                ROW_NUMBER() OVER (PARTITION BY purchase_frequency ORDER BY RANDOM()) as rn
            FROM user_features
        )
        SELECT customer_id
        FROM stratified
        WHERE rn <= ?
        """
    
    return [row[0] for row in con.execute(query, [n_users]).fetchall()]

def run_ab_test(con, n_users=1000, sampling_method='random'):
    """
    A/B 테스트 시뮬레이션 실행
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    simulator = ABTestSimulator(OllamaClient())
    user_ids = sample_users(con, n_users, sampling_method)
    
    results = []
    logger.info(f"Starting A/B test simulation with {n_users} users")
    
    for user_id in tqdm(user_ids, desc="Simulating users"):
        # 랜덤 그룹 할당 (50:50)
        group = 'A' if random.random() < 0.5 else 'B'
        
        try:
            if group == 'A':
                clicked = simulator.simulate_group_a(user_id)
            else:
                clicked = simulator.simulate_group_b(user_id)
            
            results.append({
                'user_id': user_id,
                'group': group,
                'clicked': clicked,
                'timestamp': pd.Timestamp.now()
            })
            
        except Exception as e:
            logger.error(f"Simulation failed for user {user_id}: {str(e)}")
            continue
    
    # 결과 저장
    df = pd.DataFrame(results)
    df.to_csv('logs/ab_test_results.csv', index=False)
    
    # 간단한 통계 출력
    logger.info(f"Group A CTR: {df[df['group']=='A']['clicked'].mean():.2%}")
    logger.info(f"Group B CTR: {df[df['group']=='B']['clicked'].mean():.2%}")
    
    return df
```

**체크리스트**:
- [ ] 유저 샘플링 방법 선택 (random vs stratified)
- [ ] 샘플 크기 결정 (1000명 권장)
- [ ] A/B 그룹 할당 비율 설정 (50:50)
- [ ] 진행률 표시 (tqdm)
- [ ] 에러 핸들링 및 로깅
- [ ] 중간 결과 저장 (체크포인트)
- [ ] 시뮬레이션 완료 후 기본 통계 출력

**체크포인트**: 시뮬레이션 로그 생성 완료

---

## Phase 7: 분석 및 리포팅

### 목표
시뮬레이션 결과를 분석하고 대시보드를 구축합니다.

### 세부 작업

#### 7.1 통계 분석
**파일**: `src/analysis/statistical_tests.py`

```python
from scipy.stats import chi2_contingency

def analyze_ab_test(results_df):
    """
    카이제곱 검정으로 A/B 그룹 간 CTR 차이 검증
    """
    contingency_table = pd.crosstab(
        results_df['group'],
        results_df['clicked']
    )
    
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    
    return {
        'chi2': chi2,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
```

#### 7.2 Streamlit 대시보드
**파일**: `app.py`

```python
import streamlit as st

st.title('Local-Helix Dashboard')

# 모델 성능 지표
st.header('Model Performance')
st.metric('NDCG@10', 0.85)
st.metric('Hit Rate@10', 0.72)

# A/B 테스트 결과
st.header('A/B Test Results')
results = pd.read_csv('logs/ab_test_results.csv')

col1, col2 = st.columns(2)
with col1:
    st.metric('Group A CTR', f"{results[results['group']=='A']['clicked'].mean():.2%}")
with col2:
    st.metric('Group B CTR', f"{results[results['group']=='B']['clicked'].mean():.2%}")

# 통계 검정 결과
stats = analyze_ab_test(results)
st.write(f"P-value: {stats['p_value']:.4f}")
st.write(f"Statistically Significant: {stats['significant']}")
```

**체크리스트**:
- [ ] 페이지 레이아웃 설계 (사이드바, 메인 영역)
- [ ] 모델 성능 섹션 구현 (NDCG, Hit Rate)
- [ ] A/B 테스트 결과 섹션 구현
- [ ] Feature Importance 시각화
- [ ] 인터랙티브 필터 추가 (날짜, 그룹)
- [ ] 데이터 새로고침 기능
- [ ] 차트 다운로드 기능
- [ ] 로컬 서버 테스트 (streamlit run app.py)

**체크포인트**: Streamlit 대시보드 실행 성공

---

## Phase 8: 최종 문서화

### 목표
프로젝트를 완성하고 모든 문서를 정리합니다.

### 세부 작업

#### 8.1 README 업데이트
- [ ] 프로젝트 소개
- [ ] 설치 가이드
- [ ] 사용 방법
- [ ] 결과 요약
- [ ] 스크린샷 추가

#### 8.2 최종 보고서 작성
**파일**: `FINAL_REPORT.md`

- [ ] 프로젝트 배경
- [ ] 기술적 접근
- [ ] 실험 결과
- [ ] 인사이트 및 개선 방향
- [ ] 참고 문헌

#### 8.3 코드 정리
**파일**: 전체 프로젝트

**코드 품질 기준**:
```python
# 1. PEP 8 준수
# 2. Type Hints 사용
def process_data(data: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """데이터 처리 함수
    
    Args:
        data: 입력 데이터프레임
        threshold: 필터링 임계값
        
    Returns:
        처리된 데이터프레임
    """
    pass

# 3. 상수는 대문자로
MAX_CANDIDATES = 100
DEFAULT_TOP_K = 10

# 4. 매직 넘버 제거
# Bad: if score > 0.7:
# Good: if score > CONFIDENCE_THRESHOLD:
```

**체크리스트**:
- [ ] PEP 8 스타일 가이드 준수 확인
- [ ] 모든 public 함수에 Docstring 추가 (Google style)
- [ ] Type Hints 추가 (Python 3.10+)
- [ ] Dead Code 제거 (미사용 import, 함수)
- [ ] 매직 넘버를 상수로 변경
- [ ] 긴 함수 리팩토링 (50줄 이하 권장)
- [ ] Linting 실행 (flake8, pylint)
- [ ] Code Formatting (black)
- [ ] Import 정리 (isort)
- [ ] 최종 코드 리뷰

**체크포인트**: GitHub 최종 커밋

---

## 📊 Progress Tracking

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: 기획 | ✅ 완료 | 100% |
| Phase 1: 환경 설정 | ⏳ 대기 | 0% |
| Phase 2: 데이터 엔지니어링 | ⏳ 대기 | 0% |
| Phase 3: 후보군 생성 | ⏳ 대기 | 0% |
| Phase 4: 랭킹 모델 | ⏳ 대기 | 0% |
| Phase 5: 로컬 서빙 | ⏳ 대기 | 0% |
| Phase 6: 가상 유저 시뮬레이션 | ⏳ 대기 | 0% |
| Phase 7: 분석 및 리포팅 | ⏳ 대기 | 0% |
| Phase 8: 최종 문서화 | ⏳ 대기 | 0% |

---

## 🎯 Success Criteria

프로젝트 성공 기준:
- [ ] 3천만 건 데이터 처리 완료
- [ ] LightGBM 모델 NDCG@10 > 0.7
- [ ] A/B 테스트에서 통계적 유의성 확보 (p < 0.05)
- [ ] Streamlit 대시보드 정상 작동
- [ ] 전체 코드 GitHub 공개

---

**Last Updated**: 2025-12-24  
**Next Review**: Phase 1 완료 후
