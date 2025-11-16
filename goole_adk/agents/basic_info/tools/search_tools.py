"""
강남대학교 건물/시설 정보 및 행정부서 연락처 검색 도구 (Vertex AI Search 기반)
"""

import json
from google.adk.tools import FunctionTool
from google.auth import default
from google.auth.transport.requests import Request
from typing import Dict, Any, Optional

# Vertex AI Search 엔진 endpoint - 건물/시설 정보
BUILDING_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-building-informati_1762755276541/"
    "servingConfigs/default_search:search"
)

# Vertex AI Search 엔진 endpoint - 행정부서 연락처
ADMIN_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-admin-info_1762756510225/"
    "servingConfigs/default_search:search"
)

# 공통 함수: Vertex AI Search API 호출
def vertex_ai_search_request(query: str, endpoint: str, page_size: int = 10) -> Dict[str, Any]:
    """
    Vertex AI Search API를 curl 호출 형태로 실행하고 결과를 반환.
    """
    try:
        # Google Auth 라이브러리로 access token 가져오기 (배포 환경 호환)
        credentials, project = default()
        if not credentials.valid:
            credentials.refresh(Request())
        token = credentials.token
        
        payload = {
            "query": query,
            "pageSize": page_size,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "languageCode": "ko",
            "userInfo": {"timeZone": "Asia/Seoul"}
        }
        
        # API 호출
        import requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(endpoint, headers=headers, json=payload)
        result = response.json()
        
        # 정리된 형태로 반환
        if "results" in result:
            formatted_results = []
            for i, item in enumerate(result["results"], start=1):
                doc = item.get("document", {})
                structured = doc.get("structData", {})
                formatted_results.append({
                    "rank": i,
                    "title": doc.get("id"),
                    "snippet": item.get("snippet", ""),
                    "fields": structured
                })
            
            return {
                "status": "success",
                "count": len(formatted_results),
                "query": query,
                "results": formatted_results,
                "message": f"'{query}'에 대한 검색 결과 {len(formatted_results)}개를 찾았습니다."
            }
        else:
            return {
                "status": "error",
                "query": query,
                "message": "검색 결과가 없습니다.",
                "raw_response": result
            }
        
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "message": str(e)
        }
        
def search_building_by_name(building_name: str) -> Dict[str, Any]:
    """
    건물명으로 검색합니다.
    """
    return vertex_ai_search_request(f"{building_name}", BUILDING_SEARCH_ENDPOINT)

def search_facility_by_location(building: str, floor: Optional[str] = None) -> Dict[str, Any]:
    """
    건물과 층으로 시설 검색
    """
    if floor:
        query = f"{building} {floor}"
    else:
        query = f"{building} 시설"
    return vertex_ai_search_request(query, BUILDING_SEARCH_ENDPOINT)

def search_facility_by_name(facility_name: str) -> Dict[str, Any]:
    """
    시설명으로 검색
    """
    query = f"{facility_name}"
    return vertex_ai_search_request(query, BUILDING_SEARCH_ENDPOINT)

def search_building_info(query: str) -> Dict[str, Any]:
    """
    자유 입력형 검색 (건물/시설)
    """
    return vertex_ai_search_request(query, BUILDING_SEARCH_ENDPOINT)

def search_admin_department(query: str) -> Dict[str, Any]:
    """
    행정부서 및 연락처 검색
    """
    return vertex_ai_search_request(query, ADMIN_SEARCH_ENDPOINT)

def search_department_by_name(department_name: str) -> Dict[str, Any]:
    """
    부서명으로 검색
    """
    return vertex_ai_search_request(f"{department_name}", ADMIN_SEARCH_ENDPOINT)

def search_contact_info(query: str) -> Dict[str, Any]:
    """
    연락처 정보 검색 (전화번호, 팩스, 위치)
    """
    return vertex_ai_search_request(f"{query} 연락처", ADMIN_SEARCH_ENDPOINT)


search_building_info_tool = FunctionTool(search_building_info)
search_building_by_name_tool = FunctionTool(search_building_by_name)
search_facility_by_location_tool = FunctionTool(search_facility_by_location)
search_facility_by_name_tool = FunctionTool(search_facility_by_name)
search_admin_department_tool = FunctionTool(search_admin_department)
search_department_by_name_tool = FunctionTool(search_department_by_name)
search_contact_info_tool = FunctionTool(search_contact_info)

ALL_BASIC_INFO_TOOLS = [
    search_building_info_tool,
    search_building_by_name_tool,
    search_facility_by_location_tool,
    search_facility_by_name_tool,
    search_admin_department_tool,
    search_department_by_name_tool,
    search_contact_info_tool,
]

