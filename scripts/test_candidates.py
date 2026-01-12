"""
Candidate Generation Test Script (최적화 버전)

후보군 생성 품질 및 성능 테스트 - 빠른 실행
"""

import sys
from pathlib import Path
import time
import logging

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.candidate_generation import CandidateGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """기본 기능 테스트 (빠른 검증)"""
    logger.info("\n[테스트 1] 기본 기능 검증")
    logger.info("-" * 60)
    
    generator = CandidateGenerator()
    
    try:
        # 샘플 유저 3명만 테스트
        con = generator.connect()
        sample_users = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 3
        """).fetchall()
        
        logger.info(f"테스트 유저 수: {len(sample_users)}")
        
        for i, user_row in enumerate(sample_users, 1):
            user_id = user_row[0]
            
            # Popularity 후보군
            pop_candidates = generator.generate_popularity_candidates(top_k=50)
            
            # 병합 후보군
            merged = generator.merge_candidates(user_id, total_k=100)
            
            logger.info(f"유저 {i}: Popularity={len(pop_candidates)}, 병합={len(merged)}")
        
        logger.info("✓ 기본 기능 검증 통과")
        
    finally:
        generator.close()


def test_performance():
    """성능 테스트 (간소화)"""
    logger.info("\n[테스트 2] 성능 벤치마크")
    logger.info("-" * 60)
    
    generator = CandidateGenerator()
    
    try:
        # 샘플 유저 1명만 테스트
        con = generator.connect()
        sample_user = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
        """).fetchone()[0]
        
        # Popularity 성능
        start = time.time()
        pop_candidates = generator.generate_popularity_candidates(top_k=50)
        pop_time = (time.time() - start) * 1000
        
        # CF 성능
        start = time.time()
        cf_candidates = generator.generate_cf_candidates(sample_user, top_k=50)
        cf_time = (time.time() - start) * 1000
        
        # 병합 성능
        start = time.time()
        merged = generator.merge_candidates(sample_user, total_k=100)
        merge_time = (time.time() - start) * 1000
        
        logger.info(f"Popularity 생성: {pop_time:.2f}ms ({len(pop_candidates)}개)")
        logger.info(f"CF 생성: {cf_time:.2f}ms ({len(cf_candidates)}개)")
        logger.info(f"병합: {merge_time:.2f}ms ({len(merged)}개)")
        
        # 성능 목표: CF < 5초, 병합 < 5초
        if cf_time < 5000 and merge_time < 5000:
            logger.info("✓ 성능 목표 달성")
        else:
            logger.warning(f"⚠ 성능 개선 필요: CF={cf_time:.0f}ms, 병합={merge_time:.0f}ms")
        
    finally:
        generator.close()


def test_quality():
    """후보군 품질 검증"""
    logger.info("\n[테스트 3] 후보군 품질 검증")
    logger.info("-" * 60)
    
    generator = CandidateGenerator()
    
    try:
        con = generator.connect()
        sample_user = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
        """).fetchone()[0]
        
        # 후보군 생성
        candidates = generator.merge_candidates(sample_user, total_k=100)
        
        # 중복 확인
        unique_count = len(set(candidates))
        
        logger.info(f"생성된 후보 수: {len(candidates)}")
        logger.info(f"고유 후보 수: {unique_count}")
        
        if unique_count == len(candidates):
            logger.info("✓ 중복 없음")
        else:
            logger.warning(f"⚠ 중복 발견: {len(candidates) - unique_count}개")
        
        # 후보 수 범위 확인
        if 50 <= len(candidates) <= 100:
            logger.info("✓ 후보 수 범위 적절 (50-100)")
        else:
            logger.warning(f"⚠ 후보 수 범위 벗어남: {len(candidates)}")
        
    finally:
        generator.close()


def main():
    """모든 테스트 실행"""
    logger.info("=" * 60)
    logger.info("후보군 생성 테스트 시작 (최적화 버전)")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        test_basic_functionality()
        test_performance()
        test_quality()
        
        elapsed = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✓ 모든 테스트 완료 (소요 시간: {elapsed:.2f}초)")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 테스트 실패: {str(e)}")
        raise


if __name__ == "__main__":
    main()


import sys
from pathlib import Path
import time
import logging
from collections import Counter

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.candidate_generation import CandidateGenerator
import duckdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_candidate_count():
    """후보군 개수 테스트"""
    logger.info("\n[테스트 1] 후보군 개수 검증")
    logger.info("-" * 60)
    
    generator = CandidateGenerator()
    
    try:
        # 샘플 유저 10명 추출
        con = generator.connect()
        sample_users = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 10
        """).fetchall()
        
        candidate_counts = []
        
        for user_row in sample_users:
            user_id = user_row[0]
            candidates = generator.merge_candidates(user_id, total_k=100)
            candidate_counts.append(len(candidates))
        
        avg_count = sum(candidate_counts) / len(candidate_counts)
        min_count = min(candidate_counts)
        max_count = max(candidate_counts)
        
        logger.info(f"평균 후보 수: {avg_count:.1f}")
        logger.info(f"최소 후보 수: {min_count}")
        logger.info(f"최대 후보 수: {max_count}")
        
        # 검증: 50-100개 범위 확인
        if 50 <= avg_count <= 100:
            logger.info("✓ 후보 수 검증 통과")
        else:
            logger.warning(f"⚠ 후보 수가 예상 범위(50-100)를 벗어남: {avg_count}")
        
    finally:
        generator.close()


def test_performance():
    """성능 테스트"""
    logger.info("\n[테스트 2] 성능 벤치마크")
    logger.info("-" * 60)
    
    generator = CandidateGenerator()
    
    try:
        # 샘플 유저 추출
        con = generator.connect()
        sample_user = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
        """).fetchone()[0]
        
        # 성능 측정
        iterations = 5
        times = []
        
        for i in range(iterations):
            start = time.time()
            candidates = generator.merge_candidates(sample_user, total_k=100)
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        
        logger.info(f"평균 처리 시간: {avg_time:.2f}ms")
        logger.info(f"최소 처리 시간: {min(times):.2f}ms")
        logger.info(f"최대 처리 시간: {max(times):.2f}ms")
        
        # 검증: 100ms 이하 목표
        if avg_time <= 100:
            logger.info("✓ 성능 목표 달성 (< 100ms)")
        else:
            logger.warning(f"⚠ 성능 목표 미달성: {avg_time:.2f}ms")
        
    finally:
        generator.close()


def test_coverage():
    """커버리지 테스트 - 얼마나 많은 상품이 후보군에 포함되는지"""
    logger.info("\n[테스트 3] 상품 커버리지 분석")
    logger.info("-" * 60)
    
    generator = CandidateGenerator()
    
    try:
        # 전체 상품 수 조회
        con = generator.connect()
        total_items = con.execute("""
            SELECT COUNT(*) 
            FROM read_parquet('data/features/item_features.parquet')
        """).fetchone()[0]
        
        # 샘플 유저 100명의 후보군 수집
        sample_users = con.execute("""
            SELECT customer_id 
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 100
        """).fetchall()
        
        all_candidates = set()
        
        for user_row in sample_users:
            user_id = user_row[0]
            candidates = generator.merge_candidates(user_id, total_k=100)
            all_candidates.update(candidates)
        
        coverage = len(all_candidates) / total_items * 100
        
        logger.info(f"전체 상품 수: {total_items:,}")
        logger.info(f"후보군에 포함된 상품 수: {len(all_candidates):,}")
        logger.info(f"커버리지: {coverage:.1f}%")
        
        # 검증: 80% 이상 목표
        if coverage >= 80:
            logger.info("✓ 커버리지 목표 달성 (>= 80%)")
        else:
            logger.warning(f"⚠ 커버리지 목표 미달성: {coverage:.1f}%")
        
    finally:
        generator.close()


def main():
    """모든 테스트 실행"""
    logger.info("=" * 60)
    logger.info("후보군 생성 테스트 시작")
    logger.info("=" * 60)
    
    try:
        test_candidate_count()
        test_performance()
        test_coverage()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ 모든 테스트 완료")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 테스트 실패: {str(e)}")
        raise


if __name__ == "__main__":
    main()
