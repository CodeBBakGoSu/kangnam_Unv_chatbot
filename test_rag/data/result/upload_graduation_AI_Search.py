"""
강남대학교 졸업요건 데이터 Vertex AI Search 임포트 스크립트

사용법:
    1. JSONL 파일을 GCS 버킷에 업로드:
       gsutil cp kangnam_univ_graduation_requirements.jsonl gs://kangnam-univ/rag_data/graduation/
    
    2. 이 스크립트 실행:
       python test_rag/data/result/upload_graduation_AI_Search.py
"""

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

PROJECT_ID = "kangnam-backend"
LOCATION = "global"
DATA_STORE_ID = "kangnam-univ-graduation-requirements-datastore"

# GCS 버킷 경로 (와일드카드 사용 가능)
GCS_INPUT_URIS = [
    "gs://kangnam-univ/rag_data/kangnam_univ_graduation_requirements_2017_2025.jsonl"
]

def import_graduation_docs():
    print("=" * 60)
    print("📤 Vertex AI Search - 졸업요건 JSONL Import 시작")
    print("=" * 60)
    print(f"📦 프로젝트: {PROJECT_ID}")
    print(f"🆔 데이터스토어: {DATA_STORE_ID}")
    print(f"📁 소스: {GCS_INPUT_URIS[0]}")
    print("=" * 60)
    
    # 클라이언트 설정
    client_options = ClientOptions(api_endpoint="global-discoveryengine.googleapis.com")
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # branch 경로 설정 (기본값은 항상 "default_branch")
    parent = client.branch_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATA_STORE_ID,
        branch="default_branch",
    )

    # GCS 소스 구성
    gcs_source = discoveryengine.GcsSource(
        input_uris=GCS_INPUT_URIS,
        data_schema="custom",  # JSONL 커스텀 포맷
    )

    # 임포트 요청 구성
    import_request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
        auto_generate_ids=True,  # 문서 ID 자동 생성 (JSONL에 id 필드가 없으므로)
    )

    # 실행
    print("\n🚀 문서 가져오기 요청 중...")
    operation = client.import_documents(request=import_request)
    print(f"🕐 작업 ID: {operation.operation.name}")
    print("⏳ 데이터 수집 중... (약 1~3분 소요)")

    try:
        result = operation.result(timeout=600)
        print("\n✅ 데이터 가져오기 완료!")
        print("=" * 60)
        print(f"📊 결과: {result}")
        print("=" * 60)
        
        print("\n🎉 졸업요건 데이터가 성공적으로 임포트되었습니다!")
        print("\n🔍 메타데이터 검색 가능 필드:")
        print("   - college: 복지융합대학, 경영관리대학, 공과대학 등")
        print("   - division: 인문사회, 공학, 예체능")
        print("   - department: 학과/전공명")
        print("   - year_range: 2017~2020, 2021~2024, 2025 이후")
        print("   - category: 졸업요건, 교양이수표")
        
    except Exception as e:
        print(f"\n❌ 임포트 실패: {e}")
        print("\n💡 확인사항:")
        print("  1. GCS 버킷에 JSONL 파일이 업로드되어 있는지 확인")
        print("  2. 서비스 계정에 GCS 읽기 권한이 있는지 확인")
        print("  3. 데이터스토어가 이미 생성되어 있는지 확인")

if __name__ == "__main__":
    import_graduation_docs()

