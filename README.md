# Local-Helix (Commerce Edition)

**유저 구매 이력 기반의 시계열 푸시 타겟팅 및 랭킹 엔진**

## 프로젝트 소개
이 프로젝트는 H&M의 실제 구매 데이터(3,100만 건)를 활용하여, 로컬 환경(비용 0원)에서 동작하는 **개인화 추천 및 푸시 최적화 시스템**의 MVP(Minimum Viable Product)를 구축하는 것을 목표로 합니다.

## 핵심 목표
1.  **비용 효율성:** DuckDB를 활용하여 별도의 서버 구축 없이 대용량 데이터를 처리합니다.
2.  **비즈니스 최적화:** 단순 상품 추천을 넘어, "언제(When)" 푸시를 보낼지에 대한 시계열 최적화를 수행합니다.
3.  **랭킹 모델링:** LightGBM을 사용하여 구매 확률 기반의 정교한 랭킹 시스템을 구현합니다.

## 기술 스택
-   **Data Engine:** DuckDB (SQL)
-   **Language:** Python (Polars/Pandas)
-   **Model:** LightGBM (Ranking)
-   **Tracking:** MLflow
-   **Report:** Jupyter / Quarto

## 프로젝트 구조
-   `TASKS.md`: 프로젝트 진행 상황 및 할 일 목록
-   `PRD.md`: 상세 기획서 (제품 요구 사항 정의)
-   `projects/`: 아이디어 및 기획 노트

## 시작하기
(추후 업데이트 예정: 설치 및 실행 방법)
