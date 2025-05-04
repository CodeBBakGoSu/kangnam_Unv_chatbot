from typing import Dict, Any, List
from google import genai

class BaseAgent:
    def __init__(self):
        # Gemini 모델 초기화
        self.client = genai.Client(api_key="AIzaSyBTFbN8a9clizv4u1Us1wE_1o8kRsuJ24Y")
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