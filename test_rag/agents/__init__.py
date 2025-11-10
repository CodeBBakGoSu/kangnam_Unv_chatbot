"""
강남대학교 RAG Agent Team

각 도메인별로 특화된 Sub-Agent들
"""

from .graduation.agent import graduation_agent
from .subject.agent import subject_agent
from .basic_info.agent import basic_info_agent
# from .professor.agent import professor_agent  # 추후 추가
# from .admission.agent import admission_agent   # 추후 추가

__all__ = [
    'graduation_agent',
    'subject_agent',
    'basic_info_agent',
    # 'professor_agent',
    # 'admission_agent',
]

