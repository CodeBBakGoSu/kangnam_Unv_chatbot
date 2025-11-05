"""
강남대학교 RAG 검색 도구

사용자 질문에 대해 졸업이수학점 및 교양과목 정보를 검색하는 도구
"""

import vertexai
from vertexai.preview import rag
from google.adk.tools import FunctionTool
from typing import Dict, Optional, Any, List
from test_rag.config import (
    PROJECT_ID,
    VERTEX_AI_LOCATION,
    KANGNAM_CORPUS_ID,
    RAG_DEFAULT_TOP_K,
    RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD
)

# Vertex AI 초기화
vertexai.init(project=PROJECT_ID, location=VERTEX_AI_LOCATION)

# 강남대 코퍼스 전체 경로
KANGNAM_CORPUS_NAME = f"projects/{PROJECT_ID}/locations/{VERTEX_AI_LOCATION}/ragCorpora/{KANGNAM_CORPUS_ID}"


def search_graduation_requirements(
    query: str,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    강남대학교 졸업이수학점 및 교양과목 정보를 검색합니다.
    
    사용자가 질문하면 자동으로:
    1. 질문을 벡터로 변환 (임베딩)
    2. 코퍼스에서 유사한 문서 검색
    3. 관련 정보 반환 (학년도, 대학, 계열 정보 포함)
    
    Args:
        query: 사용자 질문 (예: "2024년 입학생 복지융합대학 졸업 요건은?")
        top_k: 반환할 최대 결과 개수 (기본값: 5)
        similarity_threshold: 유사도 임계값 0~1 (기본값: 0.3, 낮을수록 더 많은 결과)
    
    Returns:
        검색 결과를 포함한 딕셔너리:
        - status: "success" 또는 "error"
        - results: 검색된 문서 리스트
        - count: 결과 개수
        - query: 원본 질문
        - message: 상태 메시지
        
    내부 동작:
        1. query를 text-multilingual-embedding-002 모델로 임베딩
        2. 코퍼스 내 모든 chunk와 벡터 유사도 계산
        3. similarity_threshold 이상인 것만 필터링
        4. 유사도 순으로 정렬하여 top_k개 반환
        5. 각 결과에 메타데이터 포함 (year_range, college, division 등)
    """
    # 기본값 설정
    if top_k is None:
        top_k = RAG_DEFAULT_TOP_K
    if similarity_threshold is None:
        similarity_threshold = RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD
    
    try:
        # 1. RAG Resource 생성 (코퍼스 지정)
        rag_resource = rag.RagResource(
            rag_corpus=KANGNAM_CORPUS_NAME
        )
        
        # 2. 검색 설정 (top_k, 유사도 임계값)
        retrieval_config = rag.RagRetrievalConfig(
            top_k=top_k,
            filter=rag.Filter(
                vector_distance_threshold=similarity_threshold
            )
        )
        
        # 3. 검색 실행
        # - query를 임베딩으로 변환 (자동)
        # - 벡터 유사도 계산 (자동)
        # - 유사도 순 정렬 (자동)
        response = rag.retrieval_query(
            rag_resources=[rag_resource],
            text=query,
            rag_retrieval_config=retrieval_config
        )
        
        # 4. 결과 처리
        results = []
        if hasattr(response, "contexts"):
            contexts = response.contexts
            if hasattr(contexts, "contexts"):
                contexts = contexts.contexts
            
            # 각 컨텍스트에서 정보 추출
            for idx, context in enumerate(contexts, 1):
                # 기본 정보
                text = getattr(context, "text", "")
                source_uri = getattr(context, "source_uri", None)
                relevance_score = getattr(context, "relevance_score", None)
                
                # 메타데이터 추출 (있는 경우)
                # 메타데이터는 text 내에 포함되어 있음
                # 예: "[졸업요건 정보]\n대학: 복지융합대학\n계열: 인문사회\n학년도: 2021~2024..."
                
                result = {
                    "rank": idx,
                    "text": text,
                    "source_uri": source_uri,
                    "relevance_score": relevance_score,
                    "relevance_percentage": f"{relevance_score * 100:.1f}%" if relevance_score else "N/A"
                }
                
                results.append(result)
        
        return {
            "status": "success",
            "results": results,
            "count": len(results),
            "query": query,
            "corpus_id": KANGNAM_CORPUS_ID,
            "search_params": {
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            },
            "message": f"'{query}'에 대해 {len(results)}개의 관련 정보를 찾았습니다."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error_message": str(e),
            "message": f"검색 중 오류 발생: {str(e)}"
        }


def search_by_year_and_college(
    year: str,
    college: str,
    category: str = "졸업요건",
    top_k: Optional[int] = 3
) -> Dict[str, Any]:
    """
    학년도와 대학으로 특정 정보를 검색합니다.
    
    이 함수는 더 구조화된 검색을 제공합니다.
    예: "2024년 입학생" + "복지융합대학" + "졸업요건"
    
    Args:
        year: 입학 연도 (예: "2024", "2019")
        college: 대학 이름 (예: "복지융합대학", "공과대학")
        category: 정보 종류 ("졸업요건" 또는 "교양이수표")
        top_k: 반환할 결과 개수
    
    Returns:
        검색 결과 딕셔너리
        
    내부 동작:
        1. year를 year_range로 매핑 (2024 → "2021~2024")
        2. 구조화된 쿼리 생성
        3. search_graduation_requirements 호출
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
    result = search_graduation_requirements(
        query=query,
        top_k=top_k,
        similarity_threshold=0.3
    )
    
    # 결과에 검색 조건 추가
    if result["status"] == "success":
        result["search_criteria"] = {
            "year": year,
            "year_range": year_range_query,
            "college": college,
            "category": category
        }
    
    return result


def get_available_information() -> Dict[str, Any]:
    """
    사용 가능한 정보 목록을 반환합니다.
    
    사용자가 "어떤 정보를 검색할 수 있어?" 같은 질문을 할 때 사용.
    
    Returns:
        사용 가능한 대학, 학년도 범위, 카테고리 정보
        
    내부 동작:
        1. 강남대 코퍼스의 메타데이터 요약 제공
        2. 하드코딩된 정보 (실제로는 코퍼스에서 추출 가능)
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
        "message": "강남대학교 졸업이수학점 및 교양과목 정보를 검색할 수 있습니다.",
        "corpus_info": {
            "corpus_id": KANGNAM_CORPUS_ID,
            "embedding_model": "text-multilingual-embedding-002",
            "language": "한국어"
        }
    }


# Google ADK FunctionTool로 변환
# 이렇게 하면 AI Agent가 자동으로 이 함수들을 사용할 수 있습니다
search_graduation_requirements_tool = FunctionTool(search_graduation_requirements)
search_by_year_and_college_tool = FunctionTool(search_by_year_and_college)
get_available_information_tool = FunctionTool(get_available_information)


# 모든 tool을 리스트로 export
ALL_SEARCH_TOOLS = [
    search_graduation_requirements_tool,
    search_by_year_and_college_tool,
    get_available_information_tool
]

