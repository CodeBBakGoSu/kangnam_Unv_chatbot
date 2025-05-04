from typing import Dict, Any, List
import os
from dotenv import load_dotenv
import google.generativeai as genai

class BaseAgent:
    def __init__(self):
        # .env 파일 로드
        load_dotenv()
        
        # API 키를 환경 변수에서 가져오기
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 환경 변수에 설정되지 않았습니다.")
        
        # Gemini API 클라이언트 초기화
        self.client = genai.Client(api_key=api_key)
        
        # 대화 기록을 저장하는 메모리
        self.memory: List[Dict[str, Any]] = []
    
    def add_to_memory(self, message: Dict[str, Any]):
        """대화 기록을 메모리에 추가"""
        self.memory.append(message)
    
    def get_memory(self) -> List[Dict[str, Any]]:
        """메모리 반환"""
        return self.memory
    
    def clear_memory(self):
        """메모리 초기화"""
        self.memory = []
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """메시지 처리 기본 메서드"""
        raise NotImplementedError("Subclasses must implement process method") 