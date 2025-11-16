import google.generativeai as genai
from app.config import GOOGLE_API_KEY, GEMINI_MODEL
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

# Gemini API 설정
genai.configure(api_key=GOOGLE_API_KEY)
llm = genai.GenerativeModel(GEMINI_MODEL)

def extract_text(response):
    """Gemini 응답에서 텍스트 안전하게 추출"""
    if hasattr(response, 'text') and response.text:
        return response.text
    try:
        return response.candidates[0].content.parts[0].text
    except Exception:
        return str(response)

def count_tokens(text: str) -> Optional[int]:
    """텍스트의 토큰 수 계산"""
    try:
        # 새로운 API 호출 방식: content 대신 contents 사용
        response = llm.count_tokens(contents=text)
        return response.total_tokens
    except Exception as e:
        print(f"토큰 계산 중 오류 발생: {e}")
        return None

def get_token_usage_details(prompt: str, response_text: str, response_metadata=None) -> Dict[str, Any]:
    """토큰 사용량에 대한 자세한 정보 생성"""
    try:
        # response_metadata가 제공된 경우 이를 사용
        if response_metadata and hasattr(response_metadata, 'usage_metadata'):
            metadata = response_metadata.usage_metadata
            prompt_tokens = getattr(metadata, 'prompt_token_count', 0)
            response_tokens = getattr(metadata, 'candidates_token_count', 0)
            total_tokens = getattr(metadata, 'total_token_count', 0)
        else:
            # 기존 방식 (개별 토큰 계산)
            prompt_tokens = count_tokens(prompt) or 0
            response_tokens = count_tokens(response_text) or 0
            total_tokens = prompt_tokens + response_tokens
        
        # 토큰당 비용 계산 (예상치)
        input_cost_per_1k = 0.00025  # 입력 토큰 1K당 $0.00025 (Gemini Pro 기준)
        output_cost_per_1k = 0.0005  # 출력 토큰 1K당 $0.0005 (Gemini Pro 기준)
        
        prompt_cost = (prompt_tokens / 1000) * input_cost_per_1k
        response_cost = (response_tokens / 1000) * output_cost_per_1k
        total_cost = prompt_cost + response_cost
        
        return {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "prompt_cost_usd": round(prompt_cost, 6),
            "response_cost_usd": round(response_cost, 6),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"토큰 사용량 계산 중 오류 발생: {e}")
        return None

def get_current_week_info() -> Dict[str, str]:
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

def format_context(chunks: list) -> str:
    """검색된 청크들을 컨텍스트로 포맷팅"""
    time_info = get_current_week_info()
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

def generate_response(query: str, context: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Gemini를 사용하여 응답 생성"""
    time_info = get_current_week_info()
    
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
        # 응답 생성 시작 시간 기록
        start_time = datetime.now()
        
        # Gemini API 호출 (최신 방식)
        try:
            print(f"Gemini API 호출 시작: {datetime.now().isoformat()}")
            response = llm.generate_content(contents=prompt)
            print(f"Gemini API 호출 완료: {datetime.now().isoformat()}")
            
            # 응답 메타데이터 로깅
            if hasattr(response, 'usage_metadata'):
                print(f"응답 메타데이터: {response.usage_metadata}")
            else:
                print("응답에 usage_metadata 속성이 없습니다")
                
        except Exception as api_error:
            print(f"Gemini API 호출 오류: {api_error}")
            raise
            
        response_text = extract_text(response)
        
        # 응답 생성 종료 시간 및 소요 시간 계산
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # 토큰 사용량 상세 정보 가져오기 (usage_metadata 활용)
        token_usage = get_token_usage_details(prompt, response_text, response)
        
        if token_usage:
            token_usage['response_time_seconds'] = response_time
            print(f"토큰 사용량 정보: {token_usage}")
        else:
            print("토큰 사용량 정보를 가져올 수 없습니다")
        
        return response_text, token_usage
        
    except Exception as e:
        print(f"응답 생성 중 오류 발생: {e}")
        return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", None 