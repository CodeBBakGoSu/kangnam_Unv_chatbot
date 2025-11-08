"""
강남대학교 교수정보 검색 도구 (Vertex AI Search 기반)
"""

import json
from google.adk.tools import FunctionTool
from google.auth import default
from google.auth.transport.requests import Request
from typing import Dict, Any, Optional

# Vertex AI Search 엔진 endpoint
VERTEX_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-professor-search-a_1761497936584/"
    "servingConfigs/default_search:search"
)

# 공통 함수: Vertex AI Search API 호출
def vertex_ai_search_request(query: str, page_size: int = 10) -> Dict[str, Any]:
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
        response = requests.post(VERTEX_SEARCH_ENDPOINT, headers=headers, json=payload)
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
        
def search_professor_by_name(query: str) -> Dict[str, Any]:
    """
    교수 이름으로 검색합니다.
    """
    return vertex_ai_search_request(f"{query} 교수")

def search_professor_by_department(college: str, department: Optional[str] = None) -> Dict[str, Any]:
    """
    학과/전공으로 교수 검색
    """
    if department:
        query = f"{college} {department} 교수"
    else:
        query = f"{college} 교수"
    return vertex_ai_search_request(query)

def search_professor_by_research_field(research_field: str) -> Dict[str, Any]:
    """
    연구분야로 교수 검색
    """
    query = f"{research_field} 연구 교수"
    return vertex_ai_search_request(query)

def search_professor_info(query: str) -> Dict[str, Any]:
    """
    자유 입력형 검색
    """
    return vertex_ai_search_request(query)


search_professor_info_tool = FunctionTool(search_professor_info)
search_professor_by_name_tool = FunctionTool(search_professor_by_name)
search_professor_by_department_tool = FunctionTool(search_professor_by_department)
search_professor_by_research_field_tool = FunctionTool(search_professor_by_research_field)

ALL_PROFESSOR_TOOLS = [
    search_professor_info_tool,
    search_professor_by_name_tool,
    search_professor_by_department_tool,
    search_professor_by_research_field_tool,
]
