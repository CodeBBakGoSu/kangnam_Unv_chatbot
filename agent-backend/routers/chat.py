"""
채팅 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.chat_service import ChatService, get_chat_service
import json

router = APIRouter()

# ============================================================================
# Request/Response 모델
# ============================================================================

class MessageRequest(BaseModel):
    """메시지 전송 요청"""
    user_id: str
    session_id: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "anon_a1b2c3d4",
                "session_id": "1234567890",
                "message": "2024년 공과대학 졸업 요건 알려줘"
            }
        }

class NewChatResponse(BaseModel):
    """새 채팅 응답"""
    user_id: str
    session_id: str
    message: str = "새 채팅이 시작되었습니다."

# ============================================================================
# API 엔드포인트
# ============================================================================

@router.post("/new", response_model=NewChatResponse)
async def create_new_chat(
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    새 채팅 시작
    
    - 익명 user_id 자동 생성
    - Agent Engine에 새 세션 생성
    - user_id와 session_id 반환
    
    프론트엔드는 이 정보를 저장해서 메시지 전송 시 사용
    """
    try:
        result = chat_service.create_new_chat()
        
        return NewChatResponse(
            user_id=result["user_id"],
            session_id=result["session_id"],
            message="새 채팅이 시작되었습니다."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"세션 생성 실패: {str(e)}"
        )

@router.post("/message")
async def send_message(
    request: MessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    메시지 전송 및 스트리밍 응답
    
    - Agent Engine에 메시지 전송
    - SSE (Server-Sent Events) 방식으로 스트리밍 응답
    - 프론트엔드는 EventSource 또는 fetch로 수신
    
    응답 포맷:
        data: {"text": "응답 텍스트", "done": false}
        data: {"text": "", "done": true}
    """
    try:
        async def event_generator():
            """SSE 이벤트 생성기"""
            try:
                # Agent Engine에서 스트리밍 응답 받기
                for text_chunk in chat_service.stream_message(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    message=request.message
                ):
                    # SSE 포맷으로 전송
                    event_data = {
                        "text": text_chunk,
                        "done": False
                    }
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                
                # 스트림 종료 신호
                yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"
            
            except Exception as e:
                # 에러 발생 시
                error_data = {
                    "text": f"[오류] {str(e)}",
                    "done": True,
                    "error": True
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"메시지 전송 실패: {str(e)}"
        )

