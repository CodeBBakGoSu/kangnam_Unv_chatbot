from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat
import os

app = FastAPI(
    title="KangnamBot API",
    description="강남대학교 챗봇 API",
    version="0.1.0"
)

# CORS 설정 추가 (Streamlit Cloud에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # 로컬 Streamlit
        "https://*.streamlit.app",  # Streamlit Cloud
        "https://kangnam-chatbot.streamlit.app"  # 실제 배포된 Streamlit URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(chat.router, prefix="/api/chat", tags=["챗봇"])

@app.get("/")
async def root():
    return {"message": "강남대학교 챗봇 API에 오신 것을 환영합니다!"} 