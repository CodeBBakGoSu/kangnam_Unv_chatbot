"""
강남대학교 졸업요건 검색 도구 (Vertex AI Search)

현재 사용: Vertex AI Search (이 파일)
  - 빠르고 정확한 메타데이터 기반 검색
  - 메타데이터 필터링 지원 (college, division, department, year_range, category)

백업용: RAG (rag_search_tools.py)
  - 사용 안 함
  - 필요시 rag_search_tools.py에서 import하여 재활성화 가능
  - 예: from .rag_search_tools import ALL_RAG_GRADUATION_TOOLS
"""

import json
from google.adk.tools import FunctionTool
from google.auth import default
from google.auth.transport.requests import Request
from typing import Dict, Optional, Any

# ============================================================================
# Vertex AI Search 기반 검색 도구
# ============================================================================

# Vertex AI Search 엔진 endpoint
VERTEX_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-univ-graduation-re_1762133185323/"
    "servingConfigs/default_search:search"
)


# 공통 함수: Vertex AI Search API 호출
def vertex_ai_search_request(query: str, page_size: int = 10) -> Dict[str, Any]:
    """
    Vertex AI Search API를 호출하고 결과를 반환합니다.
    
    Args:
        query: 검색 질문
        page_size: 반환할 결과 개수 (기본값: 10)
    
    Returns:
        검색 결과 딕셔너리
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
                
                # content와 metadata 추출
                content = structured.get("content", "")
                metadata = structured.get("metadata", {})
                
                formatted_results.append({
                    "rank": i,
                    "content": content,
                    "metadata": metadata,
                    "college": metadata.get("college", "N/A"),
                    "division": metadata.get("division", "N/A"),
                    "department": metadata.get("department", "N/A"),
                    "year_range": metadata.get("year_range", "N/A"),
                    "category": metadata.get("category", "N/A")
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
            "message": f"검색 중 오류 발생: {str(e)}"
        }


def search_graduation_requirements(query: str, page_size: Optional[int] = 10) -> Dict[str, Any]:
    """
    강남대학교 졸업이수학점 및 교양과목 정보를 검색합니다.
    
    Args:
        query: 사용자 질문 (예: "2024년 입학생 복지융합대학 졸업 요건은?")
        page_size: 반환할 최대 결과 개수 (기본값: 10)
    
    Returns:
        검색 결과를 포함한 딕셔너리:
        - status: "success" 또는 "error"
        - results: 검색된 문서 리스트 (content, metadata 포함)
        - count: 결과 개수
        - query: 원본 질문
        - message: 상태 메시지
    """
    return vertex_ai_search_request(query, page_size)


def search_by_year_and_college(
    year: str,
    college: str,
    category: str = "졸업요건",
    page_size: Optional[int] = 5
) -> Dict[str, Any]:
    """
    학년도와 대학으로 특정 정보를 검색합니다.
    
    이 함수는 더 구조화된 검색을 제공합니다.
    예: "2024년 입학생" + "복지융합대학" + "졸업요건"
    
    Args:
        year: 입학 연도 (예: "2024", "2019")
        college: 대학 이름 (예: "복지융합대학", "공과대학")
        category: 정보 종류 ("졸업요건" 또는 "교양이수표")
        page_size: 반환할 결과 개수
    
    Returns:
        검색 결과 딕셔너리
    """
    # 학년도 매핑
    year_int = int(year)
    if 2017 <= year_int <= 2020:
        year_range_query = "2017~2020"
    elif 2021 <= year_int <= 2024:
        year_range_query = "2021~2024"
    elif year_int >= 2025:
        year_range_query = "2025 이후"
    else:
        year_range_query = year
    
    # 구조화된 쿼리 생성
    query = f"{year_range_query} {college} {category}"
    
    # 검색 실행
    result = search_graduation_requirements(query=query, page_size=page_size)
    
    # 결과에 검색 조건 추가
    if result["status"] == "success":
        result["search_criteria"] = {
            "year": year,
            "year_range": year_range_query,
            "college": college,
            "category": category
        }
    
    return result


def search_by_department(
    department: str,
    year: Optional[str] = None,
    category: str = "졸업요건"
) -> Dict[str, Any]:
    """
    학과/전공으로 졸업요건을 검색합니다.
    
    Args:
        department: 학과/전공 이름 (예: "소프트웨어응용학부", "사회복지학전공")
        year: 입학 연도 (선택, 예: "2024")
        category: 정보 종류 ("졸업요건" 또는 "교양이수표")
    
    Returns:
        검색 결과 딕셔너리
    """
    if year:
        query = f"{year} {department} {category}"
    else:
        query = f"{department} {category}"
    
    return vertex_ai_search_request(query, page_size=5)


def get_available_information() -> Dict[str, Any]:
    """
    사용 가능한 정보 목록을 반환합니다.
    
    사용자가 "어떤 정보를 검색할 수 있어?" 같은 질문을 할 때 사용.
    
    Returns:
        사용 가능한 대학, 학년도 범위, 카테고리 정보
    """
    return {
        "status": "success",
        "available_data": {
            "colleges": [
                "복지융합대학",
                "경영관리대학",
                "글로벌인재대학 / 글로벌문화콘텐츠대학",
                "공과대학 / ICT건설복지융합대학",
                "예체능대학",
                "사범대학"
            ],
            "year_ranges": [
                "2017~2020학년도 입학자",
                "2021~2024학년도 입학자",
                "2025학년도 이후 입학자"
            ],
            "categories": [
                "졸업요건 (기초교양, 계열교양, 균형교양, 전공학점, 최소졸업학점)",
                "교양이수표 (기초교양 과목, 계열교양 과목, 균형교양 요건)"
            ],
            "search_examples": [
                "2024년 입학생 복지융합대학 졸업 요건",
                "공과대학 기초교양 과목",
                "2019년 입학생 최소 졸업학점",
                "사범대학 교양이수표"
            ]
        },
        "message": "강남대학교 졸업이수학점 및 교양과목 정보를 Vertex AI Search로 검색할 수 있습니다.",
        "search_engine": "Vertex AI Search (Discovery Engine)"
    }


# Google ADK FunctionTool로 변환
# 이렇게 하면 AI Agent가 자동으로 이 함수들을 사용할 수 있습니다
search_graduation_requirements_tool = FunctionTool(search_graduation_requirements)
search_by_year_and_college_tool = FunctionTool(search_by_year_and_college)
search_by_department_tool = FunctionTool(search_by_department)
get_available_information_tool = FunctionTool(get_available_information)


# 졸업요건 Agent 전용 도구들
ALL_GRADUATION_TOOLS = [
    search_graduation_requirements_tool,
    search_by_year_and_college_tool,
    search_by_department_tool,
    get_available_information_tool
]

