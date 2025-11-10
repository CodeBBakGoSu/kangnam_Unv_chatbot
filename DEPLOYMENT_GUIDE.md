# 🚀 강남대 챗봇 배포 가이드

## 📋 목차
1. [배포 개요](#배포-개요)
2. [자동화된 배포 방법](#자동화된-배포-방법)
3. [수동 배포 방법](#수동-배포-방법)
4. [환경 변수 관리](#환경-변수-관리)
5. [트러블슈팅](#트러블슈팅)

---

## 배포 개요

강남대 챗봇은 3개의 주요 컴포넌트로 구성됩니다:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1. Agent Engine (Vertex AI Reasoning Engine)          │
│     - test_rag 폴더의 에이전트 코드                      │
│     - 졸업, 과목, 교수, 캠퍼스 정보 등 서브 에이전트     │
│     - Resource ID로 식별됨                               │
│                                                         │
│  2. Backend API (Cloud Run)                             │
│     - agent-backend 폴더의 FastAPI 서버                  │
│     - Agent Engine과 통신                                │
│     - 스트리밍 응답 제공                                  │
│                                                         │
│  3. Frontend (Vercel)                                   │
│     - agent-frontend 폴더의 React 앱                     │
│     - Backend API와 통신                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 배포 순서

**중요**: Agent Engine은 배포 후 수정 불가능합니다!
- 코드 수정 시 → 새로운 Agent Engine 배포 필요
- Backend는 새 Agent Engine의 Resource ID만 업데이트하면 됨

```
Agent Engine 배포 → Backend 배포 → Frontend 환경변수 업데이트
```

---

## 자동화된 배포 방법

### 🎯 방법 1: 통합 배포 스크립트 (권장)

**모든 것을 한 번에 배포**:

```bash
cd /Users/hong-gihyeon/Desktop/cap
chmod +x deploy_all.sh
./deploy_all.sh
```

**선택 옵션**:
- `1`: 전체 배포 (Agent Engine + Backend API)
- `2`: Agent Engine만 배포
- `3`: Backend API만 배포

**자동으로 수행되는 작업**:
1. ✅ Agent Engine 배포 (Blue-Green 방식)
2. ✅ `.env` 파일에 새 Resource ID 자동 저장
3. ✅ Backend API 배포 (새 Resource ID 사용)
4. ✅ 배포 완료 후 테스트 명령어 제공

---

### 🎯 방법 2: 개별 배포

#### Step 1: Agent Engine 배포

```bash
cd /Users/hong-gihyeon/Desktop/cap
./update_deployment.sh
```

**자동으로 수행되는 작업**:
- 새 Agent Engine 배포
- 테스트 실행
- `.env` 파일 업데이트:
  ```
  AGENT_RESOURCE_ID=projects/.../reasoningEngines/새ID
  AGENT_RESOURCE_ID_BACKUP=projects/.../reasoningEngines/이전ID
  ```

#### Step 2: Backend API 배포

```bash
cd /Users/hong-gihyeon/Desktop/cap/agent-backend
./deploy_backend.sh
```

**자동으로 수행되는 작업**:
- `.env`에서 `AGENT_RESOURCE_ID` 로드
- Cloud Run에 Backend 배포
- 환경변수로 Agent Resource ID 전달

---

## 수동 배포 방법

### Agent Engine 수동 배포

```bash
cd /Users/hong-gihyeon/Desktop/cap
python deploy.py --create
```

**출력 예시**:
```
Resource ID: projects/88199591627/locations/us-east4/reasoningEngines/1234567890
```

**`.env` 파일 수동 업데이트**:
```bash
# .env 파일 편집
echo "AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1234567890" > .env
```

### Backend API 수동 배포

```bash
cd /Users/hong-gihyeon/Desktop/cap/agent-backend

# 환경변수 설정
export AGENT_RESOURCE_ID="projects/.../reasoningEngines/..."
export GOOGLE_CLOUD_PROJECT="kangnam-backend"
export VERTEX_AI_LOCATION="us-east4"

# Cloud Run 배포
gcloud run deploy agent-backend-api \
  --source=. \
  --region=us-east4 \
  --project=kangnam-backend \
  --allow-unauthenticated \
  --set-env-vars="AGENT_RESOURCE_ID=$AGENT_RESOURCE_ID,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION"
```

---

## 환경 변수 관리

### `.env` 파일 구조

프로젝트 루트의 `.env` 파일:

```bash
# Agent Engine Resource ID (자동 업데이트됨)
AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664

# 백업 (롤백용)
AGENT_RESOURCE_ID_BACKUP=projects/88199591627/locations/us-east4/reasoningEngines/이전ID

# Google Cloud 설정
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4
```

### 환경변수 흐름

```
1. update_deployment.sh 실행
   ↓
2. 새 Agent Engine 배포
   ↓
3. .env 파일 자동 업데이트
   AGENT_RESOURCE_ID=새ID
   AGENT_RESOURCE_ID_BACKUP=이전ID
   ↓
4. deploy_backend.sh 실행
   ↓
5. .env에서 AGENT_RESOURCE_ID 로드
   ↓
6. Cloud Run에 환경변수로 전달
   ↓
7. Backend가 새 Agent Engine과 연결됨
```

### Frontend 환경변수 (Vercel)

Backend 배포 후 Vercel에 설정:

```bash
REACT_APP_API_URL=https://agent-backend-api-xxx-uc.a.run.app
```

**설정 방법**:
1. Vercel Dashboard → 프로젝트 선택
2. Settings → Environment Variables
3. `REACT_APP_API_URL` 추가
4. Redeploy

---

## 배포 시나리오

### 시나리오 1: 에이전트 코드 수정 후 배포

```bash
# 1. test_rag 폴더의 코드 수정
# 2. 통합 배포 실행
./deploy_all.sh
# → 옵션 1 선택 (전체 배포)

# 3. Frontend 환경변수 확인 (변경 없으면 스킵)
```

### 시나리오 2: Backend 코드만 수정

```bash
# 1. agent-backend 폴더의 코드 수정
# 2. Backend만 재배포
cd agent-backend
./deploy_backend.sh

# Agent Engine은 그대로 사용됨
```

### 시나리오 3: 롤백

```bash
# .env.backup에서 이전 Resource ID 확인
cat .env.backup

# .env 파일 복원
cp .env.backup .env

# Backend 재배포
cd agent-backend
./deploy_backend.sh
```

---

## 트러블슈팅

### 문제 1: AGENT_RESOURCE_ID가 없다는 에러

**증상**:
```
에러: AGENT_RESOURCE_ID가 설정되지 않았습니다.
```

**해결**:
```bash
# 1. .env 파일 확인
cat .env

# 2. 없으면 Agent Engine 먼저 배포
./update_deployment.sh

# 3. Backend 재배포
cd agent-backend
./deploy_backend.sh
```

### 문제 2: Backend가 이전 Agent Engine에 연결됨

**증상**:
- 코드 수정했는데 반영 안됨
- 이전 응답이 나옴

**해결**:
```bash
# 1. .env 파일의 AGENT_RESOURCE_ID 확인
cat .env | grep AGENT_RESOURCE_ID

# 2. Backend 로그 확인
gcloud run logs tail agent-backend-api --region=us-east4

# 3. Backend 재배포
cd agent-backend
./deploy_backend.sh
```

### 문제 3: .env 파일이 없음

**증상**:
```
에러: ../.env 파일을 찾을 수 없습니다.
```

**해결**:
```bash
# 1. 프로젝트 루트로 이동
cd /Users/hong-gihyeon/Desktop/cap

# 2. .env 파일 생성
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4
EOF

# 3. Agent Engine 배포 (AGENT_RESOURCE_ID 자동 추가됨)
./update_deployment.sh
```

### 문제 4: 배포 스크립트 실행 권한 없음

**증상**:
```
Permission denied: ./deploy_all.sh
```

**해결**:
```bash
chmod +x deploy_all.sh
chmod +x update_deployment.sh
chmod +x agent-backend/deploy_backend.sh
```

---

## 배포 체크리스트

### ✅ Agent Engine 배포 전
- [ ] test_rag 코드 수정 완료
- [ ] 로컬 테스트 완료
- [ ] Google Cloud 인증 확인: `gcloud auth list`

### ✅ Backend 배포 전
- [ ] `.env` 파일에 `AGENT_RESOURCE_ID` 존재 확인
- [ ] agent-backend 코드 수정 완료 (필요시)
- [ ] Google Cloud 인증 확인

### ✅ 배포 후
- [ ] Backend URL 확인
- [ ] 테스트 메시지 전송: `curl -X POST [URL]/chat/new`
- [ ] Frontend 환경변수 업데이트 (필요시)
- [ ] Frontend 재배포 (필요시)

---

## 유용한 명령어

### 배포 상태 확인

```bash
# Agent Engine 목록
gcloud ai reasoning-engines list \
  --location=us-east4 \
  --project=kangnam-backend

# Backend 서비스 상태
gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --project=kangnam-backend

# Backend 로그
gcloud run logs tail agent-backend-api \
  --region=us-east4
```

### 테스트

```bash
# Backend 테스트
BACKEND_URL=$(gcloud run services describe agent-backend-api \
  --region=us-east4 \
  --format="value(status.url)")

curl -X POST $BACKEND_URL/chat/new

curl -X POST $BACKEND_URL/chat/message \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"test","session_id":"123","message":"안녕"}' \
  -N
```

---

## 참고 문서

- [test_rag/DEPLOYMENT.md](test_rag/DEPLOYMENT.md) - Agent Engine 상세 가이드
- [agent-backend/README.md](agent-backend/README.md) - Backend API 가이드
- [agent-frontend/README.md](agent-frontend/README.md) - Frontend 가이드

---

**작성일**: 2025-11-10  
**최종 수정**: 2025-11-10

