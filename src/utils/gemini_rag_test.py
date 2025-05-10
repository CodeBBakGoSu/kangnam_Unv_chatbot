import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
import json
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
import tiktoken
import re
from src.etl.course_preprocessor import SimilarityMatcher

# .env 파일 로드
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'))
load_dotenv(dotenv_path=env_path)

# Supabase 클라이언트 초기화
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# Sentence Transformer 모델 초기화 (데이터 저장 시 사용한 것과 동일한 모델)
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# Gemini 설정 (응답 생성용)
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
llm = genai.GenerativeModel('gemini-2.0-flash-001')

# 과목명 매핑 정보
COURSE_NAME_MAPPING = {
    'aiot': 'AIoT소프트웨어',
    'ai': 'AIoT소프트웨어',
    'iot': 'AIoT소프트웨어',
    '데이터수집': '데이터수집과처리',
    '데이터처리': '데이터수집과처리',
    '기계학습': '기계학습전처리',
    '머신러닝': '기계학습전처리',
    '딥러닝': '딥러닝프레임워크',
    '데이터베이스': '데이터베이스실습',
    'db': '데이터베이스실습'
}

class GeminiRAGTest:
    def __init__(self):
        self.similarity_matcher = SimilarityMatcher()
        self.course_data = self._load_course_data()
        self.course_names = self._extract_course_names()
        
    def _load_course_data(self) -> Dict[str, Any]:
        """코스 데이터 로드"""
        try:
            with open(os.path.join(os.path.dirname(__file__), '../../user_data/kangnam_courses_processed.json'), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"코스 데이터 로드 실패: {e}")
            return {"courses": []}

    def _extract_course_names(self) -> List[str]:
        """과목명 추출"""
        course_names = set()
        for course in self.course_data.get("courses", []):
            if "title" in course:
                # 시간 정보만 제거 (마지막 괄호)
                course_name = course["title"]
                if "(" in course_name and ")" in course_name:
                    last_bracket_start = course_name.rfind("(")
                    if last_bracket_start != -1:
                        course_name = course_name[:last_bracket_start].strip()
                course_names.add(course_name)
        return list(course_names)

    def find_course_by_name(self, query: str, threshold: float = 0.15) -> List[Dict[str, Any]]:
        """과목명으로 코스 검색"""
        # 유사도 기반 매칭 수행
        matches = self.similarity_matcher.find_best_matches(query, self.course_names, top_k=5)
        
        # threshold 이상의 매칭만 필터링
        filtered_matches = [(name, score) for name, score in matches if score > threshold]
        
        # 매칭된 과목명에 해당하는 코스 정보 찾기
        results = []
        for course_name, similarity in filtered_matches:
            for course in self.course_data.get("courses", []):
                course_title = course.get("title", "")
                # 시간 정보를 제외한 과목명으로 비교
                if "(" in course_title and ")" in course_title:
                    compare_title = course_title[:course_title.rfind("(")].strip()
                else:
                    compare_title = course_title
                
                if course_name == compare_title:
                    course_info = {
                        "title": course["title"],
                        "similarity_score": similarity,
                        "weeks": course.get("weeks", {}),
                        "notices": course.get("notices", [])
                    }
                    results.append(course_info)
        
        # 유사도 점수로 정렬
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results

    def get_course_info(self, course_name: str) -> Dict[str, Any]:
        """과목 상세 정보 조회"""
        matches = self.find_course_by_name(course_name)
        if not matches:
            return {}
        
        # 가장 유사도가 높은 과목 선택
        best_match = matches[0]
        
        # 주차별 정보 정리
        weeks_info = []
        if "weeks" in best_match and "weeks" in best_match["weeks"]:
            for week in best_match["weeks"]["weeks"]:
                week_info = {
                    "title": week.get("title", ""),
                    "date": week.get("date", ""),
                    "activities": week.get("activities", []),
                    "assignments": week.get("assignments", [])
                }
                weeks_info.append(week_info)
        
        # 공지사항 정리
        notices = best_match.get("notices", [])
        
        return {
            "title": best_match["title"],
            "similarity_score": best_match["similarity_score"],
            "weeks": weeks_info,
            "notices": notices
        }

    def search_course_activities(self, query: str) -> List[Dict[str, Any]]:
        """과목 활동 검색"""
        matches = self.find_course_by_name(query)
        results = []
        
        for match in matches:
            if "weeks" in match and "weeks" in match["weeks"]:
                for week in match["weeks"]["weeks"]:
                    for activity in week.get("activities", []):
                        activity_info = {
                            "course": match["title"],
                            "week": week.get("title", ""),
                            "activity": activity,
                            "date": week.get("date", ""),
                            "similarity_score": match["similarity_score"]
                        }
                        results.append(activity_info)
        
        return results

def normalize_course_name(query: str) -> str:
    """질문에서 과목명을 정규화"""
    # 유사도 기반 매칭 사용
    matcher = SimilarityMatcher()
    courses = get_course_list()
    if not courses:
        return None
        
    matches = matcher.find_best_matches(query, courses, top_k=1)
    if matches and matches[0][1] > 0.15:  # 유사도 임계값
        return matches[0][0]
            
    return None

def get_course_list() -> List[str]:
    """현재 운영 중인 모든 과목 목록 반환"""
    try:
        # chunks 테이블에서 직접 유니크한 과목 목록 조회
        response = supabase.table('chunks')\
            .select('course')\
            .execute()
        
        # 중복 제거 및 정렬
        courses = list(set(item['course'] for item in response.data))
        courses.sort()
        return courses
    except Exception as e:
        print(f"과목 목록 조회 중 오류 발생: {e}")
        return []

def find_most_similar_course(query: str) -> str:
    """유사도 기반으로 가장 유사한 과목명 찾기"""
    if not query:
        return None
        
    try:
        # 1. 먼저 축약어/단순 문자열 매칭 시도
        response = supabase.table('course_names')\
            .select('original_name, normalized_name, short_name')\
            .execute()
            
        if not response.data:
            return None
            
        # 축약어 매칭
        query_lower = query.lower()
        for course in response.data:
            # short_name은 '/'로 구분된 여러 축약어를 포함
            short_names = course['short_name'].lower().split('/')
            if any(query_lower in name or name in query_lower for name in short_names):
                return course['original_name']
            
            # 정규화된 이름으로도 매칭 시도
            if query_lower in course['normalized_name'].lower():
                return course['original_name']
        
        # 2. 문자열 매칭이 실패하면 임베딩 기반 검색
        query_embedding = embedding_model.encode(query).tolist()
        
        response = supabase.rpc(
            'match_course_name',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,  # 임계값을 조금 낮춤
                'match_count': 1
            }
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['original_name']
        
        return None
    except Exception as e:
        print(f"과목명 검색 중 오류 발생: {e}")
        return None

def normalize_query(query: str) -> str:
    """질문을 정규화하고 구조화"""
    # 과목명 찾기
    course_name = find_most_similar_course(query)
    if not course_name:
        return query
        
    # 시간 관련 키워드 처리
    time_keywords = {
        '다음주': 'next_week',
        '이번주': 'this_week',
        '저번주': 'last_week',
        '다음 주': 'next_week',
        '이번 주': 'this_week',
        '저번 주': 'last_week'
    }
    
    normalized_query = query
    for keyword, replacement in time_keywords.items():
        if keyword in query:
            normalized_query = f"{course_name} 수업 {replacement}"
            return normalized_query
            
    # 일반적인 수업 내용 질문
    if '뭐' in query and ('배워' in query or '해' in query):
        normalized_query = f"{course_name} 수업 내용"
    elif '언제' in query:
        normalized_query = f"{course_name} 수업 시간"
    elif '과제' in query:
        normalized_query = f"{course_name} 과제"
    
    return normalized_query

def get_current_week_info() -> dict:
    """현재 날짜 기준으로 이번주 정보 반환"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    return {
        'today': today.strftime('%Y-%m-%d'),
        'weekday': today.strftime('%A'),
        'week_start': monday.strftime('%Y-%m-%d'),
        'week_end': sunday.strftime('%Y-%m-%d'),
        'current_time': today.strftime('%H:%M')
    }

def get_relevant_chunks(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """벡터 DB에서 관련 청크 검색"""
    try:
        # 쿼리 텍스트를 임베딩으로 변환 (Sentence Transformer 사용)
        query_embedding = embedding_model.encode(query).tolist()
        
        # 벡터 검색 쿼리
        response = supabase.rpc(
            'match_chunks',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.4,
                'match_count': limit
            }
        ).execute()
        return response.data
    except Exception as e:
        print(f"청크 검색 중 오류 발생: {e}")
        return []

def format_context(chunks: List[Dict[str, Any]]) -> str:
    """검색된 청크들을 컨텍스트로 포맷팅"""
    context = "다음은 관련된 강의 정보입니다:\n\n"
    
    for chunk in chunks:
        context += f"강좌: {chunk['course']}\n"
        context += f"주차: {chunk['week']}\n"
        context += f"내용: {chunk['content']}\n"
        if chunk.get('metadata'):
            if chunk['metadata'].get('date'):
                context += f"날짜: {chunk['metadata']['date']}\n"
            if chunk['metadata'].get('due_date'):
                context += f"제출기한: {chunk['metadata']['due_date']}\n"
        context += "\n"
    
    return context

def count_tokens(text: str) -> int:
    """Gemini API를 사용하여 텍스트의 토큰 수를 계산"""
    try:
        response = llm.count_tokens(text)
        return response.total_tokens
    except Exception as e:
        print(f"토큰 계산 중 오류 발생: {e}")
        return 0

def generate_response(query: str, context: str) -> str:
    """Gemini를 사용하여 응답 생성"""
    # 현재 시간 정보 가져오기
    time_info = get_current_week_info()
    
    prompt = f"""
당신은 강남대학교 학생들을 위한 학습 도우미입니다.
주어진 컨텍스트를 기반으로 학생의 질문에 답변해주세요.
모르는 내용이나 컨텍스트에 없는 내용에 대해서는 모른다고 말씀해주세요.

현재 시간 정보:
- 오늘 날짜: {time_info['today']} ({time_info['weekday']})
- 이번주 기간: {time_info['week_start']} ~ {time_info['week_end']}
- 현재 시각: {time_info['current_time']}

컨텍스트:
{context}

학생의 질문: {query}

답변 시 참고사항:
1. "이번주"는 {time_info['week_start']}부터 {time_info['week_end']}까지를 의미합니다.
2. 과제나 수업 일정이 이번주에 해당하는지 날짜를 확인해주세요.
3. 날짜 정보가 있는 경우, 현재 날짜 기준으로 남은 기간도 알려주세요.

답변을 한국어로 작성해주세요.
답변에는 다음 정보들을 포함해주세요:
1. 관련 강좌명
2. 해당 주차
3. 구체적인 내용이나 과제
4. 날짜나 기한 정보 (있는 경우)
"""
    
    try:
        response = llm.generate_content(prompt)
        
        # 토큰 사용량 출력
        print("\n토큰 사용량:")
        if hasattr(response, 'usage_metadata'):
            print(f"프롬프트 토큰: {response.usage_metadata.prompt_token_count}")
            print(f"응답 토큰: {response.usage_metadata.candidates_token_count}")
            print(f"총 토큰: {response.usage_metadata.total_token_count}")
        else:
            # 토큰 수를 직접 계산
            prompt_tokens = count_tokens(prompt)
            response_tokens = count_tokens(response.text)
            print(f"프롬프트 토큰: {prompt_tokens}")
            print(f"응답 토큰: {response_tokens}")
            print(f"총 토큰: {prompt_tokens + response_tokens}")
        
        return response.text
    except Exception as e:
        print(f"응답 생성 중 오류 발생: {e}")
        return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."

def print_chunks_summary(chunks: List[Dict[str, Any]]) -> None:
    """검색된 청크들의 요약 정보 출력"""
    time_info = get_current_week_info()
    print(f"\n현재 날짜: {time_info['today']} ({time_info['weekday']})")
    print(f"이번주: {time_info['week_start']} ~ {time_info['week_end']}")
    print("\n검색된 관련 정보:")
    print("-" * 30)
    for i, chunk in enumerate(chunks, 1):
        print(f"[청크 {i}]")
        print(f"강좌: {chunk['course']}")
        print(f"주차: {chunk['week']}")
        if chunk.get('metadata') and chunk['metadata'].get('date'):
            date = chunk['metadata']['date']
            print(f"날짜: {date}")
            # 이번주 해당 여부 표시
            if time_info['week_start'] <= date <= time_info['week_end']:
                print("※ 이번주 해당")
        print("-" * 30)

def normalize_course_name_with_llm(query: str, user_courses: List[Dict[str, Any]]) -> str:
    """LLM을 사용하여 사용자 입력에서 과목명 추론"""
    # 사용자의 과목 목록 추출 (분반 정보 포함)
    course_names = [
        course["title"].split("(")[0].strip()  # 시간 정보 제외
        for course in user_courses
        if "title" in course
    ]
    
    print("\n=== 과목명 추출 디버깅 ===")
    print(f"총 과목 수: {len(course_names)}")
    print("추출된 과목명 목록:")
    for i, name in enumerate(course_names, 1):
        print(f"{i}. {name}")
    print("=" * 30)
    
    prompt = f"""
당신은 대학교 학생의 수강 과목을 찾아주는 도우미입니다.
학생이 수강 중인 과목 목록입니다:
{', '.join(course_names)}

학생의 입력: "{query}"

위 과목 목록 중에서 학생이 언급한 과목을 찾아주세요.

다음과 같은 패턴을 고려하여 매칭해주세요:
1. 정확한 과목명과 일치하는 경우
2. 과목명의 축약어나 별칭 (예: 첫 글자들을 조합, 주요 단어의 첫 글자 조합 등)
3. 과목명의 일부만 언급된 경우
4. 영문 약자가 한글로 쓰인 경우나 그 반대의 경우

출력 규칙:
- 매칭된 경우: 정확한 과목명만 한 줄로 출력
- 매칭되지 않은 경우: "없음"

답변:"""

    try:
        response = llm.generate_content(prompt)
        normalized_name = response.text.strip()
        print(f"\nLLM 응답: {normalized_name}")
        
        if normalized_name == "없음":
            print("매칭 실패: 과목명이 없음")
            return None
            
        # 정규화된 과목명으로 시작하는 과목 찾기
        for course in user_courses:
            course_title = course["title"].split("(")[0].strip()
            if course_title.startswith(normalized_name) or normalized_name.startswith(course_title):
                print(f"매칭 성공: {course['title']}")
                return course["title"]
        
        print("매칭 실패: 전체 과목명 찾기 실패")
        return None
    except Exception as e:
        print(f"과목명 정규화 중 오류 발생: {e}")
        return None

def rag_query(query: str) -> str:
    """RAG 파이프라인 실행"""
    print(f"\n원본 질문: {query}")
    
    # 사용자의 과목 데이터 로드
    try:
        with open(os.path.join(os.path.dirname(__file__), '../../user_data/kangnam_courses_processed.json'), 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            user_courses = user_data.get("courses", [])
    except Exception as e:
        print(f"사용자 과목 데이터 로드 실패: {e}")
        return "죄송합니다. 사용자 과목 정보를 불러올 수 없습니다."
    
    # LLM으로 과목명 정규화
    normalized_course = normalize_course_name_with_llm(query, user_courses)
    if normalized_course:
        print(f"정규화된 과목명: {normalized_course}")
    else:
        print("매칭되는 과목을 찾을 수 없습니다.")
    
    # 정규화된 과목명으로 검색
    relevant_chunks = get_relevant_chunks(normalized_course if normalized_course else query)
    
    # 검색 결과가 없는 경우
    if not relevant_chunks:
        return "죄송합니다. 관련된 정보를 찾을 수 없습니다."
    
    # 검색된 청크 요약 출력
    print_chunks_summary(relevant_chunks)
    
    # 컨텍스트 포맷팅
    context = format_context(relevant_chunks)
    print(f"컨텍스트 토큰 수: {count_tokens(context)}")
    
    print("응답 생성 중...")
    # 응답 생성
    response = generate_response(query, context)
    
    return response

def test_rag():
    """RAG 시스템 테스트"""
    test_queries = [
        "캡스톤 디자인 수업 교수님이 누구야?",
        "데베실 과제 있어?",
        "기계학습 다음주에 뭐해?",
        "aiot 수업 언제야?"
    ]
    
    for query in test_queries:
        print(f"\n질문: {query}")
        print("-" * 50)
        response = rag_query(query)
        print(f"답변: {response}")
        print("=" * 50)

if __name__ == "__main__":
    test_rag() 