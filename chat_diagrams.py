from diagrams import Diagram, Cluster
from diagrams.programming.framework import Fastapi
from diagrams.programming.language import Python
from diagrams.custom import Custom
from diagrams.onprem.client import Users
from diagrams.onprem.inmemory import Redis
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack
from diagrams.aws.ml import Sagemaker
from diagrams.generic.database import SQL
from diagrams.onprem.network import Nginx

with Diagram("LangGraph 기반 챗봇 시스템 전체 구조", direction="TB", outformat="png", show=True, graph_attr={"fontsize": "18", "bgcolor": "white", "pad": "1.5"}):
    user = Users("User\n(Streamlit UI)")

    with Cluster("🟦 FastAPI 백엔드 (API 게이트웨이)", graph_attr={"bgcolor": "#e3f2fd", "pencolor": "#2196f3", "style": "filled", "fontsize": "14"}):
        api = Fastapi("FastAPI 엔드포인트")
        login_request = Python("학교 로그인 요청\n(request.session)")
        session_store = Redis("세션 저장소\n(Redis / Token 기반)")
        main_router = Nginx("LangGraph MainRouter\n질문 분기 처리")

    user >> api >> login_request >> session_store
    api >> main_router

    with Cluster("🟩 학교 공통 정보 처리 흐름", graph_attr={"bgcolor": "#e8f5e9", "pencolor": "#43a047", "style": "filled", "fontsize": "14"}):
        faiss = Storage("FAISS VDB\n(학교 정보 사전 구축)")
        retriever_info = Python("Retriever\n(문서 추출)")
        prompt_info = Python("Prompt Template\n(질문+문서 결합)")
        llm_info = Sagemaker("LLM\n(OpenAI 등)")

    main_router >> retriever_info >> faiss
    retriever_info >> prompt_info >> llm_info

    with Cluster("🟨 개인 맞춤형 정보 흐름", graph_attr={"bgcolor": "#fff8e1", "pencolor": "#f9a825", "style": "filled", "fontsize": "14"}):
        sub_router = Nginx("서브 Router\n(과제/공지/성적 분기)")

        with Cluster("📘 정보 검색 흐름", graph_attr={"bgcolor": "#e0f7fa", "pencolor": "#00acc1", "style": "filled"}):
            retriever_private = Python("Retriever\n(개인화 문서 검색)")
            llm_private = Sagemaker("LLM\n(맞춤 응답 생성)")

        with Cluster("📗 개인정보 수집 흐름", graph_attr={"bgcolor": "#f1f8e9", "pencolor": "#7cb342", "style": "filled"}):
            crawl_private = Python("크롤링 Agent\n(비동기 실행)")
            preprocess_private = Python("전처리 Agent")
            temp_vdb_private = Storage("Ephemeral VDB\n(임시 메모리 저장)")

        session_store >> crawl_private
        crawl_private >> preprocess_private >> temp_vdb_private >> retriever_private >> llm_private

    main_router >> sub_router
    sub_router >> retriever_private

    with Cluster("🟪 기타 일반 질문 처리 흐름", graph_attr={"bgcolor": "#f3e5f5", "pencolor": "#8e24aa", "style": "filled", "fontsize": "14"}):
        search_router = Python("Mini Router\n(잡담/검색/모호 질문 분류)")
        web_search = Python("Web Search Agent\n(Tavily, Serper 등)")
        chat_agent = Python("Chat Agent\n(일반 대화)")
        ask_user = Users("Clarify 질문\n(모호한 질문 재확인)")

        main_router >> search_router
        search_router >> web_search
        search_router >> chat_agent
        search_router >> ask_user

    # 최종 응답 흐름
    llm_info >> user
    llm_private >> user
    web_search >> user
    chat_agent >> user
    ask_user >> user
