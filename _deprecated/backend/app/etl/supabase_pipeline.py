import json
import os
import uuid
import re
from typing import List, Dict, Any, Tuple, Optional
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

from app.config import SUPABASE_URL, SUPABASE_KEY

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

def initialize_supabase_client() -> Optional[Client]:
    """Supabase 클라이언트를 초기화하고 반환합니다."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        error_msg = "Supabase 연결 실패: 환경 변수 SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다."
        print(error_msg)
        raise Exception(error_msg)
        
    try:
        print(f"Supabase 연결 시도: {SUPABASE_URL[:20]}...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase 연결 성공")
        return supabase
    except Exception as e:
        error_msg = f"Supabase 클라이언트 초기화 실패: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def generate_embedding(text: str) -> Optional[List[float]]:
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

def clean_user_data(user_id: str) -> bool:
    """
    특정 사용자의 모든 데이터를 정리합니다.
    
    Args:
        user_id: 학번
        
    Returns:
        bool: 성공 여부
    """
    try:
        print(f"사용자 {user_id}의 모든 데이터 정리 시작")
        supabase_client = initialize_supabase_client()
        
        # 학번을 UUID로 변환
        student_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kangnam.student.{user_id}"))
        
        # 해당 사용자의 모든 청크 삭제
        result = supabase_client.table('chunks').delete().eq('user_id', student_uuid).execute()
        print(f"사용자 {user_id}의 모든 청크 삭제 완료")
        
        return True
    except Exception as e:
        print(f"사용자 데이터 정리 중 오류 발생: {str(e)}")
        return False

def get_user_chunks_count(user_id: str) -> int:
    """
    특정 사용자의 청크 수를 반환합니다.
    
    Args:
        user_id: 학번
        
    Returns:
        int: 청크 수
    """
    try:
        supabase_client = initialize_supabase_client()
        
        # 학번을 UUID로 변환
        student_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kangnam.student.{user_id}"))
        
        # 해당 사용자의 청크 수 조회
        result = supabase_client.table('chunks').select('id', count='exact').eq('user_id', student_uuid).execute()
        count = len(result.data) if result.data else 0
        
        print(f"사용자 {user_id}의 저장된 청크 수: {count}")
        return count
    except Exception as e:
        print(f"사용자 청크 수 조회 중 오류 발생: {str(e)}")
        return 0

def insert_chunks_to_supabase(chunks: List[Dict[str, Any]], user_id: str) -> bool:
    """
    청크를 Supabase에 삽입합니다.
    
    Args:
        chunks: 삽입할 청크 목록
        user_id: 사용자 ID
        
    Returns:
        bool: 삽입 성공 여부
    """
    try:
        print(f"Supabase 벡터 DB에 청크 삽입 시작 (총 {len(chunks)}개)")
        supabase_client = initialize_supabase_client()
        
        if not chunks:
            print("경고: 삽입할 청크가 없습니다.")
            return True
            
        # 학번(user_id)으로 일관된 UUID 생성 (항상 같은 학번은 같은 UUID가 나오도록)
        student_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kangnam.student.{user_id}"))
        print(f"학번 {user_id}에 대한 UUID 생성: {student_uuid}")
        
        # 이전 데이터 확인
        existing_count = get_user_chunks_count(user_id)
        if existing_count > 0:
            print(f"기존 데이터 {existing_count}개 발견됨")
            
            # 기존 사용자 데이터 삭제 (강제로 실행)
            print(f"기존 사용자 데이터 삭제 시작...")
            deletion_success = False
            max_retries = 3
            retry_count = 0
            
            while not deletion_success and retry_count < max_retries:
                try:
                    retry_count += 1
                    supabase_client.table('chunks').delete().eq('user_id', student_uuid).execute()
                    print(f"이전 청크 데이터 삭제 완료 (시도 {retry_count})")
                    deletion_success = True
                except Exception as e:
                    print(f"이전 데이터 삭제 중 오류 (시도 {retry_count}): {str(e)}")
                    if retry_count < max_retries:
                        print(f"3초 후 다시 시도...")
                        import time
                        time.sleep(3)
            
            if not deletion_success:
                print("이전 데이터 삭제 실패, 새 데이터는 추가로 삽입됩니다.")
        
        # 테이블 스키마 확인 (필요한 필드 목록)
        required_fields = ['id', 'user_id', 'course', 'week', 'chunk_type', 'content', 'embedding', 'metadata']
        print(f"필수 필드 확인: {', '.join(required_fields)}")
        
        # 청크 배치 처리
        batch_size = 100
        batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
        print(f"총 {len(batches)}개 배치로 나누어 처리합니다.")
        
        for i, batch in enumerate(batches):
            print(f"배치 {i+1}/{len(batches)} 처리 중 ({len(batch)}개 청크)...")
            
            # 청크에 임베딩 추가
            processed_chunks = []
            for chunk in batch:
                # 테이블 스키마에 맞는 새 객체 생성
                processed_chunk = {
                    'id': str(uuid.uuid4()),  # 청크마다 고유 UUID 생성
                    'user_id': student_uuid,  # 학번 대신 생성된 UUID 사용
                    'course': chunk.get('course', ''),
                    'week': chunk.get('week', ''),
                    'chunk_type': chunk.get('chunk_type', 'text'),
                    'content': chunk.get('content', ''),
                    'metadata': chunk.get('metadata', {})
                }
                
                # 임베딩 생성 (없으면 건너뜀)
                content_to_embed = chunk.get('content', '')
                if content_to_embed:
                    processed_chunk['embedding'] = generate_embedding(content_to_embed)
                    if processed_chunk['embedding']:
                        processed_chunks.append(processed_chunk)
                    else:
                        print(f"경고: 청크 '{processed_chunk['id'][:8]}'의 임베딩 생성 실패. 건너뜁니다.")
            
            if not processed_chunks:
                print("배치에 유효한 청크가 없습니다. 건너뜁니다.")
                continue
                
            try:
                # Supabase에 삽입
                result = supabase_client.table('chunks').insert(processed_chunks).execute()
                print(f"배치 {i+1} 삽입 완료: {len(processed_chunks)}개 청크")
            except Exception as e:
                print(f"배치 {i+1} 삽입 중 오류: {str(e)}")
                # 객체 구조를 출력해서 디버깅
                if processed_chunks:
                    print(f"첫 번째 청크 구조: {list(processed_chunks[0].keys())}")
                # 단일 오류가 전체를 중단시키지 않도록 계속 진행
                continue
        
        print(f"Supabase 벡터 DB 삽입 완료")
        return True
        
    except Exception as e:
        error_msg = f"Supabase에 청크 삽입 중 오류 발생: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def process_user_data(user_id: str, data_file: str) -> bool:
    """
    사용자의 크롤링된 데이터를 처리하여 벡터 DB에 저장합니다.
    
    Args:
        user_id: 학번
        data_file: 크롤링된 데이터 파일 경로
        
    Returns:
        bool: 처리 성공 여부
    """
    try:
        # 진행 상태 초기화
        etl_status = {
            "stage": "validating",
            "message": "데이터 파일 유효성 검증 중",
            "progress": 5
        }
        print(f"ETL 상태 업데이트: {etl_status}")
        
        if not os.path.exists(data_file):
            print(f"오류: 파일이 존재하지 않습니다: {data_file}")
            etl_status = {"stage": "error", "message": "데이터 파일을 찾을 수 없습니다", "progress": 0}
            print(f"ETL 상태 업데이트: {etl_status}")
            return False
            
        print(f"사용자 {user_id}의 데이터 파일 처리 시작: {data_file}")
        
        # 데이터 파일 읽기
        etl_status = {"stage": "loading", "message": "LMS 데이터 파일 로드 중", "progress": 10}
        print(f"ETL 상태 업데이트: {etl_status}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"오류: JSON 파싱 실패: {str(e)}")
                etl_status = {"stage": "error", "message": "JSON 데이터 구문 오류", "progress": 0}
                print(f"ETL 상태 업데이트: {etl_status}")
                return False
                
        # 사용자 정보 및 과목 정보 가져오기
        etl_status = {"stage": "extracting", "message": "사용자 및 과목 정보 추출 중", "progress": 20}
        print(f"ETL 상태 업데이트: {etl_status}")
        
        user_info = data.get('user', {})
        courses = data.get('courses', [])
        
        if not courses:
            print(f"경고: 과목 정보가 없습니다.")
            etl_status = {"stage": "warning", "message": "과목 정보가 없습니다", "progress": 0}
            print(f"ETL 상태 업데이트: {etl_status}")
            return False
            
        print(f"사용자 {user_id} ({user_info.get('name', '이름 없음')})의 {len(courses)}개 과목 처리 시작")
        
        # 청크 목록 초기화
        chunks = []
        
        # 과목 데이터 처리 시작
        etl_status = {"stage": "processing", "message": f"{len(courses)}개 과목 데이터 처리 중", "progress": 30}
        print(f"ETL 상태 업데이트: {etl_status}")
        
        # 각 과목별로 청크 생성
        for i, course in enumerate(courses):
            course_name = course.get('title', f'과목_{i+1}')
            professor = course.get('professor', '교수 정보 없음')
            
            # 진행률 업데이트 (30~50%)
            progress = 30 + int((i / len(courses)) * 20)
            etl_status = {
                "stage": "processing", 
                "message": f"과목 처리 중: {course_name} ({i+1}/{len(courses)})", 
                "progress": progress
            }
            if (i % 3 == 0) or (i == len(courses) - 1):  # 모든 과목에 대해 출력하지 않고 일부만
                print(f"ETL 상태 업데이트: {etl_status}")
            
            # 기본 메타데이터
            metadata = {
                'professor': professor,
                'course_type': course.get('type', '일반'),
                'semester': course.get('semester', '현재학기'),
                'source': 'KNU LMS'
            }
            
            # 과목 소개 청크
            course_info = f"과목명: {course_name}\n교수: {professor}"
            if 'description' in course:
                course_info += f"\n설명: {course['description']}"
                
            chunks.append({
                'course': course_name,
                'week': '기본정보',
                'chunk_type': 'course_info',
                'content': course_info,
                'metadata': metadata
            })
            
            # 주차 정보 처리 - 구조 변경
            weeks_data = course.get('weeks', {})
            weeks_list = weeks_data.get('weeks', []) if isinstance(weeks_data, dict) else []
            
            for week_idx, week in enumerate(weeks_list):
                if not isinstance(week, dict):
                    continue
                    
                # 주차 번호와 제목 가져오기
                week_num = str(week_idx + 1)  # 주차 정보가 없으면 인덱스 기반으로 번호 부여
                week_title = week.get('title', f'{week_num}주차')
                
                # 주차 메타데이터
                week_metadata = metadata.copy()
                week_metadata.update({
                    'week': week_num,
                    'week_title': week_title
                })
                
                # 주차 소개 청크
                week_info = f"{course_name} {week_num}주차: {week_title}"
                chunks.append({
                    'course': course_name,
                    'week': week_num,
                    'chunk_type': 'week_info',
                    'content': week_info,
                    'metadata': week_metadata
                })
                
                # 주차별 활동 목록 처리
                activities = week.get('activities', [])
                if activities and isinstance(activities, list):
                    activities_text = f"{course_name} {week_num}주차 활동 목록:\n"
                    for idx, activity in enumerate(activities):
                        if isinstance(activity, str):
                            activities_text += f"- {activity}\n"
                    
                    if len(activities_text) > 30:  # 의미 있는 내용이 있는 경우만 추가
                        chunks.append({
                            'course': course_name,
                            'week': week_num,
                            'chunk_type': 'activities',
                            'content': activities_text,
                            'metadata': week_metadata
                        })
                
                # 주차 내 컨텐츠 처리 (있는 경우)
                contents = week.get('contents', [])
                if isinstance(contents, list):
                    for content_idx, content in enumerate(contents):
                        if not isinstance(content, dict):
                            continue
                            
                        content_type = content.get('type', '텍스트')
                        content_title = content.get('title', '제목 없음')
                        content_text = content.get('text', '')
                        
                        if content_text:
                            # 컨텐츠 메타데이터
                            content_metadata = week_metadata.copy()
                            content_metadata.update({
                                'content_type': content_type,
                                'content_title': content_title
                            })
                            
                            # 내용이 너무 길면 여러 청크로 분할
                            if len(content_text) > 1000:
                                # 문단별로 분할
                                paragraphs = content_text.split('\n\n')
                                
                                for j, paragraph in enumerate(paragraphs):
                                    if not paragraph.strip():
                                        continue
                                        
                                    part_metadata = content_metadata.copy()
                                    part_metadata.update({
                                        'part': j+1,
                                        'total_parts': len(paragraphs)
                                    })
                                    
                                    chunks.append({
                                        'course': course_name,
                                        'week': week_num,
                                        'chunk_type': 'content',
                                        'content': paragraph,
                                        'metadata': part_metadata
                                    })
                            else:
                                # 짧은 내용은 그대로 하나의 청크로
                                chunks.append({
                                    'course': course_name,
                                    'week': week_num,
                                    'chunk_type': 'content',
                                    'content': content_text,
                                    'metadata': content_metadata
                                })
        
        # 총 청크 수 확인
        etl_status = {"stage": "vectorizing", "message": "텍스트 벡터화 준비 중", "progress": 60}
        print(f"ETL 상태 업데이트: {etl_status}")
        print(f"생성된 총 청크 수: {len(chunks)}")
        
        if not chunks:
            print("경고: 생성된 청크가 없습니다.")
            etl_status = {"stage": "error", "message": "생성된 청크가 없습니다", "progress": 0}
            print(f"ETL 상태 업데이트: {etl_status}")
            return False
        
        # 벡터화 및 삽입 단계
        etl_status = {"stage": "storing", "message": f"{len(chunks)}개 청크 벡터 DB에 저장 중", "progress": 70}
        print(f"ETL 상태 업데이트: {etl_status}")
        
        # Supabase에 청크 삽입
        result = insert_chunks_to_supabase(chunks, user_id)
        
        # 과목명 정규화 단계
        etl_status = {"stage": "normalizing", "message": "과목명 정규화 및 최종 처리 중", "progress": 90}
        print(f"ETL 상태 업데이트: {etl_status}")
        
        # 사용자의 과목명 정규화 및 저장
        try:
            supabase_client = initialize_supabase_client()
            process_course_names(supabase_client)
        except Exception as e:
            print(f"과목명 처리 중 오류 (무시하고 진행): {str(e)}")
        
        # 완료 상태 업데이트
        etl_status = {"stage": "completed", "message": "ETL 파이프라인 완료", "progress": 100}
        print(f"ETL 상태 업데이트: {etl_status}")
        
        return result
        
    except Exception as e:
        print(f"사용자 데이터 처리 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        etl_status = {"stage": "error", "message": f"처리 오류: {str(e)}", "progress": 0}
        print(f"ETL 상태 업데이트: {etl_status}")
        return False 