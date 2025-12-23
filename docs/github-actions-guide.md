# GitHub Actions 워크플로우 상세 가이드

이 문서는 `.github/workflows/marp-deploy.yml` 파일의 내용을 대학생도 쉽게 이해할 수 있도록 상세하게 설명합니다.

## 📚 목차
1. [GitHub Actions란?](#github-actions란)
2. [워크플로우 전체 구조](#워크플로우-전체-구조)
3. [코드 라인별 상세 설명](#코드-라인별-상세-설명)
4. [실행 흐름도](#실행-흐름도)

---

## GitHub Actions란?

**GitHub Actions**는 GitHub에서 제공하는 CI/CD(Continuous Integration/Continuous Deployment) 자동화 도구입니다.

### 쉽게 말하면?
- 코드를 푸시하면 자동으로 테스트, 빌드, 배포를 해주는 로봇 🤖
- 여러분이 직접 서버에 접속해서 명령어를 입력할 필요 없이, GitHub가 대신 해줍니다

### 우리 프로젝트에서는?
Markdown으로 작성한 프레젠테이션(`presentation.md`)을 HTML로 변환하고, 웹사이트로 배포하는 과정을 자동화합니다.

---

## 워크플로우 전체 구조

```
┌─────────────────────────────────────┐
│  코드를 main 브랜치에 push          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  GitHub Actions 워크플로우 시작     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Job 1: Build (빌드 작업)           │
│  ├─ 코드 다운로드                   │
│  ├─ Node.js 설치                    │
│  ├─ Marp CLI 설치                   │
│  ├─ Markdown → HTML 변환            │
│  └─ 결과물 업로드                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Job 2: Deploy (배포 작업)          │
│  └─ GitHub Pages에 배포             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  웹사이트 완성! 🎉                  │
│  https://username.github.io/repo/   │
└─────────────────────────────────────┘
```

---

## 코드 라인별 상세 설명

### 1. 워크플로우 이름 설정

```yaml
name: Deploy Marp Presentation to GitHub Pages
```

**설명:**
- 이 워크플로우의 이름을 정의합니다
- GitHub의 "Actions" 탭에서 이 이름으로 표시됩니다

**비유:** 프로그램의 제목 같은 것입니다

---

### 2. 트리거 설정 (언제 실행할까?)

```yaml
on:
  push:
    branches:
      - main
  workflow_dispatch:
```

**설명:**
- `on`: 워크플로우가 실행되는 조건을 정의
- `push`: Git push 이벤트가 발생했을 때
- `branches: - main`: main 브랜치에 푸시했을 때만 실행
- `workflow_dispatch`: GitHub 웹사이트에서 수동으로도 실행 가능

**예시:**
```
git push origin main  ← 이 명령어를 실행하면 워크플로우가 자동 시작!
```

**비유:** 
- `push`: 자동문의 센서 (누군가 지나가면 자동으로 열림)
- `workflow_dispatch`: 수동 버튼 (직접 눌러서 열 수도 있음)

---

### 3. 권한 설정

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

**설명:**
- 워크플로우가 GitHub에서 할 수 있는 작업의 권한을 정의
- `contents: read`: 저장소의 코드를 읽을 수 있음
- `pages: write`: GitHub Pages에 배포할 수 있음
- `id-token: write`: 인증 토큰을 생성할 수 있음

**비유:** 
건물 출입증의 권한 레벨
- 읽기 권한 = 구경만 가능
- 쓰기 권한 = 수정 가능

---

### 4. 동시 실행 제어

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false
```

**설명:**
- `group`: 같은 그룹의 워크플로우는 동시에 하나만 실행
- `cancel-in-progress: false`: 이미 실행 중인 워크플로우가 있어도 취소하지 않음

**예시 상황:**
```
1. 첫 번째 push → 워크플로우 A 시작 (진행 중...)
2. 두 번째 push → 워크플로우 B 대기 (A가 끝날 때까지)
3. A 완료 → B 시작
```

**비유:** 
화장실 한 칸 - 한 명이 사용 중이면 다음 사람은 기다려야 함

---

### 5. Job 1: Build (빌드 작업)

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
```

**설명:**
- `jobs`: 실행할 작업들의 목록
- `build`: 첫 번째 작업의 이름
- `runs-on: ubuntu-latest`: Ubuntu Linux 최신 버전에서 실행

**비유:** 
작업을 수행할 컴퓨터를 빌려오는 것
- GitHub가 클라우드에 Ubuntu 컴퓨터를 준비해줌

---

#### Step 1: 코드 다운로드

```yaml
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
```

**설명:**
- `steps`: 작업 내의 세부 단계들
- `name`: 이 단계의 이름
- `uses`: 다른 사람이 만든 액션(도구)을 사용
- `actions/checkout@v4`: GitHub 저장소의 코드를 다운로드하는 공식 액션

**실제로 하는 일:**
```bash
# 이것과 비슷한 작업을 자동으로 수행
git clone https://github.com/username/repo.git
cd repo
```

**비유:** 
도서관에서 책을 빌려오는 것

---

#### Step 2: Node.js 설치

```yaml
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
```

**설명:**
- `actions/setup-node@v4`: Node.js를 설치하는 공식 액션
- `with`: 액션에 전달할 옵션
- `node-version: '20'`: Node.js 버전 20을 설치

**왜 필요한가?**
- Marp CLI는 Node.js 기반 프로그램이므로 Node.js가 필요합니다

**비유:** 
게임을 하기 위해 먼저 게임 플랫폼(Steam, Epic)을 설치하는 것

---

#### Step 3: Marp CLI 설치

```yaml
      - name: Install Marp CLI
        run: npm install -g @marp-team/marp-cli
```

**설명:**
- `run`: 직접 명령어를 실행
- `npm install -g`: npm(Node Package Manager)으로 전역 설치
- `@marp-team/marp-cli`: Marp CLI 패키지

**실제로 하는 일:**
```bash
# 터미널에서 이 명령어를 실행하는 것과 동일
npm install -g @marp-team/marp-cli
```

**비유:** 
앱스토어에서 앱을 다운로드하는 것

---

#### Step 4: Markdown을 HTML로 변환

```yaml
      - name: Convert Marp to HTML
        run: marp presentation.md -o index.html --html
```

**설명:**
- `marp`: Marp CLI 명령어
- `presentation.md`: 입력 파일 (Markdown 프레젠테이션)
- `-o index.html`: 출력 파일 이름
- `--html`: HTML 태그를 허용

**실제로 하는 일:**
```
presentation.md (Markdown) → index.html (웹페이지)
```

**비유:** 
한글 문서(.hwp)를 PDF로 변환하는 것

---

#### Step 5: 결과물 업로드

```yaml
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
```

**설명:**
- `actions/upload-pages-artifact@v3`: GitHub Pages용 파일을 업로드하는 액션
- `path: '.'`: 현재 디렉토리의 모든 파일을 업로드

**왜 필요한가?**
- Build Job에서 만든 `index.html`을 Deploy Job에 전달하기 위해

**비유:** 
택배 상자에 물건을 넣어서 다음 단계로 보내는 것

---

### 6. Job 2: Deploy (배포 작업)

```yaml
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
```

**설명:**
- `deploy`: 두 번째 작업의 이름
- `environment`: 배포 환경 설정
  - `name: github-pages`: GitHub Pages 환경
  - `url`: 배포된 사이트의 URL (자동 생성)
- `needs: build`: build 작업이 완료된 후에만 실행

**실행 순서:**
```
Build 완료 → Deploy 시작
```

**비유:** 
조립(Build) 완료 후 → 배송(Deploy)

---

#### Deploy Step: GitHub Pages에 배포

```yaml
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**설명:**
- `actions/deploy-pages@v4`: GitHub Pages에 배포하는 공식 액션
- `id: deployment`: 이 단계의 ID (나중에 참조 가능)

**실제로 하는 일:**
- 업로드된 `index.html`을 GitHub Pages 서버에 배포
- 웹사이트 URL 생성: `https://username.github.io/repo/`

**비유:** 
완성된 웹사이트를 인터넷에 올리는 것 (호스팅)

---

## 실행 흐름도

### 전체 타임라인

```
시간 →

0초: git push origin main
     ↓
5초: GitHub Actions 워크플로우 시작
     ↓
10초: [Build Job 시작]
      - 코드 다운로드 (5초)
      - Node.js 설치 (10초)
      - Marp CLI 설치 (15초)
      - HTML 변환 (3초)
      - 업로드 (2초)
     ↓
45초: [Build Job 완료]
     ↓
50초: [Deploy Job 시작]
      - GitHub Pages 배포 (10초)
     ↓
60초: 배포 완료! 🎉
      웹사이트 접속 가능
```

---

## 💡 핵심 개념 정리

### 1. **워크플로우 (Workflow)**
- 자동화된 작업의 전체 프로세스
- `.github/workflows/` 폴더의 YAML 파일로 정의

### 2. **Job (작업)**
- 워크플로우 내의 독립적인 작업 단위
- 우리 예제: `build`와 `deploy` 두 개의 Job

### 3. **Step (단계)**
- Job 내의 개별 실행 단계
- 순차적으로 실행됨

### 4. **Action (액션)**
- 재사용 가능한 작업 단위
- GitHub Marketplace에서 다운로드 가능
- 예: `actions/checkout`, `actions/setup-node`

---

## 🔍 자주 묻는 질문 (FAQ)

### Q1: 워크플로우가 실행되는지 어떻게 확인하나요?
**A:** GitHub 저장소 → Actions 탭 → 워크플로우 이름 클릭

### Q2: 실패하면 어떻게 되나요?
**A:** 
- GitHub가 이메일로 알림을 보냅니다
- Actions 탭에서 빨간색 X 표시로 확인 가능
- 로그를 확인하여 어느 단계에서 실패했는지 파악

### Q3: 비용이 드나요?
**A:** 
- Public 저장소: 무료
- Private 저장소: 월 2,000분 무료 (초과 시 과금)

### Q4: 로컬에서 테스트할 수 있나요?
**A:** 
- `act`라는 도구를 사용하면 로컬에서 테스트 가능
- 하지만 GitHub에 푸시해서 테스트하는 것이 더 정확함

---

## 📖 더 공부하고 싶다면?

1. **GitHub Actions 공식 문서**
   - https://docs.github.com/en/actions

2. **Marp 공식 문서**
   - https://marp.app/

3. **YAML 문법 배우기**
   - https://yaml.org/

---

## 🎓 학습 팁

1. **작은 변경부터 시작하기**
   - 워크플로우 이름만 바꿔보기
   - 새로운 step 추가해보기

2. **로그 읽는 습관 들이기**
   - Actions 탭에서 각 단계의 로그 확인
   - 에러 메시지를 구글에 검색하기

3. **다른 사람의 워크플로우 참고하기**
   - GitHub에서 인기 있는 저장소의 `.github/workflows/` 폴더 구경
   - 어떤 액션들을 사용하는지 살펴보기

---

**작성일:** 2025-12-23  
**대상:** 대학생 및 GitHub Actions 초보자  
**난이도:** ⭐⭐☆☆☆ (초급~중급)
