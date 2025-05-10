from typing import Dict, Any
from .base_agent import BaseAgent
import google.generativeai as genai
import os
from dotenv import load_dotenv

class GeneralAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        load_dotenv()
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-001')
        self.system_prompt = """당신은 강남대학교 학생들을 위한 친근한 챗봇입니다.
        다음 주제에 대해 친절하고 자연스럽게 대화해주세요:
        - 기타 잡담
        
        항상 친근하고 도움이 되는 태도로 응답해주세요."""
    
    def count_tokens(self, text: str) -> int:
        try:
            return self.model.count_tokens(text).total_tokens
        except Exception:
            return 0

    async def answer(self, message: str) -> Dict[str, Any]:
        """일반적인 질문에 답변"""
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