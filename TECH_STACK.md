# Tech Stack: Local-Helix (Commerce Edition)

이 문서는 Local-Helix 프로젝트의 구현에 사용되는 기술 스택과 각 기술의 역할, 선정 이유, 그리고 사용 방법을 상세히 정의합니다.

---

## 1. 🗄️ Data Engineering

### DuckDB
- **역할**: 로컬 환경에서 대용량 데이터 처리를 위한 In-Process OLAP 데이터베이스
- **버전**: `0.9.0+` (최신 stable 권장)
- **선정 이유**:
  - 별도의 서버 설치 없이 Python 프로세스 내에서 직접 실행
  - Parquet/CSV 파일에 대한 고성능 SQL 쿼리 지원
  - 3천만 건 이상의 트랜잭션 데이터를 로컬 메모리에서 효율적으로 처리
- **주요 사용 사례**:
  - Raw CSV 데이터 로드 및 탐색적 분석
  - User/Item Feature 생성을 위한 집계 쿼리 실행
  - 시계열 데이터 필터링 및 윈도우 함수 활용
- **설치**:
  ```bash
  pip install duckdb
  ```
- **예제 코드**:
  ```python
  import duckdb
  
  con = duckdb.connect('local_helix.db')
  con.execute("SELECT * FROM 'data/raw/transactions.csv' LIMIT 10")
  ```

### Polars
- **역할**: 고성능 DataFrame 라이브러리
- **버전**: `0.20.0+`
- **선정 이유**:
  - Pandas보다 빠른 처리 속도 (Rust 기반)
  - Lazy Evaluation을 통한 메모리 효율성
  - DuckDB와의 원활한 연동
- **주요 사용 사례**:
  - Feature Engineering 파이프라인 구축
  - 데이터 전처리 및 변환
  - Parquet 파일 I/O
- **설치**:
  ```bash
  pip install polars
  ```

---

## 2. 🤖 Machine Learning

### LightGBM
- **역할**: Gradient Boosting 기반 랭킹 모델
- **버전**: `4.0.0+`
- **선정 이유**:
  - 대용량 데이터에서 빠른 학습 속도
  - Ranking Objective 지원 (`lambdarank`, `rank_xendcg`)
  - Feature Importance 분석 용이
- **주요 사용 사례**:
  - (User, Item, Time) 조합에 대한 구매 확률 예측
  - 후보군 상품에 대한 랭킹 스코어 산출
- **설치**:
  ```bash
  pip install lightgbm
  ```
- **예제 코드**:
  ```python
  import lightgbm as lgb
  
  train_data = lgb.Dataset(X_train, label=y_train, group=group_train)
  params = {'objective': 'lambdarank', 'metric': 'ndcg'}
  model = lgb.train(params, train_data, num_boost_round=100)
  ```

### MLflow
- **역할**: 실험 관리 및 모델 트래킹
- **버전**: `2.10.0+`
- **선정 이유**:
  - 하이퍼파라미터, 메트릭, 아티팩트 자동 로깅
  - 로컬 환경에서 간편한 UI 제공
  - 모델 버전 관리 및 재현성 확보
- **주요 사용 사례**:
  - LightGBM 학습 파라미터 및 성능 지표 기록
  - 모델 아티팩트 저장 및 로드
- **설치**:
  ```bash
  pip install mlflow
  ```
- **실행**:
  ```bash
  mlflow ui
  ```

---

## 3. 🧪 Simulation & Testing

### Ollama (Llama 3)
- **역할**: 로컬 LLM 기반 가상 유저 시뮬레이션
- **모델**: `llama3:8b` 또는 `llama3:70b`
- **선정 이유**:
  - 로컬 환경에서 API 비용 없이 LLM 활용 가능
  - 유저 페르소나 생성 및 행동 시뮬레이션에 적합
  - REST API를 통한 간편한 Python 연동
- **주요 사용 사례**:
  - H&M 유저 메타데이터 기반 페르소나 프롬프트 생성
  - A/B 테스트 시나리오에서 가상 유저의 클릭 여부 판단
- **설치**:
  ```bash
  # Ollama 설치 (https://ollama.ai)
  ollama pull llama3
  ```
- **예제 코드**:
  ```python
  import requests
  
  response = requests.post('http://localhost:11434/api/generate', json={
      'model': 'llama3',
      'prompt': '당신은 20대 여성 직장인입니다. 이 상품을 클릭하시겠습니까?'
  })
  ```

### SciPy / Statsmodels
- **역할**: 통계 분석 및 가설 검정
- **버전**: `scipy>=1.11.0`, `statsmodels>=0.14.0`
- **선정 이유**:
  - A/B 테스트 결과의 통계적 유의성 검증
  - 카이제곱 검정, t-test 등 다양한 통계 기법 지원
- **주요 사용 사례**:
  - Control vs Test 그룹 간 CTR 차이 검정
  - 신뢰 구간 산출
- **설치**:
  ```bash
  pip install scipy statsmodels
  ```

---

## 4. 📊 Visualization & Reporting

### Streamlit
- **역할**: 인터랙티브 대시보드 및 리포팅
- **버전**: `1.30.0+`
- **선정 이유**:
  - Python 코드만으로 웹 대시보드 구축 가능
  - 실시간 데이터 업데이트 및 시각화
  - 배포 없이 로컬에서 즉시 실행 가능
- **주요 사용 사례**:
  - 모델 성능 지표 (Hit Rate, NDCG) 시각화
  - A/B 테스트 결과 비교 차트
  - Feature Importance 그래프
- **설치**:
  ```bash
  pip install streamlit
  ```
- **실행**:
  ```bash
  streamlit run app.py
  ```

### Matplotlib / Seaborn
- **역할**: 정적 그래프 생성
- **버전**: `matplotlib>=3.7.0`, `seaborn>=0.12.0`
- **선정 이유**:
  - 논문/보고서용 고품질 차트 생성
  - Streamlit과 연동하여 커스텀 시각화 구현
- **주요 사용 사례**:
  - 시계열 구매 패턴 분석
  - 카테고리별 판매 분포 시각화

---

## 5. 🛠️ Development Tools

### Jupyter Notebook
- **역할**: 탐색적 데이터 분석 (EDA) 및 프로토타이핑
- **버전**: `jupyter>=1.0.0`
- **선정 이유**:
  - 단계별 코드 실행 및 결과 확인
  - 데이터 시각화 및 문서화 동시 진행
- **설치**:
  ```bash
  pip install jupyter
  ```

### Git & GitHub
- **역할**: 버전 관리 및 협업
- **주요 사용 사례**:
  - 코드 버전 관리
  - GitHub Issues를 통한 태스크 트래킹
  - GitHub Actions를 활용한 자동화 (선택 사항)

---

## 6. 📦 Package Management

### Poetry (권장) 또는 pip
- **역할**: Python 패키지 의존성 관리
- **선정 이유**:
  - 재현 가능한 개발 환경 구축
  - `pyproject.toml`을 통한 의존성 명시
- **설치 (Poetry)**:
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  poetry install
  ```

### requirements.txt (대안)
```txt
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
```

---

## 7. 🗂️ Data Formats

### Parquet
- **역할**: 컬럼 기반 데이터 저장 포맷
- **선정 이유**:
  - CSV 대비 압축률 및 읽기 속도 우수
  - DuckDB, Polars와 네이티브 호환
- **사용 사례**:
  - Feature Store (`user_features.parquet`, `item_features.parquet`)
  - 중간 처리 결과 저장

### CSV
- **역할**: Raw 데이터 입력 포맷
- **사용 사례**:
  - Kaggle 데이터셋 다운로드 원본

### SQLite (선택 사항)
- **역할**: 추천 결과 저장
- **사용 사례**:
  - `recommendations.db`에 배치 추론 결과 저장

---

## 8. 🚀 Deployment & Execution

### Local Execution
- **환경**: Python 3.10+ (3.11 권장)
- **OS**: Windows / macOS / Linux
- **메모리**: 최소 16GB RAM 권장 (32GB 이상 이상적)
- **스토리지**: 최소 10GB 여유 공간

### Docker (선택 사항)
- **역할**: 재현 가능한 실행 환경 제공
- **사용 사례**:
  - 팀원 간 동일한 환경 공유
  - 배포 시 환경 일관성 보장

---

## 9. 📚 Reference Documentation

| 기술 | 공식 문서 |
|------|-----------|
| DuckDB | https://duckdb.org/docs/ |
| Polars | https://pola-rs.github.io/polars/ |
| LightGBM | https://lightgbm.readthedocs.io/ |
| MLflow | https://mlflow.org/docs/latest/ |
| Ollama | https://ollama.ai/docs |
| Streamlit | https://docs.streamlit.io/ |

---

## 10. ✅ Quick Start Checklist

- [ ] Python 3.10+ 설치 확인
- [ ] `requirements.txt` 또는 Poetry를 통한 패키지 설치
- [ ] Ollama 설치 및 `llama3` 모델 다운로드
- [ ] Kaggle API를 통한 H&M 데이터셋 다운로드
- [ ] DuckDB 연결 테스트
- [ ] Jupyter Notebook 실행 확인

---

**Last Updated**: 2025-12-24  
**Maintainer**: Local-Helix Team
