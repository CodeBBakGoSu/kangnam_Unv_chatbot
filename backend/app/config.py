import os
from dotenv import load_dotenv
from pydantic import BaseModel

# 디렉토리 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env 파일 로드
load_dotenv()

# JWT 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "YOUR_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24 * 14  # 14일

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Gemini API 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-001"

# 앱 설정
class Settings(BaseModel):
    app_name: str = "KangnamBot API"
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    BASE_DIR: str = BASE_DIR
    BACKEND_DIR: str = BACKEND_DIR
    AUTO_RUN_ETL_FOR_NEW_USERS: bool = True  # 새 사용자 로그인 시 자동으로 ETL 실행

settings = Settings() 