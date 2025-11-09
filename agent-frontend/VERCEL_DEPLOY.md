# Vercel 배포 가이드

강남대학교 챗봇 프론트엔드를 Vercel에 배포하는 방법입니다.

## 📋 사전 준비

### 1. 환경 변수 파일 생성
```bash
cd agent-frontend
cp .env.example .env.local
```

`.env.local` 파일이 생성되며, 백엔드 API URL이 자동으로 설정되어 있습니다:
```
REACT_APP_API_URL=https://agent-backend-api-88199591627.us-east4.run.app
```

## 🚀 배포 방법

### 방법 1: GitHub 연동 배포 (추천)

가장 간편하고 자동화된 방법입니다.

#### 1단계: GitHub 저장소에 코드 push
```bash
git add .
git commit -m "Add frontend with backend integration"
git push origin main
```

#### 2단계: Vercel에서 프로젝트 import
1. [Vercel Dashboard](https://vercel.com/dashboard) 접속
2. "New Project" 클릭
3. GitHub 저장소 연결 (최초 1회)
4. 저장소 선택 (`cap` 또는 해당 저장소)
5. 프로젝트 루트 설정:
   - **Root Directory**: `agent-frontend` 선택
6. 환경 변수 설정:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://agent-backend-api-88199591627.us-east4.run.app`
7. "Deploy" 클릭

#### 3단계: 배포 완료
- 몇 분 후 배포 완료
- Vercel이 자동으로 URL 생성 (예: `https://your-project.vercel.app`)
- 이후 `main` 브랜치에 push하면 자동 재배포

### 방법 2: Vercel CLI 배포

CLI를 통한 수동 배포 방법입니다.

#### 1단계: Vercel CLI 설치
```bash
npm install -g vercel
```

#### 2단계: 로그인
```bash
vercel login
```

#### 3단계: 배포
```bash
cd agent-frontend
vercel
```

프롬프트에서:
- **Set up and deploy**: `Y`
- **Which scope**: 본인 계정 선택
- **Link to existing project**: `N` (최초) / `Y` (재배포)
- **Project name**: 원하는 이름 입력
- **Directory**: `.` (현재 디렉토리)
- **Override settings**: `N`

#### 4단계: 환경 변수 설정 (최초 1회)
```bash
vercel env add REACT_APP_API_URL
# 입력: https://agent-backend-api-88199591627.us-east4.run.app
# 환경: Production, Preview, Development 모두 선택
```

#### 5단계: 프로덕션 배포
```bash
vercel --prod
```

## ✅ 배포 후 확인

### 1. 웹사이트 접속
배포 완료 후 제공된 URL로 접속

### 2. 기능 테스트
- ✅ 페이지 로드 시 자동으로 세션 생성
- ✅ "New" 버튼 클릭 시 채팅 초기화
- ✅ 추천 질문 클릭하여 질문 입력
- ✅ 메시지 전송 시 스트리밍 응답 확인
- ✅ 여러 메시지 연속 전송 테스트

### 3. 브라우저 콘솔 확인
F12를 눌러 개발자 도구를 열고:
- Network 탭에서 API 호출 확인
- Console 탭에서 에러 없는지 확인

## 🔧 재배포 (업데이트)

### GitHub 연동 시
```bash
git add .
git commit -m "Update frontend"
git push origin main
```
→ 자동으로 Vercel에 재배포됨

### Vercel CLI 사용 시
```bash
cd agent-frontend
vercel --prod
```

## 🐛 문제 해결

### "REACT_APP_API_URL is not defined"
→ Vercel 대시보드에서 환경 변수 설정:
1. Project Settings → Environment Variables
2. `REACT_APP_API_URL` 추가
3. 값: `https://agent-backend-api-88199591627.us-east4.run.app`
4. Save → Redeploy

### "Failed to create chat: CORS error"
→ 백엔드 API가 CORS를 허용하는지 확인
- 백엔드 `main.py`에 CORS 설정 확인:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 Vercel URL 추가
    ...
)
```

### "Build failed"
→ 로컬에서 먼저 테스트:
```bash
cd agent-frontend
npm run build
```
에러 메시지 확인 후 수정

### 배포는 성공했지만 API 호출 실패
→ 백엔드 API URL 확인:
1. `.env.local` 파일 확인
2. Vercel 환경 변수 확인
3. 백엔드 API가 실행 중인지 확인:
```bash
curl https://agent-backend-api-88199591627.us-east4.run.app/health
```

## 📊 배포 상태 확인

### Vercel Dashboard
- 배포 로그 확인
- 트래픽 모니터링
- 빌드 히스토리

### Vercel CLI
```bash
# 배포 목록
vercel list

# 로그 확인
vercel logs [deployment-url]

# 도메인 확인
vercel domains
```

## 🔗 유용한 링크

- **Vercel 문서**: https://vercel.com/docs
- **Create React App 배포**: https://create-react-app.dev/docs/deployment/
- **백엔드 API 문서**: https://agent-backend-api-88199591627.us-east4.run.app/docs

## 💡 Tip

### 커스텀 도메인 설정
Vercel 대시보드에서:
1. Project Settings → Domains
2. 도메인 추가
3. DNS 설정 (Vercel이 가이드 제공)

### Preview 배포
Pull Request 생성 시 자동으로 preview 환경 배포됨

### 환경별 설정
- **Production**: `main` 브랜치
- **Preview**: Pull Request
- **Development**: 로컬 환경

---

**배포 완료 후 프론트엔드와 백엔드가 연동되어 작동합니다!** 🎉

