from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import get_chat_response
from app.utils.jwt import get_current_user
from typing import Dict, Any
import logging
import datetime

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    챗봇 메시지 처리 및 응답 생성
    """
    try:
        response = await get_chat_response(
            message=request.message,
            user_context=current_user
        )
        
        return ChatResponse(
            message=request.message,
            response=response["response"],
            current_flow=response.get("current_flow"),
            rag_chunks=response.get("rag_chunks")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/test", response_model=ChatResponse)
async def chat_test(request: ChatRequest):
    """
    인증 없이 테스트 가능한 챗봇 메시지 처리 및 응답 생성
    
    개발 및 테스트 환경에서만 사용해야 합니다.
    """
    try:
        logger.info(f"테스트 엔드포인트 호출: 메시지='{request.message}'")
        
        # 테스트용 더미 사용자 컨텍스트
        test_user = {
            "username": "test_user",
            "name": "테스트 사용자",
            "department": "소프트웨어응용학부",
            "courses": [
                {
                    "title": "캡스톤디자인(SW)I",
                    "professor": "최인엽"
                },
                {
                    "title": "AIoT소프트웨어[00]",
                    "professor": "김교수"
                }
            ]
        }
        
        logger.info("테스트 사용자 컨텍스트 생성 완료")
        
        # 응답 생성
        response = await get_chat_response(
            message=request.message,
            user_context=test_user
        )
        
        logger.info(f"테스트 응답 생성 완료: 플로우={response.get('current_flow')}, 청크 수={len(response.get('rag_chunks', []))}개")
        
        chat_response = ChatResponse(
            message=request.message,
            response=response["response"],
            current_flow=response.get("current_flow"),
            rag_chunks=response.get("rag_chunks")
        )
        
        # 응답에 디버그 정보 추가
        debug_info = {
            "test_mode": True,
            "user": "test_user",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if hasattr(chat_response, "model_dump"):
            result_dict = chat_response.model_dump()
            result_dict["debug"] = debug_info
            return result_dict
        else:
            # 이전 버전 Pydantic 호환성
            chat_response_dict = chat_response.dict()
            chat_response_dict["debug"] = debug_info
            return chat_response_dict
            
    except Exception as e:
        logger.error(f"테스트 응답 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        ) 