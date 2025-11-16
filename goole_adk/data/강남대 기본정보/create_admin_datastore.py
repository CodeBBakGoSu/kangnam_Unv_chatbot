"""
강남대학교 행정부서 연락처 Vertex AI Search 데이터 스토어 생성 스크립트

사용법:
    python goole_adk/data/강남대\ 기본정보/create_admin_datastore.py
"""

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine
import time

# ==============================
# 설정
# ==============================
PROJECT_ID = "kangnam-backend"
LOCATION = "global"  # or "us-east4" (리전 통일)
DATA_STORE_ID = "kangnam-univ-admin-contacts-datastore"  # 고유 ID (RFC-1034 준수)

# ==============================
# 실행
# ==============================
print("=" * 60)
print("🔍 강남대학교 행정부서 연락처 Vertex AI Search 데이터 스토어 생성")
print("=" * 60)
print(f"📦 프로젝트: {PROJECT_ID}")
print(f"🌍 리전: {LOCATION}")
print(f"🆔 데이터스토어 ID: {DATA_STORE_ID}")
print("=" * 60)

try:
    # 클라이언트 설정
    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # 부모 경로 설정
    parent = client.collection_path(
        project=PROJECT_ID,
        location=LOCATION,
        collection="default_collection",
    )

    # 데이터스토어 구성
    data_store = discoveryengine.DataStore(
        display_name="강남대학교 행정부서 연락처 검색 스토어",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.NO_CONTENT,
    )

    # 생성 요청
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=DATA_STORE_ID,
        data_store=data_store,
    )

    print("\n🚀 데이터 스토어 생성 요청 중...")
    operation = client.create_data_store(request=request)
    print(f"🕐 작업 ID: {operation.operation.name}")

    # 완료 대기
    print("\n⏳ 작업 진행 중... (약 1~3분 소요)")
    response = operation.result(timeout=600)

    print("\n✅ 데이터 스토어 생성 완료!")
    print("=" * 60)
    print(f"📋 이름: {response.display_name}")
    print(f"🆔 ID: {DATA_STORE_ID}")
    print(f"🔗 리소스 경로: {response.name}")
    print("=" * 60)

    print("\n📝 다음 단계:")
    print("1️⃣ 행정부서 연락처 JSONL 파일을 Cloud Storage 버킷에 업로드합니다.")
    print("2️⃣ 'import_documents' API로 데이터를 데이터스토어에 추가합니다.")
    print("3️⃣ upload_admin_to_ai_search.py 스크립트를 실행하세요.")

except Exception as e:
    print("\n❌ 데이터스토어 생성 실패")
    print(f"에러: {e}")
    print("\n💡 확인사항:")
    print("  1. 인증: gcloud auth application-default login")
    print("  2. 역할: Vertex AI Search Admin 또는 Vertex AI User 권한 필요")
    print("  3. API 활성화: Vertex AI Search API (Discovery Engine)")
    print("  4. data_store_id 형식 확인 (소문자, 숫자, 하이픈만 허용)")

