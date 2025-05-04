from typing import Dict, Any
from .base_agent import BaseAgent

class GeneralAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.system_prompt = """당신은 강남대학교 소프트웨어응용학부 학생들을 위한 친근한 챗봇입니다.
        다음 주제에 대해 친절하고 자연스럽게 대화해주세요:
        - 학교 생활 일반
        - 동아리 정보
        - 장학금 정보
        - 기숙사 정보
        - 기타 잡담
        
        항상 친근하고 도움이 되는 태도로 응답해주세요."""
    
    async def answer(self, message: str) -> Dict[str, Any]:
        """일반적인 질문에 답변"""
        prompt = f"{self.system_prompt}\n\n사용자 메시지: {message}"
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return {
                "response": response.text,
                "requires_auth": False
            }
        except Exception as e:
            return {
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "requires_auth": False
            } 