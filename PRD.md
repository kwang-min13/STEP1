# Project Requirements Document (PRD): Local-Helix (Commerce Edition)

## 1. 프로젝트 개요 (Project Overview)
**프로젝트명:** Local-Helix (Commerce Edition)
**한줄 소개:** 유저 구매 이력 기반의 시계열 푸시 타겟팅 및 랭킹 엔진 구현 프로젝트
**목표:**
- 로컬 환경(비용 0원)에서 대용량 데이터(3,100만 건)를 처리하여 추천/랭킹 모델 역량 증명.
- H&M 구매 데이터를 활용하여 "어떤 상품을, 몇 시에 추천(푸시)할 것인가"를 결정하는 로직 구현.
- DuckDB와 LightGBM을 활용한 효율적인 추천 시스템 아키텍처 설계.

## 2. 데이터셋 및 환경 (Dataset & Environment)
### 2.1 데이터셋
- **출처:** [Kaggle H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data)
- **규모:** 약 3,100만 건의 트랜잭션 데이터.
- **특징:** 유저 ID, 상품 ID, 구매 시각(Timestamp) 포함 → 시계열 분석 및 푸시 최적화 실험 가능.

### 2.2 개발 환경
- **로컬 머신:** Python 환경 (노트북 등)
- **필수 라이브러리:**
  - **DuckDB:** 서버 없는 인메모리 OLAP DB, 대용량 SQL 처리.
  - **Python:** Polars/Pandas (데이터 조작).
  - **LightGBM:** 랭킹 모델 학습.
  - **MLflow:** 실험 추적 및 모델 관리.
  - **Jupyter / Quarto:** 분석 리포트 및 문서화.

## 3. 핵심 기능 및 워크플로우 (Core Features & Workflow)

### Phase 1: Data Engineering (SQL with DuckDB)
- **목표:** 로컬 파일(CSV/Parquet)을 DuckDB에 연결하여 SQL 기반 피처 엔지니어링 수행.
- **주요 작업:**
  - **User Features:** 최근 4주 평균 구매 시간대, 선호 카테고리, Recency(구매 주기).
  - **Item Features:** 최근 1주 판매 순위(Popularity), 주 구매 시간대.
  - **Feature Store:** `user_features`, `item_features` 테이블 생성 및 관리.

### Phase 2: Candidate Generation (1차 필터링)
- **목표:** 전체 상품(10만+) 중 유저별 추천 후보군 50개 선정.
- **로직:**
  - **Item-based CF:** 최근 구매 상품과 유사한 상품.
  - **Popularity:** 현재 인기 Top 50 상품.
- **의의:** 대규모 탐색 공간을 효율적으로 줄이는 추천 시스템 기본기 구현.

### Phase 3: Ranking Model (LightGBM)
- **목표:** 후보군 50개 중 실제 구매 확률(Rank) 예측.
- **모델:** LightGBM Ranker 또는 Binary Classifier.
- **입력:** (User, Item, Time) 조합.
- **출력:** 구매 확률(Score) 0~1.
- **평가 지표:** Hit Rate (실제 구매가 상위 랭킹에 포함되었는지).

### Phase 4: Local Serving Simulation (Push Optimization)
- **목표:** 유저별 최적 푸시 시간 및 상품 제안.
- **기능:** `predict(user_id)` 실행 시 예측 결과 반환.
- **출력 예시:**
  > "User A에게 오늘 **오후 7시**에 **'스키니 진'** 푸시 발송 시 구매 확률 **최대**"
- **저장:** 결과를 Text 또는 SQLite로 저장하여 서빙 시뮬레이션.

## 4. 기술적 차별점 (Key Selling Points)
본 프로젝트는 단순한 모델링을 넘어 "실무형 엔지니어링 역량"을 강조합니다.
1.  **Cost Efficiency:** DuckDB를 활용한 "서버비 0원" 대용량 데이터 처리 아키텍처.
2.  **Business Logic:** 단순 추천을 넘어 "언제 보낼 것인가(Time Optimization)"를 포함한 비즈니스 문제 해결.
3.  **Ranking implementation:** Candidates → Ranking의 2-Stage 추천 시스템 파이프라인 정석 구현.

## 5. 산출물 (Deliverables)
1.  **Github Repository:** 소스 코드, SQL 쿼리, 모델링 노트북.
2.  **Analysis Report:** EDA 결과 및 모델 성능 리포트 (Quarto/Jupyter).
3.  **Demo Script:** `predict()` 함수 시연 및 결과 로그.
