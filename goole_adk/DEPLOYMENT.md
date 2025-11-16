# goole_adk 배포 가이드

강남대학교 Multi-Agent 시스템을 Vertex AI Agent Engine에 배포하는 가이드입니다.

## 📋 사전 요구사항

### 1. GCP 설정
- GCP 프로젝트: `kangnam-backend`
- 리전: `us-east4` (Agent Engine 지원 리전)
- 필요한 API 활성화:
  - Vertex AI API
  - Cloud Storage API
  - Discovery Engine API (Vertex AI Search)

### 2. 인증 설정
```bash
# GCP 로그인
gcloud auth login

# Application Default Credentials 설정
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project kangnam-backend
```

### 3. 환경 변수 설정

`.env` 파일을 생성하거나 업데이트하세요:

```bash
# Google Cloud 기본 설정
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4
GOOGLE_CLOUD_STAGING_BUCKET=gs://kangnam-backend-agent-staging

# Vertex AI Search (이미 설정되어 있음)
KANGNAM_CORPUS_ID=6917529027641081856
GCS_BUCKET_NAME=kangnam-univ
GCS_BUCKET_LOCATION=asia-northeast3
```

## 🚀 배포 프로세스

### Step 1: Staging Bucket 생성

배포에 필요한 staging bucket을 생성합니다:

```bash
cd /Users/hong-gihyeon/Desktop/cap
python create_staging_bucket.py
```

**출력 예시:**
```
======================================================================
  GCP Staging Bucket Creator
======================================================================

🪣 Creating staging bucket: gs://kangnam-backend-agent-staging
📍 Location: us-east4
🏷️  Project: kangnam-backend

🚀 Creating bucket...
✅ Successfully created: gs://kangnam-backend-agent-staging

📝 Add this to your .env file:
GOOGLE_CLOUD_STAGING_BUCKET=gs://kangnam-backend-agent-staging

💡 Next steps:
   1. Add the line above to your .env file
   2. Run: python deploy.py --create
```

출력된 `GOOGLE_CLOUD_STAGING_BUCKET` 라인을 `.env` 파일에 추가하세요.

### Step 2: Agent Engine에 배포

```bash
python deploy.py --create
```

배포 과정:
1. `root_agent`를 `AdkApp`으로 래핑
2. `goole_adk` 패키지 전체를 패키징
3. 필요한 requirements 설치:
   - `google-cloud-aiplatform[adk,agent_engines]`
   - `requests`
   - `beautifulsoup4`
   - `python-dotenv`
4. Agent Engine에 업로드 및 배포

**예상 소요 시간:** 5-10분

**출력 예시:**
```
🚀 Starting deployment...

📦 Packaging goole_adk...

======================================================================
✅ Deployment successful!
======================================================================

📝 Resource ID: projects/88199591627/locations/us-east4/reasoningEngines/1234567890

💾 Save this ID for later use!

🔑 Next steps:
   1. Create a session:
      python deploy.py --create_session \
        --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1234567890"

   2. Send a message:
      python deploy.py --send \
        --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1234567890" \
        --session_id="<SESSION_ID>" \
        --message="2024년 졸업 요건 알려줘"
```

**중요:** `Resource ID`를 복사하여 저장하세요!

### Step 3: Session 생성

배포된 Agent와 통신하려면 세션을 생성해야 합니다:

```bash
python deploy.py --create_session \
  --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1234567890"
```

**출력 예시:**
```
🔑 Creating session for user: test_user

======================================================================
✅ Session created!
======================================================================

  Session ID: session_abc123def456
  User ID: test_user
  App name: kangnam_assistant
  Last update: 2025-01-09T12:34:56Z

💡 Use this session ID with --session_id when sending messages.
```

**중요:** `Session ID`를 복사하여 저장하세요!

### Step 4: 메시지 전송 테스트

```bash
python deploy.py --send \
  --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1234567890" \
  --session_id="session_abc123def456" \
  --message="2024년 입학생 공과대학 졸업 요건 알려줘"
```

**응답 예시:**
```
📤 Sending message to session session_abc123def456:
Message: 2024년 입학생 공과대학 졸업 요건 알려줘

🤖 Response:
----------------------------------------------------------------------
안녕하세요! 2024년 입학생(2021~2024학년도)의 공과대학 졸업 요건을 안내해드리겠습니다.

📌 공과대학 2021~2024학년도 졸업요건

✅ 기초교양: 14학점
✅ 계열교양: 6학점
✅ 균형교양: 15학점 (5개 영역에서 각 1개)
✅ 전공학점: 
   - 심화전공자: 66학점
   - 다전공자: 42학점
✅ 최소졸업학점: 130학점

다른 궁금하신 사항이 있으신가요?
```

## 🔧 추가 명령어

### 배포 목록 확인
```bash
python deploy.py --list
```

### 세션 목록 확인
```bash
python deploy.py --list_sessions \
  --resource_id="..."
```

### 특정 세션 조회
```bash
python deploy.py --get_session \
  --resource_id="..." \
  --session_id="..."
```

### 배포 삭제
```bash
python deploy.py --delete \
  --resource_id="..."
```

## 📦 배포되는 구성 요소

### Agent 구조
```
Root Agent (kangnam_agent)
├── Graduation Agent (졸업요건 검색)
│   └── Tools: Vertex AI Search 기반
├── Subject Agent (과목 정보 검색)
│   └── Tools: 크롤링 + 파싱
├── Professor Agent (교수 정보 검색)
│   └── Tools: Vertex AI Search 기반
└── Admission Agent (입학 정보 - Placeholder)
```

### 포함되는 패키지
- `goole_adk/` 전체 (agents, config, tools 등)
- Python requirements:
  - `google-cloud-aiplatform[adk,agent_engines]`
  - `requests`
  - `beautifulsoup4`
  - `python-dotenv`

### 사용하는 GCP 서비스
1. **Vertex AI Agent Engine**: Agent 호스팅
2. **Vertex AI Search**: 졸업요건, 교수 정보 검색
3. **Cloud Storage**: Staging bucket (배포 파일 저장)
4. **Gemini 2.0 Flash**: LLM 모델

## 🌐 프론트엔드 연동

### REST API 호출 방식

배포된 Agent Engine은 gRPC 및 REST API를 제공합니다. 프론트엔드 연동을 위해서는:

1. **백엔드 API 서버 구성** (FastAPI/Flask 권장)
2. 백엔드가 Agent Engine API 호출
3. 프론트엔드는 백엔드 API 호출

```
[Frontend (React)] 
    ↓ HTTP
[Backend API (FastAPI)]
    ↓ gRPC/REST
[Agent Engine (Deployed)]
    ↓
[Vertex AI Search + Gemini]
```

### 백엔드 API 예시 (FastAPI)

```python
from fastapi import FastAPI
from vertexai import agent_engines

app = FastAPI()

RESOURCE_ID = "projects/.../reasoningEngines/..."

@app.post("/chat")
async def chat(user_id: str, session_id: str, message: str):
    remote_app = agent_engines.get(RESOURCE_ID)
    
    responses = []
    for event in remote_app.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message
    ):
        responses.append(event)
    
    return {"response": responses}
```

## ⚠️ 주의사항

### 1. 리전 일치
- Agent Engine 배포: `us-east4`
- Staging Bucket: `us-east4`
- Vertex AI Search: `global` (자동)
- GCS 데이터: `asia-northeast3` (별도)

### 2. 권한 확인
필요한 IAM 역할:
- Vertex AI User
- Storage Admin
- Discovery Engine Admin (Vertex AI Search)

### 3. 비용
- **Agent Engine**: 요청당 과금 (idle 시 무료)
- **Vertex AI Search**: 검색 요청당 과금
- **Gemini API**: 토큰당 과금
- **Cloud Storage**: 저장 용량 + 네트워크

### 4. 세션 관리
- 세션은 영구적이지 않음 (일정 시간 후 만료)
- 프로덕션에서는 세션 ID를 DB에 저장하여 관리 권장

## 🐛 트러블슈팅

### "Missing: GOOGLE_CLOUD_STAGING_BUCKET"
→ `create_staging_bucket.py`를 실행하고 `.env`에 추가하세요.

### "Permission denied"
→ `gcloud auth application-default login` 실행

### "API not enabled"
→ GCP Console에서 Vertex AI API 활성화

### "Deployment failed"
→ 로그 확인: `gcloud logging read "resource.type=vertex_ai_agent_engine"`

### Staging bucket 리전 오류
→ Bucket이 `us-east4`에 생성되었는지 확인:
```bash
gsutil ls -L gs://kangnam-backend-agent-staging | grep Location
```

## 📞 문의

배포 관련 이슈 발생 시:
1. GCP Console > Vertex AI > Agent Engine에서 로그 확인
2. `gcloud` CLI로 배포 상태 확인
3. `.env` 파일의 모든 환경 변수 확인

---

**배포 완료 후 다음 단계:**
- 프론트엔드 API 연동
- 모니터링 설정
- 로깅 및 에러 트래킹
- 사용량 모니터링

