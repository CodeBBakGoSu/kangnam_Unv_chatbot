# ⚡ 빠른 시작 가이드

## 🚀 한 줄 배포

```bash
./deploy_all.sh
```

선택 옵션:
- `1`: 전체 배포 (Agent + Backend) ⭐ **권장**
- `2`: Agent만 배포
- `3`: Backend만 배포

---

## 📝 배포 시나리오

### 1️⃣ Agent 코드 수정 후 배포 (가장 흔한 경우)

```bash
# test_rag 폴더 코드 수정 후
./deploy_all.sh
# → 옵션 2 선택 (Agent만 배포)
```

**결과**:
- ✅ 새 Agent Engine 배포
- ✅ `.env` 자동 업데이트
- ✅ Backend는 자동으로 새 Agent 사용
- ✅ **Frontend 재배포 불필요** (Backend URL 변경 없음)

### 2️⃣ Backend 코드 수정 후 배포

```bash
cd agent-backend
./deploy_backend.sh
```

**결과**:
- ✅ Backend API 재배포
- ✅ **Frontend 재배포 불필요** (Backend URL 변경 없음)

### 3️⃣ 처음 배포하는 경우

```bash
./deploy_all.sh
# → 옵션 1 선택 (전체 배포)
```

**이후 작업**:
- Backend URL을 Vercel에 설정:
  ```
  REACT_APP_API_URL=https://agent-backend-api-xxx.run.app
  ```
- Frontend 재배포

---

## 🔧 자동화된 작업

### `deploy_all.sh`가 자동으로 수행:

1. ✅ Agent Engine 배포
2. ✅ `.env` 파일 업데이트
   ```
   AGENT_RESOURCE_ID=새로운ID
   ```
3. ✅ Backend API 배포 (새 Agent와 자동 연결)
4. ✅ 테스트 명령어 제공

### `.env` 파일 구조:

```bash
AGENT_RESOURCE_ID=projects/.../reasoningEngines/최신ID
AGENT_RESOURCE_ID_BACKUP=projects/.../reasoningEngines/이전ID
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4
```

---

## 🎯 핵심 포인트

### ✅ Frontend 재배포가 필요한 경우
- **처음 배포할 때만!**
- Backend URL을 Vercel 환경변수에 설정
- 이후에는 재배포 불필요

### ❌ Frontend 재배포가 필요 없는 경우
- Agent 코드 수정 후 배포
- Backend 코드 수정 후 배포
- **Backend URL은 변경되지 않음!**

### Agent Engine은 수정 불가!
- 코드 수정 → 새로 배포 필요
- `.env`에 새 Resource ID 자동 저장됨

### Backend는 Resource ID만 업데이트
- `.env`에서 자동으로 최신 ID 로드
- 재배포만 하면 새 Agent와 연결됨

---

## 🆘 문제 해결

### "AGENT_RESOURCE_ID가 없다"는 에러?

```bash
# Agent Engine 먼저 배포
./update_deployment.sh

# 그 다음 Backend 배포
cd agent-backend
./deploy_backend.sh
```

### 코드 수정이 반영 안됨?

```bash
# Agent Engine 재배포 필요
./deploy_all.sh
# → 옵션 1 선택
```

### 실행 권한 에러?

```bash
chmod +x deploy_all.sh
chmod +x update_deployment.sh
chmod +x agent-backend/deploy_backend.sh
```

---

## 📚 상세 가이드

더 자세한 내용은 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 참고

---

**마지막 업데이트**: 2025-11-10

