# 🚀 빠른 배포 가이드

## 재배포/업데이트 방법

### 1️⃣ 코드 수정
원하는 파일을 수정합니다:
- `main.py` - FastAPI 앱 수정
- `routers/chat.py` - API 엔드포인트 수정
- `services/chat_service.py` - Agent Engine 통신 로직 수정
- `requirements.txt` - 패키지 추가/변경

### 2️⃣ 배포 스크립트 실행
```bash
cd agent-backend
./deploy_backend.sh
```

**끝!** 🎉

## 📋 사전 요구사항

배포 스크립트가 자동으로 확인하는 항목:

### ✅ .env 파일 (프로젝트 루트)
```bash
# 위치: /Users/hong-gihyeon/Desktop/cap/.env
AGENT_RESOURCE_ID=projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4
```

### ✅ Google Cloud 인증
```bash
gcloud auth list
# ACTIVE 계정이 있어야 함

# 로그인 안 되어있으면
gcloud auth login
```

### ✅ 실행 권한
```bash
chmod +x deploy_backend.sh  # 이미 설정되어 있음
```

## 🔧 배포 프로세스

스크립트가 자동으로 수행하는 작업:

1. **환경 변수 로드** - `../.env` 파일 읽기
2. **필수 변수 확인** - AGENT_RESOURCE_ID 등 검증
3. **인증 확인** - gcloud 로그인 상태 확인
4. **Cloud Run 배포** - 소스 기반 배포 실행
   - Buildpack이 자동으로 Python/FastAPI 감지
   - 의존성 자동 설치
   - 컨테이너 빌드 및 배포

## ⚙️ 배포 설정

현재 설정:
- **메모리**: 1Gi
- **CPU**: 1
- **Min Instances**: 0 (비용 절감)
- **Max Instances**: 10 (자동 스케일링)
- **Timeout**: 300초 (5분)
- **인증**: Unauthenticated (공개 API)

## 📝 수정이 필요한 경우

### 메모리 증가
`deploy_backend.sh` 수정:
```bash
--memory=2Gi  # 1Gi → 2Gi
```

### 인스턴스 최소 개수 설정 (항상 켜놓기)
```bash
--min-instances=1  # 0 → 1 (콜드 스타트 방지, 비용 증가)
```

### 환경 변수 추가
```bash
--set-env-vars="AGENT_RESOURCE_ID=$AGENT_RESOURCE_ID,NEW_VAR=value"
```

## 🐛 문제 해결

### "../.env 파일을 찾을 수 없습니다"
→ 프로젝트 루트에 .env 파일이 있는지 확인

### "AGENT_RESOURCE_ID가 설정되지 않았습니다"
→ .env 파일에 AGENT_RESOURCE_ID 추가
→ 또는 Agent Engine을 먼저 배포: `python deploy.py --create`

### "Google Cloud에 로그인되어 있지 않습니다"
→ `gcloud auth login` 실행

### 배포 실패
→ 로그 확인: `gcloud run logs tail agent-backend-api --region=us-east4`

## 📊 배포 후 확인

```bash
# 헬스체크
curl https://agent-backend-api-88199591627.us-east4.run.app/health

# 새 채팅
curl -X POST https://agent-backend-api-88199591627.us-east4.run.app/chat/new

# API 문서
# 브라우저에서: https://agent-backend-api-88199591627.us-east4.run.app/docs
```

## 💡 팁

### 수동 배포 (스크립트 없이)
```bash
cd agent-backend
gcloud run deploy agent-backend-api \
  --source=. \
  --region=us-east4 \
  --project=kangnam-backend \
  --allow-unauthenticated \
  --set-env-vars="AGENT_RESOURCE_ID=projects/.../reasoningEngines/...,GOOGLE_CLOUD_PROJECT=kangnam-backend,VERTEX_AI_LOCATION=us-east4" \
  --memory=1Gi
```

### 빠른 테스트 (로컬)
```bash
cd agent-backend
uvicorn main:app --reload --port 8080
```

### 로그 실시간 확인
```bash
gcloud run logs tail agent-backend-api --region=us-east4 --follow
```

---

**정리:**
1. 코드 수정
2. `cd agent-backend && ./deploy_backend.sh`
3. 완료! 🎉

