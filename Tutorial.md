# AI-Driven Development Tutorial: Local-Helix Project

이 문서는 **Local-Helix (Commerce Edition)** 프로젝트가 AI와의 협업을 통해 어떻게 기획되고 초기화되었는지를 기록한 튜토리얼입니다.  
프로젝트의 현재 상태(PRD, Task List, Folder Structure)를 만들어내기 위해 사용된 **프롬프트(Prompt)**와 사고 과정을 중심으로 정리했습니다.

---

## 1. 프로젝트 기획 (Defining the Goal)

가장 먼저 모호한 아이디어를 구체적인 요구사항 문서(PRD)로 변환하는 단계입니다.

### 🎯 목표
"서버 비용 없이 로컬 환경에서 3천만 건의 데이터를 처리하는 추천 시스템을 만들겠다"는 핵심 아이디어를 AI에게 전달하여 상세 기획서를 작성합니다.

### 💬 사용된 프롬프트 (Prompt)
> **Role:** Senior Data Engineer & PM  
> **Goal:** H&M 데이터를 활용한 패션 추천 및 푸시 최적화 시스템의 PRD(요구사항 정의서)를 작성해줘.  
> **Constraints:**  
> 1. **No Server Cost:** DuckDB를 메인 엔진으로 사용하여 로컬 랩탑에서 돌릴 수 있어야 함.  
> 2. **Model:** LightGBM Ranker 사용.  
> 3. **Validation:** 3,100만 건의 대용량 트랜잭션을 처리할 수 있는 아키텍처 포함.  
> 4. **Output:** `PRD.md` 파일로 작성.  

### 📝 결과물 (Result)
- **`PRD.md`**: 프로젝트의 배경, 목표, 기술 스택, 4단계 워크플로우(Data Engineering -> Candidate -> Ranking -> Serving)가 정의되었습니다.

---

## 2. 작업 세분화 (Actionable Planning)

기획서(PRD)를 바탕으로, 개발자가 실제로 수행할 수 있는 단위 작업(Task)으로 쪼개는 단계입니다.

### 🎯 목표
PRD의 큰 그림을 구체적인 Todo List로 변환하여 `TASKS.md` 로 관리합니다.

### 💬 사용된 프롬프트 (Prompt)
> **Context:** 방금 작성된 `PRD.md`를 바탕으로 개발 진행을 위한 상세 Task List를 작성해줘.  
> **Requirements:**  
> 1. **Step-by-Step:** 초기 환경 설정부터 모델 서빙 시뮬레이션까지 순서대로 나열.  
> 2. **Checklist:** 각 항목은 체크박스(`- [ ]`) 형태여야 함.  
> 3. **Tech Detail:** 각 단계별로 필요한 라이브러리나 기술적 포인트(예: DuckDB SQL, MLflow)를 명시할 것.  
> 4. **Output:** `TASKS.md` 파일로 저장.

### 📝 결과물 (Result)
- **`TASKS.md`**: 프로젝트 초기화 -> 데이터 엔지니어링 -> 후보군 생성 -> 랭킹 모델 -> 서빙 시뮬레이션의 5단계 로드맵이 완성되었습니다.

---

## 3. 프로젝트 초기화 (Initialization)

계획이 섰으니, 실제 폴더 구조와 Git 저장소를 세팅하고 프로젝트를 시작합니다.

### 🎯 목표
기본적인 파일 구조(Scaffold)를 잡고, 프로젝트의 대문인 README를 작성합니다.

### 💬 사용된 프롬프트 (Prompt)
> **Action:** 프로젝트 시작을 위한 초기 파일들을 생성해줘.  
> **Detail:**  
> 1. **Git:** `git init` 명령어를 실행하고, Python 데이터 프로젝트에 적합한 `.gitignore` 생성.  
> 2. **README:** 프로젝트의 한 줄 소개와 핵심 목표를 담은 `README.md` 작성.  
> 3. **Structure:** 필요한 폴더(예: `projects/`) 생성.  

### 📝 결과물 (Result)
- **Folder Structure:** `.git`, `.gitignore`, `projects/` 폴더 생성.
- **`README.md`**: 프로젝트의 정체성을 요약한 문서 생성.

---

## 4. 결론 및 다음 단계 (Next Steps)

이제 이 튜토리얼을 통해 준비된 설계도(PRD, TASKS)를 바탕으로 실제 코딩을 시작할 준비가 되었습니다.
다음 단계는 **`TASKS.md`의 "1단계: 데이터 엔지니어링"**부터 시작하여 DuckDB를 연동하는 것입니다.
