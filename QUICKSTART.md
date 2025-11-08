# test_rag 빠른 시작 가이드

## 1️⃣ 의존성 설치

```bash
cd /Users/hong-gihyeon/Desktop/cap

# uv 사용 (권장)
uv pip install -r requirements.txt

# 또는 일반 pip 사용
pip install -r requirements.txt
```

설치되는 패키지:
- `google-cloud-aiplatform[adk,agent_engines]` - Vertex AI + ADK
- `requests` - HTTP 클라이언트
- `beautifulsoup4` - HTML 파싱
- `python-dotenv` - 환경 변수
- `absl-py` - 커맨드 라인 플래그

## 2️⃣ 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```bash
# Google Cloud 설정
GOOGLE_CLOUD_PROJECT=kangnam-backend
VERTEX_AI_LOCATION=us-east4

# GCS Bucket (데이터 저장용)
GCS_BUCKET_NAME=kangnam-univ
GCS_BUCKET_LOCATION=asia-northeast3

# Vertex AI Search Corpus (졸업요건)
KANGNAM_CORPUS_ID=6917529027641081856
```

## 3️⃣ GCP 인증

```bash
# GCP 로그인
gcloud auth login

# Application Default Credentials 설정
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project kangnam-backend
```

## 4️⃣ Staging Bucket 생성

```bash
python create_staging_bucket.py
```

출력된 `GOOGLE_CLOUD_STAGING_BUCKET` 라인을 `.env` 파일에 추가하세요.

## 5️⃣ 배포

```bash
python deploy.py --create
```

배포가 완료되면 `Resource ID`가 출력됩니다. 이를 저장하세요!

## 6️⃣ 테스트

### 세션 생성
```bash
python deploy.py --create_session \
  --resource_id="projects/.../reasoningEngines/..."
```

### 메시지 전송
```bash
python deploy.py --send \
  --resource_id="projects/.../reasoningEngines/..." \
  --session_id="session_..." \
  --message="2024년 공과대학 졸업 요건 알려줘"
```

## 🔍 트러블슈팅

### "ModuleNotFoundError: No module named 'absl'"
→ `uv pip install -r requirements.txt` 실행

### "ModuleNotFoundError: No module named 'test_rag'"
→ 프로젝트 루트(`/Users/hong-gihyeon/Desktop/cap`)에서 실행하세요

### "Permission denied"
→ `gcloud auth application-default login` 실행

### "Missing: GOOGLE_CLOUD_STAGING_BUCKET"
→ `python create_staging_bucket.py` 실행 후 `.env` 파일 업데이트

## 📚 자세한 문서

- **배포 가이드**: `test_rag/DEPLOYMENT.md`
- **의존성 상세**: `test_rag/REQUIREMENTS.md`
- **프로젝트 구조**: `test_rag/README_STRUCTURE.md`

## 🚀 다음 단계

1. 프론트엔드 연동
2. 모니터링 설정
3. 에러 로깅 구성
4. 사용량 추적

