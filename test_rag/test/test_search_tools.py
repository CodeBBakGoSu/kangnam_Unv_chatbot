"""
강남대학교 RAG 검색 도구 테스트

search_tools.py의 각 함수가 어떻게 동작하는지 확인하는 스크립트
"""

from tools.search_tools import (
    search_graduation_requirements,
    search_by_year_and_college,
    get_available_information
)
import json


def print_divider(title=""):
    """구분선 출력"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'-'*70}\n")


def print_result(result, show_full_text=False):
    """검색 결과를 보기 좋게 출력"""
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print(f"📊 결과 개수: {result['count']}")
        
        if "search_params" in result:
            print(f"\n검색 파라미터:")
            print(f"  - top_k: {result['search_params']['top_k']}")
            print(f"  - 유사도 임계값: {result['search_params']['similarity_threshold']}")
        
        if result['count'] > 0:
            print(f"\n검색 결과:")
            for r in result["results"]:
                print(f"\n{'─'*70}")
                print(f"순위 {r['rank']}: 유사도 {r['relevance_percentage']}")
                print(f"{'─'*70}")
                
                # 텍스트 일부만 출력 (또는 전체 출력)
                text = r['text']
                if show_full_text:
                    print(text)
                else:
                    # 처음 300자만
                    print(text[:300])
                    if len(text) > 300:
                        print("...")
                
                if r['source_uri']:
                    print(f"\n📎 출처: {r['source_uri']}")
        else:
            print("\n⚠️  검색 결과가 없습니다.")
    else:
        print(f"❌ {result['message']}")
        if 'error_message' in result:
            print(f"   오류: {result['error_message']}")


# ============================================================================
# 테스트 1: 사용 가능한 정보 확인
# ============================================================================
print_divider("테스트 1: 사용 가능한 정보 확인")
print("📋 get_available_information() 호출\n")

info = get_available_information()
print(f"✅ {info['message']}\n")

print("📚 검색 가능한 대학:")
for college in info['available_data']['colleges']:
    print(f"  - {college}")

print("\n📅 검색 가능한 학년도:")
for year_range in info['available_data']['year_ranges']:
    print(f"  - {year_range}")

print("\n📂 검색 가능한 카테고리:")
for category in info['available_data']['categories']:
    print(f"  - {category}")

print("\n💡 검색 예시:")
for example in info['available_data']['search_examples']:
    print(f"  - \"{example}\"")


# ============================================================================
# 테스트 2: 기본 검색 (search_graduation_requirements)
# ============================================================================
print_divider("테스트 2: 기본 검색 - search_graduation_requirements()")

test_queries = [
    "2024년 입학생 복지융합대학 졸업 요건",
    "공과대학 기초교양 학점",
    "최소 졸업학점은 얼마야?",
]

for i, query in enumerate(test_queries, 1):
    print(f"\n질문 {i}: \"{query}\"")
    print_divider()
    
    result = search_graduation_requirements(
        query=query,
        top_k=3,  # 상위 3개만
        similarity_threshold=0.3  # 30% 이상 유사도
    )
    
    print_result(result, show_full_text=False)


# ============================================================================
# 테스트 3: 구조화된 검색 (search_by_year_and_college)
# ============================================================================
print_divider("테스트 3: 구조화된 검색 - search_by_year_and_college()")

test_cases = [
    {"year": "2024", "college": "복지융합대학", "category": "졸업요건"},
    {"year": "2019", "college": "공과대학", "category": "교양이수표"},
    {"year": "2025", "college": "사범대학", "category": "졸업요건"},
]

for i, case in enumerate(test_cases, 1):
    print(f"\n테스트 케이스 {i}:")
    print(f"  - 입학 연도: {case['year']}")
    print(f"  - 대학: {case['college']}")
    print(f"  - 카테고리: {case['category']}")
    print_divider()
    
    result = search_by_year_and_college(
        year=case['year'],
        college=case['college'],
        category=case['category'],
        top_k=2
    )
    
    if result["status"] == "success" and "search_criteria" in result:
        print(f"🔍 매핑된 검색 조건:")
        print(f"  - 학년도 범위: {result['search_criteria']['year_range']}")
        print(f"  - 실제 쿼리: \"{result['query']}\"\n")
    
    print_result(result, show_full_text=False)


# ============================================================================
# 테스트 4: 다양한 similarity_threshold 비교
# ============================================================================
print_divider("테스트 4: 유사도 임계값 비교")

query = "복지융합대학 졸업학점"
thresholds = [0.2, 0.3, 0.5]

print(f"질문: \"{query}\"\n")

for threshold in thresholds:
    print(f"\n{'─'*70}")
    print(f"유사도 임계값: {threshold} ({threshold*100}% 이상)")
    print(f"{'─'*70}")
    
    result = search_graduation_requirements(
        query=query,
        top_k=10,
        similarity_threshold=threshold
    )
    
    if result["status"] == "success":
        print(f"결과 개수: {result['count']}개")
        if result['count'] > 0:
            print(f"최고 유사도: {result['results'][0]['relevance_percentage']}")
            print(f"최저 유사도: {result['results'][-1]['relevance_percentage']}")
    else:
        print(f"오류: {result.get('error_message', 'Unknown')}")


# ============================================================================
# 테스트 5: 전체 텍스트 출력 예시
# ============================================================================
print_divider("테스트 5: 전체 텍스트 출력 예시")

query = "2021~2024학년도 복지융합대학 인문사회 계열 졸업요건"
print(f"질문: \"{query}\"\n")

result = search_graduation_requirements(
    query=query,
    top_k=1,  # 최상위 1개만
    similarity_threshold=0.2
)

if result["status"] == "success" and result['count'] > 0:
    print_result(result, show_full_text=True)  # 전체 텍스트 출력
else:
    print("결과 없음")


# ============================================================================
# 테스트 완료
# ============================================================================
print_divider("✅ 모든 테스트 완료!")

print("""
🎯 내부 동작 요약:

1. search_graduation_requirements(query):
   - 사용자 질문을 임베딩으로 변환 (자동)
   - 코퍼스 내 모든 chunk와 유사도 계산 (자동)
   - similarity_threshold 이상인 것만 필터링
   - 유사도 순으로 정렬하여 top_k개 반환
   
2. search_by_year_and_college(year, college, category):
   - year를 year_range로 매핑 (2024 → "2021~2024")
   - 구조화된 쿼리 생성
   - search_graduation_requirements() 호출
   
3. get_available_information():
   - 검색 가능한 대학, 학년도, 카테고리 정보 반환
   - 사용자에게 어떤 질문을 할 수 있는지 안내

🔑 핵심 개념:

- 임베딩(Embedding): 텍스트를 숫자 벡터로 변환
  예: "졸업 요건" → [0.23, -0.45, 0.67, ...]
  
- 벡터 유사도: 두 벡터 간의 유사성 측정 (0~1)
  1.0 = 완전 동일
  0.0 = 완전 다름
  
- top_k: 상위 k개 결과만 반환
  
- threshold: 최소 유사도 기준
  낮을수록 더 많은 결과, 높을수록 더 정확한 결과

📌 AI Agent 사용 시:
  AI가 자동으로 적절한 함수를 선택하여 호출합니다.
  예: 사용자가 "2024년 공대 졸업 요건?" 질문
  → AI가 search_by_year_and_college() 자동 호출
  → 결과를 자연어로 변환하여 답변
""")

