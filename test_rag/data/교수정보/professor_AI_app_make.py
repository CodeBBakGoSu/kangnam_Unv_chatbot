from typing import List
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

# ----------------------------
# ⚙️ 환경 설정
# ----------------------------
project_id = "kangnamuniv-professor-info"  # 예: kangnamuniv-ai
location = "global"
engine_id = "kangnamuniv-professor-search"
data_store_ids = ["kangnamuniv-professor-info-datastore"]

# ----------------------------
# 🚀 엔진 생성 함수
# ----------------------------
def create_engine_sample(
    project_id: str,
    location: str,
    engine_id: str,
    data_store_ids: List[str],
) -> str:
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    client = discoveryengine.EngineServiceClient(client_options=client_options)

    parent = client.collection_path(
        project=project_id,
        location=location,
        collection="default_collection",
    )

    engine = discoveryengine.Engine(
        display_name="강남대학교 교수정보 검색 엔진",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
        search_engine_config=discoveryengine.Engine.SearchEngineConfig(
            search_tier=discoveryengine.SearchTier.SEARCH_TIER_ENTERPRISE,
            # LLM 기능 제거 → Add-on 미설정
            search_add_ons=[discoveryengine.SearchAddOn.SEARCH_ADD_ON_UNSPECIFIED],
        ),
        data_store_ids=data_store_ids,
    )

    request = discoveryengine.CreateEngineRequest(
        parent=parent,
        engine=engine,
        engine_id=engine_id,
    )

    operation = client.create_engine(request=request)
    print(f"엔진 생성 중... 작업 ID: {operation.operation.name}")
    response = operation.result()
    print("✅ 엔진 생성 완료!")

    metadata = discoveryengine.CreateEngineMetadata(operation.metadata)
    print(response)
    print(metadata)
    return operation.operation.name


if __name__ == "__main__":
    create_engine_sample(project_id, location, engine_id, data_store_ids)
