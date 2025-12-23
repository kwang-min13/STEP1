# Project Tasks: Local-Helix (Commerce Edition)

이 문서는 [PRD.md](./PRD.md)에 정의된 요구사항을 구현하기 위한 세부 단계별 태스크 리스트입니다.

## 1. ⚙️ 환경 설정 (Environment Setup)
- [ ] **프로젝트 구조 생성**: 폴더 구조 (`data/`, `notebooks/`, `src/`, `models/`) 생성
- [ ] **라이브러리 설치**: `duckdb`, `polars`, `lightgbm`, `mlflow`, `streamlit` 등 필수 패키지 설치
- [ ] **데이터 다운로드**: Kaggle H&M 데이터셋 다운로드 및 `data/raw/` 위치

## 2. 🗄️ 데이터 엔지니어링 (Data Engineering)
- [ ] **DuckDB 연결 및 로드**: CSV 데이터를 DuckDB 파이프라인으로 연결
- [ ] **User Feature 생성**:
    - [ ] 유저별 최근 4주 평균 구매 시간대 계산
    - [ ] 유저별 선호 카테고리 집계
    - [ ] 유저별 Recency (마지막 구매로부터 경과일) 계산
- [ ] **Item Feature 생성**:
    - [ ] 최근 1주간 판매량 기준 Popularity 랭킹 산출
    - [ ] 상품별 주된 판매 시간대 집계
- [ ] **Feature Store 구축**: 전처리된 데이터를 `user_features.parquet`, `item_features.parquet`으로 저장

## 3. 🎯 후보군 생성 (Candidate Generation)
- [ ] **Popularity 기반 후보군**: 전체 유저 대상 Top 50 인기 상품 리스트 생성
- [ ] **Item-based CF 구현**:
    - [ ] 상품 간 유사도 행렬 계산 (또는 간단한 Co-visitation)
    - [ ] 유저의 최근 구매 이력 기반 유사 상품 추출
- [ ] **후보군 병합**: 유저별 최종 후보군(Candidate) 50~100개 생성

## 4. 🏆 랭킹 모델링 (Ranking Model)
- [ ] **학습 데이터셋 구성**: (User, Item, Time) Feature와 Label(구매여부 1/0) 병합
- [ ] **LightGBM 모델 학습**:
    - [ ] Train/Validation Split (Time-series split 권장)
    - [ ] 모델 학습 및 하이퍼파라미터 튜닝
- [ ] **평가 (Evaluation)**:
    - [ ] Hit Rate @ K 산출 (Validation 셋 기준)
    - [ ] 중요 Feature 중요도(Feature Importance) 분석

## 5. 🚀 로컬 서빙 및 시뮬레이션 (Local Simulation)
- [ ] **Serving 함수 구현**: `predict(user_id)` 입력 시 추천 상품 및 최적 발송 시간 반환
- [ ] **배치 추론 (Batch Inference)**: 전체 타겟 유저에 대한 추천 결과 파일 생성 (`recommendations.db` 또는 csv)

## 6. 🤖 가상 유저 실험 (Virtual User w/ Ollama)
- [ ] **Ollama 연동**: 로컬 Llama 3 모델 API 연결 설정
- [ ] **페르소나 프롬프트 작성**: 유저 메타데이터 기반 페르소나 생성 프롬프트 템플릿 작성
- [ ] **A/B 테스트 시뮬레이터 구현**:
    - [ ] **Group A (Control)**: 인기 상품 제안 -> LLM 응답 수집
    - [ ] **Group B (Test)**: 모델 추천 상품 제안 -> LLM 응답 수집
- [ ] **로그 수집**: 시뮬레이션 결과(클릭 여부) 로깅

## 7. 📊 분석 및 리포팅 (Analysis & Report)
- [ ] **통계 검정**: Python(`scipy`) 활용 A/B 그룹 간 CTR 차이 카이제곱 검정
- [ ] **Streamlit 대시보드 개발**:
    - [ ] 모델 성능 지표 그래프
    - [ ] A/B 테스트 결과 요약 및 시각화
- [ ] **최종 결과 정리**: `README.md` 업데이트 및 보고서 작성
