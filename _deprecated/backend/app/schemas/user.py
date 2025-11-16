from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class UserLogin(BaseModel):
    username: str = Field(..., description="학번")
    password: str = Field(..., description="비밀번호")

class UserBase(BaseModel):
    username: str
    name: str
    
class User(UserBase):
    department: str
    courses: List[Dict[str, Any]] = []
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None 