---
marp: true
theme: gaia
paginate: true
backgroundColor: #fff
style: |
  section { font-family: 'Arial', sans-serif; }
  h1 { color: #2c3e50; }
  h2 { color: #34495e; }
  strong { color: #e74c3c; }
---

<!-- _class: lead -->

# Local-Helix (Commerce Edition)
## 유저 구매 이력 기반 푸시 타겟팅 및 랭킹 엔진

**Infra-less, Cost $0, High Performance**

---

## 1. 프로젝트 개요 (Overview)

**"누구에게, 언제, 무엇을 추천할 것인가?"**

- **목표**: 서버 비용 없이 로컬 환경에서 3천만 건의 데이터를 처리하는 추천 시스템 구축
- **핵심 가치**:
  - **비용 효율성 (Cost Efficiency)**: DuckDB 활용 (Serverless)
  - **기술 증명 (Tech Proof)**: 대용량 데이터 처리 및 정교한 랭킹 모델링
  - **End-to-End 파이프라인**: 데이터 전처리 -> 모델링 -> 서빙 -> 분석

---

## 2. 왜 Local-Helix인가? (Why Local?)

### 💸 No Server Cost
- 클라우드 비용 0원
- 로컬 랩탑(MacBook/Windows) 하나로 3,100만 건 트랜잭션 처리

### 🚀 High Performance
- **DuckDB**: In-process OLAP DB로 메모리 한계를 극복하는 고성능 쿼리
- **LightGBM**: 빠르고 정확한 랭킹 모델 학습

---

## 3. 데이터셋 및 환경

- **데이터셋**: H&M Personalized Fashion Recommendations (Kaggle)
  - **규모**: 3,100만 건 트랜잭션, 10만+ 상품, 130만+ 유저
- **환경**: Local Python Environment
- **Core Engine**: **DuckDB**

---

## 4. 핵심 파이프라인 (Unified Workflow)

1. **Data Engineering**: DuckDB로 User/Item Feature 생성 (Recency, Popularity 등)
2. **Candidate Generation**: Item-based CF + Popularity (1차 필터링)
3. **Ranking Model**: LightGBM으로 구매 확률(Probability) 예측
4. **Serving & Push**: 최적 상품 + 최적 발송 시간(Time Slot) 결정

---

## 5. 시뮬레이션 및 검증 (A/B Test)

**LLM(Llama 3)을 활용한 가상 유저 테스트**

- **Persona**: 유저 메타데이터 기반 페르소나 생성 ("20대 직장인", "캐주얼 선호")
- **Simulation**:
  - **Group A (Control)**: 인기 상품 랜덤 발송
  - **Group B (Test)**: 개인화 추천 + 최적 시간 발송
- **Metric**: 클릭 여부(CTR) 비교 검증

---

## 6. 기술 스택 (Tech Stack)

| Domain | Tech | Role |
| :--- | :--- | :--- |
| **Data Engine** | **DuckDB** | 대용량 SQL 처리 |
| **Logic** | Python (Polars) | 파이프라인 제어 |
| **Model** | **LightGBM** | 랭킹/추천 모델 |
| **Tracking** | MLflow | 실험 관리 |
| **Sim** | Ollama (Llama 3) | 가상 유저 시뮬레이션 |
| **View** | Streamlit | 대시보드 |

---

<!-- _class: lead -->

# Q&A

**Local-Helix Project**
Recommendation System on your Laptop.
