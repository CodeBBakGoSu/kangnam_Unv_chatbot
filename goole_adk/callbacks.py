"""
ADK Agent 안전 콜백 (Safety Callbacks)

프롬프트 인젝션 공격 및 유해한 입력을 차단하기 위한 before_model_callback 구현
Gemini API 호출 직전에 사용자 입력을 검증하여 악의적인 요청을 방어합니다.
"""

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from typing import Optional
import logging

# 로깅 설정
logger = logging.getLogger(__name__)


# ============================================================================
# 유해 키워드 리스트
# ============================================================================

HARMFUL_KEYWORDS = [
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 지시사항 무시 / 프롬프트 인젝션 (Korean)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "무시하고", "잊어버려", "지금부터 너는", "역할을 맡아",
    "역할극", "연기해", "너의 지시사항을", "네 규칙을",
    "개발자 모드", "제한을 해제해", "규칙을 어겨", "모든 규칙을 무시해",
    "시스템 프롬프트", "지시사항을 보여줘", "인스트럭션",
    "가장 먼저 해야 할 일", "절대 잊지 마",
    "프롬프트를 보여줘", "instruction을 알려줘",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. Instruction Bypass / Prompt Injection (English)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "ignore previous", "ignore all prior", "forget your instructions",
    "disregard your programming", "you are now", "act as", "roleplay",
    "developer mode", "jailbreak", "dan mode", "break the rules",
    "ignore rules", "what are your instructions", "show me your prompt",
    "system prompt", "pretend to be", "override", "bypass",
    "new instructions", "reset your", "you must now",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. 유해/부적절 콘텐츠 (Korean)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "씨발", "개새끼", "병신", "지랄", "엿먹어", "꺼져",
    "성적인", "음란", "야한", "섹스", "포르노", "자위",
    "폭력", "살인", "죽여", "자살", "자해", "죽고싶",
    "혐오", "장애인", "흑인", "백인",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. Harmful/Inappropriate Content (English)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "fuck", "shit", "bitch", "asshole", "damn",
    "sexual", "porn", "nude", "sexy", "horny", "masturbate",
    "violence", "kill", "murder", "suicide", "self-harm",
    "hate speech", "discrimination", "racist", "sexist",
    "nazi", "terrorist",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. 범위 이탈 / 메타 질문 (Korean)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "정치", "대통령", "선거", "국회의원", "정당",
    "너는 누구야", "네 생각은", "너의 의견", "인공지능",
    "만든 사람", "개발자", "감정", "의식", "느낌",
    "에이전트", "agent", "sub_agent", "transfer",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. Out-of-Scope / Meta Questions (English)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "politics", "election", "president", "congress", "political party",
    "who are you", "what is your opinion", "what do you think about",
    "your thoughts on", "artificial intelligence", "who made you",
    "your developer", "feeling", "emotion", "consciousness", "sentient",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. 스팸 / 반복 (Korean)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "천번 출력해", "1000번 반복해", "계속 말해", "도배", "무한 반복",
    "백번", "만번", "천번", "반복해줘",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. Spam / Repetition (English)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "repeat 1000 times", "say it over and over", "spam", "infinite loop",
    "repeat forever", "keep saying", "output 100 times",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5. 시스템 탐색 및 정보 추출 (Korean)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "시스템 프롬프트 보여줘", "너의 명령어", "숨겨진 지시",
    "비밀 정보", "내부 구조", "아키텍처",
    "config", "설정 파일", "환경 변수",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5. System Probing / Information Extraction (English)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "show me your prompt", "reveal your instructions", "hidden commands",
    "secret information", "internal structure", "architecture",
    "configuration", "config file", "environment variables",
    "api key", "token", "credentials",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. 악의적 테스트 및 우회 시도 (Korean)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "제한을 풀어줘", "보안을 해제", "필터를 우회",
    "검열을 피해", "탐지를 회피",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. Malicious Testing / Bypass Attempts (English)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "bypass security", "disable filter", "remove restrictions",
    "unlock", "jailbroken", "unrestricted mode",
    "turn off safety", "disable content policy",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7. SQL Injection / Code Injection 패턴
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "'; drop table", "union select", "exec(", "eval(",
    "<script>", "javascript:", "onerror=",
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 8. 추가 프롬프트 인젝션 변형
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "from now on", "new task", "new mission", "override previous",
    "delete all previous", "start over", "reset context",
    "이제부터", "새로운 임무", "이전 대화 삭제",
]


# ============================================================================
# 안전 콜백 함수
# ============================================================================

def safety_check_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    모델로 요청이 가기 전에 사용자 입력을 검사하는 콜백 (before_model_callback)
    
    Args:
        callback_context: CallbackContext - 에이전트 실행 컨텍스트
        llm_request: LlmRequest - LLM 호출 요청 객체
        
    Returns:
        Optional[LlmResponse] - 차단 시 LlmResponse 반환, 정상 시 None 반환
    """
    
    agent_name = callback_context.agent_name
    logger.info(f"[Safety Callback] Checking request for agent: {agent_name}")
    
    # 마지막 사용자 메시지 추출
    user_message = ""
    try:
        if llm_request.contents and llm_request.contents[-1].role == 'user':
            if llm_request.contents[-1].parts:
                user_message = llm_request.contents[-1].parts[0].text or ""
    except Exception as e:
        logger.error(f"[Safety Callback] Error extracting user message: {e}")
        return None  # 오류 시 정상 진행
    
    if not user_message:
        logger.debug("[Safety Callback] No user message found, proceeding normally")
        return None
    
    logger.debug(f"[Safety Callback] User message: '{user_message[:100]}...'")
    
    # 소문자로 변환하여 대소문자 무시 검사
    user_message_lower = user_message.lower()
    
    # 💡 오탐 방지 - 학술 용어는 통과
    allowed_academic_keywords = [
        "정치외교", "ai융합", "인공지능학", "정치학", "ai학과",
        "인공지능전공", "ai전공", "정치외교학과"
    ]
    
    if any(keyword in user_message_lower for keyword in allowed_academic_keywords):
        logger.debug("[Safety Callback] Academic keyword detected, allowing request")
        return None
    
    # 🚫 유해 키워드 탐지
    detected_keyword = None
    for keyword in HARMFUL_KEYWORDS:
        if keyword.lower() in user_message_lower:
            detected_keyword = keyword
            break
    
    if detected_keyword:
        logger.warning(
            f"[Safety Callback] BLOCKED - Detected harmful keyword: '{detected_keyword}' "
            f"in message: '{user_message[:50]}...'"
        )
        
        # ⚠️ LLM 호출을 건너뛰고 안전한 거부 메시지 반환
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=(
                    "죄송합니다. 해당 요청은 처리할 수 없습니다. "
                    "강남대학교와 관련된 정보(졸업요건, 과목, 교수, 캠퍼스 등)에 대해 "
                    "질문해 주시면 성심성의껏 도와드리겠습니다!"
                ))],
            )
        )
    
    # ✅ 안전한 경우 None 반환하여 정상적으로 LLM 호출 진행
    logger.debug("[Safety Callback] No harmful content detected, proceeding with LLM call")
    return None

