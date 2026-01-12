"""
Environment Validation Script for Local-Helix Project

이 스크립트는 프로젝트 환경이 올바르게 설정되었는지 검증합니다.
- Python 버전 확인
- 필수 패키지 설치 확인
- DuckDB 연결 테스트
- 디렉토리 구조 검증
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Python 버전 확인 (3.10 이상 필요)"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        return True, f"[OK] Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"[FAIL] Python {version.major}.{version.minor}.{version.micro} (3.10+ 필요)"


def check_package(package_name: str) -> Tuple[bool, str]:
    """패키지 설치 여부 확인"""
    try:
        __import__(package_name)
        return True, f"[OK] {package_name}"
    except ImportError:
        return False, f"[FAIL] {package_name} (미설치)"


def check_packages() -> List[Tuple[bool, str]]:
    """필수 패키지 목록 확인"""
    required_packages = [
        'duckdb',
        'polars',
        'pandas',
        'lightgbm',
        'sklearn',
        'mlflow',
        'scipy',
        'statsmodels',
        'streamlit',
        'matplotlib',
        'seaborn',
        'jupyter',
        'requests',
        'tqdm'
    ]
    
    results = []
    for package in required_packages:
        results.append(check_package(package))
    
    return results


def check_duckdb_connection() -> Tuple[bool, str]:
    """DuckDB 연결 테스트"""
    try:
        import duckdb
        con = duckdb.connect(':memory:')
        result = con.execute("SELECT 'DuckDB OK' as test").fetchone()
        con.close()
        return True, f"[OK] DuckDB 연결 성공: {result[0]}"
    except Exception as e:
        return False, f"[FAIL] DuckDB 연결 실패: {str(e)}"


def check_directory_structure() -> List[Tuple[bool, str]]:
    """프로젝트 디렉토리 구조 확인"""
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/features',
        'notebooks',
        'src/data',
        'src/models',
        'src/simulation',
        'src/analysis',
        'src/utils',
        'models/artifacts',
        'logs',
        'reports'
    ]
    
    results = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            results.append((True, f"[OK] {dir_path}"))
        else:
            results.append((False, f"[FAIL] {dir_path} (미생성)"))
    
    return results


def check_ollama() -> Tuple[bool, str]:
    """Ollama 설치 및 실행 확인 (선택사항)"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            if 'llama3' in result.stdout:
                return True, "[OK] Ollama 설치됨 (llama3 모델 사용 가능)"
            else:
                return True, "[WARN] Ollama 설치됨 (llama3 모델 미설치)"
        else:
            return False, "[FAIL] Ollama 실행 실패"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "[WARN] Ollama 미설치 (Phase 6에서 필요)"


def main():
    """환경 검증 메인 함수"""
    print("=" * 60)
    print("Local-Helix 환경 검증 시작")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # 1. Python 버전 확인
    print("1. Python 버전 확인")
    passed, msg = check_python_version()
    print(f"   {msg}")
    all_passed = all_passed and passed
    print()
    
    # 2. 필수 패키지 확인
    print("2. 필수 패키지 확인")
    package_results = check_packages()
    for passed, msg in package_results:
        print(f"   {msg}")
        all_passed = all_passed and passed
    print()
    
    # 3. DuckDB 연결 테스트
    print("3. DuckDB 연결 테스트")
    passed, msg = check_duckdb_connection()
    print(f"   {msg}")
    all_passed = all_passed and passed
    print()
    
    # 4. 디렉토리 구조 확인
    print("4. 디렉토리 구조 확인")
    dir_results = check_directory_structure()
    for passed, msg in dir_results:
        print(f"   {msg}")
        all_passed = all_passed and passed
    print()
    
    # 5. Ollama 확인 (선택사항)
    print("5. Ollama 확인 (선택사항)")
    passed, msg = check_ollama()
    print(f"   {msg}")
    # Ollama는 선택사항이므로 전체 결과에 영향 없음
    print()
    
    # 최종 결과
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] 모든 필수 검증 통과!")
        print("환경 설정이 완료되었습니다.")
    else:
        print("[FAILED] 일부 검증 실패")
        print("위의 실패 항목을 확인하고 설치해주세요.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
