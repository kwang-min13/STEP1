# Local-Helix (Commerce Edition)

**비용 0원, 로컬 랩탑에서 돌리는 3천만 건 데이터 추천 시스템**

## 📌 Project Overview
Local-Helix는 서버 비용 없이 로컬 환경(DuckDB)에서 대용량 데이터를 처리하고, LightGBM Ranker를 활용하여 개인화된 상품 추천 및 푸시 최적화를 수행하는 MVP 프로젝트입니다.
H&M의 실제 트랜잭션 데이터(3,100만 건)를 활용하여 "누구에게, 언제, 무엇을 추천할 것인가"를 결정하는 End-to-End 파이프라인을 구축합니다.

## 🚀 Key Features
- **Infra-less Data Engineering:** DuckDB를 활용하여 별도 DB 서버 없이 로컬에서 OLAP 처리.
- **Purchase-based Ranking:** 단순 유사도가 아닌 '구매 확률'을 예측하는 Ranking Model(LightGBM) 구현.
- **Push Optimization:** 유저별 최적의 푸시 발송 시간대를 산출하여 CTR/Conversion 극대화.
- **Virtual User Simulation:** LLM(Llama 3)을 활용한 가상 유저 페르소나 생성 및 A/B 테스트 시뮬레이션.

## 🛠 Tech Stack
- **Database:** DuckDB
- **Data Processing:** Python, Polars
- **Modeling:** LightGBM, MLflow
- **Simulation:** Ollama (Llama 3)
- **Visualization:** Streamlit

## 📂 Project Structure
```
.
├── projects/          # Ideation & Raw Data Reference
├── scripts/           # Automation Scripts
├── PRD.md             # Project Requirements Document
├── TASKS.md           # Implementation Task List
├── Tutorial.md        # AI Development Log (Tutorial)
└── README.md          # Project Introduction
```

## 🏁 Getting Started
*(Instructions for setting up the environment will be added here)*
