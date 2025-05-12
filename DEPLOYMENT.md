# 강남대학교 챗봇 배포 가이드

## 프로젝트 정보

- **프로젝트 ID**: `kangnam-backend`
- **서비스 계정**: `88199591627-compute@developer.gserviceaccount.com`
- **이미지**: `gcr.io/kangnam-backend/fastapi-backend`

## 배포 상태

빌드가 성공적으로 완료되었습니다:
- **빌드 ID**: `35857200-058e-442c-8541-f3828726fcc9`
- **소요 시간**: 10분 25초
- **상태**: SUCCESS

## 배포 확인 명령어

### 배포된 리전 확인하기
```bash
# 모든 리전의 서비스 목록 확인
gcloud run services list

# 특정 리전의 서비스 확인
gcloud run services list --region=asia-east1
gcloud run services list --region=asia-northeast3
```

### 서비스 세부 정보 확인
```bash
# 서비스 세부 정보 확인 (리전 필요)
gcloud run services describe kangnam-backend --region=REGION_NAME

# 배포된 URL 확인
gcloud run services describe kangnam-backend --region=REGION_NAME --format="value(status.url)"
```

## 환경변수 설정

서비스에 환경변수를 설정할 때는 다음 명령어를 사용합니다:
```bash
gcloud run services update kangnam-backend \
  --region=REGION_NAME \
  --update-env-vars SUPABASE_URL=https://gvyxdsrjhubzfewtodan.supabase.co,SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2eXhkc3JqaHViemZld3RvZGFuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2MzMxODEsImV4cCI6MjA2MjIwOTE4MX0.cPIX14jA0z0Y7hZaa4CCteuedAw4Jan5Ck8Vyci7sAo,GOOGLE_API_KEY=AIzaSyBTFbN8a9clizv4u1Us1wE_1o8kRsuJ24Y,DATABASE_URL=sqlite:///data/kangnam_chatbot.db
```

## 로그 확인

```bash
# 서비스 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=kangnam-backend" --limit=10
```

## 주의사항

1. **로깅 권한 문제**: 현재 서비스 계정에 로그 작성 권한이 없습니다. 다음 명령어로 권한을 부여할 수 있습니다:
   ```bash
   gcloud projects add-iam-policy-binding kangnam-backend \
     --member=serviceAccount:88199591627-compute@developer.gserviceaccount.com \
     --role=roles/logging.logWriter
   ```

2. **SQLite 데이터베이스**: Cloud Run에서 SQLite를 사용할 경우 배포마다 데이터가 초기화됩니다. 프로덕션 환경에서는 영구 데이터베이스(PostgreSQL, MySQL 등)를 고려하세요. 