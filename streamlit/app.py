import streamlit as st
import requests
import json
from datetime import datetime
import time as time_module
from urllib.parse import parse_qs
import uuid
import hashlib
import os


# API 기본 URL - Streamlit Cloud에서는 secrets에서 가져오기
API_BASE_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000/api")

# 변경 부분: 항상 HTTPS로 설정
if API_BASE_URL.startswith("http://"):
    API_BASE_URL = API_BASE_URL.replace("http://", "https://")

# 변경 부분: URL 끝에 슬래시 제거
if API_BASE_URL.endswith("/"):
    API_BASE_URL = API_BASE_URL[:-1]


# 개발 환경에서는 환경변수 사용 (로컬 테스트용)
if API_BASE_URL == "http://localhost:8000/api" and "BACKEND_URL" in os.environ:
    API_BASE_URL = os.environ["BACKEND_URL"]

# 브라우저 세션 안정성을 위한 상수
SESSION_KEY = "knu_chatbot_session"
BROWSER_HASH_KEY = "browser_hash"

# 브라우저 세션 해시 생성 (브라우저 식별용)
def get_browser_hash():
    # 이미 생성된 해시가 있으면 사용
    if BROWSER_HASH_KEY in st.session_state:
        return st.session_state[BROWSER_HASH_KEY]
    
    # 새 해시 생성 (실제로는 브라우저 특성에 기반한 해시를 만들면 좋음)
    browser_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()
    st.session_state[BROWSER_HASH_KEY] = browser_hash
    return browser_hash

# URL에서 토큰 가져오기
def get_token_from_url():
    # 쿼리 파라미터 접근
    token = st.query_params.get("token", None)
    return token

# 사용자 세션 ID 생성/관리
def get_or_create_user_session_id():
    session_id_key = f"user_session_id_{get_browser_hash()}"
    
    # 세션 ID가 없거나 매우 오래된 경우 새로 생성
    if session_id_key not in st.session_state:
        st.session_state[session_id_key] = str(uuid.uuid4())
        # URL에 세션 ID 추가 (페이지 새로고침/뒤로가기에도 보존)
        st.query_params[SESSION_KEY] = st.session_state[session_id_key]
    
    # URL에서 세션 ID 가져오기 시도
    url_session_id = st.query_params.get(SESSION_KEY, None)
    
    # URL에 세션 ID가 있고 로컬과 다르면 로컬 업데이트
    if url_session_id and url_session_id != st.session_state[session_id_key]:
        # 세션 충돌 감지 - 브라우저 뒤로가기 등으로 인한
        st.session_state[session_id_key] = url_session_id
    
    # URL에 세션 ID가 없으면 URL 업데이트
    if not url_session_id:
        st.query_params[SESSION_KEY] = st.session_state[session_id_key]
    
    return st.session_state[session_id_key]

# JWT 토큰 가져오기
def get_token():
    """JWT 토큰 가져오기"""
    token_key = f'token_{get_or_create_user_session_id()}'
    # 세션에서 토큰 가져오기
    return st.session_state.get(token_key, "")

# 챗봇 API 호출
def call_chat_api(message, data_ready=True):
    """채팅 API 호출"""
    token = get_token()
    try:
        # 서버 엔드포인트 URL
        url = f"{API_BASE_URL}/chat/"
        
        # 요청 헤더 및 데이터
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 데이터 준비 여부에 따라 다른 파라미터 전달
        data = {
            "message": message
        }
        
        if not data_ready:
            # 데이터가 준비되지 않은 경우 일반 모드로 강제 설정
            data["force_general"] = True
        
        # API 호출
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "response": result["response"],
                "current_flow": result.get("current_flow", "general"),
                "rag_chunks": result.get("rag_chunks", [])
            }
        elif response.status_code == 401:
            # 인증 오류 - 토큰 만료 또는 유효하지 않음
            # 세션에서 토큰 제거
            token_key = f'token_{get_or_create_user_session_id()}'
            if token_key in st.session_state:
                del st.session_state[token_key]
            
            return {
                "response": "로그인 세션이 만료되었습니다. 다시 로그인해주세요.",
                "current_flow": "error"
            }
        else:
            return {
                "response": f"요청 중 오류가 발생했습니다 (상태 코드: {response.status_code})",
                "current_flow": "error"
            }
            
    except Exception as e:
        return {
            "response": f"요청 중 오류가 발생했습니다: {str(e)}",
            "current_flow": "error"
        }

# 이전 메시지를 삭제하고 세션을 새로 시작하는 기능
def reset_conversation():
    """대화 기록 초기화"""
    messages_key = f'messages_{get_or_create_user_session_id()}'
    if messages_key in st.session_state:
        del st.session_state[messages_key]
    st.rerun()

# 사용자 데이터 갱신 함수
def refresh_user_data(force_refresh=False):
    """데이터 갱신 - 동기 방식"""
    try:
        token = get_token()
        if not token:
            return False
            
        # 강제 갱신이 아니면서 이미 상태 확인 중이면 중복 호출 방지
        if not force_refresh and "refreshing_data" in st.session_state and st.session_state["refreshing_data"]:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 강제 갱신인 경우 /refresh API 호출
        if force_refresh:
            username = st.session_state.get("username", "")
            password = st.session_state.get("password", "")
            
            if not username or not password:
                st.error("로그인 정보가 없습니다. 다시 로그인해주세요.")
                return False
                
            # 갱신 중임을 표시
            st.session_state["refreshing_data"] = True
            
            # 진행 상황 표시를 위한 컨테이너
            progress_container = st.empty()
            status_container = st.empty()
            
            # 비동기 호출을 위한 세션
            with requests.Session() as session:
                # 1단계: 로그인 및 기본 정보 확인
                progress_container.progress(5, text="데이터 갱신 준비 중...")
                status_container.info("1/5 단계: 로그인 확인 중...")
                
                # 2단계: 강남대 LMS에서 데이터 크롤링
                progress_container.progress(20, text="강남대 LMS 연결 중...")
                status_container.info("2/5 단계: 강남대 LMS에서 과목 데이터 수집 중...")
                
                # 실제 API 호출
                refresh_url = f"{API_BASE_URL}/auth/refresh"
                response = session.post(
                    refresh_url,
                    json={"username": username, "password": password},
                    params={"run_full_etl": "true"}
                )
                
                if response.status_code != 200:
                    error_msg = "데이터 갱신 중 오류가 발생했습니다."
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_msg = error_data["detail"]
                    except:
                        pass
                    
                    progress_container.empty()
                    status_container.error(error_msg)
                    st.session_state["refreshing_data"] = False
                    return False
                
                # 3단계: 데이터 전처리
                progress_container.progress(50, text="데이터 전처리 중...")
                status_container.info("3/5 단계: 수집된 데이터 분석 및 정리 중...")
                time_module.sleep(0.5)  # 사용자 경험을 위한 잠시 대기
                
                # 4단계: 벡터화 및 청크 생성
                progress_container.progress(75, text="벡터화 및 청크 생성 중...")
                status_container.info("4/5 단계: AI 분석을 위한 벡터 데이터 생성 중...")
                time_module.sleep(0.5)  # 사용자 경험을 위한 잠시 대기
                
                # 갱신 성공 상태 업데이트
                result = response.json()
                chunks_count = result.get("chunks_count", 0)
                
                # 5단계: 완료
                progress_container.progress(100, text=f"데이터 갱신 완료!")
                status_container.success(f"5/5 단계: 완료! 생성된 청크: {chunks_count}개")
                
                # 상태 업데이트
                st.session_state["refreshing_data"] = False
                return True
        
        return True
        
    except Exception as e:
        st.error(f"데이터 갱신 중 오류가 발생했습니다: {str(e)}")
        st.session_state["refreshing_data"] = False
        return False

# 데이터 준비 상태 확인
def check_data_status():
    """사용자 데이터 상태 확인"""
    try:
        token = get_token()
        if not token:
            return {"status": "none", "chunks": 0, "last_update": "없음"}
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 상태 요청
        status_url = f"{API_BASE_URL}/auth/data-status"
        response = requests.get(status_url, headers=headers)
        
        if response.status_code != 200:
            return {"status": "error", "chunks": 0, "last_update": "오류"}
            
        data = response.json()
        
        # 벡터 DB에 저장된 청크 수
        chunks_count = data.get("stored_chunks", 0)
        
        # 상태 결정 - 청크가 있으면 무조건 ready
        if chunks_count > 0:
            status_value = "ready"
        else:
            status_value = data.get("status", "not_ready")
        
        # 마지막 업데이트 시간
        last_update = data.get("last_modified", "알 수 없음")
        
        return {
            "status": status_value,
            "chunks": chunks_count,
            "last_update": last_update,
            "file_exists": data.get("file_exists", False),
            "file_size_kb": data.get("file_size_kb", 0)
        }
        
    except Exception as e:
        print(f"상태 확인 오류: {str(e)}")
        return {"status": "error", "chunks": 0, "last_update": "오류"}

# 로그인 상태 확인
def check_login():
    """로그인 상태 확인"""
    # 토큰이 있는지 확인
    token_key = f'token_{get_or_create_user_session_id()}'
    user_info_key = f'user_info_{get_or_create_user_session_id()}'
    
    if token_key not in st.session_state:
        # 로그인 상태가 아니므로 false 반환
        return False
    
    # 토큰 유효성 검증 (API 호출)
    try:
        token = st.session_state[token_key]
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            # 토큰이 유효하면 사용자 정보 업데이트
            user_info = response.json()
            st.session_state[user_info_key] = user_info
            return True
        else:
            # 토큰이 유효하지 않으면 삭제
            del st.session_state[token_key]
            if user_info_key in st.session_state:
                del st.session_state[user_info_key]
            return False
    except Exception as e:
        print(f"사용자 인증 확인 중 오류 발생: {e}")
        return False

# 데이터 갱신 진행 상황 확인 및 표시
def check_refresh_progress():
    """데이터 갱신 진행 상황 확인"""
    data_status = check_data_status()
    
    if data_status["status"] == "ready":
        # 이미 준비 완료
        return True
    
    if data_status["status"] == "partial":
        # 크롤링만 되고 벡터화가 안 된 상태
        st.warning("데이터 파일은 있지만 벡터 DB에 저장되지 않았습니다. 데이터 갱신이 필요합니다.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("강남대학교 LMS에서 데이터는 수집되었지만, 벡터 데이터베이스에 저장되지 않았습니다. 벡터화를 완료해야 개인화된 답변이 가능합니다.")
        with col2:
            if st.button("지금 벡터화 시작", key="vector_button"):
                # 진행 상태 표시 UI
                status_container = st.empty()
                progress_container = st.empty()
                detail_container = st.empty()
                
                status_container.info("벡터화 과정을 시작합니다...")
                
                # ETL 실행
                with st.spinner("데이터 처리 중..."):
                    # 프로그레스 바 초기화 
                    progress_container.progress(10, "준비 중...")
                    
                    # 벡터화 시작
                    refresh_success = refresh_user_data(force_refresh=True)
                    
                    if not refresh_success:
                        status_container.error("벡터화 시작에 실패했습니다. 다시 시도해주세요.")
                        time_module.sleep(2)
                        st.rerun()
                    
                    # 단계별 진행 표시
                    stages = [
                        {"progress": 30, "status": "3/5 단계: 데이터 전처리 중...", 
                         "detail": "강남대 LMS에서 수집된 데이터를 분석하고 정리하는 중입니다."},
                        {"progress": 50, "status": "4/5 단계: 텍스트 벡터화 중...", 
                         "detail": "AI 모델이 이해할 수 있는 형태로 텍스트를 변환하는 중입니다."},
                        {"progress": 80, "status": "5/5 단계: 벡터 DB에 저장 중...", 
                         "detail": "생성된 벡터 데이터를 데이터베이스에 저장하는 중입니다."},
                        {"progress": 100, "status": "✅ 완료!", 
                         "detail": "벡터화가 완료되었습니다. 개인화된 질문에 답변할 준비가 되었습니다."}
                    ]
                    
                    # 각 단계 표시 및 진행
                    for stage in stages:
                        progress_container.progress(stage["progress"], stage["status"])
                        detail_container.info(stage["detail"])
                        
                        # 상태 확인 (청크가 생성되었는지)
                        current_status = check_data_status()
                        if current_status.get("chunks", 0) > 0 and stage["progress"] < 100:
                            # 청크가 생성되었으면 마지막 단계로 건너뛰기
                            progress_container.progress(100, "✅ 완료!")
                            detail_container.success(f"벡터화가 완료되었습니다! {current_status.get('chunks', 0)}개의 청크가 생성되었습니다.")
                            break
                        
                        time_module.sleep(2)  # 각 단계별 지연
                
                status_container.success("데이터 준비가 완료되었습니다! 이제 개인화된 질문에 답변할 수 있습니다.")
                time_module.sleep(1)
                st.rerun()
    
    # 데이터 준비 안 됨
    return False

# 페이지 설정
st.set_page_config(
    page_title="강남대학교 AI 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
<style>
    .main {
        background-color: #121212;
        color: #e0e0e0;
    }
    
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    .stChatMessage.user {
        background-color: #4A69BD;
        color: white !important;
        border-top-right-radius: 0;
    }
    
    .stChatMessage.assistant {
        background-color: #2d2d2d;
        color: #e0e0e0 !important;
        border-top-left-radius: 0;
    }
    
    .stSidebar {
        background-color: #1a1a1a;
        padding: 20px;
    }
    
    .css-18e3th9 {
        padding-top: 2rem;
    }
    
    .sidebar-content {
        padding: 20px;
        border-radius: 15px;
        background-color: #2d2d2d;
        margin-bottom: 20px;
    }
    
    .course-item {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: #2d2d2d;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #4A69BD;
        color: white !important;
        border-radius: 30px;
    }
    
    .stButton > button:hover {
        background-color: #3A59AD;
    }
    
    .header {
        padding: 20px 0;
        color: #4A69BD;
        font-weight: bold;
        text-align: center;
        border-bottom: 1px solid #444;
        margin-bottom: 20px;
    }
    
    .chat-header {
        background-color: #4A69BD;
        color: white;
        padding: 10px 20px;
        border-radius: 10px 10px 0 0;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }
    
    /* 글자색 가시성 문제 해결을 위한 추가 스타일 */
    .stMarkdown {
        color: #e0e0e0 !important;
    }
    
    .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: #e0e0e0 !important;
    }
    
    .stSidebar .stMarkdown {
        color: #e0e0e0 !important;
    }
    
    .stChatInput input {
        color: #e0e0e0 !important;
        background-color: #2d2d2d !important;
        border-color: #444 !important;
    }
    
    .stChatMessage div {
        color: inherit !important; 
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #e0e0e0 !important;
    }
    
    .stChatMessage.user div, .stChatMessage.user p {
        color: white !important;
    }
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 10px;
        background-color: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background-color: #444;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background-color: #555;
    }
    
    /* 입력 필드 포커스 상태 */
    .stChatInput input:focus {
        border-color: #4A69BD !important;
        box-shadow: 0 0 0 1px #4A69BD !important;
    }
    
    /* 채팅 컨테이너 배경 */
    .css-1kyxreq {
        background-color: #121212 !important;
    }
    
    /* 경고 메시지 스타일 */
    .stAlert {
        background-color: #2d2d2d !important;
        color: #e0e0e0 !important;
        border-color: #555 !important;
    }
</style>
""", unsafe_allow_html=True)

# 페이지 초기화 후 JS 코드 삽입 (뒤로가기 감지용)
st.markdown("""
<script>
window.addEventListener('popstate', function(event) {
    // 페이지 새로고침 (세션 상태 복구를 위해)
    window.location.reload();
});
</script>
""", unsafe_allow_html=True)

# 세션 ID 가져오기 (브라우저 세션과 동기화)
user_session_id = get_or_create_user_session_id()

# 변수들 초기화 
token_key = f'token_{user_session_id}'
user_info_key = f'user_info_{user_session_id}'
messages_key = f'messages_{user_session_id}'

# 사용자별 대화 내역 초기화
if messages_key not in st.session_state:
    st.session_state[messages_key] = []

# URL에서 토큰 가져오기
if token_key not in st.session_state:
    token = get_token_from_url()
    if token:
        st.session_state[token_key] = token
        # 토큰 파라미터를 URL에서 제거 (보안 강화)
        if "token" in st.query_params:
            # 현재 쿼리 파라미터 복사
            params = dict(st.query_params)
            # token 제거
            del params["token"]
            # 새 쿼리 파라미터 설정
            for key in list(st.query_params.keys()):
                if key != SESSION_KEY:  # 세션 키는 유지
                    del st.query_params[key]
            # 나머지 파라미터 복원
            for key, value in params.items():
                if key != "token":
                    st.query_params[key] = value

# 사용자 정보 초기화
if user_info_key not in st.session_state:
    # 실제 API에서 사용자 정보 가져오기
    if token_key in st.session_state:
        try:
            response = requests.get(
                f"{API_BASE_URL}/auth/me", 
                headers={"Authorization": f"Bearer {st.session_state[token_key]}"}
            )
            if response.status_code == 200:
                st.session_state[user_info_key] = response.json()
                
                # 첫 로그인 시 ETL 실행 플래그 설정 
                if "first_login" not in st.session_state:
                    st.session_state["first_login"] = True
            else:
                st.error(f"사용자 정보를 가져오는 중 오류가 발생했습니다: {response.status_code}")
                # 오류 발생 시 기본 정보 설정
                st.session_state[user_info_key] = {
                    "username": f"사용자_{user_session_id[:4]}",
                    "student_id": "미확인",
                    "department": "미확인",
                    "courses": []
                }
        except Exception as e:
            st.error(f"사용자 정보를 가져오는 중 오류가 발생했습니다: {e}")
            # 오류 발생 시 기본 정보 설정
            st.session_state[user_info_key] = {
                "username": f"사용자_{user_session_id[:4]}",
                "student_id": "미확인",
                "department": "미확인",
                "courses": []
            }
    else:
        # 토큰이 없는 경우 기본 정보 설정
        st.session_state[user_info_key] = {
            "username": f"Guest_{user_session_id[:4]}",
            "student_id": "미확인",
            "department": "미확인",
            "courses": []
        }

# 로그인 처리
if not check_login():
    st.markdown('<div class="login-header"><h1>🎓 강남대학교 AI 챗봇</h1></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h2>로그인</h2>', unsafe_allow_html=True)
        
        # 오류 메시지 표시 영역
        error_placeholder = st.empty()
        
        # 로그인 폼
        with st.form("login_form"):
            username = st.text_input("학번", placeholder="학번을 입력하세요")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submit_button = st.form_submit_button(label="로그인")
            
            # 로그인 시도
            if submit_button:
                if not username or not password:
                    error_placeholder.error("학번과 비밀번호를 모두 입력해주세요.")
                else:
                    # 로그인 진행 상태 표시를 위한 컨테이너들
                    login_status = st.empty()
                    progress_container = st.empty()
                    status_detail = st.empty()
                    
                    # 초기 상태 표시
                    login_status.info("로그인 및 데이터 처리를 시작합니다...")
                    progress_container.progress(0, "준비 중...")
                    
                    # 1단계: 로그인 시도
                    progress_container.progress(10, "1/5 단계: 로그인 중...")
                    status_detail.info("강남대학교 계정으로 로그인을 시도하고 있습니다.")
                    
                    try:
                        # 2단계: 서버 연결
                        progress_container.progress(20, "2/5 단계: 서버 연결 중...")
                        status_detail.info("서버에 연결하여 계정 정보를 확인하고 있습니다.")
                        
                        # API 호출
                        response = requests.post(
                            f"{API_BASE_URL}/auth/login",
                            json={"username": username, "password": password},
                            params={"run_etl": "true"}  # 새 사용자면 자동으로 ETL 시작
                        )
                        
                        # 3단계: 응답 처리
                        progress_container.progress(40, "3/5 단계: 응답 처리 중...")
                        status_detail.info("서버 응답을 확인하고 있습니다.")
                        
                        if response.status_code == 200:
                            # 4단계: 토큰 저장
                            progress_container.progress(70, "4/5 단계: 사용자 정보 불러오는 중...")
                            status_detail.info("로그인에 성공했습니다. 사용자 정보를 불러오고 있습니다.")
                            
                            # 토큰 저장
                            token = response.json().get("access_token")
                            if not token:
                                error_placeholder.error("서버에서 토큰을 받지 못했습니다. 다시 시도해주세요.")
                                progress_container.empty()
                                status_detail.empty()
                            else:
                                token_key = f'token_{get_or_create_user_session_id()}'
                                st.session_state[token_key] = token
                                
                                # 비밀번호 임시 저장 (데이터 갱신 기능을 위해)
                                st.session_state["username"] = username
                                st.session_state["password"] = password
                                
                                # 5단계: 데이터 준비
                                progress_container.progress(90, "5/5 단계: 데이터 준비 중...")
                                status_detail.info("사용자 데이터를 준비하고 있습니다. 완료 후 자동으로 이동합니다.")
                                
                                # 사용자 정보 가져오기
                                try:
                                    # API 호출하여 사용자 정보 가져오기
                                    user_info_response = requests.get(
                                        f"{API_BASE_URL}/auth/me", 
                                        headers={"Authorization": f"Bearer {token}"}
                                    )
                                    
                                    if user_info_response.status_code == 200:
                                        user_info = user_info_response.json()
                                        user_info_key = f'user_info_{get_or_create_user_session_id()}'
                                        st.session_state[user_info_key] = user_info
                                        
                                        # ETL 상태가 processing이면 세션에 표시
                                        if user_info.get('etl_status') == 'processing':
                                            st.session_state["refreshing_data"] = True
                                        
                                        # 완료 표시
                                        progress_container.progress(100, "완료!")
                                        status_detail.success(f"{user_info.get('name', '사용자')}님, 환영합니다! 메인 화면으로 이동합니다...")
                                        
                                        # 첫 로그인 플래그 설정 (ETL 실행을 위해)
                                        st.session_state["first_login"] = True
                                        
                                        time_module.sleep(1)
                                        st.rerun()
                                    else:
                                        error_placeholder.error("사용자 정보를 가져오는데 실패했습니다. 다시 시도해주세요.")
                                        progress_container.empty()
                                        status_detail.empty()
                                except Exception as e:
                                    error_placeholder.error(f"사용자 정보 조회 중 오류: {str(e)}")
                                    progress_container.empty()
                                    status_detail.empty()
                        else:
                            error_msg = "로그인에 실패했습니다."
                            try:
                                error_data = response.json()
                                if "detail" in error_data:
                                    error_msg = error_data["detail"]
                            except:
                                pass
                            error_placeholder.error(f"로그인 처리 중 오류가 발생했습니다: {error_msg}")
                            progress_container.empty()
                            status_detail.empty()
                    except Exception as e:
                        error_placeholder.error(f"로그인 요청 중 오류가 발생했습니다: {str(e)}")
                        if 'progress_container' in locals():
                            progress_container.empty()
                        if 'status_detail' in locals():
                            status_detail.empty()
        
        # 도움말 정보
        st.markdown("""
        <div style="margin-top: 20px; font-size: 0.8em; color: #999 !important; text-align: center;">
            <p>강남대학교 포털 계정으로 로그인해 주세요.</p>
            <p>처음 로그인 시 데이터 수집을 위해 약간의 시간이 소요될 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 5단계 로그인 프로세스 안내
        with st.expander("로그인 과정 안내", expanded=False):
            st.markdown("""
            <div style="font-size: 0.9em; color: #e0e0e0 !important;">
                <p>로그인 시 다음과 같은 5단계 과정이 진행됩니다:</p>
                <ol>
                    <li><strong>로그인 인증</strong>: 강남대학교 계정 정보를 확인합니다.</li>
                    <li><strong>서버 연결</strong>: AI 챗봇 서버에 연결하여 인증 정보를 전송합니다.</li>
                    <li><strong>응답 처리</strong>: 로그인 요청에 대한 서버 응답을 확인합니다.</li>
                    <li><strong>사용자 정보 불러오기</strong>: 로그인 성공 시 사용자 정보를 불러옵니다.</li>
                    <li><strong>데이터 준비</strong>: 개인화된 챗봇 사용을 위해 필요한 데이터를 준비합니다.</li>
                </ol>
                <p>첫 로그인 시 학습 데이터 수집 과정이 추가로 진행되며, 이 과정은 약 1-2분 정도 소요될 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)

# 로그인 된 경우에만 채팅 인터페이스 표시
if check_login():
    # 현재 사용자 세션 정보 표시 (디버깅용)
    st.sidebar.markdown(f"<div style='color: #666 !important; font-size: 10px;'>세션 ID: {user_session_id[:8]}... (브라우저 세션: {get_browser_hash()[:6]})</div>", unsafe_allow_html=True)
    
    # 첫 로그인 시 자동으로 ETL 실행 (페이지 로딩 후)
    if "first_login" in st.session_state and st.session_state["first_login"]:
        # 데이터 상태 확인
        data_status = check_data_status()
        
        # 데이터가 없거나 부분적으로만 있는 경우 자동으로 ETL 실행
        if data_status["status"] != "ready" or data_status["chunks"] == 0:
            # 기존 알림 영역
            notification = st.empty()
            notification.info("사용자 데이터를 자동으로 수집합니다. 잠시만 기다려주세요...")
            
            # 진행 상태 표시 UI
            progress_container = st.empty()
            progress_bar = st.empty()
            status_text = st.empty()
            
            # ETL 실행
            progress_container.markdown("""
            <div style="padding: 12px; background-color: #1E3A8A; border-radius: 8px; margin: 12px 0;">
                <div style="font-weight: bold; margin-bottom: 8px;">데이터 수집 및 처리 중...</div>
                <div style="font-size: 0.9em;">
                    첫 로그인 시에만 필요한 과정입니다. 강남대학교 LMS에서 과목 정보를 수집하고 처리합니다.
                    이 과정은 1분 정도 소요될 수 있습니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ETL 실행
            with st.spinner("데이터 수집 중..."):
                success = refresh_user_data(force_refresh=True)
                if success:
                    status_text.success("데이터 수집이 시작되었습니다!")
                else:
                    status_text.error("데이터 수집 시작에 실패했습니다. '내 데이터 갱신하기' 버튼을 눌러 수동으로 시도해주세요.")
            
            # 상태 확인 및 진행 상황 업데이트
            max_retries = 15  # 최대 75초 (5초 * 15)
            for i in range(max_retries):
                # 상태 확인
                current_status = check_data_status()
                chunks_count = current_status.get("chunks", 0)
                
                # 진행 단계 결정 (현재 진행 상황에 따라 단계 추정)
                if i < 2:
                    stage = "login"
                    progress = 10
                    status_msg = "1/5 단계: 강남대학교 LMS 로그인 중..."
                elif i < 4:
                    stage = "crawling"
                    progress = 25
                    status_msg = "2/5 단계: 강남대학교 LMS에서 과목 데이터 수집 중..."
                elif i < 7:
                    stage = "processing"
                    progress = 45
                    status_msg = "3/5 단계: 수집된 데이터 처리 및 정리 중..."
                elif i < 10:
                    stage = "vectorizing"
                    progress = 70
                    status_msg = "4/5 단계: AI 분석을 위한 벡터 데이터 생성 중..."
                else:
                    stage = "storing"
                    progress = 85
                    status_msg = "5/5 단계: 데이터베이스에 정보 저장 중..."
                
                # 청크가 이미 생성되었으면 성공으로 간주
                if chunks_count > 0:
                    progress = 100
                    stage = "completed"
                    status_msg = f"✅ 완료! {chunks_count}개의 청크가 생성되었습니다."
                
                # 진행률 표시
                progress_bar.progress(progress, f"진행 중... {progress}%")
                
                # 단계별 상태 표시
                if stage == "completed":
                    status_text.success(status_msg)
                    notification.success("데이터가 성공적으로 수집되었습니다! 이제 개인화된 질문에 답변할 수 있습니다.")
                    break
                else:
                    status_text.info(status_msg)
                
                # 5초 대기
                time_module.sleep(5)
            
            # 첫 로그인 플래그 제거
            st.session_state["first_login"] = False
            if chunks_count > 0:  # 성공적으로 데이터를 불러왔을 때만 새로고침
                time_module.sleep(2)
                st.rerun()
    
    # 사이드바 - 사용자 정보 표시
    with st.sidebar:
        st.markdown('<div class="header">🧑‍🎓 학생 정보</div>', unsafe_allow_html=True)
        
        user_info = st.session_state[user_info_key]
        
        # 사용자 이름이 있는지 확인하고 표시 방식 결정
        username = user_info.get('username', '알 수 없음')
        name = user_info.get('name', username)  # 이름이 없으면 사용자명 표시
        department = user_info.get('department', '학과 정보 없음')
        student_id = user_info.get('student_id', username if username != '알 수 없음' else '학번 정보 없음')
        
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h3 style="color: #e0e0e0 !important;">{name} 님</h3>
            <p style="color: #e0e0e0 !important;">{department} / 학번: {student_id}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="header">📚 수강 중인 과목</div>', unsafe_allow_html=True)
        
        # 과목 정보 표시
        courses = user_info.get('courses', [])
        if courses:
            for course in courses:
                # 과목 정보 형식 확인 및 처리
                title = course.get('title', '과목명 없음')
                professor = course.get('professor', '교수 정보 없음')
                class_time = course.get('class_time', course.get('time', ''))  # 시간 정보는 선택적 (하위 호환성 유지)
                
                course_info = f"""
                <div class='course-item'>
                    <strong style="color: #e0e0e0 !important;">{title}</strong><br>
                    <span style="color: #e0e0e0 !important;">교수: {professor}</span>
                """
                
                # 시간 정보가 있는 경우에만 표시
                if class_time:
                    course_info += f"<br><span style='color: #e0e0e0 !important;'>시간: {class_time}</span>"
                
                course_info += "</div>"
                st.markdown(course_info, unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; color: #888 !important;'>수강 중인 과목 정보가 없습니다.</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="header">🔍 메뉴</div>', unsafe_allow_html=True)
        
        if st.button('학사 일정'):
            st.session_state[messages_key].append({"role": "user", "content": "이번 학기 학사 일정을 알려줘"})
            # 상태 변경 후 페이지 새로고침 (안정성 향상)
            st.rerun()
        
        if st.button('수강 신청'):
            st.session_state[messages_key].append({"role": "user", "content": "수강 신청 기간이 언제야?"})
            st.rerun()
        
        if st.button('도서관 서비스'):
            st.session_state[messages_key].append({"role": "user", "content": "도서관 이용 시간 알려줘"})
            st.rerun()
        
        # 데이터 갱신 버튼 추가
        data_status = check_data_status()
        
        # 데이터 상태에 따른 아이콘과 색상
        status_icon = "✅" if data_status["status"] == "ready" else "⏳" if data_status["status"] == "refreshing" else "❌"
        status_color = "#4CAF50" if data_status["status"] == "ready" else "#FFC107" if data_status["status"] == "refreshing" else "#F44336"
        status_text = "준비 완료" if data_status["status"] == "ready" else "준비 중" if data_status["status"] == "refreshing" else "미준비"
        
        data_status_info = f"""
        <div style='margin: 10px 0; padding: 12px; background-color: #333; border-radius: 5px;'>
            <div style='font-weight: bold; color: #aaa !important; display: flex; align-items: center;'>
                <span style='margin-right: 8px; color: {status_color} !important;'>{status_icon}</span>
                <span>데이터 상태: <span style='color: {status_color} !important;'>{status_text}</span></span>
            </div>
            <div style='display: flex; justify-content: space-between; margin-top: 8px;'>
                <span style='color: #aaa !important;'>저장된 데이터:</span>
                <span style='color: {"#4A69BD" if data_status["chunks"] > 0 else "#888"} !important;'>{data_status["chunks"]}개 청크</span>
            </div>
            <div style='display: flex; justify-content: space-between; margin-top: 5px;'>
                <span style='color: #aaa !important;'>마지막 업데이트:</span>
                <span style='color: #aaa !important;'>{data_status["last_update"]}</span>
            </div>
            
            <div style='margin-top: 10px; font-size: 0.8em; color: #888 !important;'>
                {
                    "첫 로그인 시 데이터를 자동으로 수집합니다. 개인 자료 질문을 더 잘 이해하기 위한 과정이니 잠시만 기다려 주세요." 
                    if data_status["status"] == "refreshing" else 
                    "개인 학습 자료가 준비되었습니다. 강남대학교 관련 질문을 자유롭게 해보세요!" 
                    if data_status["status"] == "ready" else 
                    "데이터 갱신이 필요합니다. 아래 버튼을 눌러 데이터를 수집해 주세요."
                }
            </div>
        </div>
        """
        st.markdown(data_status_info, unsafe_allow_html=True)
        
        if st.button('내 데이터 갱신하기'):
            refresh_user_data(force_refresh=True)
            st.rerun()
        
        # 대화 초기화 버튼
        if st.button('대화 초기화'):
            reset_conversation()
        
        if st.button('로그아웃'):
            # 현재 사용자 세션 정보만 초기화
            for key in list(st.session_state.keys()):
                if user_session_id in key:
                    del st.session_state[key]
            # 브라우저 세션 해시도 초기화
            if BROWSER_HASH_KEY in st.session_state:
                del st.session_state[BROWSER_HASH_KEY]
            # 세션 키 제거
            if SESSION_KEY in st.query_params:
                del st.query_params[SESSION_KEY]
            # 페이지 리프레시
            st.rerun()
        
        st.markdown('<div style="position: fixed; bottom: 20px; width: 100%; text-align: center; color: #888 !important; font-size: 12px;">© 2025 강남대학교 AI 챗봇 서비스</div>', unsafe_allow_html=True)

    # 메인 영역 - 채팅 인터페이스
    st.markdown('<div class="chat-header"><h2>🤖 강남대학교 AI 챗봇</h2></div>', unsafe_allow_html=True)

    # 채팅 메시지 표시
    for message in st.session_state[messages_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # RAG 청크가 있으면 표시 (이전 응답에서도)
            if message["role"] == "assistant" and "rag_chunks" in message and message["rag_chunks"]:
                with st.expander("참고 자료", expanded=False):
                    st.markdown("<div style='font-size: 0.8em; color: #888 !important;'>이 답변은 다음 자료를 참고했습니다:</div>", unsafe_allow_html=True)
                    
                    for i, chunk in enumerate(message["rag_chunks"]):
                        source = chunk.get("source", "알 수 없는 출처")
                        text = chunk.get("text", "내용 없음")
                        
                        st.markdown(f"""
                        <div style='margin-bottom: 10px; padding: 10px; background-color: #222; border-radius: 8px;'>
                            <div style='font-weight: bold; margin-bottom: 5px; color: #4A69BD !important;'>출처 {i+1}: {source}</div>
                            <div style='color: #aaa !important; font-size: 0.9em;'>{text}</div>
                        </div>
                        """, unsafe_allow_html=True)

    # 데이터 상태 확인
    data_status = check_data_status()
    
    # 데이터가 없거나 준비 중인 경우
    if data_status["status"] == "none" or data_status["status"] == "not_ready":
        status_container = st.empty()
        status_container.warning("개인 학습 데이터가 아직 준비되지 않았습니다. 데이터 생성을 시작합니다...")
        
        # 간단한 질문은 여전히 가능함을 표시
        info_container = st.empty()
        info_container.info("일반적인 질문은 지금도 가능합니다. 개인화된 답변은 데이터 준비 후에 가능합니다.")
        
        # 자동으로 데이터 생성 시작
        with st.spinner("데이터 준비를 시작합니다..."):
            success = refresh_user_data(force_refresh=True)
            if success:
                status_container.success("데이터 생성이 시작되었습니다. 잠시 기다려주세요...")
            else:
                status_container.error("데이터 생성 시작에 실패했습니다. '내 데이터 갱신하기' 버튼을 눌러 수동으로 시도해주세요.")
        
        # 진행 상황 표시
        progress_container = st.empty()
        progress_container.markdown("""
        <div style="padding: 10px; border-radius: 5px; border: 1px solid #4A69BD; margin: 10px 0;">
            <div style="font-weight: bold; margin-bottom: 8px;">데이터 준비 중...</div>
            <div style="height: 20px; background-color: #333; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                <div style="width: 20%; height: 100%; background-color: #4A69BD; border-radius: 10px;"></div>
            </div>
            <div style="font-size: 0.9em; color: #aaa !important;">
                첫 로그인 시에만 필요한 과정입니다. 이 과정은 최대 1분 정도 소요될 수 있으며,
                완료되면 자동으로 알림이 표시됩니다. 그동안 일반적인 질문을 해보세요!
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 주기적으로 상태를 확인하고 업데이트
        auto_refresh = True
        check_count = 0
        
        while auto_refresh and check_count < 12:  # 최대 12번(약 1분) 확인
            check_count += 1
            time_module.sleep(5)  # 5초마다 확인
            
            # 데이터 상태 다시 확인
            updated_status = check_data_status()
            
            # 진행 상황 업데이트
            progress_width = min(check_count * 8, 95)  # 최대 95%까지만 표시
            
            if updated_status["status"] == "ready":
                # 데이터 준비 완료
                progress_container.markdown("""
                <div style="padding: 10px; border-radius: 5px; border: 1px solid #4CAF50; margin: 10px 0;">
                    <div style="font-weight: bold; margin-bottom: 8px;">데이터 준비 완료!</div>
                    <div style="height: 20px; background-color: #333; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                        <div style="width: 100%; height: 100%; background-color: #4CAF50; border-radius: 10px;"></div>
                    </div>
                    <div style="font-size: 0.9em; color: #aaa !important;">
                        이제 개인 과목 관련 질문에 답변할 수 있습니다. 자유롭게 질문해 보세요!
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                status_container.success("데이터가 성공적으로 준비되었습니다! 이제 개인화된 질문에 답변할 수 있습니다.")
                info_container.empty()
                
                # 잠시 후 페이지 새로고침
                time_module.sleep(2)
                auto_refresh = False
                st.rerun()
                break
            
            elif updated_status["status"] == "partial":
                # 일부만 준비됨
                progress_container.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; border: 1px solid #FFC107; margin: 10px 0;">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #FFC107 !important;">⚠️ 데이터 일부 준비됨</div>
                    <div style="height: 20px; background-color: #333; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                        <div style="width: {progress_width}%; height: 100%; background-color: #FFC107; border-radius: 10px;"></div>
                    </div>
                    <div style="font-size: 0.9em; color: #aaa !important;">
                        기본 정보는 수집되었지만 벡터 데이터베이스에 저장 중입니다... 잠시만 기다려주세요.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 계속 준비 중
                progress_container.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; border: 1px solid #4A69BD; margin: 10px 0;">
                    <div style="font-weight: bold; margin-bottom: 8px;">데이터 준비 중... ({check_count}/12)</div>
                    <div style="height: 20px; background-color: #333; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                        <div style="width: {progress_width}%; height: 100%; background-color: #4A69BD; border-radius: 10px;"></div>
                    </div>
                    <div style="font-size: 0.9em; color: #aaa !important;">
                        강남대학교 LMS에서 데이터를 수집하고 있습니다. 잠시만 기다려주세요.
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # 시간 초과 시 수동 갱신 버튼 표시
        if auto_refresh:
            status_container.warning("데이터 준비가 예상보다 오래 걸리고 있습니다.")
            progress_container.markdown("""
            <div style="padding: 10px; border-radius: 5px; border: 1px solid #FFC107; margin: 10px 0;">
                <div style="font-weight: bold; margin-bottom: 8px; color: #FFC107 !important;">⚠️ 시간이 초과되었습니다</div>
                <div style="height: 20px; background-color: #333; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                    <div style="width: 100%; height: 100%; background-color: #FFC107; border-radius: 10px;"></div>
                </div>
                <div style="font-size: 0.9em; color: #aaa !important;">
                    데이터 준비가 백그라운드에서 계속 진행 중입니다. 아래 버튼을 눌러 상태를 확인하거나 갱신할 수 있습니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button('데이터 상태 확인 및 갱신', key='check_refresh'):
                st.rerun()

    elif data_status["status"] == "partial":
        # 크롤링만 되고 벡터화가 안 된 상태
        st.warning("데이터 파일은 있지만 벡터 DB에 저장되지 않았습니다. 데이터 갱신이 필요합니다.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("강남대학교 LMS에서 데이터는 수집되었지만, 벡터 데이터베이스에 저장되지 않았습니다. 벡터화를 완료해야 개인화된 답변이 가능합니다.")
        with col2:
            if st.button("지금 벡터화 시작", key="vector_button"):
                # 진행 상태 표시 UI
                status_container = st.empty()
                progress_container = st.empty()
                detail_container = st.empty()
                
                status_container.info("벡터화 과정을 시작합니다...")
                
                # ETL 실행
                with st.spinner("데이터 처리 중..."):
                    # 프로그레스 바 초기화 
                    progress_container.progress(10, "준비 중...")
                    
                    # 벡터화 시작
                    refresh_success = refresh_user_data(force_refresh=True)
                    
                    if not refresh_success:
                        status_container.error("벡터화 시작에 실패했습니다. 다시 시도해주세요.")
                        time_module.sleep(2)
                        st.rerun()
                    
                    # 단계별 진행 표시
                    stages = [
                        {"progress": 30, "status": "3/5 단계: 데이터 전처리 중...", 
                         "detail": "강남대 LMS에서 수집된 데이터를 분석하고 정리하는 중입니다."},
                        {"progress": 50, "status": "4/5 단계: 텍스트 벡터화 중...", 
                         "detail": "AI 모델이 이해할 수 있는 형태로 텍스트를 변환하는 중입니다."},
                        {"progress": 80, "status": "5/5 단계: 벡터 DB에 저장 중...", 
                         "detail": "생성된 벡터 데이터를 데이터베이스에 저장하는 중입니다."},
                        {"progress": 100, "status": "✅ 완료!", 
                         "detail": "벡터화가 완료되었습니다. 개인화된 질문에 답변할 준비가 되었습니다."}
                    ]
                    
                    # 각 단계 표시 및 진행
                    for stage in stages:
                        progress_container.progress(stage["progress"], stage["status"])
                        detail_container.info(stage["detail"])
                        
                        # 상태 확인 (청크가 생성되었는지)
                        current_status = check_data_status()
                        if current_status.get("chunks", 0) > 0 and stage["progress"] < 100:
                            # 청크가 생성되었으면 마지막 단계로 건너뛰기
                            progress_container.progress(100, "✅ 완료!")
                            detail_container.success(f"벡터화가 완료되었습니다! {current_status.get('chunks', 0)}개의 청크가 생성되었습니다.")
                            break
                        
                        time_module.sleep(2)  # 각 단계별 지연
                
                status_container.success("데이터 준비가 완료되었습니다! 이제 개인화된 질문에 답변할 수 있습니다.")
                time_module.sleep(1)
                st.rerun()

    # 사용자 입력 처리
    if prompt := st.chat_input("메시지를 입력하세요..." + (" (일반 질문만 가능)" if data_status["status"] != "ready" else "")):
        # 사용자 메시지 추가
        st.session_state[messages_key].append({"role": "user", "content": prompt})
        
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 챗봇 응답 처리
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # API 호출 전 상태 표시
            message_placeholder.markdown("생각 중입니다...")
            
            # 데이터 준비 상태 확인
            data_ready = data_status["status"] == "ready"
            
            # 데이터가 준비되지 않은 경우 안내 메시지 추가
            if not data_ready and any(keyword in prompt.lower() for keyword in ["내 과목", "내 수업", "내 성적", "내 학점", "내 시간표"]):
                warning_container = st.warning("개인 데이터가 준비되지 않아 일반적인 답변만 제공합니다. 개인화된 답변을 원하시면 '내 데이터 갱신하기' 버튼을 클릭해주세요.")
            
            # 실제 API 호출
            start_time = time_module.time()
            response_data = call_chat_api(prompt, data_ready)
            elapsed_time = time_module.time() - start_time
            
            # 디버그 로그 (개발 중에만 표시)
            debug_mode = st.session_state.get('debug_mode', False)
            if debug_mode:
                with st.expander("API 응답 디버그 정보"):
                    st.write(f"API 응답 시간: {elapsed_time:.2f}초")
                    st.write(f"응답 플로우: {response_data.get('current_flow', 'unknown')}")
                    st.write(f"RAG 청크 수: {len(response_data.get('rag_chunks', []))}")
                    st.write(f"데이터 준비 상태: {data_status['status']}")
            
            # 타이핑 효과 시뮬레이션
            for chunk in response_data["response"].split():
                full_response += chunk + " "
                time_module.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # 데이터가 준비되지 않은 경우 추가 안내
            if not data_ready and response_data["current_flow"] == "personal":
                st.info("보다 정확한 개인화된 답변을 원하시면 '내 데이터 갱신하기' 버튼을 클릭하여 데이터를 생성해주세요.")
            
            # RAG 청크가 있으면 표시
            rag_chunks = response_data.get("rag_chunks", [])
            if rag_chunks and len(rag_chunks) > 0:
                with st.expander("참고 자료", expanded=False):
                    st.markdown("<div style='font-size: 0.8em; color: #888 !important;'>이 답변은 다음 자료를 참고했습니다:</div>", unsafe_allow_html=True)
                    
                    for i, chunk in enumerate(rag_chunks):
                        source = chunk.get("source", "알 수 없는 출처")
                        text = chunk.get("text", "내용 없음")
                        
                        st.markdown(f"""
                        <div style='margin-bottom: 10px; padding: 10px; background-color: #222; border-radius: 8px;'>
                            <div style='font-weight: bold; margin-bottom: 5px; color: #4A69BD !important;'>출처 {i+1}: {source}</div>
                            <div style='color: #aaa !important; font-size: 0.9em;'>{text}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
            # 응답 메시지 저장 (RAG 청크 포함)
            st.session_state[messages_key].append({
                "role": "assistant", 
                "content": response_data["response"],
                "rag_chunks": response_data.get("rag_chunks", []),
                "current_flow": response_data.get("current_flow", "general")
            })

    # 첫 방문 시 인사말 표시
    if len(st.session_state[messages_key]) == 0:
        with st.chat_message("assistant"):
            st.markdown("안녕하세요! 강남대학교 AI 챗봇입니다. 무엇을 도와드릴까요?")
            st.session_state[messages_key].append({"role": "assistant", "content": "안녕하세요! 강남대학교 AI 챗봇입니다. 무엇을 도와드릴까요?"})
        
    # 디버깅을 위한 추가 정보 표시 (개발 중에만 사용)
    if st.checkbox("디버그 정보 표시", value=False):
        # 디버그 모드 상태 저장
        st.session_state['debug_mode'] = True
        
        with st.expander("API 연결 정보"):
            st.write(f"토큰 상태: {'있음' if token_key in st.session_state else '없음'}")
            st.write(f"세션 ID: {user_session_id}")
            st.write(f"브라우저 해시: {get_browser_hash()}")
            
            # 토큰이 있으면 만료 시간 표시 시도
            if token_key in st.session_state:
                token = st.session_state[token_key]
                # JWT는 base64로 인코딩된 header.payload.signature 형식
                try:
                    # JWT 페이로드 부분 디코딩
                    import base64
                    import json
                    
                    payload = token.split('.')[1]
                    # 패딩 조정 (base64url 형식)
                    payload += '=' * (-len(payload) % 4)
                    decoded = base64.b64decode(payload.replace('-', '+').replace('_', '/'))
                    payload_data = json.loads(decoded)
                    
                    # 만료 시간 표시
                    if 'exp' in payload_data:
                        exp_time = datetime.fromtimestamp(payload_data['exp'])
                        now = datetime.now()
                        remaining = exp_time - now
                        st.write(f"토큰 만료: {exp_time.strftime('%Y-%m-%d %H:%M:%S')} (남은 시간: {remaining.total_seconds()/60:.1f}분)")
                except Exception as e:
                    st.write(f"토큰 정보 디코딩 실패: {e}")
    else:
        # 디버그 모드 꺼짐
        st.session_state['debug_mode'] = False 