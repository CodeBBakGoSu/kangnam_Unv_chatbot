from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseAgent

class AcademicAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 강남대학교 소프트웨어응용학부의 학사 담당자입니다.
            다음 정보를 바탕으로 학생들의 학사 관련 질문에 답변해주세요:
            
            - 졸업요건: 총 130학점 (전공 60학점, 교양 30학점, 자유선택 40학점)
            - 전공필수: 21학점
            - 전공선택: 39학점
            - 교양필수: 15학점
            - 교양선택: 15학점
            
            답변은 친절하고 명확하게 해주시되, 모르는 내용은 솔직하게 말씀해주세요."""),
            ("human", "{input}")
        ])
    
    async def answer(self, message: str) -> Dict[str, Any]:
        """학사 관련 질문에 답변"""
        chain = self.prompt | self.llm
        result = await chain.ainvoke({"input": message})
        return {
            "response": result.content,
            "source": "academic_agent"
        } 