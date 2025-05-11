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
            # 최신 API 방식으로 수정
            return self.model.count_tokens(contents=text).total_tokens
        except Exception as e:
            print(f"[DEBUG] 토큰 계산 중 오류: {e}")
            return 0

    async def answer(self, message: str) -> Dict[str, Any]:
        """일반 질문에 답변"""
        prompt = f"{self.system_prompt}\n\n사용자 메시지: {message}"
        
        try:
            # 최신 API 방식으로 수정
            response = self.model.generate_content(contents=prompt)
            response_text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            
            # 토큰 사용량 계산 (디버그용)
            prompt_tokens = self.count_tokens(prompt)
            response_tokens = self.count_tokens(response_text)
            token_usage = {
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": prompt_tokens + response_tokens
            }
            
            # 토큰 사용량을 디버그 로그로 출력 (응답에는 포함하지 않음)
            print(f"[DEBUG] 일반 질문 토큰 사용량: {token_usage}")
            
            return {
                "response": response_text,
                "requires_auth": False
            }
        except Exception as e:
            print(f"일반 질문 응답 생성 중 오류 발생: {e}")
            return {
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "requires_auth": False
            } 