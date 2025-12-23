# Project Requirements Document (PRD): Local-Helix (Commerce Edition)

## 1. 개요 (Overview)
**프로젝트명:** Local-Helix (Commerce Edition)  
**한줄 설명:** 유저 구매 이력을 기반으로 한 시계열 푸시 타겟팅 및 랭킹 엔진 MVP

이 프로젝트는 로컬 환경에서 비용 0원으로 구현 가능하며, 대규모 트랜잭션 데이터를 효율적으로 처리하고 추천/랭킹 모델링 역량을 증명하는 것을 목표로 합니다. H&M 실제 데이터를 활용하여 "누구에게, 어떤 상품을, 언제 추천(푸시)할 것인가"를 결정하는 로직을 구축합니다.

## 2. 목표 (Goals)
- **비용 효율성:** 별도의 서버 인프라 없이 로컬 노트북 환경(DuckDB 활용)에서 대용량 데이터 처리.
- **기술 역량 증명:** 
    - SQL 기반의 대용량 데이터 전처리 역량.
    - 구매 시점(Timestamp)을 고려한 추천 최적화 로직 구현.
    - 단순 추천을 넘어선 구매 확률 기반의 랭킹 모델 설계.
- **완결성:** 데이터 전처리부터 모델링, 가상 유저 테스트, 결과 분석까지 End-to-End 파이프라인 구축.

## 3. 데이터셋 및 환경 (Dataset & Environment)
- **데이터셋:** [Kaggle H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data) (3,100만 건 트랜잭션)
- **개발 환경:** 로컬 노트북 (Python)
- **핵심 도구:** DuckDB (In-process SQL OLAP DBMS)

## 4. 기능 상세 (Functional Specifications)

### 4.1. 데이터 엔지니어링 (Data Engineering)
- **도구:** DuckDB
- **기능:** 
    - 로컬 CSV/Parquet 파일에 대한 고성능 SQL 쿼리 수행.
    - **피처 생성:**
        - **User Features:** 최근 4주 평균 구매 시간대, 선호 카테고리, Recency(구매 주기).
        - **Item Features:** 최근 1주 판매 순위(Popularity), 상품별 주 구매 시간대.
    - **결과물:** `user_features`, `item_features` 테이블.

### 4.2. 후보군 생성 (Candidate Generation)
- **로직:**
    1. **Item-based CF:** 유저의 최근 구매 상품과 유사한 상품 추천.
    2. **Popularity:** 현재 가장 인기 있는 Top 50 상품 추천.
- **목표:** 전체 상품(10만+ 개) 중 유저별 연산 가능한 수준으로 1차 필터링.

### 4.3. 랭킹 모델링 (Ranking Model)
- **알고리즘:** LightGBM
- **입력:** (User, Item, Time) 조합.
- **출력:** 구매 확률 (0~1).
- **학습 목표:** 유저가 실제로 구매할 확률이 높은 순서대로 상품 랭킹 산출.
- **평가 지표:** Hit Rate (실제 구매 시각 vs 모델 추천 시각/상품 일치도).

### 4.4. 로컬 서빙 & 푸시 시뮬레이션 (Local Serving & Push)
- **기능:** `predict(user_id)` 실행 시 최적 상품 및 발송 시각 결정.
- **시나리오 예시:** "User A에게 오늘 오후 7시에 '스키니 진' 푸시 발송 시 구매 확률 최고."
- **저장:** 결과를 텍스트 파일 또는 SQLite에 기록.

### 4.5. 가상 유저 시뮬레이션 (Virtual User Project w/ LLM)
- **도구:** Ollama (Llama 3 모델 활용)
- **기능:** 
    - H&M 유저 메타데이터 기반 페르소나 생성 (예: "파스텔톤 선호 20대 직장인").
    - **실험 (A/B Test):**
        - **Group A (Control):** 인기 상품 + 임의 시각 발송.
        - **Group B (Test):** 랭킹 모델 추천 상품 + 최적 시각 발송.
    - **반응 수집:** LLM 에이전트에게 푸시 내용을 제시하고 클릭 여부(Yes/No) 응답 수집.

### 4.6. 분석 및 리포팅 (Analysis & Reporting)
- **통계 검증:** 수집된 클릭 데이터를 바탕으로 카이제곱 검정(Chi-square test) 수행하여 통계적 유의성 확보.
- **대시보드:** Streamlit을 활용하여 모델 성능 및 A/B 테스트 결과 시각화.

## 5. 기술 스택 (Technology Stack)
| 구분 | 기술 | 설명 |
| :--- | :--- | :--- |
| **Data Engine** | DuckDB | 대용량 데이터 SQL 처리 (Infra-less) |
| **Language** | Python (Polars/Pandas) | 데이터 처리 및 로직 구현 |
| **ML Model** | LightGBM | 추천 랭킹 모델 |
| **Tracking** | MLflow | 실험 관리 및 파라미터 트래킹 |
| **Simulation** | Ollama (Llama 3) | 가상 유저 페르소나 및 행동 시뮬레이션 |
| **Statistics** | SciPy / Statsmodels | A/B 테스트 통계 분석 |
| **Reporting** | Streamlit | 결과 대시보드 및 문서화 |
