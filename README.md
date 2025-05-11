# 강남대학교 소프트웨어응용학부 AI 챗봇

## 프로젝트 개요

강남대학교 소프트웨어응용학부 학생들이 학교생활 관련 궁금증을 24시간 빠르게 해결할 수 있는 AI 챗봇입니다.

- RAG + LLM(Gemini) 기반 자연어 이해 챗봇
- 개인화된 학습 정보 제공 (수강과목, 과제, 출석, 일정 등)
- SSO 로그인 통합

## 기술 스택

- **프론트엔드**: React + Tailwind CSS, Streamlit
- **백엔드**: FastAPI
- **데이터베이스**: Supabase (pgvector)
- **LLM**: Gemini 2.0 Flash
- **인증**: JWT + 강남대 이러닝 SSO 통합

## 개발 환경 설정

### 필수 요구사항

- Python 3.10 이상
- Node.js 18 이상
- Docker 및 Docker Compose (선택사항)

### 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=your_supabase_connection_string
JWT_SECRET=your_jwt_secret
```

### 개발 모드 실행

#### 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 프론트엔드 실행 (React)

```bash
cd frontend
npm install
npm start
```

#### Streamlit 실행

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

### Docker로 실행

전체 애플리케이션을 Docker로 실행할 수 있습니다:

```bash
docker build -t knuchatbot .
docker run -p 80:80 -d knuchatbot
```

## 프로젝트 구조

```
├── backend/             # FastAPI 백엔드
│   ├── app/
│   │   ├── api/         # API 엔드포인트
│   │   ├── services/    # 비즈니스 로직
│   │   └── utils/       # 유틸리티 함수
│   └── requirements.txt
├── frontend/            # React 프론트엔드
│   ├── public/
│   ├── src/
│   │   ├── components/  # 재사용 가능한 컴포넌트
│   │   ├── pages/       # 페이지 컴포넌트
│   │   └── utils/       # 유틸리티 함수
│   └── package.json
├── streamlit/           # Streamlit 챗봇 인터페이스
│   ├── app.py           # 메인 Streamlit 앱
│   └── requirements.txt
├── src/                 # 핵심 챗봇 로직
│   └── agents/          # 에이전트 구현
├── Dockerfile           # 통합 Docker 구성
├── nginx.conf           # NGINX 설정
├── start.sh             # 시작 스크립트
└── README.md
```

## 사용 예시

1. 로그인 페이지에서 강남대학교 학생 계정으로 로그인
2. 챗봇 인터페이스에서 다음과 같은 질문을 할 수 있습니다:
   - "인공지능개론 이번주 과제가 뭐야?"
   - "데이터베이스 수업 내일 뭐해?"
   - "졸업 요건 알려줘"
   - "캡스톤 교수님 연락처 알려줘"

## 라이센스

이 프로젝트는 MIT 라이센스로 제공됩니다. 