from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.user import Token, UserLogin
from app.services.auth import authenticate_user, refresh_user_data
from app.utils.jwt import create_access_token, get_current_user
from typing import Dict, Any
from app.etl.supabase_pipeline import clean_user_data, get_user_chunks_count
import os
from app.config import settings

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, run_etl: bool = Query(False, description="전체 ETL 파이프라인 실행 여부")):
    """
    사용자 로그인 및 JWT 토큰 발급
    
    - **username**: 학번
    - **password**: 비밀번호
    - **run_etl**: 전체 ETL 파이프라인(크롤링, 전처리, 청크 생성, 벡터DB 저장) 실행 여부 (기본값: False)
    """
    user = await authenticate_user(form_data.username, form_data.password, run_etl)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 학번 또는 비밀번호입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT 토큰 생성
    access_token = create_access_token(user)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", status_code=200)
async def refresh_data(
    form_data: UserLogin,
    run_full_etl: bool = Query(True, description="전체 ETL 파이프라인 실행 여부")
):
    """
    사용자 데이터 강제 갱신 (캐시 새로고침)
    
    - **username**: 학번
    - **password**: 비밀번호
    - **run_full_etl**: 전체 ETL 파이프라인 실행 여부 (기본값: True)
      - True: 크롤링, 전처리, 청크 생성, 벡터DB 저장까지 모두 실행
      - False: 사용자 정보만 갱신 (크롤링)
    """
    # 로그인 시도하여 사용자 확인
    try:
        # 먼저 기본 로그인 확인
        user = await authenticate_user(form_data.username, form_data.password, False)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 학번 또는 비밀번호입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 데이터 갱신 시도
        result = await refresh_user_data(form_data.username, form_data.password, run_full_etl)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"데이터 갱신 중 오류가 발생했습니다: {result['message']}",
            )
            
        # 성공 메시지와 함께 자세한 정보 반환
        response = {
            "message": "데이터가 성공적으로 갱신되었습니다",
            "details": result.get("message", ""),
            "etl_stages": {
                "login": "completed", 
                "crawling": "completed",
                "processing": "completed",
                "vectorizing": "completed",
                "storing": "completed"
            }
        }
        
        # 청크 정보가 있으면 추가
        if "chunks_count" in result:
            response["chunks_count"] = result["chunks_count"]
            
        return response
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"인증 과정에서 오류 발생: {str(e)}",
        )

@router.post("/clear-data", status_code=200)
async def clear_user_data(
    form_data: UserLogin
):
    """
    사용자 데이터 완전 삭제 (벡터 DB 청크 제거)
    
    - **username**: 학번
    - **password**: 비밀번호
    """
    try:
        # 먼저 기본 로그인 확인
        user = await authenticate_user(form_data.username, form_data.password, False)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 학번 또는 비밀번호입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 데이터 삭제 시도
        result = clean_user_data(form_data.username)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터 삭제 중 오류가 발생했습니다",
            )
            
        # 청크 수 확인
        count = get_user_chunks_count(form_data.username)
            
        return {
            "message": "사용자 데이터가 성공적으로 삭제되었습니다",
            "remaining_chunks": count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"처리 중 오류 발생: {str(e)}",
        )

@router.get("/data-status")
async def get_data_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    현재 사용자의 데이터 상태 확인 (저장된 청크 수 등)
    """
    try:
        username = current_user.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 정보가 없습니다",
            )
            
        # 청크 수 확인
        count = get_user_chunks_count(username)
        
        # 사용자 데이터 파일 경로
        user_data_dir = os.path.join(settings.BASE_DIR, "user_data")
        detailed_data_file = os.path.join(user_data_dir, f"kangnam_courses_{username}.json")
        
        # 파일 존재 여부 및 마지막 수정 시간 확인
        file_exists = os.path.exists(detailed_data_file)
        last_modified = None
        file_size = 0
        
        if file_exists:
            import datetime
            last_modified = datetime.datetime.fromtimestamp(
                os.path.getmtime(detailed_data_file)
            ).strftime('%Y-%m-%d %H:%M:%S')
            file_size = os.path.getsize(detailed_data_file) / 1024  # KB 단위
        
        # 데이터 상태 결정
        status_value = "ready" if count > 0 else "not_ready"
        if count == 0 and file_exists:
            status_value = "partial"  # 크롤링은 되었지만 벡터화는 안된 상태
        
        return {
            "username": username,
            "name": current_user.get("name", ""),
            "status": status_value,
            "stored_chunks": count,
            "file_exists": file_exists,
            "last_modified": last_modified,
            "file_size_kb": round(file_size, 2) if file_exists else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터 상태 확인 중 오류 발생: {str(e)}",
        )

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 반환 (JWT 토큰 검증)
    """
    return current_user 