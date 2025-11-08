#!/bin/bash
# test_rag Agent 업데이트 스크립트 (Blue-Green 배포)

set -e

echo "🔄 Agent 업데이트 시작..."
echo ""

# 현재 배포된 Resource ID 읽기
CURRENT_ID=$(grep "AGENT_RESOURCE_ID=" .env 2>/dev/null | cut -d '=' -f2)

if [ -z "$CURRENT_ID" ]; then
    echo "⚠️  .env 파일에 AGENT_RESOURCE_ID가 없습니다."
    echo "   초기 배포를 실행합니다..."
    echo ""
    
    # 초기 배포
    INITIAL_RESOURCE_ID=$(python deploy.py --create 2>&1 | grep "Resource ID:" | awk '{print $4}')
    
    if [ -z "$INITIAL_RESOURCE_ID" ]; then
        echo "❌ 배포 실패!"
        exit 1
    fi
    
    echo ""
    echo "✅ 배포 완료: $INITIAL_RESOURCE_ID"
    echo ""
    echo "📝 .env 파일에 자동 등록 중..."
    
    # .env 파일에 추가
    echo "AGENT_RESOURCE_ID=$INITIAL_RESOURCE_ID" >> .env
    
    echo "✅ .env 파일 업데이트 완료!"
    echo ""
    echo "=" | tr '=' '=' | head -c 70
    echo ""
    echo "🎉 초기 배포 완료!"
    echo "=" | tr '=' '=' | head -c 70
    echo ""
    echo "📌 Resource ID: $INITIAL_RESOURCE_ID"
    echo ""
    echo "🔑 다음 단계:"
    echo "   1. 세션 생성:"
    echo "      python deploy.py --create_session --resource_id=\"$INITIAL_RESOURCE_ID\""
    echo ""
    echo "   2. 메시지 전송:"
    echo "      python deploy.py --send --resource_id=\"$INITIAL_RESOURCE_ID\" --session_id=\"세션ID\" --message=\"테스트\""
    echo ""
    exit 0
fi

echo "📌 현재 배포: $CURRENT_ID"
echo ""

# 새 버전 배포
echo "🚀 새 버전 배포 중..."
NEW_RESOURCE_ID=$(python deploy.py --create 2>&1 | grep "Resource ID:" | awk '{print $4}')

if [ -z "$NEW_RESOURCE_ID" ]; then
    echo "❌ 배포 실패!"
    exit 1
fi

echo ""
echo "✅ 새 버전 배포 완료: $NEW_RESOURCE_ID"
echo ""

# 테스트 세션 생성
echo "🧪 새 버전 테스트 중..."
TEST_SESSION=$(python deploy.py --create_session --resource_id="$NEW_RESOURCE_ID" 2>&1 | grep "Session ID:" | awk '{print $4}')

if [ -z "$TEST_SESSION" ]; then
    echo "❌ 세션 생성 실패!"
    echo "   새 배포를 삭제합니다..."
    python deploy.py --delete --resource_id="$NEW_RESOURCE_ID"
    exit 1
fi

echo "✅ 테스트 세션 생성: $TEST_SESSION"
echo ""

# 간단한 테스트 메시지
echo "📨 테스트 메시지 전송 중..."
python deploy.py --send \
    --resource_id="$NEW_RESOURCE_ID" \
    --session_id="$TEST_SESSION" \
    --message="안녕" \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 테스트 통과!"
else
    echo "❌ 테스트 실패!"
    echo "   새 배포를 삭제합니다..."
    python deploy.py --delete --resource_id="$NEW_RESOURCE_ID"
    exit 1
fi

echo ""
echo "🔄 환경변수 업데이트 중..."

# .env 파일 백업
cp .env .env.backup

# 이전 ID를 백업으로 저장하고 새 ID를 활성화
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i.bak "s|AGENT_RESOURCE_ID=.*|AGENT_RESOURCE_ID=$NEW_RESOURCE_ID|g" .env
else
    # Linux
    sed -i.bak "s|AGENT_RESOURCE_ID=.*|AGENT_RESOURCE_ID=$NEW_RESOURCE_ID|g" .env
fi

# 백업 ID 추가 (중복 방지)
if grep -q "AGENT_RESOURCE_ID_BACKUP=" .env; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i.bak "s|AGENT_RESOURCE_ID_BACKUP=.*|AGENT_RESOURCE_ID_BACKUP=$CURRENT_ID|g" .env
    else
        sed -i.bak "s|AGENT_RESOURCE_ID_BACKUP=.*|AGENT_RESOURCE_ID_BACKUP=$CURRENT_ID|g" .env
    fi
else
    echo "AGENT_RESOURCE_ID_BACKUP=$CURRENT_ID" >> .env
fi

# 임시 백업 파일 삭제
rm -f .env.bak

echo ""
echo "=" | tr '=' '=' | head -c 70
echo ""
echo "✅ 업데이트 완료!"
echo "=" | tr '=' '=' | head -c 70
echo ""
echo "📌 새 버전: $NEW_RESOURCE_ID"
echo "💾 이전 버전 (롤백용): $CURRENT_ID"
echo ""
echo "⚠️  프로덕션 환경에 적용하기 전에 충분히 테스트하세요!"
echo ""
echo "🔙 롤백이 필요하면:"
echo "   python deploy.py --delete --resource_id=\"$NEW_RESOURCE_ID\""
echo "   (그리고 .env 파일을 .env.backup에서 복구)"
echo ""
echo "✅ 문제없으면 이전 버전 삭제:"
echo "   python deploy.py --delete --resource_id=\"$CURRENT_ID\""
echo ""

