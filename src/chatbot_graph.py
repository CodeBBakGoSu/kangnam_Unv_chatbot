from typing import Dict, Any, TypedDict
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolNode
from src.agents.router_agent import RouterAgent
from src.agents.personal_agent import PersonalAgent
from src.agents.common_agent import CommonAgent
from src.agents.general_agent import GeneralAgent

class ChatState(TypedDict):
    messages: list[str]
    current_flow: str
    response: str
    user_context: Dict[str, Any]

def create_chatbot_graph() -> Graph:
    # 에이전트 초기화
    router = RouterAgent()
    personal = PersonalAgent()
    common = CommonAgent()
    general = GeneralAgent()
    
    # 상태 그래프 생성
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node("router", router.classify)
    
    def merge_state(state, result):
        merged = dict(state)
        for k, v in result.items():
            if v is not None:
                merged[k] = v
        return merged

    async def personal_node(state: ChatState):
        agent = PersonalAgent()
        message = state["messages"][-1]
        context = state.get("user_context", {})
        result = await agent.answer(message, context)
        return merge_state(state, result)
    
    async def common_node(state: ChatState):
        agent = CommonAgent()
        message = state["messages"][-1]
        result = await agent.answer(message)
        return merge_state(state, result)

    async def general_node(state: ChatState):
        agent = GeneralAgent()
        message = state["messages"][-1]
        result = await agent.answer(message)
        return merge_state(state, result)

    workflow.add_node("personal", personal_node)
    workflow.add_node("common", common_node)
    workflow.add_node("general", general_node)
    
    # 엣지 연결
    def route_to_agent(state: ChatState) -> str:
        flow = state.get("current_flow", "")
        if flow == "personal":
            return "personal"
        elif flow == "common":
            return "common"
        else:
            return "general"
    
    # 조건부 엣지 추가
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "personal": "personal",
            "common": "common",
            "general": "general"
        }
    )
    
    # 시작 노드 설정
    workflow.set_entry_point("router")
    
    # 각 에이전트의 응답을 최종 상태로 설정
    for end_node in ["personal", "common", "general"]:
        workflow.set_finish_point(end_node)
    
    return workflow.compile()


# 구지 어싱크로 짠 이유?
# 사람 한명이 사용하면 어싱크로 할 필요 없음
# 하지만 만약 두사람 이상이 사용한다면 필요한거임
# 만약 a사람은 오늘 밥이 뭐야 b 사람은 내가할 과제 정리해줘 하면
# 이럴 때 동기(sync) 코드라면 → 한 명 끝날 때까지 다음 사람은 기다려야 함
async def process_message(message: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """메시지 처리 및 응답 생성"""
    graph = create_chatbot_graph()
    
    # RouterAgent로 먼저 분류
    router = RouterAgent()
    classification = await router.classify(message)
    
    # 초기 상태 설정 (RouterAgent의 분류 결과 반영)
    #"current_flow": classification["flow"]
    #이걸 통해서 flow 를 current_flow 에 저장
    initial_state = {
        "messages": [message],
        "current_flow": classification["flow"],
        "response": "",
        "user_context": user_context if user_context else {}
    }
    
    # 그래프 실행
    result = await graph.ainvoke(initial_state)
    
    # 최종 응답에 token_usage, rag_chunks가 있으면 포함해서 반환
    return {
        "messages": result.get("messages"),
        "current_flow": result.get("current_flow"),
        "response": result.get("response"),
        "user_context": result.get("user_context"),
        "token_usage": result.get("token_usage"),
        "rag_chunks": result.get("rag_chunks"),
    }