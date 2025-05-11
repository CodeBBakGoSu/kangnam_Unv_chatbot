from typing import Dict, Any, Optional, List, TypedDict
from app.utils.supabase import get_relevant_chunks, find_most_similar_course
from app.utils.gemini import format_context, generate_response
import json
import os
from datetime import datetime, timedelta
import logging
from langgraph.graph import StateGraph

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 상태 정의
class ChatState(TypedDict):
    message: str
    user_context: Dict[str, Any]
    current_flow: str
    response: str
    rag_chunks: List[Dict[str, Any]]
    token_usage: Optional[Dict[str, Any]]
    context_str: Optional[str]
    normalized_course: Optional[str]
    force_personal: Optional[bool]

# 인사말 처리를 위한 기본 응답 템플릿
GREETING_RESPONSES = {
    "안녕": "안녕하세요! 강남대학교 챗봇입니다. 수업, 과제, 일정 등에 대해 물어보세요.",
    "안녕하세요": "안녕하세요! 강남대학교 챗봇입니다. 무엇을 도와드릴까요?",
    "반가워": "반갑습니다! 강남대학교 학생을 위한 AI 챗봇입니다.",
    "Hi": "안녕하세요! 영어보다는 한국어로 질문해주시면 더 정확한 답변을 드릴 수 있어요.",
    "Hello": "안녕하세요! 강남대학교 AI 챗봇입니다. 어떤 도움이 필요하신가요?"
}

async def normalize_course_name_with_llm(query: str, user_courses: List[Dict[str, Any]]) -> Optional[str]:
    """
    LLM을 사용하여 사용자 입력에서 과목명 추론
    """
    # 사용자의 과목 목록 추출 (분반 정보 포함)
    course_names = [
        course["title"].split("(")[0].strip()  # 시간 정보 제외
        for course in user_courses
        if "title" in course
    ]
    
    # 교수 정보가 포함된 과목 목록 생성
    course_names_with_prof = [
        f"{course['title'].split('(')[0].strip()} (교수: {course.get('professor', 'N/A')})"
        for course in user_courses
        if "title" in course
    ]
    
    logger.info(f"사용자 과목 수: {len(user_courses)}개")
    logger.info(f"사용자의 수강 과목 목록: {course_names}")
    logger.info(f"교수 정보 포함 수강 과목 목록: {course_names_with_prof}")
    
    # Gemini를 사용하여 과목명 추출
    prompt = f"""
당신은 대학교 학생의 수강 과목을 찾아주는 도우미입니다.
학생이 수강 중인 과목 목록입니다(과목명과 교수명):
{', '.join(course_names_with_prof)}

학생의 입력: "{query}"

위 과목 목록 중에서 학생이 언급한 과목을 찾아주세요.

다음과 같은 패턴을 고려하여 매칭해주세요:
1. 정확한 과목명과 일치하는 경우
2. 과목명의 축약어나 별칭 (예: 첫 글자들을 조합, 주요 단어의 첫 글자 조합 등)
3. 과목명의 일부만 언급된 경우
4. 영문 약자가 한글로 쓰인 경우나 그 반대의 경우
5. 교수명을 언급한 경우 (예: "김교수님 수업", "최교수님 과목")

출력 규칙:
- 매칭된 경우: 정확한 과목명만 한 줄로 출력
- 매칭되지 않은 경우: "없음"

답변:"""

    try:
        logger.info("LLM을 사용한 과목명 추론 시작")
        response_text, token_usage = generate_response(query, prompt)
        normalized_name = response_text.strip()
        logger.info(f"LLM 응답: {normalized_name}")
        
        if token_usage:
            logger.info(f"과목명 추론 토큰 사용량: 프롬프트={token_usage.get('prompt_tokens')}, 응답={token_usage.get('response_tokens')}, 총={token_usage.get('total_tokens')}")
            logger.info(f"과목명 추론 시간: {token_usage.get('response_time_seconds', 0):.2f}초")
            logger.info(f"과목명 추론 예상 비용: ${token_usage.get('estimated_cost_usd', 0):.6f} USD")
        
        if normalized_name == "없음":
            logger.info("매칭 실패: 과목명이 없음")
            return None
            
        # 정규화된 과목명으로 시작하는 과목 찾기
        for course in user_courses:
            course_title = course["title"].split("(")[0].strip()
            if course_title.startswith(normalized_name) or normalized_name.startswith(course_title):
                logger.info(f"매칭 성공: {course['title']}")
                return course["title"]
        
        logger.info("매칭 실패: 전체 과목명 찾기 실패")
        return None
    except Exception as e:
        logger.error(f"과목명 정규화 중 오류 발생: {e}")
        return None

def is_greeting(message: str) -> bool:
    """
    사용자 메시지가 인사말인지 확인
    """
    greetings = ["안녕", "반가워", "hi", "hello"]
    
    message_lower = message.lower()
    for greeting in greetings:
        if greeting in message_lower:
            logger.info(f"인사말 감지: '{message}' -> '{greeting}'")
            return True
    
    return False

def determine_flow(message: str, context: str = "") -> str:
    """
    메시지 내용에 따라 적절한 플로우 결정
    """
    # 메시지 길이가 짧고, 특정 키워드가 있으면 general 플로우 배정
    if len(message) < 10 and is_greeting(message):
        logger.info(f"플로우 결정: general (인사말)")
        return "general"
    
    # 학교 관련 키워드가 있으면 common 플로우 배정
    school_keywords = ["강남대", "교학팀", "교수", "강의실", "시설", "도서관", "졸업", "학점", "수강신청", "장학금"]
    for keyword in school_keywords:
        if keyword in message:
            logger.info(f"플로우 결정: common (학교 관련 키워드: {keyword})")
            return "common"
    
    # 벡터 DB 검색 결과가 있으면 personal 플로우 배정
    if context and len(context) > 50:
        logger.info("플로우 결정: personal (벡터 DB 검색 결과 있음)")
        return "personal"
    
    # 기본값은 general
    logger.info("플로우 결정: general (기본값)")
    return "general"

# LangGraph 노드 함수들
async def handle_greeting(state: ChatState) -> ChatState:
    """인사말 처리 노드"""
    message = state["message"]
    
    logger.info(f"인사말 처리 노드: '{message}'")
    
    # 인사말 대응 (빠른 응답을 위해)
    for greeting, response in GREETING_RESPONSES.items():
        if greeting in message.lower():
            logger.info(f"인사말 응답: '{response}'")
            return {
                **state,
                "response": response,
                "current_flow": "general",
                "token_usage": None,
                "rag_chunks": []
            }
    
    # 인사말이 아닌 경우 다음 단계로
    return state

async def extract_course_name(state: ChatState) -> ChatState:
    """과목명 추출 노드"""
    message = state["message"]
    user_context = state["user_context"]
    
    # 사용자 컨텍스트에서 과목 정보 추출
    user_courses = user_context.get("courses", [])
    logger.info(f"사용자 과목 수: {len(user_courses)}개")
    
    # 과목명 추출
    normalized_course = await normalize_course_name_with_llm(message, user_courses)
    
    return {
        **state,
        "normalized_course": normalized_course
    }

async def perform_rag_search(state: ChatState) -> ChatState:
    """RAG 검색 노드"""
    message = state["message"]
    normalized_course = state.get("normalized_course")
    
    # RAG 검색: 벡터DB에서 관련 청크 가져오기
    search_query = normalized_course if normalized_course else message
    logger.info(f"벡터 DB 검색 시작: 쿼리={search_query}")
    
    # LLM을 사용한 검색 쿼리 최적화
    if normalized_course:
        try:
            optimize_prompt = f"""
당신은 검색 쿼리를 최적화하는 전문가입니다. 아래 정보를 바탕으로 벡터 검색을 위한 최적의 쿼리를 만들어주세요.

과목명: {normalized_course}
사용자 질문: {message}

다음과 같은 정보를 추출하여 검색에 최적화된 쿼리를 만들어주세요:
1. 과목명의 핵심 부분
2. 질문에서 나타난 주요 키워드(과제, 시험, 프로젝트, 일정 등)
3. 시간 관련 표현(이번주, 다음주, 저번주 등)

검색 쿼리 형식으로 출력해주세요. 부가 설명이나 다른 텍스트를 포함하지 마세요.
예시: "AIoT소프트웨어 다음주 과제"
"""
            
            optimized_query_text, _ = generate_response(message, optimize_prompt)
            optimized_query = optimized_query_text.strip().replace('"', '')
            logger.info(f"LLM으로 최적화된 검색 쿼리: {optimized_query}")
            search_query = optimized_query
        except Exception as e:
            logger.error(f"검색 쿼리 최적화 중 오류 발생: {e}")
            # 오류 발생 시 기본 쿼리 사용
            search_query = normalized_course if normalized_course else message
    
    # 벡터 DB 검색 실행
    relevant_chunks = get_relevant_chunks(search_query, limit=5)
    logger.info(f"벡터 DB 검색 결과: {len(relevant_chunks)}개 청크 발견")
    
    # 컨텍스트 포맷팅
    context_str = format_context(relevant_chunks) if relevant_chunks else ""
    
    # 과목명이 확인되었지만 검색 결과가 없는 경우 처리
    force_personal = False
    if normalized_course and not relevant_chunks:
        logger.info(f"과목명 '{normalized_course}'이(가) 인식되었지만 검색 결과가 없습니다. Personal 플로우로 강제 라우팅합니다.")
        force_personal = True
        # 과목 정보 컨텍스트 생성
        context_str = f"사용자가 '{normalized_course}' 과목에 대해 질문했습니다. 이 과목에 대한 정보가 데이터베이스에 충분하지 않지만, 최대한 도움을 주세요."
    
    return {
        **state,
        "rag_chunks": relevant_chunks,
        "context_str": context_str,
        "force_personal": force_personal
    }

async def decide_flow(state: ChatState) -> ChatState:
    """플로우 결정 노드"""
    message = state["message"]
    context_str = state.get("context_str", "")
    normalized_course = state.get("normalized_course")
    force_personal = state.get("force_personal", False)
    
    # 1. 과목이 인식되었고 실제 과목 관련 질문인 경우만 personal 플로우로 라우팅
    if normalized_course:
        # 과목 관련 키워드 확인
        course_related_keywords = ["과제", "시험", "수업", "강의", "교재", "프로젝트", "일정", "퀴즈", "발표", "점수", "성적"]
        is_course_related = any(keyword in message for keyword in course_related_keywords)
        
        if is_course_related or force_personal:
            logger.info(f"과목명 '{normalized_course}'이(가) 인식되고 과목 관련 질문으로 판단되어 personal 플로우로 결정")
            return {
                **state,
                "current_flow": "personal"
            }
        else:
            logger.info(f"과목명 '{normalized_course}'이(가) 인식되었으나 과목 관련 질문이 아닌 것으로 판단됨")
    
    # 2. 학교 관련 키워드 확인
    school_keywords = ["강남대", "교학팀", "교수", "강의실", "시설", "도서관", "졸업", "학점", "수강신청", "장학금"]
    for keyword in school_keywords:
        if keyword in message:
            logger.info(f"플로우 결정: common (학교 관련 키워드: {keyword})")
            return {
                **state,
                "current_flow": "common"
            }
    
    # 3. 벡터 DB 검색 결과가 있으면 personal 플로우 배정
    if context_str and len(context_str) > 50:
        logger.info("플로우 결정: personal (벡터 DB 검색 결과 있음)")
        return {
            **state,
            "current_flow": "personal"
        }
    
    # 4. 기본값은 general
    logger.info("플로우 결정: general (기본값)")
    return {
        **state,
        "current_flow": "general"
    }

async def generate_personal_response(state: ChatState) -> ChatState:
    """개인 맞춤형 응답 생성 노드"""
    message = state["message"]
    context_str = state.get("context_str", "")
    rag_chunks = state.get("rag_chunks", [])
    user_context = state.get("user_context", {})
    courses = user_context.get("courses", [])
    
    # 과목 목록 텍스트 생성 (교수 정보 포함)
    course_info = [f"{course.get('title', '')} (교수: {course.get('professor', 'N/A')})" for course in courses if "title" in course]
    courses_text = "현재 수강 중인 과목 목록: " + ", ".join(course_info) if course_info else ""
    
    if not rag_chunks:
        return {
            **state,
            "response": "죄송합니다. 질문과 관련된 개인 정보를 찾을 수 없습니다. 다른 질문을 해보시겠어요?"
        }
    
    # LLM으로 응답 생성
    logger.info(f"Personal 플로우 응답 생성 시작")
    
    # 프롬프트에 과목 목록 추가
    enhanced_context = f"{context_str}\n\n{courses_text}"
    response_text, token_usage = generate_response(message, enhanced_context)
    logger.info(f"Personal 플로우 응답 생성 완료: {len(response_text)} 글자")
    
    if token_usage:
        logger.info(f"토큰 사용량: 프롬프트={token_usage.get('prompt_tokens')}, 응답={token_usage.get('response_tokens')}, 총={token_usage.get('total_tokens')}")
        logger.info(f"응답 생성 시간: {token_usage.get('response_time_seconds', 0):.2f}초")
        logger.info(f"예상 비용: ${token_usage.get('estimated_cost_usd', 0):.6f} USD")
    
    return {
        **state,
        "response": response_text,
        "token_usage": token_usage
    }

async def generate_common_response(state: ChatState) -> ChatState:
    """학교 공통 정보 응답 생성 노드"""
    message = state["message"]
    user_context = state.get("user_context", {})
    courses = user_context.get("courses", [])
    
    # 과목 목록 텍스트 생성 (교수 정보 포함)
    course_info = [f"{course.get('title', '')} (교수: {course.get('professor', 'N/A')})" for course in courses if "title" in course]
    courses_text = "현재 수강 중인 과목 목록: " + ", ".join(course_info) if course_info else ""
    
    # 공통 정보에 대한 응답 생성
    logger.info(f"Common 플로우 응답 생성 시작")
    
    # 학교 관련 키워드 및 시스템 프롬프트
    system_prompt = """당신은 강남대학교 소프트웨어응용학부의 학사 정보를 제공하는 챗봇입니다.
        다음 주제에 대해 정확하고 상세한 정보를 제공해주세요:
        - 학사 제도
        - 졸업 요건
        - 수강신청 방법
        - 학과 공지사항
        - 교수 정보
        - 시설 정보
        
        정보를 제공할 때는 항상 공식적인 태도를 유지하고, 정확한 정보를 제공해주세요."""
    
    # 프롬프트에 과목 목록 추가
    prompt = f"{system_prompt}\n\n{courses_text}\n\n사용자 메시지: {message}"
    response_text, token_usage = generate_response(message, prompt)
    logger.info(f"Common 플로우 응답 생성 완료: {len(response_text)} 글자")
    
    if token_usage:
        logger.info(f"토큰 사용량: 프롬프트={token_usage.get('prompt_tokens')}, 응답={token_usage.get('response_tokens')}, 총={token_usage.get('total_tokens')}")
        logger.info(f"응답 생성 시간: {token_usage.get('response_time_seconds', 0):.2f}초")
        logger.info(f"예상 비용: ${token_usage.get('estimated_cost_usd', 0):.6f} USD")
    
    return {
        **state,
        "response": response_text,
        "token_usage": token_usage
    }

async def generate_general_response(state: ChatState) -> ChatState:
    """일반 응답 생성 노드"""
    message = state["message"]
    user_context = state.get("user_context", {})
    courses = user_context.get("courses", [])
    
    # 과목 목록 텍스트 생성 (교수 정보 포함)
    course_info = [f"{course.get('title', '')} (교수: {course.get('professor', 'N/A')})" for course in courses if "title" in course]
    courses_text = "현재 수강 중인 과목 목록: " + ", ".join(course_info) if course_info else ""
    
    # 일반 정보에 대한 응답 생성
    logger.info(f"General 플로우 응답 생성 시작")
    
    # 친근한 응답 시스템 프롬프트
    system_prompt = """당신은 강남대학교 학생들을 위한 친근한 챗봇입니다.
        다음 주제에 대해 친절하고 자연스럽게 대화해주세요:
        - 기타 잡담
        
        항상 친근하고 도움이 되는 태도로 응답해주세요."""
    
    # 프롬프트에 과목 목록 추가
    prompt = f"{system_prompt}\n\n{courses_text}\n\n사용자 메시지: {message}"
    response_text, token_usage = generate_response(message, prompt)
    logger.info(f"General 플로우 응답 생성 완료: {len(response_text)} 글자")
    
    if token_usage:
        logger.info(f"토큰 사용량: 프롬프트={token_usage.get('prompt_tokens')}, 응답={token_usage.get('response_tokens')}, 총={token_usage.get('total_tokens')}")
        logger.info(f"응답 생성 시간: {token_usage.get('response_time_seconds', 0):.2f}초")
        logger.info(f"예상 비용: ${token_usage.get('estimated_cost_usd', 0):.6f} USD")
    
    return {
        **state,
        "response": response_text,
        "token_usage": token_usage
    }

# 그래프 생성
def create_chat_graph():
    """챗봇 워크플로우 그래프 생성"""
    # 워크플로우 그래프 초기화
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node("greeting", handle_greeting)
    workflow.add_node("extract_course", extract_course_name)
    workflow.add_node("rag_search", perform_rag_search)
    workflow.add_node("decide_flow", decide_flow)
    workflow.add_node("personal_response", generate_personal_response)
    workflow.add_node("common_response", generate_common_response) 
    workflow.add_node("general_response", generate_general_response)
    
    # 엣지 연결
    workflow.add_edge("greeting", "extract_course")
    workflow.add_edge("extract_course", "rag_search")
    workflow.add_edge("rag_search", "decide_flow")
    
    # 조건부 엣지 추가
    def route_to_agent(state: ChatState) -> str:
        flow = state.get("current_flow", "")
        if flow == "personal":
            return "personal_response"
        elif flow == "common":
            return "common_response"
        else:
            return "general_response"
    
    workflow.add_conditional_edges(
        "decide_flow",
        route_to_agent,
        {
            "personal_response": "personal_response",
            "common_response": "common_response",
            "general_response": "general_response"
        }
    )
    
    # 시작 노드 설정
    workflow.set_entry_point("greeting")
    
    # 종료 노드 설정
    for end_node in ["personal_response", "common_response", "general_response"]:
        workflow.set_finish_point(end_node)
    
    # 그래프 컴파일
    return workflow.compile()

# 메인 사용자 인터페이스 함수
async def get_chat_response(message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 기반 챗봇 응답 생성
    """
    try:
        logger.info(f"사용자 '{user_context.get('username')}' 메시지 수신: '{message}'")
        
        # 전체 처리 시작 시간 기록
        start_time = datetime.now()
        total_tokens = {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0
        }
        
        # 인사말 처리 - 빠른 응답을 위한 특별 처리
        if is_greeting(message):
            for greeting, response in GREETING_RESPONSES.items():
                if greeting in message.lower():
                    logger.info(f"인사말 빠른 응답: '{response}'")
                    return {
                        "response": response,
                        "current_flow": "general",
                        "rag_chunks": []
                    }
        
        # 그래프 생성
        graph = create_chat_graph()
        
        # 초기 상태 설정
        initial_state = {
            "message": message,
            "user_context": user_context,
            "current_flow": "",
            "response": "",
            "rag_chunks": [],
            "token_usage": None,
            "context_str": "",
            "normalized_course": None,
            "force_personal": False
        }
        
        # 그래프 실행
        logger.info("LangGraph 워크플로우 실행 시작")
        result = await graph.ainvoke(initial_state)
        logger.info(f"LangGraph 워크플로우 완료: flow={result['current_flow']}")
        
        # 토큰 사용량 집계
        if result.get("token_usage"):
            token_usage = result.get("token_usage")
            for key in ["prompt_tokens", "response_tokens", "total_tokens"]:
                if key in token_usage:
                    total_tokens[key] += token_usage[key]
            if "estimated_cost_usd" in token_usage:
                total_tokens["estimated_cost_usd"] += token_usage["estimated_cost_usd"]
                
        # 전체 처리 종료 시간 및 소요 시간 계산
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # 전체 처리 시간 및 토큰 사용량 요약 로깅
        logger.info(f"전체 처리 시간: {total_time:.2f}초")
        logger.info(f"전체 토큰 사용량: 프롬프트={total_tokens['prompt_tokens']}, 응답={total_tokens['response_tokens']}, 총={total_tokens['total_tokens']}")
        logger.info(f"전체 예상 비용: ${total_tokens['estimated_cost_usd']:.6f} USD")
        
        # 결과 반환 (token_usage 제외)
        return {
            "response": result["response"],
            "current_flow": result["current_flow"],
            "rag_chunks": result.get("rag_chunks", [])
        }
        
    except Exception as e:
        logger.error(f"응답 생성 중 오류 발생: {str(e)}", exc_info=True)
        # 오류 발생 시
        return {
            "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
            "current_flow": "error",
            "rag_chunks": []
        } 