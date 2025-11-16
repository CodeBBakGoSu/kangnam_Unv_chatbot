# 강남대학교 챗봇 API

강남대학교 챗봇의 FastAPI 백엔드입니다.

## 기능

- 사용자 인증 (JWT)
- RAG 기반 챗봇 응답 생성
- Supabase 벡터DB 연동
- Gemini API 통합

## 설치 및 실행

### 환경 설정

1. `.env.example`을 복사하여 `.env` 파일 생성
```bash
cp .env.example .env
```

2. `.env` 파일에 필요한 환경변수 입력
   - JWT_SECRET_KEY: JWT 서명용 비밀키
   - SUPABASE_URL, SUPABASE_KEY: Supabase 연결 정보
   - GOOGLE_API_KEY: Gemini API 키

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 서버 실행

개발 모드:
```bash
uvicorn app.main:app --reload
```

프로덕션 모드:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인 가능:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 배포

Vercel Serverless Functions 또는 Fly.io에 배포 가능합니다.

### Vercel 배포 (서버리스)

```bash
vercel
```

### Fly.io 배포

```bash
flyctl deploy
``` 