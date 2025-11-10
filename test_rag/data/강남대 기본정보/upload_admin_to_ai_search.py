"""
강남대학교 행정부서 연락처 Vertex AI Search 업로드 스크립트

사용법:
    python test_rag/data/강남대\ 기본정보/upload_admin_to_ai_search.py
"""

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine
from google.cloud import storage
import os

PROJECT_ID = "kangnam-backend"
LOCATION = "global"
DATA_STORE_ID = "kangnam-univ-admin-contacts-datastore"

# GCS 버킷 설정
BUCKET_NAME = "kangnam-univ"
GCS_FOLDER = "rag_data/admin_contacts"
LOCAL_FILE = "test_rag/data/강남대 기본정보/행정부서 전화번호.jsonl"

# GCS 버킷 경로
GCS_INPUT_URIS = [
    f"gs://{BUCKET_NAME}/{GCS_FOLDER}/*.jsonl"
]

def upload_to_gcs():
    """JSONL 파일을 GCS에 업로드"""
    print("=" * 60)
    print("📤 GCS 업로드 시작")
    print("=" * 60)
    
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # 파일명 추출
    filename = os.path.basename(LOCAL_FILE)
    blob_name = f"{GCS_FOLDER}/{filename}"
    blob = bucket.blob(blob_name)
    
    print(f"📁 로컬 파일: {LOCAL_FILE}")
    print(f"☁️  GCS 경로: gs://{BUCKET_NAME}/{blob_name}")
    
    # 업로드
    blob.upload_from_filename(LOCAL_FILE)
    print("✅ GCS 업로드 완료!")
    print("=" * 60)

def import_admin_docs():
    """Vertex AI Search에 행정부서 연락처 문서 가져오기"""
    print("\n" + "=" * 60)
    print("📤 Vertex AI Search - 행정부서 연락처 JSONL Import 시작")
    print("=" * 60)
    
    client_options = ClientOptions(api_endpoint="global-discoveryengine.googleapis.com")

    parent = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # branch 기본값은 항상 "default_branch"
    parent = client.branch_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATA_STORE_ID,
        branch="default_branch",
    )

    # 요청 구성
    gcs_source = discoveryengine.GcsSource(
        input_uris=GCS_INPUT_URIS,
        data_schema="custom",  # JSONL 데이터일 경우 custom
    )

    import_request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
        auto_generate_ids=False,  # ID 필드 직접 지정
        id_field="id",  # JSON의 문서 ID 필드
    )

    # 실행
    print("🚀 문서 가져오기 요청 중...")
    operation = client.import_documents(request=import_request)
    print(f"🕐 작업 ID: {operation.operation.name}")
    print("⏳ 데이터 수집 중... (약 1~3분 소요)")

    result = operation.result(timeout=600)
    print("\n✅ 데이터 가져오기 완료!")
    print(result)

if __name__ == "__main__":
    # Step 1: GCS 업로드
    upload_to_gcs()
    
    # Step 2: Vertex AI Search에 import
    import_admin_docs()
    
    print("\n" + "=" * 60)
    print("🎉 모든 작업 완료!")
    print("=" * 60)

