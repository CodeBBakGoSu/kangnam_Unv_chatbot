# 🚀 강남대학교 챗봇 배포 가이드

> **완전 자동화된 배포 시스템** - 한 줄 명령어로 모든 것을 처리합니다!

## 📋 목차

1. [빠른 시작](#빠른-시작)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [배포 시나리오](#배포-시나리오)
4. [환경 설정](#환경-설정)
5. [배포 방법](#배포-방법)
6. [테스트](#테스트)
7. [트러블슈팅](#트러블슈팅)

---

## 빠른 시작

### ⚡ 한 줄 배포 (권장)

```bash
cd /Users/hong-gihyeon/Desktop/cap
./deploy_all.sh
```

**선택 옵션**:
- `1`: 전체 배포 (Agent Engine + Backend API) ⭐ **처음 배포 시**
- `2`: Agent Engine만 배포 (코드 수정 시)
- `3`: Backend API만 배포 (Backend 수정 시)

---

## 시스템 아키텍처

### 📐 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    강남대 챗봇 시스템                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1️⃣ Agent Engine (Vertex AI Reasoning Engine)      │  │
│  │     - 위치: goole_adk 폴더                            │  │
│  │     - 플랫폼: Vertex AI Agent Engine                │  │
│  │     - 모델: Gemini 2.0 Flash                         │  │
│  │     - ⚠️ 배포 후 수정 불가 (재배포 필요)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2️⃣ Backend API (Cloud Run)                         │  │
│  │     - 위치: agent-backend 폴더                       │  │
│  │     - 기술: FastAPI + Server-Sent Events            │  │
│  │     - 역할: Agent Engine과 통신, 스트리밍 제공       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  3️⃣ Frontend (Vercel)                               │  │
│  │     - 위치: agent-frontend 폴더                      │  │
│  │     - 기술: React + Tailwind CSS                     │  │
│  │     - 역할: 사용자 인터페이스                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🤖 Multi-Agent 시스템

```
Root Agent (kangnam_assistant) - 강냉봇
├── 🎓 Graduation Agent (졸업요건 검색)
│   └── Vertex AI Search (6917529027641081856)
├── 📚 Subject Agent (과목 정보 검색)
│   └── 강의계획서 크롤링 API
├── 👨‍🏫 Professor Agent (교수 정보 검색)
│   └── Vertex AI Search
├── 🏢 Basic Info Agent (캠퍼스 안내)
│   └── Vertex AI Search
└── 📝 Admission Agent (입학 정보)
    └── Placeholder (준비 중)
```

### 🔧 기술 스택

| 컴포넌트 | 기술 |
|---------|------|
| **Agent 프레임워크** | Google ADK (Agent Development Kit) |
| **LLM 모델** | Gemini 2.0 Flash |
| **배포 플랫폼** | Vertex AI Agent Engine |
| **검색 엔진** | Vertex AI Search (Discovery Engine) |
| **Backend** | FastAPI + Cloud Run |
| **Frontend** | React + Vercel |
| **인증** | Google Cloud Service Account |

### 📊 GCP 프로젝트 정보

```yaml
프로젝트 ID: kangnam-backend
프로젝트 번호: 88199591627

리전:
  - Agent Engine: us-east4
  - Backend API: us-east4
  - GCS 데이터: asia-northeast3

주요 서비스:
  - Vertex AI Agent Engine (Multi-Agent 호스팅)
  - Vertex AI Search (졸업요건, 교수 정보)
  - Cloud Storage (배포 파일 저장)
  - Cloud Run (Backend API 호스팅)
```

---

## 배포 시나리오

### 🎯 시나리오 1: Agent 코드 수정 후 배포 (가장 흔함)

**상황**: `goole_adk/` 폴더의 에이전트 코드를 수정했을 때

```bash
# 1단계: Agent Engine 재배포
./deploy_all.sh
# → 옵션 2 선택 (Agent만 배포)

# 2단계: Backend는 자동으로 새 Agent 사용
# 추가 작업 없음!
```

**자동으로 수행되는 작업**:
- ✅ 새 Agent Engine 배포
- ✅ `.env` 파일에 새 Resource ID 자동 저장
- ✅ 이전 Resource ID는 백업으로 보관
- ✅ Backend는 다음 재배포 시 자동으로 새 Agent 사용

**Frontend 재배포**: ❌ **불필요** (Backend URL 변경 없음)

---

### 🎯 시나리오 2: Backend 코드 수정 후 배포

**상황**: `agent-backend/` 폴더의 코드를 수정했을 때

```bash
cd agent-backend
./deploy_backend.sh
```

**자동으로 수행되는 작업**:
- ✅ Backend API 재배포
- ✅ `.env`에서 최신 AGENT_RESOURCE_ID 자동 로드
- ✅ Cloud Run에 환경변수 전달

**Frontend 재배포**: ❌ **불필요** (Backend URL 변경 없음)

---

### 🎯 시나리오 3: 처음 배포하는 경우

```bash
# 1단계: 초기 설정
# (환경 설정 섹션 참고)

# 2단계: 전체 배포
./deploy_all.sh
# → 옵션 1 선택 (전체 배포)

# 3단계: Backend URL 확인
gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)"

# 4단계: Vercel에 환경변수 설정
# REACT_APP_API_URL=https://agent-backend-api-xxx.run.app

# 5단계: Frontend 재배포
cd agent-frontend
vercel --prod
```

**Frontend 재배포**: ✅ **필요** (최초 1회만)

---

### 🎯 시나리오 4: 롤백 (이전 버전으로 복구)

```bash
# 1단계: 백업된 Resource ID 확인
cat .env | grep BACKUP

# 2단계: .env 파일 수정
# AGENT_RESOURCE_ID를 BACKUP ID로 변경

# 3단계: Backend 재배포
cd agent-backend
./deploy_backend.sh

# 4단계: 테스트
curl -X POST $BACKEND_URL/chat/new
```

---

## 환경 설정

### 📝 필수 사전 준비

#### 1. GCP CLI 설치 및 인증

```bash
# GCP CLI 인증
gcloud auth login

# Application Default Credentials
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project kangnam-backend
```

#### 2. Python 환경 설정

```bash
cd /Users/hong-gihyeon/Desktop/cap

# uv 사용 (권장)
uv pip install -r requirements.txt

# 또는 일반 pip
pip install -r requirements.txt
```

**설치되는 주요 패키지**:
- `google-cloud-aiplatform[adk,agent_engines]` - Vertex AI + ADK
- `requests`, `beautifulsoup4` - 웹 크롤링
- `python-dotenv` - 환경 변수 관리
- `fastapi`, `uvicorn` - Backend API

#### 3. `.env` 파일 생성

프로젝트 루트에 `.env` 파일 생성:

```bash
# Google Cloud 설정
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4

# GCS Bucket (데이터 저장용)
GCS_BUCKET_NAME=kangnam-univ
GCS_BUCKET_LOCATION=asia-northeast3

# Vertex AI Search Corpus IDs
KANGNAM_CORPUS_ID=6917529027641081856

# Agent Resource ID (배포 후 자동 추가됨)
AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664
AGENT_RESOURCE_ID_BACKUP=projects/88199591627/locations/us-east4/reasoningEngines/이전ID
```

#### 4. Staging Bucket 생성 (최초 1회)

```bash
python create_staging_bucket.py
```

**출력 예시**:
```
✅ Staging bucket created: agent-engine-staging-abc123
GOOGLE_CLOUD_STAGING_BUCKET=agent-engine-staging-abc123
```

출력된 `GOOGLE_CLOUD_STAGING_BUCKET` 라인을 `.env` 파일에 추가하세요.

---

### 🔑 IAM 권한 설정 (최초 1회)

Agent Engine이 Vertex AI Search를 사용하려면 권한이 필요합니다.

```bash
# Reasoning Engine Service Account에 권한 부여
gcloud projects add-iam-policy-binding kangnam-backend \
  --member="serviceAccount:service-88199591627@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.editor"

# Compute Engine Default Service Account에도 부여 (보험)
gcloud projects add-iam-policy-binding kangnam-backend \
  --member="serviceAccount:88199591627-compute@developer.gserviceaccount.com" \
  --role="roles/discoveryengine.editor"
```

**중요**: 
- ✅ 프로젝트 레벨 권한이므로 **영구적**으로 유지됩니다
- ✅ 재배포 시 다시 설정할 필요 없습니다
- ⏱️ 권한 전파에 2-3분 소요될 수 있습니다

#### 권한 확인

```bash
gcloud projects get-iam-policy kangnam-backend \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:service-88199591627@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
```

---

## 배포 방법

### 🎯 방법 1: 자동 통합 배포 (권장)

```bash
cd /Users/hong-gihyeon/Desktop/cap
chmod +x deploy_all.sh
./deploy_all.sh
```

**대화형 메뉴**:
```
===========================================
   강남대 챗봇 배포 시스템
===========================================

배포 옵션을 선택하세요:
1) 전체 배포 (Agent Engine + Backend API)
2) Agent Engine만 배포
3) Backend API만 배포
4) 종료

선택 (1-4):
```

**자동으로 수행되는 작업**:

#### 옵션 1 선택 시:
1. ✅ Agent Engine 배포 (Blue-Green 방식)
2. ✅ `.env` 파일에 새 Resource ID 자동 저장
3. ✅ 이전 Resource ID는 BACKUP으로 보관
4. ✅ Backend API 배포 (새 Resource ID 사용)
5. ✅ 배포 완료 후 테스트 명령어 제공

#### 옵션 2 선택 시:
1. ✅ Agent Engine만 배포
2. ✅ `.env` 파일 업데이트
3. ✅ Backend는 다음 배포 시 자동으로 새 Agent 사용

#### 옵션 3 선택 시:
1. ✅ Backend API만 재배포
2. ✅ `.env`에서 최신 Resource ID 로드

---

### 🎯 방법 2: 개별 수동 배포

#### Step 1: Agent Engine 배포

```bash
cd /Users/hong-gihyeon/Desktop/cap
./update_deployment.sh
```

**자동 처리 항목**:
- 새 Agent Engine 배포
- 테스트 실행
- `.env` 파일 업데이트
- 백업 Resource ID 저장

**또는 완전 수동**:
```bash
python deploy.py --create
```

**출력 예시**:
```
✅ Agent Engine deployed successfully!
Resource ID: projects/88199591627/locations/us-east4/reasoningEngines/1234567890
```

이 Resource ID를 `.env` 파일에 수동으로 추가:
```bash
echo "AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1234567890" >> .env
```

#### Step 2: Backend API 배포

```bash
cd agent-backend
./deploy_backend.sh
```

**자동 처리 항목**:
- `.env`에서 `AGENT_RESOURCE_ID` 로드
- Cloud Run에 Backend 배포
- 환경변수로 Agent Resource ID 전달
- Backend URL 출력

**또는 완전 수동**:
```bash
cd agent-backend

export AGENT_RESOURCE_ID="projects/.../reasoningEngines/..."
export GOOGLE_CLOUD_PROJECT="kangnam-backend"
export VERTEX_AI_LOCATION="us-east4"

gcloud run deploy agent-backend-api \
  --source=. \
  --region=us-east4 \
  --project=kangnam-backend \
  --allow-unauthenticated \
  --set-env-vars="AGENT_RESOURCE_ID=$AGENT_RESOURCE_ID,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION"
```

#### Step 3: Frontend 환경변수 설정 (최초 1회)

```bash
# Backend URL 확인
gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)"
```

**Vercel Dashboard에서 설정**:
1. Vercel Dashboard → 프로젝트 선택
2. Settings → Environment Variables
3. `REACT_APP_API_URL` 추가:
   ```
   REACT_APP_API_URL=https://agent-backend-api-xxx.run.app
   ```
4. Redeploy

---

### 📂 배포 시 포함되는 항목

#### Python 패키지 (자동 설치)

```python
requirements = [
    "google-cloud-aiplatform[adk,agent_engines]",
    "requests",
    "beautifulsoup4",
    "python-dotenv",
]
```

#### 프로젝트 파일

```python
extra_packages = ["./goole_adk"]
```

**포함되는 항목**:
- `goole_adk/agent.py` (Root Agent)
- `goole_adk/agents/` (모든 Sub-Agents)
  - `graduation/` (졸업요건 Agent + Tools)
  - `subject/` (과목 정보 Agent + Tools)
  - `professor/` (교수 정보 Agent + Tools)
  - `basic_info/` (캠퍼스 안내 Agent + Tools)
  - `admission/` (입학 정보 Agent - Placeholder)
- `goole_adk/callbacks.py` (안전 콜백)
- `goole_adk/config/` (환경 설정)
- 모든 Tools 및 의존성

---

## 환경 변수 관리

### 📝 `.env` 파일 구조

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent Resource ID (자동 업데이트됨)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664

# 백업 (롤백용)
AGENT_RESOURCE_ID_BACKUP=projects/88199591627/locations/us-east4/reasoningEngines/이전ID

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Google Cloud 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GCS 버킷 (데이터 저장용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GCS_BUCKET_NAME=kangnam-univ
GCS_BUCKET_LOCATION=asia-northeast3
GOOGLE_CLOUD_STAGING_BUCKET=agent-engine-staging-abc123

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Vertex AI Search Corpus IDs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KANGNAM_CORPUS_ID=6917529027641081856
```

### 🔄 환경변수 자동 업데이트 흐름

```
┌────────────────────────────────────────────────────────┐
│ 1. update_deployment.sh 실행                           │
│    또는 deploy_all.sh (옵션 1 또는 2)                  │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 2. 새 Agent Engine 배포                                │
│    Resource ID: ...reasoningEngines/새ID               │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 3. .env 파일 자동 업데이트                             │
│    AGENT_RESOURCE_ID=새ID                              │
│    AGENT_RESOURCE_ID_BACKUP=이전ID                     │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 4. deploy_backend.sh 실행                              │
│    (deploy_all.sh 옵션 1 선택 시 자동 실행)           │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 5. .env에서 AGENT_RESOURCE_ID 로드                     │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 6. Cloud Run에 환경변수로 전달                         │
│    --set-env-vars="AGENT_RESOURCE_ID=새ID,..."        │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 7. Backend가 새 Agent Engine과 자동 연결됨 ✅         │
└────────────────────────────────────────────────────────┘
```

---

## 테스트

### 🧪 Agent Engine 테스트

#### 1. 세션 생성

```bash
python deploy.py --create_session \
  --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664"
```

**성공 시 출력**:
```
✅ Session created!
  Session ID: 1522160049202397184
```

#### 2. 메시지 전송

```bash
python deploy.py --send \
  --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664" \
  --session_id="1522160049202397184" \
  --message="2021년 ICT융합공학부 졸업 요건 알려줘"
```

**성공 응답 예시**:
```json
{
  "model_version": "gemini-2.0-flash",
  "content": {
    "parts": [{
      "text": "2021~2024학년도 공과대학 ICT융합공학부 졸업요건은 다음과 같습니다:\n\n✅ 기초교양: 17학점\n✅ 계열교양: 9학점\n✅ 균형교양: 9학점\n✅ 전공학점: \n   - 심화전공자: 66학점\n   - 다전공자: 39학점\n✅ 최소졸업학점: 130학점\n\n더 자세한 정보가 필요하시면 말씀해주세요!"
    }]
  },
  "author": "graduation_agent",
  "usageMetadata": {
    "candidatesTokenCount": 156,
    "promptTokenCount": 2504,
    "totalTokenCount": 2660
  }
}
```

#### 3. 배포 목록 확인

```bash
python deploy.py --list
```

**출력 예시**:
```
=== Deployed Agent Engines ===

1. projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664
   Created: 2025-01-09 14:23:45
   
2. projects/88199591627/locations/us-east4/reasoningEngines/이전ID
   Created: 2025-01-08 10:15:30
```

---

### 🧪 Backend API 테스트

#### 1. Backend URL 확인

```bash
BACKEND_URL=$(gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)")

echo $BACKEND_URL
```

#### 2. 새 세션 생성

```bash
curl -X POST $BACKEND_URL/chat/new
```

**응답**:
```json
{
  "session_id": "d4e2f8a3-1b7c-4e5d-9f2a-8c3b1e4d6a7f",
  "user_id": "anonymous_abc123"
}
```

#### 3. 메시지 전송 (스트리밍)

```bash
curl -X POST $BACKEND_URL/chat/message \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "anonymous_abc123",
    "session_id": "d4e2f8a3-1b7c-4e5d-9f2a-8c3b1e4d6a7f",
    "message": "안녕하세요! 강남대학교 챗봇입니다."
  }' \
  -N
```

**응답 (Server-Sent Events)**:
```
data: {"type":"text","content":"안녕하세요! 강남대학교에 대해 궁금하신 게 있으신가요?"}

data: {"type":"done"}
```

#### 4. 헬스 체크

```bash
curl $BACKEND_URL/health
```

**응답**:
```json
{
  "status": "healthy",
  "agent_resource_id": "projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664",
  "project": "kangnam-backend",
  "location": "us-east4"
}
```

---

### 🧪 통합 테스트 (Frontend → Backend → Agent)

```bash
# 1. Frontend 로컬 실행
cd agent-frontend
npm start

# 2. 브라우저에서 http://localhost:3000 접속
# 3. 테스트 질문 입력:
#    - "2024년 공과대학 졸업 요건 알려줘"
#    - "김철주 교수님 알려줘"
#    - "소프트웨어공학 강의계획서 보여줘"

# 4. Chrome DevTools에서 Network 탭 확인
#    - POST /chat/message
#    - EventStream 응답 확인
```

---

## 트러블슈팅

### 🔴 문제 1: `AGENT_RESOURCE_ID`가 없다는 에러

**증상**:
```bash
에러: AGENT_RESOURCE_ID가 설정되지 않았습니다.
에러: ../.env 파일을 찾을 수 없습니다.
```

**원인**: `.env` 파일이 없거나 `AGENT_RESOURCE_ID`가 설정되지 않음

**해결 방법**:

```bash
# 1. 프로젝트 루트로 이동
cd /Users/hong-gihyeon/Desktop/cap

# 2. .env 파일 확인
cat .env

# 3. 없으면 Agent Engine 먼저 배포
./update_deployment.sh

# 4. Backend 재배포
cd agent-backend
./deploy_backend.sh
```

---

### 🔴 문제 2: Backend가 이전 Agent Engine에 연결됨

**증상**:
- 코드 수정했는데 반영 안됨
- 이전 응답이 계속 나옴
- 헬스 체크에서 이전 Resource ID 표시

**원인**: Backend가 배포 시점의 환경변수를 캐시함

**해결 방법**:

```bash
# 1. .env 파일의 AGENT_RESOURCE_ID 확인
cat .env | grep AGENT_RESOURCE_ID

# 2. Backend 로그 확인
gcloud run logs tail agent-backend-api --region=us-east4

# 3. Backend 강제 재배포
cd agent-backend
./deploy_backend.sh

# 4. 헬스 체크로 확인
curl $(gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)")/health
```

---

### 🔴 문제 3: 403 Permission Denied (Discovery Engine)

**증상**:
```
Error 403: Permission 'discoveryengine.servingConfigs.search' denied
```

**원인**: Agent Engine의 Service Account에 Vertex AI Search 접근 권한 없음

**해결 방법**:

```bash
# 1. Service Account 권한 부여
gcloud projects add-iam-policy-binding kangnam-backend \
  --member="serviceAccount:service-88199591627@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.editor"

# 2. Compute Engine Default SA에도 부여 (보험)
gcloud projects add-iam-policy-binding kangnam-backend \
  --member="serviceAccount:88199591627-compute@developer.gserviceaccount.com" \
  --role="roles/discoveryengine.editor"

# 3. 2-3분 대기 (IAM 전파 시간)

# 4. Agent Engine 재배포
./update_deployment.sh

# 5. 테스트
python deploy.py --send \
  --resource_id="..." \
  --session_id="..." \
  --message="2024년 공과대학 졸업 요건"
```

---

### 🔴 문제 4: ModuleNotFoundError

**증상**:
```bash
ModuleNotFoundError: No module named 'goole_adk'
ModuleNotFoundError: No module named 'absl'
```

**원인**: 
- 잘못된 디렉토리에서 실행
- 의존성 미설치

**해결 방법**:

```bash
# 1. 프로젝트 루트로 이동
cd /Users/hong-gihyeon/Desktop/cap

# 2. 의존성 재설치
uv pip install -r requirements.txt

# 3. Python 경로 확인
which python
# /Users/hong-gihyeon/Desktop/cap/.venv/bin/python 이어야 함

# 4. 다시 실행
python deploy.py --create
```

---

### 🔴 문제 5: 배포 스크립트 실행 권한 없음

**증상**:
```bash
Permission denied: ./deploy_all.sh
zsh: permission denied: ./update_deployment.sh
```

**원인**: 실행 권한이 없음

**해결 방법**:

```bash
chmod +x deploy_all.sh
chmod +x update_deployment.sh
chmod +x agent-backend/deploy_backend.sh
```

---

### 🔴 문제 6: Frontend에서 "Network Error"

**증상**:
```
Network Error
ERR_CONNECTION_REFUSED
CORS Error
```

**원인**: 
1. Backend URL이 잘못 설정됨
2. Backend가 배포되지 않음
3. CORS 설정 문제

**해결 방법**:

```bash
# 1. Backend 상태 확인
gcloud run services describe agent-backend-api \
  --region=us-east4

# 2. Backend URL 확인
gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)"

# 3. Vercel 환경변수 확인
# Vercel Dashboard → Settings → Environment Variables
# REACT_APP_API_URL이 올바른지 확인

# 4. Backend 로그 확인
gcloud run logs tail agent-backend-api --region=us-east4

# 5. Backend 재배포
cd agent-backend
./deploy_backend.sh
```

---

### 🔴 문제 7: Session ID 오류

**증상**:
```python
KeyError: 'user_id'
KeyError: 'id'
```

**원인**: 세션 응답 구조가 예상과 다름 (이미 수정됨)

**해결 방법**:

최신 `deploy.py` 사용 중이면 이미 수정된 버전입니다.
만약 여전히 발생한다면:

```bash
# 최신 코드로 업데이트
git pull origin main

# 또는 deploy.py에서 선택적 필드 처리 확인
# remote_session.get('id') or remote_session
# 'user_id' in remote_session
```

---

## 배포 체크리스트

### ✅ 초기 배포 (최초 1회)

- [ ] GCP CLI 설치 및 인증
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```
- [ ] Python 의존성 설치
  ```bash
  uv pip install -r requirements.txt
  ```
- [ ] `.env` 파일 생성 및 설정
- [ ] Staging bucket 생성
  ```bash
  python create_staging_bucket.py
  ```
- [ ] Discovery Engine 권한 설정 (IAM)
  ```bash
  gcloud projects add-iam-policy-binding kangnam-backend ...
  ```
- [ ] Agent Engine 배포
  ```bash
  ./update_deployment.sh
  ```
- [ ] Backend API 배포
  ```bash
  cd agent-backend && ./deploy_backend.sh
  ```
- [ ] Frontend 환경변수 설정 (Vercel)
- [ ] Frontend 배포
- [ ] 통합 테스트

---

### ✅ Agent 코드 업데이트 배포

- [ ] `goole_adk/` 코드 수정 완료
- [ ] 로컬 테스트 (선택)
- [ ] Agent Engine 재배포
  ```bash
  ./deploy_all.sh → 옵션 2
  ```
- [ ] `.env` 파일 자동 업데이트 확인
- [ ] Backend 재배포 (선택, 다음에 해도 됨)
- [ ] 테스트 메시지 전송

---

### ✅ Backend 코드 업데이트 배포

- [ ] `agent-backend/` 코드 수정 완료
- [ ] 로컬 테스트 (선택)
- [ ] Backend 재배포
  ```bash
  cd agent-backend && ./deploy_backend.sh
  ```
- [ ] 헬스 체크
  ```bash
  curl $BACKEND_URL/health
  ```
- [ ] 테스트 메시지 전송

---

### ✅ 배포 후 검증

- [ ] Agent Engine 상태 확인
  ```bash
  python deploy.py --list
  ```
- [ ] Backend 상태 확인
  ```bash
  gcloud run services describe agent-backend-api --region=us-east4
  ```
- [ ] 헬스 체크
  ```bash
  curl $BACKEND_URL/health
  ```
- [ ] 테스트 세션 생성
  ```bash
  curl -X POST $BACKEND_URL/chat/new
  ```
- [ ] 테스트 메시지 전송
  ```bash
  curl -X POST $BACKEND_URL/chat/message -H 'Content-Type: application/json' -d '...'
  ```
- [ ] Frontend 동작 확인
- [ ] 각 에이전트 기능 테스트
  - [ ] 졸업요건 검색
  - [ ] 과목 정보 검색
  - [ ] 교수 정보 검색
  - [ ] 캠퍼스 안내

---

## 유용한 명령어

### 📊 배포 상태 확인

```bash
# Agent Engine 목록
gcloud ai reasoning-engines list \
  --location=us-east4 \
  --project=kangnam-backend

# Backend 서비스 상태
gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --project=kangnam-backend

# Backend 로그 (실시간)
gcloud run logs tail agent-backend-api \
  --region=us-east4

# Backend 로그 (최근 50줄)
gcloud run logs read agent-backend-api \
  --region=us-east4 \
  --limit=50
```

---

### 🧹 리소스 정리

```bash
# 오래된 Agent Engine 삭제
python deploy.py --delete \
  --resource_id="projects/.../reasoningEngines/이전ID"

# 또는 수동 삭제
gcloud ai reasoning-engines delete 이전ID \
  --location=us-east4 \
  --project=kangnam-backend

# Backend 서비스 삭제 (주의!)
gcloud run services delete agent-backend-api \
  --region=us-east4 \
  --project=kangnam-backend
```

---

### 💰 비용 확인

```bash
# 프로젝트 전체 비용 확인 (Cloud Console)
# https://console.cloud.google.com/billing/projects/kangnam-backend

# Agent Engine 사용량 확인
gcloud ai reasoning-engines describe RESOURCE_ID \
  --location=us-east4 \
  --project=kangnam-backend

# Cloud Run 호출 횟수 확인
gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.traffic)"
```

---

## 비용 최적화

### 📊 Agent Engine 과금 구조

**Idle 시**: 무료 (비용 없음)

**실행 시**: 
- **LLM 토큰 사용량** (Gemini 2.0 Flash)
  - Input: $0.075 / 1M tokens
  - Output: $0.30 / 1M tokens
- **실행 시간** (초 단위 과금)
- **Vertex AI Search** 검색 요청
  - $5 / 1,000 queries

### 💡 권장 최적화 방안

#### 1. 세션 재사용
```javascript
// Frontend에서 세션 유지
const [sessionId, setSessionId] = useState(null);

// 같은 사용자는 세션 재사용
if (!sessionId) {
  const session = await createNewSession();
  setSessionId(session.session_id);
}
```

#### 2. 응답 캐싱
```python
# Backend에서 자주 묻는 질문 캐싱
CACHE = {}

@app.post("/chat/message")
async def chat(request: ChatRequest):
    cache_key = f"{request.user_id}:{request.message}"
    
    if cache_key in CACHE:
        return CACHE[cache_key]
    
    # ... Agent 호출 ...
    
    CACHE[cache_key] = response
    return response
```

#### 3. 검색 최적화
```python
# Tools에서 top_k 조정
search_request = {
    "query": query,
    "top_k": 3  # 기본 5 → 3으로 줄임
}
```

#### 4. 프롬프트 최적화
```python
# 긴 프롬프트 줄이기
instruction = """
당신은 강남대학교 챗봇입니다.
간결하고 정확하게 답변하세요.
"""  # 불필요한 예시 제거
```

---

## Blue-Green 배포 전략

### 🔄 무중단 배포 프로세스

```
┌─────────────────────────────────────────────────────────┐
│ 1. 현재 운영 중 (Blue)                                   │
│    AGENT_RESOURCE_ID=...reasoningEngines/1234567890     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 새 버전 배포 (Green)                                  │
│    ./update_deployment.sh                               │
│    → ...reasoningEngines/새ID                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 자동 테스트                                           │
│    - 세션 생성 테스트                                     │
│    - 샘플 메시지 테스트                                   │
└─────────────────────────────────────────────────────────┘
                         ↓
                    ✅ 성공?
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. .env 자동 업데이트                                    │
│    AGENT_RESOURCE_ID=새ID                                │
│    AGENT_RESOURCE_ID_BACKUP=이전ID                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Backend 재배포 (선택)                                 │
│    새 Agent와 자동 연결                                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 6. 이전 버전(Blue) 보관                                  │
│    문제 발생 시 즉시 롤백 가능                            │
└─────────────────────────────────────────────────────────┘
```

### 🔙 롤백 절차

```bash
# 1. 백업 ID 확인
cat .env | grep BACKUP

# 2. Resource ID 교체
# .env 파일에서 AGENT_RESOURCE_ID를 BACKUP ID로 변경

# 3. Backend 재배포
cd agent-backend
./deploy_backend.sh

# 4. 검증
curl $BACKEND_URL/health
```

---

## 참고 문서

### 📚 프로젝트 문서

- **Agent Engine 상세**: `goole_adk/DEPLOYMENT.md`
- **프로젝트 구조**: `goole_adk/README_STRUCTURE.md`
- **의존성 정보**: `goole_adk/REQUIREMENTS.md`
- **Backend API**: `agent-backend/README.md`
- **Frontend**: `agent-frontend/README.md`
- **트러블슈팅**: `TROUBLESHOOTING.md`

### 🌐 외부 문서

- [Vertex AI Agent Engine 공식 문서](https://cloud.google.com/vertex-ai/docs/reasoning-engine)
- [Google ADK GitHub](https://github.com/google/adk-docs)
- [Vertex AI Search 가이드](https://cloud.google.com/generative-ai-app-builder/docs/introduction)
- [Cloud Run 공식 문서](https://cloud.google.com/run/docs)
- [Vercel 배포 가이드](https://vercel.com/docs/deployments/overview)

---

## 🎯 핵심 요약

### 배포 명령어 (한눈에 보기)

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 가장 많이 쓰는 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 전체 배포 (처음 배포 시)
./deploy_all.sh  → 옵션 1

# Agent 코드 수정 후
./deploy_all.sh  → 옵션 2

# Backend 코드 수정 후
cd agent-backend && ./deploy_backend.sh

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 테스트 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Backend 헬스 체크
curl $(gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)")/health

# 새 세션 생성
curl -X POST $BACKEND_URL/chat/new

# 메시지 전송
curl -X POST $BACKEND_URL/chat/message \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"test","session_id":"123","message":"안녕"}'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 상태 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Agent Engine 목록
gcloud ai reasoning-engines list --location=us-east4

# Backend 서비스 상태
gcloud run services describe agent-backend-api --region=us-east4

# Backend 로그 확인
gcloud run logs tail agent-backend-api --region=us-east4
```

### 주요 특징

| 항목 | 설명 |
|------|------|
| **배포 플랫폼** | Vertex AI Agent Engine (서버리스) |
| **배포 방식** | Blue-Green (무중단) |
| **업데이트** | Agent: 재배포 필요, Backend: Resource ID만 업데이트 |
| **비용** | Idle 시 무료, 사용량 기반 과금 |
| **권한** | IAM 설정 1회 (프로젝트 레벨) |
| **확장** | 프론트엔드는 별도 API로 연동 |

### 배포 파이프라인

```
코드 수정
   ↓
./deploy_all.sh (옵션 선택)
   ↓
Agent Engine 배포 (자동)
   ↓
.env 업데이트 (자동)
   ↓
Backend 배포 (자동 또는 수동)
   ↓
헬스 체크 (자동)
   ↓
✅ 배포 완료!
```

---

## 📝 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-01-09 | 1.0 | 초기 배포 가이드 작성 |
| 2025-01-09 | 1.1 | Blue-Green 배포 추가 |
| 2025-01-10 | 1.2 | 자동화 스크립트 추가 |
| 2025-11-10 | 2.0 | Backend API 통합, 전체 재구성 |
| 2025-11-16 | 2.1 | 문서 통합 및 개선 |

---

**작성자**: 강남대 챗봇 개발팀  
**최종 수정**: 2025-11-16  
**배포 상태**: ✅ 정상 작동 중  
**현재 Resource ID**: `projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664`

---

**문의**: 추가 질문이나 문제가 있으시면 TROUBLESHOOTING.md를 참고하거나 개발팀에 문의하세요.
