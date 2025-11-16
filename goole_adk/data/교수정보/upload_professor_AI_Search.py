from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

PROJECT_ID = "kangnam-backend"
LOCATION = "global"
DATA_STORE_ID = "kangnam-univ-professor-info-datastore"

# GCS 버킷 경로
GCS_INPUT_URIS = [
    "gs://kangnam-univ/rag_data/professors/*.jsonl"
]

def import_professor_docs():
    print("=" * 60)
    print("📤 Vertex AI Search - 교수정보 JSONL Import 시작")
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
    import_professor_docs()
