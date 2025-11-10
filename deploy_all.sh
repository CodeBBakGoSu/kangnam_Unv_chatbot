#!/bin/bash

# 강남대 챗봇 전체 배포 스크립트
# Agent Engine 배포 → Backend API 배포를 자동으로 수행

set -e          # 에러 발생 시 중단
set -o pipefail # 파이프라인에서도 에러 감지

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}║       🚀 강남대 챗봇 통합 배포 스크립트              ║${NC}"
echo -e "${BLUE}║          Agent Engine + Backend API                   ║${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}💡 TIP: 배포 로그가 실시간으로 표시됩니다${NC}"
echo ""

# 배포 모드 선택
echo -e "${YELLOW}배포 모드를 선택하세요:${NC}"
echo "  1) 전체 배포 (Agent Engine + Backend API)"
echo "  2) Agent Engine만 배포"
echo "  3) Backend API만 배포"
echo ""
read -p "선택 (1-3): " DEPLOY_MODE
echo ""

case $DEPLOY_MODE in
    1)
        echo -e "${GREEN}전체 배포 모드 선택됨${NC}"
        DEPLOY_AGENT=true
        DEPLOY_BACKEND=true
        ;;
    2)
        echo -e "${GREEN}Agent Engine만 배포${NC}"
        DEPLOY_AGENT=true
        DEPLOY_BACKEND=false
        ;;
    3)
        echo -e "${GREEN}Backend API만 배포${NC}"
        DEPLOY_AGENT=false
        DEPLOY_BACKEND=true
        ;;
    *)
        echo -e "${RED}잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# 배포 단계 계산
TOTAL_STEPS=0
if [ "$DEPLOY_AGENT" = true ]; then
    TOTAL_STEPS=$((TOTAL_STEPS + 1))
fi
if [ "$DEPLOY_BACKEND" = true ]; then
    TOTAL_STEPS=$((TOTAL_STEPS + 1))
fi

CURRENT_STEP=0

# 배포 시작 시간 기록
DEPLOY_START_TIME=$(date +%s)

# ============================================================================
# 1단계: Agent Engine 배포
# ============================================================================

if [ "$DEPLOY_AGENT" = true ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    AGENT_START_TIME=$(date +%s)
    echo -e "${GREEN}[${CURRENT_STEP}/${TOTAL_STEPS}] 🤖 Agent Engine 배포 시작...${NC}"
    echo -e "${BLUE}⏰ 시작 시간: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    
    # update_deployment.sh 실행
    if [ ! -f "./update_deployment.sh" ]; then
        echo -e "${RED}에러: update_deployment.sh 파일을 찾을 수 없습니다.${NC}"
        exit 1
    fi
    
    chmod +x ./update_deployment.sh
    
    echo -e "${YELLOW}📋 배포 로그 (실시간):${NC}"
    echo -e "${BLUE}┌─────────────────────────────────────────────────────┐${NC}"
    
    # 임시 파일에 출력 저장하면서 실시간 표시
    AGENT_LOG=$(mktemp)
    
    # update_deployment.sh 실행 (출력을 파일과 화면에 동시 표시)
    if ./update_deployment.sh 2>&1 | tee "$AGENT_LOG" | while IFS= read -r line; do
        # 중요한 메시지는 강조
        if echo "$line" | grep -qE "(배포|완료|실패|에러|Resource ID|세션|━)"; then
            echo -e "${YELLOW}│${NC} $line"
        else
            echo "│ $line"
        fi
    done; then
        DEPLOY_STATUS=0
    else
        DEPLOY_STATUS=1
    fi
    
    echo -e "${BLUE}└─────────────────────────────────────────────────────┘${NC}"
    
    # 로그 파일 정리
    rm -f "$AGENT_LOG"
    
    if [ $DEPLOY_STATUS -ne 0 ]; then
        echo ""
        echo -e "${RED}❌ Agent Engine 배포 실패!${NC}"
        echo ""
        echo -e "${YELLOW}💡 TIP: 에러 로그가 위에 표시되어 있습니다${NC}"
        exit 1
    fi
    
    echo ""
    
    # 배포 소요 시간 계산
    AGENT_END_TIME=$(date +%s)
    AGENT_DURATION=$((AGENT_END_TIME - AGENT_START_TIME))
    
    echo -e "${GREEN}✅ Agent Engine 배포 완료!${NC}"
    echo -e "${BLUE}⏱️  소요 시간: ${AGENT_DURATION}초${NC}"
    echo ""
    
    # .env에서 새로운 AGENT_RESOURCE_ID 읽기
    if [ -f ".env" ]; then
        NEW_AGENT_ID=$(grep "^AGENT_RESOURCE_ID=" .env | cut -d '=' -f2)
        echo -e "${BLUE}📌 새 Agent Resource ID: ${NC}$NEW_AGENT_ID"
    else
        echo -e "${RED}에러: .env 파일을 찾을 수 없습니다.${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
else
    echo -e "${YELLOW}Agent Engine 배포 건너뜀${NC}"
    echo ""
fi

# ============================================================================
# 2단계: Backend API 배포
# ============================================================================

if [ "$DEPLOY_BACKEND" = true ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    BACKEND_START_TIME=$(date +%s)
    echo -e "${GREEN}[${CURRENT_STEP}/${TOTAL_STEPS}] 🔧 Backend API 배포 시작...${NC}"
    echo -e "${BLUE}⏰ 시작 시간: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        echo -e "${RED}에러: .env 파일을 찾을 수 없습니다.${NC}"
        echo "먼저 Agent Engine을 배포하거나 .env 파일을 생성하세요."
        exit 1
    fi
    
    # AGENT_RESOURCE_ID 확인
    AGENT_ID=$(grep "^AGENT_RESOURCE_ID=" .env | cut -d '=' -f2)
    if [ -z "$AGENT_ID" ]; then
        echo -e "${RED}에러: .env 파일에 AGENT_RESOURCE_ID가 없습니다.${NC}"
        echo "먼저 Agent Engine을 배포하세요."
        exit 1
    fi
    
    echo -e "${BLUE}📌 사용할 Agent Resource ID:${NC}"
    echo "   $AGENT_ID"
    echo ""
    
    # agent-backend 디렉토리로 이동
    cd agent-backend
    
    # deploy_backend.sh 실행
    if [ ! -f "./deploy_backend.sh" ]; then
        echo -e "${RED}에러: deploy_backend.sh 파일을 찾을 수 없습니다.${NC}"
        cd ..
        exit 1
    fi
    
    chmod +x ./deploy_backend.sh
    
    echo -e "${YELLOW}📋 배포 로그 (실시간):${NC}"
    echo -e "${BLUE}┌─────────────────────────────────────────────────────┐${NC}"
    
    # 임시 파일에 출력 저장하면서 실시간 표시
    BACKEND_LOG=$(mktemp)
    
    # deploy_backend.sh 실행 (출력을 파일과 화면에 동시 표시)
    if ./deploy_backend.sh 2>&1 | tee "$BACKEND_LOG" | while IFS= read -r line; do
        # 중요한 메시지는 강조
        if echo "$line" | grep -qE "(배포|완료|실패|에러|Service URL|Cloud Run|Building|Deploying|═)"; then
            echo -e "${YELLOW}│${NC} $line"
        else
            echo "│ $line"
        fi
    done; then
        BACKEND_STATUS=0
    else
        BACKEND_STATUS=1
    fi
    
    echo -e "${BLUE}└─────────────────────────────────────────────────────┘${NC}"
    
    # 로그 파일 정리
    rm -f "$BACKEND_LOG"
    
    cd ..
    
    if [ $BACKEND_STATUS -ne 0 ]; then
        echo ""
        echo -e "${RED}❌ Backend API 배포 실패!${NC}"
        echo ""
        echo -e "${YELLOW}💡 TIP: 에러 로그가 위에 표시되어 있습니다${NC}"
        exit 1
    fi
    
    echo ""
    
    # 배포 소요 시간 계산
    BACKEND_END_TIME=$(date +%s)
    BACKEND_DURATION=$((BACKEND_END_TIME - BACKEND_START_TIME))
    
    echo -e "${GREEN}✅ Backend API 배포 완료!${NC}"
    echo -e "${BLUE}⏱️  소요 시간: ${BACKEND_DURATION}초${NC}"
    echo ""
else
    echo -e "${YELLOW}Backend API 배포 건너뜀${NC}"
    echo ""
fi

# ============================================================================
# 배포 완료 요약
# ============================================================================

# 전체 배포 소요 시간 계산
DEPLOY_END_TIME=$(date +%s)
TOTAL_DURATION=$((DEPLOY_END_TIME - DEPLOY_START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}║                  🎉 배포 완료! 🎉                     ║${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}⏱️  전체 소요 시간: ${MINUTES}분 ${SECONDS}초${NC}"
echo ""

if [ "$DEPLOY_AGENT" = true ]; then
    echo -e "${GREEN}✅ Agent Engine:${NC} 배포됨 (${AGENT_DURATION}초)"
    if [ -n "$NEW_AGENT_ID" ]; then
        echo "   Resource ID: $NEW_AGENT_ID"
    fi
fi

if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "${GREEN}✅ Backend API:${NC} 배포됨 (${BACKEND_DURATION}초)"
    
    # Cloud Run 서비스 URL 가져오기
    SERVICE_URL=$(gcloud run services describe "agent-backend-api" \
        --region="us-east4" \
        --project="kangnam-backend" \
        --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo "   Service URL: $SERVICE_URL"
        echo ""
        echo -e "${YELLOW}💡 참고:${NC}"
        echo "   • Backend URL은 변경되지 않았습니다"
        echo "   • Frontend 재배포는 필요하지 않습니다"
        echo ""
        echo -e "${YELLOW}🧪 테스트:${NC}"
        echo "   curl -X POST $SERVICE_URL/chat/new"
    fi
elif [ "$DEPLOY_AGENT" = true ]; then
    # Agent만 배포한 경우
    echo ""
    echo -e "${YELLOW}💡 참고:${NC}"
    echo "   • Agent Engine만 업데이트되었습니다"
    echo "   • Backend는 자동으로 새 Agent를 사용합니다"
    echo "   • Frontend 재배포는 필요하지 않습니다"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

