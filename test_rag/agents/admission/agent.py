"""
입학 Agent (AdmissionAgent) - Placeholder

입학 정보 (전형, 모집요강, 지원 방법 등) 검색 전문 Agent
추후 구현 예정
"""

import vertexai
from google.adk.agents import Agent
from test_rag.config import PROJECT_ID, VERTEX_AI_LOCATION

# Vertex AI 초기화
vertexai.init(project=PROJECT_ID, location=VERTEX_AI_LOCATION)

# 입학 Agent (Placeholder)
admission_agent = Agent(
    model='gemini-2.0-flash',
    name='admission_agent',
    description='강남대학교 입학 정보(전형, 모집요강, 지원 방법, 입학 일정 등)를 검색하는 전문 에이전트입니다.',
    instruction='''
    당신은 강남대학교의 **입학 정보 전문 상담 에이전트**입니다.
    
    [현재 구현 중입니다]
    
    전문 분야 (예정):
    - 입학 전형 종류
    - 모집요강
    - 지원 방법 및 절차
    - 입학 일정
    - 지원 자격
    - 전형료
    
    현재는 "입학 정보 기능은 준비 중입니다"라고 안내해주세요.
    ''',
    tools=[]  # 추후 tools 추가
)

