"""
채팅 서비스 - Vertex AI Agent Engine과 통신
"""
import time
import uuid
import vertexai
from vertexai import agent_engines
from typing import Generator, Dict, Any
import config

class ChatService:
    """Agent Engine과 통신하는 서비스"""
    
    def __init__(self):
        """Vertex AI 및 Agent Engine 초기화"""
        # Vertex AI 초기화
        vertexai.init(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION
        )
        
        # 배포된 Agent Engine 가져오기
        self.engine = agent_engines.get(config.AGENT_RESOURCE_ID)
    
    def create_new_chat(self) -> Dict[str, str]:
        """
        새 채팅 시작 - 익명 user_id 생성 + 세션 생성
        
        Returns:
            {"user_id": "anon_xxx", "session_id": "session_yyy"}
        """
        # 익명 사용자 ID 생성
        user_id = f"anon_{uuid.uuid4().hex[:8]}"
        
        # 세션 생성
        session_response = self.engine.create_session(user_id=user_id)
        
        # 세션 ID 추출
        if isinstance(session_response, dict):
            session_id = session_response.get('name', '').split('/')[-1]
            if not session_id:
                session_id = session_response.get('id', str(session_response))
        else:
            session_id = str(session_response)
        
        return {
            "user_id": user_id,
            "session_id": session_id
        }
    
    def stream_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> Generator[str, None, None]:
        """
        메시지 전송 및 스트리밍 응답
        
        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            message: 사용자 메시지
            
        Yields:
            Agent 응답 텍스트 (작은 청크로 스트리밍)
        """
        try:
            # Reasoning Engine에 메시지 전송 (스트리밍)
            for event in self.engine.stream_query(
                user_id=user_id,
                session_id=session_id,
                message=message
            ):
                # 응답에서 텍스트 추출
                text = self._extract_text(event)
                if text:
                    # 텍스트를 문자 단위로 나눠서 전송 (한글도 정상 처리)
                    # 한 글자씩 전송 (프론트엔드에서 지연 처리)
                    for char in text:
                        yield char
        
        except Exception as e:
            # 에러 발생 시 에러 메시지 반환
            yield f"\n\n[오류] {str(e)}"
    
    def _extract_text(self, event: Dict[str, Any]) -> str:
        """
        Agent Engine 응답 이벤트에서 텍스트 추출
        
        Args:
            event: Agent Engine 응답 이벤트
            
        Returns:
            추출된 텍스트 또는 빈 문자열
        """
        if not isinstance(event, dict):
            return ""
        
        # content.parts[].text 구조에서 텍스트 추출
        content = event.get('content', {})
        parts = content.get('parts', [])
        
        for part in parts:
            if isinstance(part, dict) and 'text' in part:
                return part['text']
        
        return ""

# 싱글톤 인스턴스 (앱 시작 시 한 번만 초기화)
_chat_service_instance = None

def get_chat_service() -> ChatService:
    """
    ChatService 싱글톤 인스턴스 반환
    
    FastAPI dependency injection용
    """
    global _chat_service_instance
    
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    
    return _chat_service_instance

