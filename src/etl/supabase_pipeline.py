import json
import os
import uuid
import re
from typing import List, Dict, Any, Tuple
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# 명시적으로 .env 파일 경로 설정
# .env 파일에서 환경 변수 로드
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'))
print("Loading env from:", env_path)
load_dotenv(dotenv_path=env_path)

#print(os.environ.get("SUPABASE_URL"))
#print(os.environ.get("SUPABASE_KEY"))

# 환경 변수에서 Supabase 및 OpenAI 설정 가져오기
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # For data insertion, service_role key is often preferred

# Sentence Transformer 모델 초기화 (한국어 특화 모델로 변경)
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def generate_short_names(normalized: str) -> List[str]:
    """다양한 방식으로 과목명 축약"""
    short_names = set()  # 중복 제거를 위해 set 사용
    words = normalized.split()
    
    # 1. 각 단어의 첫 글자 (기본)
    first_chars = ''.join(word[0] for word in words if word)
    short_names.add(first_chars)
    
    # 2. 각 단어의 첫 2글자
    first_two_chars = ''.join(word[:2] for word in words if len(word) >= 2)
    if len(first_two_chars) >= 2:
        short_names.add(first_two_chars)
    
    # 3. 각 단어의 첫 3글자
    first_three_chars = ''.join(word[:3] for word in words if len(word) >= 3)
    if len(first_three_chars) >= 3:
        short_names.add(first_three_chars)
    
    # 4. n글자 단위로 자르기 (2,3,4글자)
    full_text = ''.join(words)
    for n in [2, 3, 4]:
        if len(full_text) >= n:
            chunks = [full_text[i:i+n] for i in range(0, len(full_text), n)]
            short_name = ''.join(chunk[0] for chunk in chunks if chunk)
            if len(short_name) >= 2:  # 최소 2글자 이상인 경우만 추가
                short_names.add(short_name)
    
    # 5. 특수 규칙 (자주 사용되는 축약어)
    special_mappings = {
        '프로그래밍': '프',
        '프레임워크': '프',
        '데이터베이스': '데베',
        '데이터': '데',
        '컴퓨터': '컴',
        '소프트웨어': '소웨',
        '알고리즘': '알고',
        '시스템': '시스',
        '네트워크': '네트',
        '프로젝트': '프로젝',
        '캡스톤': '캡스',
        '디자인': '디자',
        '실습': '실',
        '기계학습': '기학',
        '인공지능': 'AI',
        '딥러닝': '딥',
    }
    
    # 특수 규칙 적용
    for pattern, replacement in special_mappings.items():
        if pattern in normalized:
            # 원본에서 특수 패턴을 찾아서 대체
            modified = normalized.replace(pattern, replacement)
            # 나머지 단어들은 첫 글자만 사용
            other_words = [word for word in words if pattern not in word]
            other_chars = ''.join(word[0] for word in other_words)
            special_short = modified if not other_chars else f"{modified}{other_chars}"
            short_names.add(special_short)
    
    # 6. 연속된 한글 자음으로 변환
    consonants = {
        'ㄱ': ['가', '기', '과'],
        'ㄷ': ['다', '데'],
        'ㅅ': ['소', '시', '수'],
        'ㅈ': ['자', '지'],
        'ㅊ': ['처', '최'],
        'ㅍ': ['프', '파'],
        'ㄹ': ['러', '리', '래'],
    }
    
    for word in words:
        for consonant, syllables in consonants.items():
            for syllable in syllables:
                if word.startswith(syllable):
                    word = word.replace(syllable, consonant, 1)
        if any(c in consonants for c in word):
            short_names.add(word)
    
    return sorted(list(short_names))

def normalize_course_name(course_name: str) -> Tuple[str, str, List[str]]:
    """과목명을 정규화하고 축약명 생성"""
    # [00]과 시간 정보 제거
    normalized = re.sub(r'\[\d+\].*$', '', course_name).strip()
    
    # 다양한 방식으로 축약명 생성
    short_names = generate_short_names(normalized)
    
    # 축약명들을 '/'로 구분하여 하나의 문자열로 결합
    short_names_str = '/'.join(short_names)
    
    return course_name, normalized, short_names_str

def get_unique_courses(supabase_client: Client) -> List[str]:
    """chunks 테이블에서 유니크한 과목명 목록 가져오기"""
    try:
        response = supabase_client.table('chunks')\
            .select('course')\
            .execute()
        
        courses = list(set(item['course'] for item in response.data))
        courses.sort()
        return courses
    except Exception as e:
        print(f"과목 목록 조회 중 오류 발생: {e}")
        return []

def process_course_names(supabase_client: Client):
    """과목명 처리 및 저장"""
    try:
        # 기존 과목 목록 가져오기
        courses = get_unique_courses(supabase_client)
        if not courses:
            print("과목 목록을 가져올 수 없습니다.")
            return
            
        print(f"\n=== 과목명 정규화 시작 ===")
        print(f"총 {len(courses)}개 과목 처리 중...")
        
        # 각 과목명 처리
        for course in courses:
            original, normalized, short_names = normalize_course_name(course)
            
            # 임베딩 생성
            embedding = generate_embedding(normalized)
            if not embedding:
                continue
            
            # Supabase에 저장
            try:
                supabase_client.table('course_names').upsert(
                    {
                        'original_name': original,
                        'normalized_name': normalized,
                        'short_name': short_names,
                        'embedding': embedding
                    },
                    on_conflict='original_name'  # constraint 이름이 아닌 컬럼 이름을 사용
                ).execute()
                
                print(f"처리 완료: {original} -> {normalized} ({short_names})")
            except Exception as e:
                print(f"과목명 '{original}' 저장 중 오류 발생: {e}")
            
    except Exception as e:
        print(f"과목명 처리 중 오류 발생: {e}")

def initialize_supabase_client() -> Client | None:
    """Supabase 클라이언트를 초기화하고 반환합니다."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("오류: SUPABASE_URL 또는 SUPABASE_KEY 환경 변수가 설정되지 않았습니다.")
        return None
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"Supabase 클라이언트 초기화 실패: {e}")
        return None

def generate_embedding(text: str) -> list[float] | None:
    """주어진 텍스트에 대해 Sentence Transformer 임베딩을 생성합니다."""
    if not text or not isinstance(text, str):
        print("오류: 임베딩을 생성할 유효한 텍스트가 제공되지 않았습니다.")
        return None
    try:
        # Sentence Transformer로 임베딩 생성
        embedding = model.encode(text.strip())
        return embedding.tolist()
    except Exception as e:
        print(f"'{text[:50]}...'에 대한 임베딩 생성 실패: {e}")
        return None

def insert_chunks_to_supabase(supabase_client: Client, chunks_file_path: str, user_id_placeholder: str):
    """
    JSON 파일에서 청크를 로드하고, 임베딩을 생성한 후 Supabase에 삽입합니다.
    user_id_placeholder는 실제 사용자 ID로 대체되어야 합니다.
    """
    try:
        with open(chunks_file_path, 'r', encoding='utf-8') as f:
            all_chunks_data = json.load(f)
    except FileNotFoundError:
        print(f"오류: 청크 파일 '{chunks_file_path}'을(를) 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print(f"오류: 청크 파일 '{chunks_file_path}'이(가) 유효한 JSON 형식이 아닙니다.")
        return
    except Exception as e:
        print(f"청크 파일 로드 중 오류 발생: {e}")
        return

    print("\n=== 청크 업로드 시작 ===")
    processed_chunks = []
    for i, chunk in enumerate(all_chunks_data):
        print(f"청크 {i+1}/{len(all_chunks_data)} 처리 중: {chunk.get('course')} - {chunk.get('week', chunk.get('video_title', chunk.get('metadata', {}).get('title', '')))}")
        
        # 임베딩 생성 대상 텍스트
        text_to_embed = chunk.get("value") or chunk.get("content")
        if not text_to_embed:
            print(f"경고: 청크 {i+1}에 임베딩할 텍스트가 없습니다. 건너뛰었습니다.")
            continue

        embedding = generate_embedding(text_to_embed)
        if embedding:
            chunk_data_for_db = {
                "id": str(uuid.uuid4()),
                "user_id": user_id_placeholder,
                "chunk_type": chunk.get("chunk_type"),
                "course": chunk.get("course"),
                "week": chunk.get("week"),
                "content": chunk.get("content"),
                "value": chunk.get("value"),
                "embedding": embedding,
                "metadata": chunk.get("metadata", {}),
            }
            
            if chunk.get("chunk_type") == "notice":
                chunk_data_for_db["week"] = chunk.get("metadata", {}).get("title", "공지사항")
            elif chunk.get("chunk_type") == "video_lecture":
                chunk_data_for_db["week"] = chunk.get("video_title", "온라인 강의")

            processed_chunks.append(chunk_data_for_db)

    if processed_chunks:
        try:
            print(f"총 {len(processed_chunks)}개의 청크를 Supabase에 삽입합니다...")
            response = supabase_client.table("chunks").insert(processed_chunks).execute()
            
            if hasattr(response, 'data') and response.data:
                print(f"{len(response.data)}개의 청크가 성공적으로 삽입되었습니다.")
            elif hasattr(response, 'error') and response.error:
                print(f"Supabase 삽입 중 오류 발생: {response.error}")
            else:
                print("Supabase 삽입 실행 완료.")

        except Exception as e:
            print(f"Supabase에 데이터 삽입 중 심각한 오류 발생: {e}")

if __name__ == "__main__":
    supabase_client = initialize_supabase_client()
    if supabase_client:
        # workspace 루트를 기준으로 상대 경로 설정
        current_script_dir = os.path.dirname(os.path.abspath(__file__)) # src/etl
        src_dir = os.path.dirname(current_script_dir) # src
        workspace_root = os.path.dirname(src_dir) # workspace_root (cap 폴더)

        chunks_file = os.path.join(workspace_root, "user_data", "course_chunks.json")
        
        # 실제 사용자 ID로 대체해야 합니다.
        placeholder_user_uuid = "8c48f4f3-8d91-400b-9ea8-681eefaa40b9"
        print(f"테스트용 사용자 ID: {placeholder_user_uuid}")
        print(f"청크 파일 경로: {chunks_file}")
        
        # 1. 청크 업로드
        insert_chunks_to_supabase(supabase_client, chunks_file, placeholder_user_uuid)
        
        # 2. 과목명 정규화 및 임베딩
        process_course_names(supabase_client)
        
        print("\n=== 모든 처리가 완료되었습니다 ===")
    else:
        print("Supabase 클라이언트 초기화에 실패하여 스크립트를 종료합니다.") 