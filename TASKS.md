# TASKS: Local-Helix (Commerce Edition)

## 0. 프로젝트 초기화 (Project Initialization)
- [ ] **Git 저장소 설정**
    - [ ] `git init` 실행 및 `.gitignore` 생성 (Python, DuckDB, Jupyter).
    - [ ] 프로젝트 개요를 포함한 `README.md` 작성.
- [ ] **환경 설정**
    - [ ] 필요 라이브러리 설치: `duckdb`, `pandas`, `polars`, `lightgbm`, `mlflow`, `jupyter`.
    - [ ] H&M 데이터셋 다운로드 (Kaggle에서 수동 다운로드 또는 API 사용).

## 1. 1단계: 데이터 엔지니어링 (SQL with DuckDB)
- [ ] **데이터베이스 연결**
    - [ ] CSV/Parquet 파일을 DuckDB 테이블로 변환 (`users`, `items`, `transactions`).
- [ ] **유저 피처 엔지니어링 (SQL)**
    - [ ] 주요 지표 계산:
        - [ ] 평균 구매 시간대 (최근 4주).
        - [ ] 선호 카테고리 카운트.
        - [ ] Recency (마지막 구매로부터 경과한 일수).
    - [ ] `user_features` 테이블 생성.
- [ ] **상품 피처 엔지니어링 (SQL)**
    - [ ] 주요 지표 계산:
        - [ ] 인기 순위 (최근 1주).
        - [ ] 주 구매 시간대 (최빈값 또는 분포).
    - [ ] `item_features` 테이블 생성.

## 2. 2단계: 후보군 생성 (1차 필터링)
- [ ] **유사도 계산**
    - [ ] 아이템 기반 협업 필터링(Item-based CF) 로직 구현.
- [ ] **휴리스틱 필터링**
    - [ ] 기본값/베이스라인으로 인기 상품 Top 50 선정.
- [ ] **후보군 생성**
    - [ ] 매핑 데이터셋 생성: `user_id` -> `[candidate_item_ids (50)]`.

## 3. 3단계: 랭킹 모델 (LightGBM)
- [ ] **학습 데이터 구축**
    - [ ] 후보군 쌍(pair)에 `user_features`와 `item_features` 결합.
    - [ ] 라벨링: 구매 시 1, 비구매 시 0 (네거티브 샘플링 필요할 수 있음).
- [ ] **모델 학습**
    - [ ] LightGBM Ranker (또는 Classifier) 학습.
    - [ ] MLflow를 활용한 하이퍼파라미터 튜닝 (기초 수준).
- [ ] **평가**
    - [ ] 검증(Validation) 세트를 위한 특정 기간 분리 (예: 최근 1주).
    - [ ] **Hit Rate@12** 또는 **Map@12** 계산.

## 4. 4단계: 로컬 서빙 시뮬레이션
- [ ] **추론 로직**
    - [ ] `predict(user_id)` 함수 구현.
        - [ ] 피처 로드 -> 후보군 생성 -> 점수 예측 -> 정렬.
- [ ] **푸시 최적화 로직**
    - [ ] 유저 이력 또는 상품의 피크 시간을 기반으로 "최적 시간(Best Time)" 결정.
- [ ] **데모 및 리포팅**
    - [ ] 샘플 유저에 대한 시뮬레이션 실행.
    - [ ] 결과를 `push_simulation_results.txt` 또는 SQLite에 저장.
    - [ ] 최종 분석 리포트 작성 (Quarto/Notebook).
