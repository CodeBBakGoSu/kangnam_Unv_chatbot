from typing import Dict, Any
from .base_agent import BaseAgent

class PersonalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.system_prompt = """당신은 강남대학교 소프트웨어응용학부 학생들의 개인 맞춤형 정보를 제공하는 챗봇입니다.
        다음 주제에 대해 개인화된 정보를 제공해주세요:
        - 수강 중인 과목 정보
        - 과제 제출 현황
        - 출석 현황
        - 개인별 공지사항
        - 성적 정보
        
        사용자의 개인 정보를 안전하게 다루고, 필요한 경우 인증을 요청해주세요."""
    
    async def answer(self, message: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """개인 맞춤형 정보 질문에 답변"""
        if not user_context:
            return {
                "response": "죄송합니다. 개인 정보를 확인하기 위해서는 로그인이 필요합니다.",
                "requires_auth": True
            }
        
        prompt = f"{self.system_prompt}\n\n사용자 정보: {user_context}\n\n사용자 메시지: {message}"
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return {
                "response": response.text,
                "requires_auth": True
            }
        except Exception as e:
            return {
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "requires_auth": True
            } 