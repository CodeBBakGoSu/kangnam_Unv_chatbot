"""
GCS에 있는 기존 파일 이름을 더 명확한 이름으로 변경하는 스크립트

사용법:
    python goole_adk/data/rename_gcs_file.py
"""

from google.cloud import storage

# ==============================
# 설정
# ==============================
PROJECT_ID = "kangnam-backend"
BUCKET_NAME = "kangnam-univ"

# 기존 파일명 → 새 파일명
OLD_FILE_PATH = "rag_data/graduation_requirements.jsonl"
NEW_FILE_PATH = "rag_data/kangnam_univ_graduation_requirements_2017_2025.jsonl"

# ==============================
# GCS 파일 이름 변경
# ==============================
print("☁️  GCS 파일 이름 변경 중...\n")
print(f"   버킷: gs://{BUCKET_NAME}")
print(f"   기존: {OLD_FILE_PATH}")
print(f"   신규: {NEW_FILE_PATH}\n")

try:
    # GCS 클라이언트 초기화
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # 기존 파일 확인
    old_blob = bucket.blob(OLD_FILE_PATH)
    
    if not old_blob.exists():
        print(f"⚠️  기존 파일이 존재하지 않습니다: {OLD_FILE_PATH}")
        print(f"   이미 변경되었거나 파일이 없을 수 있습니다.")
        
        # 새 파일 확인
        new_blob = bucket.blob(NEW_FILE_PATH)
        if new_blob.exists():
            print(f"✅ 새 파일명으로 이미 존재합니다: {NEW_FILE_PATH}")
        exit(0)
    
    # 파일 복사 (이름 변경)
    new_blob = bucket.copy_blob(old_blob, bucket, NEW_FILE_PATH)
    
    print(f"✅ 파일 복사 완료!")
    print(f"   📍 새 URI: gs://{BUCKET_NAME}/{NEW_FILE_PATH}")
    
    # 기존 파일 삭제
    print(f"\n🗑️  기존 파일 삭제 중...")
    old_blob.delete()
    
    print(f"✅ 기존 파일 삭제 완료!")
    print(f"\n✅ 파일 이름 변경 완료!")
    print(f"   gs://{BUCKET_NAME}/{OLD_FILE_PATH}")
    print(f"   → gs://{BUCKET_NAME}/{NEW_FILE_PATH}")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print(f"\n💡 확인사항:")
    print(f"   1. 인증: gcloud auth application-default login")
    print(f"   2. 권한: Storage Object Admin")
    print(f"   3. 버킷 존재 여부: gs://{BUCKET_NAME}")

