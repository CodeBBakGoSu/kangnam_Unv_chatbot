"""
강남대학교 교수정보 JSONL 데이터를 Vertex AI RAG 코퍼스에 업로드하는 스크립트

사용법:
    python goole_adk/data/교수정보/upload_professors_to_rag.py
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
PROFESSORS_DIR = SCRIPT_DIR

# 처리할 JSONL 파일들
JSONL_FILES = [
    "공과대학.jsonl",
    "글로벌문화콘텐츠대학.jsonl",
    "법행정세무학부.jsonl",
    "사범대학.jsonl",
    "사회복지학과.jsonl",
    "상경학부.jsonl",
    "시니어비즈니스학과.jsonl",
    "예체능대학.jsonl",
]

# GCS 설정
GCS_BUCKET_NAME = "kangnam-univ"
GCS_BUCKET_LOCATION = "asia-northeast3"  # 서울
GCS_RAG_DATA_BASE_PATH = "rag_data/professors/"  # GCS 기본 경로

# Vertex AI 설정
PROJECT_ID = "kangnam-backend"
LOCATION = "us-east4"

# ⚠️ 코퍼스 ID를 입력하세요!
# create_professor_corpus.py 실행 후 생성된 코퍼스 ID로 교체
CORPUS_ID = "4532873024948404224"  # 🔴 여기에 새 코퍼스 ID 입력 필요!
CORPUS_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_ID}"

# ==============================
# 초기화
# ==============================
print("=" * 60)
print("🎓 강남대학교 교수정보 RAG 업로드")
print("=" * 60)
print(f"\n🔄 초기화 중...")
print(f"   프로젝트: {PROJECT_ID}")
print(f"   Vertex AI 리전: {LOCATION}")
print(f"   GCS 버킷: gs://{GCS_BUCKET_NAME}")
print(f"   교수정보 폴더: {PROFESSORS_DIR}")

# 코퍼스 ID 확인
if CORPUS_ID == "YOUR_NEW_CORPUS_ID":
    print("\n" + "=" * 60)
    print("⚠️  새 코퍼스를 먼저 생성해야 합니다!")
    print("=" * 60)
    print("\n아래 명령어로 새 코퍼스를 생성하세요:\n")
    print("📌 코퍼스 생성:")
    print("-" * 60)
    print(f"   python goole_adk/data/교수정보/create_professor_corpus.py")
    print("-" * 60)
    print("\n생성 후:")
    print("   1. 출력된 코퍼스 ID를 복사")
    print("   2. 이 스크립트의 CORPUS_ID 변수에 입력")
    print("   3. 스크립트 다시 실행\n")
    exit(1)

print(f"   코퍼스 ID: {CORPUS_ID}\n")

# Vertex AI 초기화
vertexai.init(project=PROJECT_ID, location=LOCATION)

# GCS 클라이언트 초기화
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# ==============================
# 교수정보 파일 확인
# ==============================
print("📁 교수정보 파일 확인 중...\n")

available_files = []
missing_files = []

for jsonl_file in JSONL_FILES:
    file_path = PROFESSORS_DIR / jsonl_file
    if file_path.exists():
        available_files.append(jsonl_file)
        with open(file_path, "r", encoding="utf-8") as f:
            line_count = sum(1 for line in f if line.strip())
        print(f"   ✅ {jsonl_file} ({line_count} 항목)")
    else:
        missing_files.append(jsonl_file)
        print(f"   ❌ {jsonl_file} (파일 없음)")

if missing_files:
    print(f"\n⚠️  {len(missing_files)}개 파일을 찾을 수 없습니다.")
    print("   계속 진행하시겠습니까?")

if not available_files:
    print("\n❌ 업로드할 파일이 없습니다.")
    exit(1)

print(f"\n📊 총 {len(available_files)}개 파일 준비 완료\n")

# ==============================
# 통계 수집
# ==============================
print("📈 데이터 통계 수집 중...\n")

total_professors = 0
total_indexes = 0
stats_by_college = {}

for jsonl_file in available_files:
    file_path = PROFESSORS_DIR / jsonl_file
    
    professors = 0
    indexes = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get("metadata", {}).get("entity") == "org_index":
                    indexes += 1
                elif data.get("metadata", {}).get("professor_id"):
                    professors += 1
            except json.JSONDecodeError:
                continue
    
    college_name = jsonl_file.replace(".jsonl", "")
    stats_by_college[college_name] = {
        "professors": professors,
        "indexes": indexes,
        "total": professors + indexes
    }
    
    total_professors += professors
    total_indexes += indexes
    
    print(f"   {college_name}:")
    print(f"      교수: {professors}명")
    print(f"      인덱스: {indexes}개")
    print(f"      합계: {professors + indexes}개")

print(f"\n" + "=" * 60)
print(f"   전체 교수: {total_professors}명")
print(f"   전체 인덱스: {total_indexes}개")
print(f"   총 항목: {total_professors + total_indexes}개")
print("=" * 60)

# 사용자 확인
print("\n")
confirm = input("🚀 GCS에 업로드하고 RAG 코퍼스에 import 하시겠습니까? (yes/no): ").strip().lower()
if confirm not in ['yes', 'y']:
    print("❌ 업로드가 취소되었습니다.")
    exit(0)

# ==============================
# GCS에 파일 업로드
# ==============================
print("\n☁️  GCS에 업로드 중...\n")

uploaded_uris = []

for jsonl_file in available_files:
    file_path = PROFESSORS_DIR / jsonl_file
    gcs_path = f"{GCS_RAG_DATA_BASE_PATH}{jsonl_file}"
    
    print(f"   📤 {jsonl_file} 업로드 중...")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(
            content,
            content_type="application/x-ndjson"
        )
        
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{gcs_path}"
        uploaded_uris.append(gcs_uri)
        
        size_kb = len(content.encode('utf-8')) / 1024
        print(f"      ✅ 완료 ({size_kb:.2f} KB)")
        print(f"      📍 {gcs_uri}")
        
    except Exception as e:
        print(f"      ❌ 실패: {str(e)}")
        continue

if not uploaded_uris:
    print("\n❌ 업로드된 파일이 없습니다.")
    exit(1)

print(f"\n✅ GCS 업로드 완료!")
print(f"   📦 {len(uploaded_uris)}개 파일 업로드됨\n")

# ==============================
# Vertex AI RAG 코퍼스로 Import
# ==============================
print("🚀 Vertex AI RAG 코퍼스에 Import 중...\n")
print(f"   코퍼스: {CORPUS_NAME}")
print(f"   파일 수: {len(uploaded_uris)}개\n")

try:
    # ImportFilesConfig 대신 TransformationConfig 와 ChunkingConfig 를 사용합니다.
    config = rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(
            chunk_size=512,
            chunk_overlap=50
        )
    )

    # 2. ✅ import_files 함수 호출 수정
    # 'import_files_config=' 대신 'transformation_config=' 를 사용합니다.
    operation = rag.import_files(
        corpus_name=CORPUS_NAME,
        paths=uploaded_uris,
        transformation_config=config,  # ✅ 여기가 수정된 핵심
    )
    
    print("   ⏳ Import 및 임베딩 생성 중...")
    print("   (교수 정보가 많아 5-10분 소요될 수 있습니다)")
    
    try:
        result = operation.result(timeout=600)  # 10분 타임아웃
        print(f"\n   ✅ Import 완료 확인됨!")
    except Exception as result_error:
        print(f"\n   ⚠️  완료 확인 타임아웃 (백그라운드 처리 중일 수 있음)")
        print(f"   에러: {str(result_error)}")
    
    print("\n" + "=" * 60)
    print("✅ Import 요청 완료!")
    print("=" * 60)
    print(f"\n📊 업로드 요약:")
    print(f"   • 교수: {total_professors}명")
    print(f"   • 인덱스: {total_indexes}개")
    print(f"   • 파일: {len(uploaded_uris)}개")
    print(f"   • 코퍼스: {CORPUS_ID}")
    
    print(f"\n☁️  GCS 경로:")
    for uri in uploaded_uris:
        print(f"   • {uri}")
    
    print(f"\n🔍 5-10분 후 코퍼스에서 검색 가능합니다!")
    print(f"\n💡 마지막 단계:")
    print(f"   goole_adk/agents/professor/tools/search_tools.py 파일을 열어")
    print(f"   PROFESSOR_CORPUS_ID를 다음으로 교체:")
    print(f"\n   PROFESSOR_CORPUS_ID = \"{CORPUS_ID}\"\n")
    print(f"\n💬 테스트 쿼리 예시:")
    print(f"   • '인공지능 교수님 알려줘'")
    print(f"   • '김철주 교수님 연구실 어디야?'")
    print(f"   • '공과대학 교수님들 알려줘'")
    print(f"   • 'VR 전공 교수님 누구야?'\n")
    
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
