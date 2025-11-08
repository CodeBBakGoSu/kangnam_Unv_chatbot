# 강남대학교 Multi-Agent 챗봇 배포 가이드

## 📋 프로젝트 정보

- **프로젝트 ID**: `kangnam-backend`
- **GCP 리전**: `us-east4` (Vertex AI Agent Engine)
- **데이터 리전**: `asia-northeast3` (GCS)
- **주요 서비스**:
  - Vertex AI Agent Engine (Multi-Agent 호스팅)
  - Vertex AI Search (졸업요건, 교수 정보 검색)
  - Cloud Storage (배포 파일 저장)

---

## 🤖 배포 아키텍처

### Multi-Agent 시스템 구조

```
Root Agent (kangnam_assistant)
├── Graduation Agent (졸업요건 검색)
│   └── Vertex AI Search
├── Subject Agent (과목 정보 검색)
│   └── 강의계획서 크롤링
├── Professor Agent (교수 정보 검색)
│   └── Vertex AI Search
└── Admission Agent (입학 정보)
    └── Placeholder
```

### 사용 기술 스택

| 컴포넌트 | 기술 |
|---------|------|
| **Agent 프레임워크** | Google ADK (Agent Development Kit) |
| **LLM 모델** | Gemini 2.0 Flash |
| **배포 플랫폼** | Vertex AI Agent Engine |
| **검색 엔진** | Vertex AI Search (Discovery Engine) |
| **인증** | google.auth (배포 환경 호환) |

---

## 🚀 빠른 시작

### 1. 초기 배포 (자동화)

```bash
# 모든 것을 자동으로 처리 (배포 + .env 등록)
chmod +x update_deployment.sh
./update_deployment.sh
```

**자동 처리 항목:**
- ✅ Agent Engine 배포
- ✅ Resource ID 추출
- ✅ `.env` 파일에 자동 등록
- ✅ 테스트 세션 생성 및 검증
- ✅ Blue-Green 배포 (업데이트 시)

### 2. 수동 배포

```bash
# Staging bucket 생성 (최초 1회)
python create_staging_bucket.py

# Agent 배포
python deploy.py --create

# Resource ID를 .env에 저장
echo "AGENT_RESOURCE_ID=projects/.../reasoningEngines/..." >> .env
```

---

## 🔄 업데이트 및 재배포

### Blue-Green 배포 전략

```bash
# 코드 수정 후 자동 업데이트
./update_deployment.sh
```

**자동 프로세스:**
1. 새 버전 배포 (Green)
2. 자동 테스트 실행
3. 성공 시 `.env` 업데이트
4. 이전 버전(Blue) ID 백업 저장
5. 문제 발생 시 자동 롤백

**수동 업데이트:**
```bash
# 새 버전 배포
python deploy.py --create

# 새 Resource ID로 .env 업데이트
# (기존 ID는 백업용으로 보관)

# 테스트 후 이전 버전 삭제
python deploy.py --delete --resource_id="이전버전ID"
```

---

## ⚠️ 해결된 주요 문제들

### 1. 배포 환경 인증 문제 ✅

**문제:**
```python
# 로컬에서만 동작 (gcloud CLI 필요)
token = subprocess.check_output(["gcloud", "auth", "print-access-token"])
```

**해결:**
```python
# 배포 환경에서도 동작 (google.auth 라이브러리)
from google.auth import default
from google.auth.transport.requests import Request

credentials, project = default()
if not credentials.valid:
    credentials.refresh(Request())
token = credentials.token
```

**변경 파일:**
- `test_rag/agents/graduation/tools/search_tools.py`
- `test_rag/agents/professor/tools/search_tools.py`

---

### 2. Discovery Engine 권한 문제 ✅

**문제:**
```
Error 403: Permission 'discoveryengine.servingConfigs.search' denied
```

**원인:**
- Agent Engine의 Service Account에 Vertex AI Search 접근 권한 없음

**해결:**
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

**중요:** 이 권한은 프로젝트 레벨에서 영구적으로 유지됩니다. 재배포 시 다시 설정할 필요 없음!

---

### 3. 세션 응답 구조 불일치 ✅

**문제:**
```python
# 예상한 필드가 없음
KeyError: 'user_id'
```

**해결:**
```python
# 선택적 필드 처리
print(f"Session ID: {remote_session.get('id') or remote_session}")

if 'user_id' in remote_session:
    print(f"User ID: {remote_session['user_id']}")
```

---

## 🔑 필수 IAM 권한

### Service Accounts

```yaml
# Reasoning Engine Service Account
service-88199591627@gcp-sa-aiplatform-re.iam.gserviceaccount.com:
  - roles/aiplatform.reasoningEngineServiceAgent  # 기본
  - roles/discoveryengine.editor                   # Vertex AI Search

# Compute Engine Default
88199591627-compute@developer.gserviceaccount.com:
  - roles/editor                                   # 프로젝트 기본
  - roles/discoveryengine.editor                   # Vertex AI Search (보험)
```

### 권한 확인

```bash
# Service Account의 역할 확인
gcloud projects get-iam-policy kangnam-backend \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:service-88199591627@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
```

---

## 🧪 테스트 방법

### 1. 세션 생성

```bash
python deploy.py --create_session \
  --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664"
```

**출력:**
```
✅ Session created!
  Session ID: 1522160049202397184
```

### 2. 메시지 전송

```bash
python deploy.py --send \
  --resource_id="projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664" \
  --session_id="1522160049202397184" \
  --message="2021년 ICT융합공학부 졸업 요건 알려줘"
```

**성공 응답:**
```json
{
  "model_version": "gemini-2.0-flash",
  "content": {
    "parts": [{
      "text": "2021~2024학년도 공과대학 졸업요건...\n✅ 기초교양: 17학점\n..."
    }]
  },
  "author": "graduation_agent"
}
```

### 3. 배포 목록 확인

```bash
python deploy.py --list
```

---

## 📦 배포 시 포함되는 항목

### Python 패키지

```
requirements = [
    "google-cloud-aiplatform[adk,agent_engines]",
    "requests",
    "beautifulsoup4",
    "python-dotenv",
]
```

### 프로젝트 파일

```
extra_packages = ["./test_rag"]
```

**포함:**
- `test_rag/agent.py` (Root Agent)
- `test_rag/agents/` (모든 Sub-Agents)
- `test_rag/config/` (환경 설정)
- 모든 Tools 및 의존성

---

## 🔍 트러블슈팅

### 403 Permission Denied

**증상:**
```
discoveryengine.servingConfigs.search denied
```

**해결:**
1. Service Account 권한 확인
2. Discovery Engine Editor 역할 부여
3. 2-3분 대기 (IAM 전파)
4. 재시도

### ModuleNotFoundError

**증상:**
```
ModuleNotFoundError: No module named 'test_rag'
```

**해결:**
- 프로젝트 루트에서 실행: `cd /Users/hong-gihyeon/Desktop/cap`
- 명령어: `python deploy.py --create`

### Session ID 오류

**증상:**
```
KeyError: 'user_id'
```

**해결:**
- 이미 수정됨 (`deploy.py`에서 선택적 필드 처리)
- 최신 `deploy.py` 사용

---

## 🌐 프론트엔드 연동

### 권장 아키텍처

```
[Frontend (React/Next.js)]
        ↓ HTTP
[Backend API (FastAPI/Cloud Run)]
        ↓ gRPC/REST
[Agent Engine (Deployed)]
        ↓
[Vertex AI Search + Gemini]
```

### 백엔드 API 예시

```python
from fastapi import FastAPI
from vertexai import agent_engines
import os

app = FastAPI()

RESOURCE_ID = os.getenv("AGENT_RESOURCE_ID")

@app.post("/chat")
async def chat(user_id: str, session_id: str, message: str):
    remote_app = agent_engines.get(RESOURCE_ID)
    
    responses = []
    for event in remote_app.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message
    ):
        # 텍스트만 추출
        if 'content' in event and 'parts' in event['content']:
            for part in event['content']['parts']:
                if 'text' in part:
                    responses.append(part['text'])
    
    return {"response": "".join(responses)}
```

---

## 📊 비용 최적화

### Agent Engine 과금 구조

- **Idle 시**: 무료 (비용 없음)
- **실행 시**: 
  - LLM 토큰 사용량 (Gemini 2.0 Flash)
  - 실행 시간 (초 단위)
  - Vertex AI Search 검색 요청

### 권장 사항

1. **세션 재사용**: 같은 사용자는 세션 유지
2. **캐싱**: 자주 묻는 질문은 캐싱
3. **검색 최적화**: `top_k` 값 조정 (기본: 5)

---

## 📚 관련 문서

- **상세 배포 가이드**: `test_rag/DEPLOYMENT.md`
- **빠른 시작**: `QUICKSTART.md`
- **의존성 정보**: `test_rag/REQUIREMENTS.md`
- **프로젝트 구조**: `test_rag/README_STRUCTURE.md`

---

## ✅ 배포 체크리스트

### 초기 배포

- [ ] `.env` 파일 설정
- [ ] GCP 인증 (`gcloud auth login`)
- [ ] Staging bucket 생성
- [ ] Discovery Engine 권한 설정
- [ ] Agent 배포 (`./update_deployment.sh`)
- [ ] 세션 생성 및 테스트

### 업데이트 배포

- [ ] 코드 수정 완료
- [ ] 로컬 테스트
- [ ] `./update_deployment.sh` 실행
- [ ] 새 버전 테스트
- [ ] 이전 버전 삭제 (선택)

---

## 🎯 핵심 요약

1. **배포**: `./update_deployment.sh` 한 번으로 모든 것 처리
2. **권한**: Discovery Engine Editor 역할 필요 (1회 설정)
3. **업데이트**: Blue-Green 배포로 안전하게 전환
4. **비용**: Idle 시 무료, 사용량 기반 과금
5. **확장**: 프론트엔드는 별도 API 서버로 연동

**배포 완료 Resource ID:**
```
projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664
```

---

**마지막 업데이트**: 2025-01-09  
**배포 상태**: ✅ 정상 작동  
**검색 기능**: ✅ Vertex AI Search 연동 완료
