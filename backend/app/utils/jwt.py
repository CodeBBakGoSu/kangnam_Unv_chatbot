from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from app.schemas.user import TokenData, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(user: Dict[str, Any]) -> str:
    """
    사용자 정보를 기반으로 JWT 토큰 생성
    """
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode = {
        "sub": user["username"],
        "name": user["name"],
        "department": user.get("department", ""),
        "exp": expire
    }
    
    # 추가 정보가 있으면 토큰에 포함
    if "courses" in user:
        to_encode["courses"] = user["courses"]
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    JWT 토큰을 검증하고 현재 사용자 정보 반환
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보입니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 디코딩
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        # 사용자 정보 구성
        token_data = TokenData(
            username=username,
            name=payload.get("name"),
            department=payload.get("department")
        )
        
        # 사용자 컨텍스트 구성 (챗봇 RAG에 사용)
        user_context = {
            "username": token_data.username,
            "name": token_data.name,
            "department": token_data.department
        }
        
        # courses 정보가 있으면 추가
        if "courses" in payload:
            user_context["courses"] = payload.get("courses")
            
        return user_context
        
    except JWTError:
        raise credentials_exception 