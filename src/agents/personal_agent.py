from typing import Dict, Any, List
import json
import os
from .base_agent import BaseAgent
from ..etl.course_preprocessor import CoursePreprocessor
from datetime import datetime, timedelta
import google.generativeai as genai
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# .env 파일 로드 (경로는 상황에 맞게 조정)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/.env'))
load_dotenv(dotenv_path=env_path)

# Supabase 클라이언트 초기화
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)
llm = genai.GenerativeModel('gemini-2.0-flash-001')
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

class PersonalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.system_prompt = """당신은 강남대학교 학생들을 위한 개인 맞춤형 정보를 제공하는 챗봇입니다.
        학생의 수강 과목, 과제 현황, 출석 상태, 개인 공지사항, 성적 등의 정보를 제공할 수 있습니다.
        항상 공손하고 정확한 정보를 제공하세요."""
    
    def get_current_week_info(self) -> dict:
        """현재 날짜 기준으로 이번주 정보 반환"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        return {
            'today': today.strftime('%Y-%m-%d'),
            'weekday': today.strftime('%A'),
            'week_start': monday.strftime('%Y-%m-%d'),
            'week_end': sunday.strftime('%Y-%m-%d'),
            'current_time': today.strftime('%H:%M')
        }

    def normalize_course_name_with_llm(self, query: str, user_courses: List[Dict[str, Any]]) -> str:
        """LLM을 사용하여 사용자 입력에서 과목명 추론"""
        course_names = [
            course["title"].split("(")[0].strip()
            for course in user_courses
            if "title" in course
        ]
        
        prompt = f"""
당신은 대학교 학생의 수강 과목을 찾아주는 도우미입니다.
학생이 수강 중인 과목 목록입니다:
{', '.join(course_names)}

학생의 입력: "{query}"

위 과목 목록 중에서 학생이 언급한 과목을 찾아주세요.

다음과 같은 패턴을 고려하여 매칭해주세요:
1. 정확한 과목명과 일치하는 경우
2. 과목명의 축약어나 별칭 (예: 첫 글자들을 조합, 주요 단어의 첫 글자 조합 등)
3. 과목명의 일부만 언급된 경우
4. 영문 약자가 한글로 쓰인 경우나 그 반대의 경우

출력 규칙:
- 매칭된 경우: 정확한 과목명만 한 줄로 출력
- 매칭되지 않은 경우: "없음"

답변:"""

        try:
            response = llm.generate_content(prompt)
            normalized_name = response.text.strip()
            
            if normalized_name == "없음":
                return None
                
            for course in user_courses:
                course_title = course["title"].split("(")[0].strip()
                if course_title.startswith(normalized_name) or normalized_name.startswith(course_title):
                    return course["title"]
            
            return None
        except Exception as e:
            print(f"과목명 정규화 중 오류 발생: {e}")
            return None

    def get_relevant_chunks(self, query: str, limit: int = 5) -> list:
        """벡터 DB에서 관련 청크 검색"""
        try:
            query_embedding = embedding_model.encode(query).tolist()
            response = supabase.rpc(
                'match_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.4,
                    'match_count': limit
                }
            ).execute()
            return response.data
        except Exception as e:
            print(f"청크 검색 중 오류 발생: {e}")
            return []

    def format_context(self, chunks: list) -> str:
        """검색된 청크들을 컨텍스트로 포맷팅"""
        time_info = self.get_current_week_info()
        context = "다음은 관련된 강의 정보입니다:\n\n"
        for chunk in chunks:
            context += f"강좌: {chunk['course']}\n"
            context += f"주차: {chunk['week']}\n"
            context += f"내용: {chunk['content']}\n"
            if chunk.get('metadata'):
                if chunk['metadata'].get('date'):
                    date = chunk['metadata']['date']
                    context += f"날짜: {date}\n"
                    if time_info['week_start'] <= date <= time_info['week_end']:
                        context += "※ 이번주 해당\n"
                if chunk['metadata'].get('due_date'):
                    context += f"제출기한: {chunk['metadata']['due_date']}\n"
            context += "\n"
        return context

    def count_tokens(self, text: str) -> int:
        try:
            response = llm.count_tokens(text)
            print(f"[DEBUG] count_tokens({text[:30]}...): {response.total_tokens}")
            return response.total_tokens
        except Exception as e:
            print(f"[DEBUG] 토큰 계산 중 오류 발생: {e}")
            return None

    def extract_text(self, response):
        # Gemini 응답에서 텍스트 안전하게 추출
        if hasattr(response, 'text') and response.text:
            return response.text
        try:
            return response.candidates[0].content.parts[0].text
        except Exception:
            return str(response)

    def generate_response(self, query: str, context: str) -> tuple:
        """Gemini를 사용하여 응답 생성"""
        time_info = self.get_current_week_info()
        prompt = f"""
당신은 강남대학교 학생들을 위한 학습 도우미입니다.
주어진 컨텍스트를 기반으로 학생의 질문에 답변해주세요.
모르는 내용이나 컨텍스트에 없는 내용에 대해서는 모른다고 말씀해주세요.

현재 시간 정보:
- 오늘 날짜: {time_info['today']} ({time_info['weekday']})
- 이번주 기간: {time_info['week_start']} ~ {time_info['week_end']}
- 현재 시각: {time_info['current_time']}

컨텍스트:
{context}

학생의 질문: {query}

답변 시 참고사항:
1. "이번주"는 {time_info['week_start']}부터 {time_info['week_end']}까지를 의미합니다.
2. 과제나 수업 일정이 이번주에 해당하는지 날짜를 확인해주세요.
3. 날짜 정보가 있는 경우, 현재 날짜 기준으로 남은 기간도 알려주세요.

답변을 한국어로 작성해주세요.
답변에는 다음 정보들을 포함해주세요:
1. 관련 강좌명
2. 해당 주차
3. 구체적인 내용이나 과제
4. 날짜나 기한 정보 (있는 경우)
"""
        try:
            response = llm.generate_content(prompt)
            response_text = self.extract_text(response)
            prompt_tokens = self.count_tokens(prompt)
            response_tokens = self.count_tokens(response_text)
            if prompt_tokens is None or response_tokens is None:
                token_usage = None
            else:
                token_usage = {
                    "prompt_tokens": prompt_tokens,
                    "response_tokens": response_tokens,
                    "total_tokens": prompt_tokens + response_tokens
                }
            return response_text, token_usage
        except Exception as e:
            print(f"응답 생성 중 오류 발생: {e}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", None

    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """개인 정보 관련 메시지 처리 (RAG 기반)"""
        print("[DEBUG] context:", context)
        if not context or not context.get("courses"):
            print("[DEBUG] context가 없거나 courses가 없음")
            return {
                "response": "로그인이 필요한 서비스입니다. 먼저 로그인해주세요.",
                "requires_auth": True
            }
        user_courses = context.get("courses", [])
        print("[DEBUG] user_courses:", user_courses)
        normalized_course = self.normalize_course_name_with_llm(message, user_courses)
        print("[DEBUG] normalized_course:", normalized_course)
        relevant_chunks = self.get_relevant_chunks(normalized_course if normalized_course else message)
        print("[DEBUG] relevant_chunks:", relevant_chunks)
        if not relevant_chunks:
            return {
                "response": "죄송합니다. 관련된 정보를 찾을 수 없습니다.",
                "requires_auth": False,
                "token_usage": None,
                "rag_chunks": []
            }
        context_str = self.format_context(relevant_chunks)
        response, token_usage = self.generate_response(message, context_str)
        self.add_to_memory({
            "role": "user",
            "content": message,
            "context": context
        })
        self.add_to_memory({
            "role": "assistant",
            "content": response
        })
        return {
            "response": response,
            "requires_auth": False,
            "token_usage": token_usage,
            "rag_chunks": relevant_chunks
        }

    async def answer(self, message: str, context: dict = None) -> dict:
        return await self.process(message, context)

    def _format_relevant_info(self, info: Dict[str, Any]) -> str:
        """관련 정보를 프롬프트에 맞게 포맷팅"""
        formatted_info = []
        
        if "courses" in info:
            formatted_info.append(f"- 수강 과목: {json.dumps(info['courses'], ensure_ascii=False)}")
        
        if "assignments" in info:
            formatted_info.append(f"- 과제 현황: {json.dumps(info['assignments'], ensure_ascii=False)}")
        
        if "attendance" in info:
            formatted_info.append(f"- 출석 현황: {json.dumps(info['attendance'], ensure_ascii=False)}")
        
        if "grades" in info:
            formatted_info.append(f"- 성적 정보: {json.dumps(info['grades'], ensure_ascii=False)}")
            
        return "\n".join(formatted_info) 