#!/bin/bash

# Agent Backend API를 Cloud Run에 배포하는 스크립트
# 소스 기반 배포 (Buildpack 사용 - Docker 불필요)

set -e  # 에러 발생 시 중단

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Agent Backend API - Cloud Run 배포  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. 환경 변수 로드
if [ -f ../.env ]; then
    echo -e "${YELLOW}[1/5]${NC} .env 파일에서 환경 변수 로드 중..."
    # .env 파일의 변수를 export
    set -a
    source ../.env
    set +a
    echo "  ✓ .env 파일 로드 완료"
else
    echo -e "${RED}에러: ../.env 파일을 찾을 수 없습니다.${NC}"
    echo "프로젝트 루트에 .env 파일이 있는지 확인하세요."
    echo ""
    echo "해결 방법:"
    echo "  1. 프로젝트 루트로 이동: cd .."
    echo "  2. Agent Engine 배포: ./update_deployment.sh"
    echo "  3. 다시 시도: cd agent-backend && ./deploy_backend.sh"
    exit 1
fi

# 2. 필수 환경 변수 확인
echo -e "${YELLOW}[2/5]${NC} 환경 변수 확인 중..."
if [ -z "$AGENT_RESOURCE_ID" ]; then
    echo -e "${RED}에러: AGENT_RESOURCE_ID가 설정되지 않았습니다.${NC}"
    echo ""
    echo "해결 방법:"
    echo "  1. 프로젝트 루트로 이동: cd .."
    echo "  2. Agent Engine 배포: ./update_deployment.sh"
    echo "  3. 다시 시도: cd agent-backend && ./deploy_backend.sh"
    echo ""
    echo "또는 통합 배포 스크립트 사용:"
    echo "  ./deploy_all.sh"
    exit 1
fi

echo "  ✓ AGENT_RESOURCE_ID: $AGENT_RESOURCE_ID"
echo "  ✓ GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-kangnam-backend}"
echo "  ✓ VERTEX_AI_LOCATION: ${VERTEX_AI_LOCATION:-us-east4}"
echo ""
echo -e "${GREEN}  → Backend가 이 Agent Engine에 연결됩니다!${NC}"

# 3. gcloud 인증 확인
echo -e "${YELLOW}[3/5]${NC} Google Cloud 인증 확인 중..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}에러: Google Cloud에 로그인되어 있지 않습니다.${NC}"
    echo "다음 명령어를 실행하세요: gcloud auth login"
    exit 1
fi
echo "  ✓ 인증 확인 완료"

# 4. 배포 설정
SERVICE_NAME="agent-backend-api"
REGION="${VERTEX_AI_LOCATION:-us-east4}"
PROJECT="${GOOGLE_CLOUD_PROJECT:-kangnam-backend}"

echo -e "${YELLOW}[4/5]${NC} 배포 설정:"
echo "  • 서비스 이름: $SERVICE_NAME"
echo "  • 리전: $REGION"
echo "  • 프로젝트: $PROJECT"
echo ""

# 5. Cloud Run 배포 (소스 기반)
echo -e "${YELLOW}[5/5]${NC} Cloud Run에 배포 중..."
echo "  (빌드팩이 자동으로 Python/FastAPI를 감지합니다)"
echo ""

gcloud run deploy "$SERVICE_NAME" \
  --source=. \
  --region="$REGION" \
  --project="$PROJECT" \
  --allow-unauthenticated \
  --set-env-vars="AGENT_RESOURCE_ID=$AGENT_RESOURCE_ID,GOOGLE_CLOUD_PROJECT=$PROJECT,VERTEX_AI_LOCATION=$REGION" \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --memory=1Gi \
  --cpu=1 \
  --platform=managed

# 배포 완료
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  배포 완료! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT" \
  --format="value(status.url)")

echo -e "${GREEN}서비스 URL:${NC} $SERVICE_URL"
echo ""
echo -e "${YELLOW}테스트 명령어:${NC}"
echo ""
echo "# 새 채팅 시작"
echo "curl -X POST $SERVICE_URL/chat/new"
echo ""
echo "# 메시지 전송 (스트리밍)"
echo "curl -X POST $SERVICE_URL/chat/message \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"user_id\":\"anon_test\",\"session_id\":\"123\",\"message\":\"안녕\"}' \\"
echo "  -N"
echo ""
echo -e "${YELLOW}API 문서:${NC} $SERVICE_URL/docs"
echo ""
echo -e "${YELLOW}로그 확인:${NC}"
echo "gcloud run logs tail $SERVICE_NAME --region=$REGION"
echo ""

