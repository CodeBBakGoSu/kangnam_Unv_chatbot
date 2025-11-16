"""
졸업요건 검색 도구

현재 사용: Vertex AI Search (search_tools.py)
백업용: RAG (rag_search_tools.py - 사용 안 함)
"""

# Vertex AI Search 도구 (현재 사용 중)
from .search_tools import (
    search_graduation_requirements,
    search_by_year_and_college,
    search_by_department,
    get_available_information,
    search_graduation_requirements_tool,
    search_by_year_and_college_tool,
    search_by_department_tool,
    get_available_information_tool,
    ALL_GRADUATION_TOOLS
)

# RAG 도구 (백업용 - 사용 안 함)
# 필요시 아래 주석 해제:
# from .rag_search_tools import (
#     search_graduation_requirements_rag,
#     search_by_year_and_college_rag,
#     ALL_RAG_GRADUATION_TOOLS
# )

__all__ = [
    # Vertex AI Search 도구
    'search_graduation_requirements',
    'search_by_year_and_college',
    'search_by_department',
    'get_available_information',
    'search_graduation_requirements_tool',
    'search_by_year_and_college_tool',
    'search_by_department_tool',
    'get_available_information_tool',
    'ALL_GRADUATION_TOOLS',
]

