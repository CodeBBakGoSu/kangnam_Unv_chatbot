from typing import Dict, Any
from .base_agent import BaseAgent
import google.generativeai as genai
import os
from dotenv import load_dotenv

class CommonAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        load_dotenv()
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-001')
        self.system_prompt = """당신은 강남대학교 소프트웨어응용학부의 학사 정보를 제공하는 챗봇입니다.
        다음 주제에 대해 정확하고 상세한 정보를 제공해주세요:
        - 학사 제도
        - 졸업 요건
        - 수강신청 방법
        - 학과 공지사항
        - 교수 정보
        - 시설 정보
        
        정보를 제공할 때는 항상 공식적인 태도를 유지하고, 정확한 정보를 제공해주세요."""
    
    def count_tokens(self, text: str) -> int:
        try:
            return self.model.count_tokens(text).total_tokens
        except Exception:
            return 0

    async def answer(self, message: str) -> Dict[str, Any]:
        """공통 정보 질문에 답변"""
        prompt = f"{self.system_prompt}\n\n사용자 메시지: {message}"
        try:
            response = self.model.generate_content(prompt)
            prompt_tokens = self.count_tokens(prompt)
            response_tokens = self.count_tokens(response.text)
            token_usage = {
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": prompt_tokens + response_tokens
            }
            return {
                "response": response.text,
                "requires_auth": False,
                "token_usage": token_usage
            }
        except Exception as e:
            return {
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "requires_auth": False,
                "token_usage": None
            } 