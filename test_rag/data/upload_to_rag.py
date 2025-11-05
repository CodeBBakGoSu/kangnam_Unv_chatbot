"""
강남대학교 졸업이수학점 JSON 데이터를 Vertex AI RAG 코퍼스에 업로드하는 스크립트

사용법:
    python test_rag/data/upload_to_rag.py
"""

import json
import os
from pathlib import Path
import vertexai
from vertexai.preview import rag
from google.cloud import storage

# ==============================
# 설정
# ==============================
# 현재 스크립트 디렉토리
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR
RESULT_DIR = SCRIPT_DIR / "result"  # 로컬 결과 저장 폴더

# result 폴더가 없으면 생성
RESULT_DIR.mkdir(exist_ok=True)

# 처리할 JSON 파일들
JSON_FILES = [
    "2017_2025_통합_졸업이수학점.json",
    # "2025이상 입학자 졸업이수학점.json",
    # "2021~2024학년도 입학자 졸업이수학점.json",
    # "2017~2020학년도 입학자 졸업이수학점.json",
]

# GCS 설정
GCS_BUCKET_NAME = "kangnam-univ"
GCS_BUCKET_LOCATION = "asia-northeast3"  # 서울
GCS_RAG_DATA_PATH = "rag_data/kangnam_univ_graduation_requirements_2017_2025.jsonl"  # GCS 경로

# 코퍼스 내 파일명 (display_name)
CORPUS_FILE_DISPLAY_NAME = "강남대학교_졸업이수학점_2017_2025"  # 코퍼스 안에서 보이는 이름

# Vertex AI 설정
PROJECT_ID = "kangnam-backend"
LOCATION = "us-east4"
CORPUS_ID = "6917529027641081856"
CORPUS_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_ID}"

# ==============================
# 초기화
# ==============================
print(f"🔄 초기화 중...")
print(f"   프로젝트: {PROJECT_ID}")
print(f"   Vertex AI 리전: {LOCATION}")
print(f"   GCS 버킷: gs://{GCS_BUCKET_NAME}")
print(f"   코퍼스 ID: {CORPUS_ID}\n")

# Vertex AI 초기화
vertexai.init(project=PROJECT_ID, location=LOCATION)

# GCS 클라이언트 초기화
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# ==============================
# 헬퍼 함수
# ==============================
def merge_departments(department_data):
    """계열 구조를 평탄화하여 학과/전공명을 하나의 문자열로 병합"""
    names = []
    for dept in department_data:
        if "학부" in dept:
            names.append(dept["학부"])
        if "학과" in dept:
            names.append(dept["학과"])
        if "전공" in dept:
            names.extend(dept["전공"])
    return ", ".join(names)

def extract_year_range_from_filename(filename):
    """파일명에서 학년도 범위 추출"""
    if "2017_2025_통합" in filename:
        return "2017-2025"
    elif "2025이상" in filename:
        return "2025+"
    elif "2021~2024" in filename:
        return "2021-2024"
    elif "2017~2020" in filename:
        return "2017-2020"
    return "unknown"

# ==============================
# JSON 데이터 처리
# ==============================
all_chunks = []

for json_file in JSON_FILES:
    json_path = DATA_DIR / json_file
    
    if not json_path.exists():
        print(f"⚠️  파일을 찾을 수 없습니다: {json_file}")
        continue
    
    print(f"📂 처리 중: {json_file}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    
    # 파일명에서 기본 year_range 추출 (fallback용)
    default_year_range = extract_year_range_from_filename(json_file)
    document_title = file_data.get("document_title", "")
    
    # data 배열 가져오기
    colleges_data = file_data.get("data", [])
    
    for college_info in colleges_data:
        college = college_info.get("대학", "")
        grad_req = college_info.get("졸업요건", {})
        liberal_arts = college_info.get("교양이수표", {})
        divisions = college_info.get("계열", [])
        
        # ⭐ JSON 내부의 year_range를 우선 사용, 없으면 파일명에서 추출한 값 사용
        year_range = college_info.get("year_range", default_year_range)
        
        for division in divisions:
            division_name = division.get("계열명", "")
            departments_list = division.get("학부및학과", [])
            departments_str = merge_departments(departments_list)
            
            # Chunk 1: 졸업요건
            if grad_req:
                content = f"""
[졸업요건 정보]
대학: {college}
계열: {division_name}
학과/전공: {departments_str}
학년도: {year_range}

졸업요건:
- 기초교양: {grad_req.get('기초교양', 'N/A')}학점
- 계열교양: {grad_req.get('계열교양', 'N/A')}학점
- 균형교양: {grad_req.get('균형교양', 'N/A')}
- 심화전공자 전공학점: {grad_req.get('심화전공자', {}).get('전공기초+전공선택', 'N/A')}학점
- 다전공자 전공학점: {grad_req.get('다전공자', {}).get('전공기초+전공선택', 'N/A')}학점
- 최소졸업학점: {grad_req.get('최소졸업학점', 'N/A')}학점
""".strip()
                
                all_chunks.append({
                    "content": content,
                    "metadata": {
                        "college": college,
                        "division": division_name,
                        "department": departments_str,
                        "year_range": year_range,
                        "category": "졸업요건",
                        "language": "ko",
                        "source_file": json_file
                    }
                })
            
            # Chunk 2: 교양이수표
            if liberal_arts:
                # 교양이수표를 텍스트로 포맷팅
                liberal_text_parts = [
                    f"[교양이수표]",
                    f"대학: {college}",
                    f"계열: {division_name}",
                    f"학과/전공: {departments_str}",
                    f"학년도: {year_range}",
                    "",
                    "교양 과목:"
                ]
                
                for category, subjects in liberal_arts.items():
                    if isinstance(subjects, list):
                        liberal_text_parts.append(f"\n{category}:")
                        for subject in subjects:
                            liberal_text_parts.append(f"  - {subject}")
                    else:
                        liberal_text_parts.append(f"{category}: {subjects}")
                
                content = "\n".join(liberal_text_parts)
                
                all_chunks.append({
                    "content": content,
                    "metadata": {
                        "college": college,
                        "division": division_name,
                        "department": departments_str,
                        "year_range": year_range,
                        "category": "교양이수표",
                        "language": "ko",
                        "source_file": json_file
                    }
                })
    
    print(f"   ✅ {len([c for c in all_chunks if c['metadata']['source_file'] == json_file])}개 chunk 생성")

print(f"\n📊 총 {len(all_chunks)}개의 chunk 생성 완료\n")

# ==============================
# 로컬 result 폴더에 JSONL 저장 (확인용)
# ==============================
print(f"💾 로컬 result 폴더에 저장 중...")

# JSONL 문자열 생성
jsonl_content = "\n".join([
    json.dumps(chunk, ensure_ascii=False) 
    for chunk in all_chunks
])

# 로컬 파일로 저장
local_jsonl_path = RESULT_DIR / "kangnam_univ_graduation_requirements.jsonl"
with open(local_jsonl_path, "w", encoding="utf-8") as f:
    f.write(jsonl_content)

print(f"   ✅ 로컬 저장 완료!")
print(f"   📁 경로: {local_jsonl_path}")
print(f"   📦 크기: {len(jsonl_content.encode('utf-8')) / 1024:.2f} KB")
print(f"\n   💡 업로드 전에 파일을 확인하세요: {local_jsonl_path}\n")

# 사용자 확인
confirm = input("🚀 GCS에 업로드하시겠습니까? (yes/no): ").strip().lower()
if confirm not in ['yes', 'y']:
    print("❌ 업로드가 취소되었습니다.")
    print(f"   로컬 파일: {local_jsonl_path}")
    exit(0)

# ==============================
# GCS에 JSONL 업로드
# ==============================
print(f"\n☁️  GCS에 업로드 중...")
print(f"   버킷: gs://{GCS_BUCKET_NAME}")
print(f"   경로: {GCS_RAG_DATA_PATH}")

# GCS에 업로드
try:
    blob = bucket.blob(GCS_RAG_DATA_PATH)
    blob.upload_from_string(
        jsonl_content,
        content_type="application/jsonl"
    )
    
    gcs_uri = f"gs://{GCS_BUCKET_NAME}/{GCS_RAG_DATA_PATH}"
    print(f"   ✅ GCS 업로드 완료!")
    print(f"   📍 URI: {gcs_uri}")
    print(f"   📦 크기: {len(jsonl_content.encode('utf-8')) / 1024:.2f} KB\n")
    
except Exception as e:
    print(f"\n❌ GCS 업로드 실패:")
    print(f"   {str(e)}")
    print(f"\n💡 확인사항:")
    print(f"   1. 버킷 존재 여부: gs://{GCS_BUCKET_NAME}")
    print(f"   2. 권한: Storage Object Admin 역할")
    print(f"   3. 인증: gcloud auth application-default login")
    exit(1)

# ==============================
# Vertex AI RAG 코퍼스로 Import
# ==============================
print(f"🚀 Vertex AI RAG 코퍼스에 Import 중...")
print(f"   코퍼스: {CORPUS_NAME}")
print(f"   소스: {gcs_uri}")

try:
    # RagFile 설정으로 display_name 지정
    operation = rag.import_files(
        corpus_name=CORPUS_NAME,
        paths=[gcs_uri],
        chunk_size=800,
        chunk_overlap=100,
    )
    
    print(f"   ⏳ Import 및 임베딩 생성 중...")
    print(f"   📝 코퍼스 내 표시명: {CORPUS_FILE_DISPLAY_NAME}")
    
    try:
        result = operation.result()
        print(f"   ✅ Import 완료 확인됨!")
    except Exception as result_error:
        print(f"   ⚠️  완료 확인 실패 (백그라운드 처리 중일 수 있음)")
        print(f"   에러: {str(result_error)}")
    
    print(f"\n✅ Import 요청 완료!")
    print(f"   📄 총 {len(all_chunks)}개 chunk")
    print(f"   📁 로컬 파일: {local_jsonl_path}")
    print(f"   ☁️  GCS 파일: {gcs_uri}")
    print(f"   🔍 1-5분 후 코퍼스에서 검색 가능합니다!")
    
except Exception as e:
    print(f"\n❌ Vertex AI Import 실패:")
    print(f"   {str(e)}")
    print(f"\n💡 확인사항:")
    print(f"   1. 인증: gcloud auth application-default login")
    print(f"   2. 권한: Vertex AI User 역할")
    print(f"   3. API 활성화: Vertex AI API")
    print(f"   4. 코퍼스 ID: {CORPUS_ID}")
    print(f"   5. GCS 파일 접근 권한")
    exit(1)

