# Kaggle H&M 데이터셋 다운로드 가이드

## 📥 데이터 다운로드 방법

### 1. Kaggle 계정 준비
- Kaggle 계정이 없다면 https://www.kaggle.com 에서 회원가입

### 2. 데이터셋 다운로드
1. 다음 링크로 이동: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data
2. "Download All" 버튼 클릭하여 전체 데이터셋 다운로드
3. 다운로드된 ZIP 파일 압축 해제

### 3. 파일 배치
압축 해제 후 다음 파일들을 `data/raw/` 폴더에 복사:

```
data/raw/
├── transactions_train.csv  (약 5GB - 31M 트랜잭션)
├── customers.csv           (약 150MB - 고객 정보)
├── articles.csv            (약 50MB - 상품 정보)
└── images/                 (선택사항 - 상품 이미지)
```

### 4. 필수 파일 확인
다음 3개 파일이 반드시 필요합니다:
- ✅ `transactions_train.csv` - 구매 트랜잭션 데이터
- ✅ `customers.csv` - 고객 메타데이터
- ✅ `articles.csv` - 상품 메타데이터

### 5. 파일 크기 확인
- `transactions_train.csv`: 약 5GB
- `customers.csv`: 약 150MB
- `articles.csv`: 약 50MB

파일 크기가 현저히 작다면 다운로드가 제대로 되지 않은 것일 수 있습니다.

## ⚠️ 주의사항

1. **디스크 공간**: 최소 10GB 이상의 여유 공간 필요
2. **다운로드 시간**: 인터넷 속도에 따라 10분~1시간 소요
3. **압축 해제**: 7-Zip, WinRAR 등의 압축 프로그램 사용 권장

## ✅ 검증

파일 배치 후 다음 명령어로 확인:

```bash
# PowerShell
Get-ChildItem data\raw\ | Select-Object Name, Length

# 또는 Python으로 확인
python -c "from pathlib import Path; print([f.name for f in Path('data/raw').glob('*.csv')])"
```

## 🔗 참고 링크

- Kaggle Competition: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations
- Data Description: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data
