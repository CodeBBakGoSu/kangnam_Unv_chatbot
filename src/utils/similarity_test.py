from course_preprocessor import SimilarityMatcher
import json

def load_real_courses():
    """실제 과목 데이터 로드"""
    try:
        with open('user_data/kangnam_courses_processed.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 중복 제거하여 과목명만 추출
            course_names = set()
            for course in data:
                if isinstance(course, dict) and 'course_name' in course:
                    course_names.add(course['course_name'])
            return list(course_names)
    except Exception as e:
        print(f"과목 데이터 로드 실패: {e}")
        return []

def test_similarity_matcher():
    # 실제 과목 데이터 로드
    course_names = load_real_courses()
    if not course_names:
        print("실제 과목 데이터를 찾을 수 없어 테스트 데이터를 사용합니다.")
        course_names = [
            "데이터수집과처리",
            "데이터베이스실습",
            "데이터마이닝",
            "데이터시각화",
            "AIoT소프트웨어"
        ]
    else:
        print(f"로드된 과목 수: {len(course_names)}")
    
    # SimilarityMatcher 인스턴스 생성
    matcher = SimilarityMatcher()
    
    # 테스트 케이스들
    test_cases = [
        "데수처",  # 데이터수집과처리와 매칭되어야 함
        "데베실",  # 데이터베이스실습과 매칭되어야 함
        "데마",    # 데이터마이닝과 매칭되어야 함
        "aiot",   # AIoT소프트웨어와 매칭되어야 함
        "인공지능", # 인공지능 관련 과목들과 매칭되어야 함
    ]
    
    print("\n=== 유사도 매칭 테스트 ===")
    for query in test_cases:
        print(f"\n입력 쿼리: {query}")
        matches = matcher.find_best_matches(query, course_names, top_k=3)
        for course_name, score in matches:
            print(f"- {course_name}: {score:.3f}")

if __name__ == "__main__":
    test_similarity_matcher() 