import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta

# .env 파일 로드
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'))
load_dotenv(dotenv_path=env_path)

# Supabase 클라이언트 초기화
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# Sentence Transformer 모델 초기화 (한국어 특화 모델로 변경)
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def create_embedding(text, metadata):
    # 컨텍스트를 풍부하게 하여 임베딩 생성
    enriched_text = f"{metadata['course']} {metadata['week']} - {text}"
    return model.encode(enriched_text).tolist()

def test_simple_query():
    """기본적인 쿼리 테스트"""
    try:
        # 모든 청크 가져오기
        response = supabase.table('chunks').select("*").limit(5).execute()
        print("\n=== 기본 쿼리 결과 (5개) ===")
        print(json.dumps(response.data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"쿼리 실행 중 오류 발생: {e}")

def get_current_week_range():
    """현재 날짜가 속한 주의 시작일과 종료일을 반환"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')

def test_semantic_search_with_date(query_text: str, limit: int = 5):
    """날짜 정보를 포함한 의미적 검색 테스트"""
    try:
        # 쿼리 텍스트를 임베딩으로 변환
        query_embedding = model.encode(query_text).tolist()
        
        # 현재 주의 날짜 범위 가져오기
        start_date, end_date = get_current_week_range()
        
        # 벡터 검색 쿼리 with 날짜 필터
        response = supabase.rpc(
            'match_chunks_with_date',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.4,
                'match_count': limit,
                'start_date': start_date,
                'end_date': end_date
            }
        ).execute()
        
        print(f"\n=== 이번 주 ({start_date} ~ {end_date}) 의미적 검색 결과 ('{query_text}') ===")
        print(json.dumps(response.data, indent=2, ensure_ascii=False))
        
        # 결과가 없으면 날짜 제한 없이 다시 검색
        if not response.data:
            print("\n=== 전체 기간 검색 결과 ===")
            response = supabase.rpc(
                'match_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.4,
                    'match_count': limit
                }
            ).execute()
            print(json.dumps(response.data, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"의미적 검색 중 오류 발생: {e}")

def test_filtered_query(course_name: str):
    """특정 강좌의 청크만 필터링하여 가져오기"""
    try:
        # 부분 문자열 매칭을 위해 ilike 사용
        response = supabase.table('chunks')\
            .select("*")\
            .ilike('course', f'%{course_name}%')\
            .limit(5)\
            .execute()
        
        print(f"\n=== 강좌 필터링 결과 ('{course_name}') ===")
        print(json.dumps(response.data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"필터링 쿼리 중 오류 발생: {e}")

def test_chunk_types():
    """청크 타입별 통계"""
    try:
        response = supabase.rpc('get_chunk_stats').execute()
        
        print("\n=== 청크 타입별 통계 ===")
        print(json.dumps(response.data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"통계 쿼리 중 오류 발생: {e}")

def test_all_courses():
    """모든 강좌 목록 확인"""
    try:
        response = supabase.table('chunks')\
            .select("course")\
            .order('course')\
            .execute()
        
        # 중복 제거
        unique_courses = list(set(item['course'] for item in response.data))
        
        print("\n=== 등록된 모든 강좌 목록 ===")
        for course in unique_courses:
            print(f"- {course}")
    except Exception as e:
        print(f"강좌 목록 조회 중 오류 발생: {e}")

if __name__ == "__main__":
    # 기본 쿼리 테스트
    #test_simple_query()
    
    # 날짜 기반 의미적 검색 테스트
    #test_semantic_search_with_date("이번주 과제", limit=10)
    
    # 모든 강좌 목록 확인
    #test_all_courses()
    
    # 특정 강좌 필터링 테스트 - 부분 문자열 사용
    test_filtered_query("데이터수집과처리")
    
    # 청크 타입별 통계 테스트
    #test_chunk_types() 