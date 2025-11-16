from typing import Dict, Any, List
import json
from .base_agent import BaseAgent
import google.generativeai as genai
import os
from dotenv import load_dotenv

class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        load_dotenv()
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-001')
        self.system_prompt = """당신은 강남대학교 소프트웨어응용학부 학생들을 위한 챗봇의 라우터입니다.
        사용자의 질문을 다음 3가지 주요 흐름 중 하나로 분류해주세요:

        1. 개인 맞춤형 정보 흐름 (personal)
        - 수강 중인 과목 정보
        - 과제 제출 현황
        - 출석 현황
        - 개인별 공지사항
        - 성적 정보

        2. 학교 공통 정보 흐름 (common)
        - 학사 제도
        - 졸업 요건
        - 수강신청 방법
        - 학과 공지사항
        - 교수 정보
        - 시설 정보
        - 동아리 정보
        - 장학금 정보
        - 기숙사 정보
        - 학교 생활 관련 제도

        3. 기타 일반 질문 흐름 (general)
        - 학교 생활 일반적인 대화
        - 기타 잡담
        - 인사
        - 감사/사과 표현
        
        반드시 다음 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요:
        {
            "flow": "personal/common/general 중 하나만 사용",
            "sub_category": "세부 카테고리",
            "confidence": 0.0 ~ 1.0 사이의 숫자,
            "explanation": "분류 이유",
            "requires_auth": true/false
        }"""
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """응답 텍스트에서 JSON 추출"""
        try:
            # JSON 형식 찾기
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_str = text[start_idx:end_idx]
            result = json.loads(json_str)
            
            # 필수 필드 확인
            required_fields = ['flow', 'sub_category', 'confidence', 'explanation', 'requires_auth']
            if not all(field in result for field in required_fields):
                return None
                
            # flow 값 검증
            if result['flow'] not in ['personal', 'common', 'general']:
                return None
                
            # confidence 값 검증
            try:
                confidence = float(result['confidence'])
                if not (0 <= confidence <= 1):
                    return None
            except (ValueError, TypeError):
                return None
                
            return result
        except json.JSONDecodeError:
            return None

    async def classify(self, message: str) -> Dict[str, Any]:
        """사용자 메시지를 분류"""
        prompt = f"{self.system_prompt}\n\n사용자 메시지: {message}"
        
        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json_from_response(response.text)
            
            if result:
                return result
            
            # JSON 파싱 실패 시, 메시지 내용 기반으로 기본 분류
            if any(keyword in message.lower() for keyword in ['과제', '출석', '성적', '수강', '내', '나의', '제']):
                return {
                    "flow": "personal",
                    "sub_category": "개인 정보",
                    "confidence": 0.7,
                    "explanation": "개인 정보 관련 키워드 감지로 인한 분류",
                    "requires_auth": True
                }
            elif any(keyword in message.lower() for keyword in ['학사', '졸업', '수강신청', '공지', '교수', '시설']):
                return {
                    "flow": "common",
                    "sub_category": "학교 공통 정보",
                    "confidence": 0.7,
                    "explanation": "학교 공통 정보 관련 키워드 감지로 인한 분류",
                    "requires_auth": False
                }
            else:
                return {
                    "flow": "general",
                    "sub_category": "기타",
                    "confidence": 0.5,
                    "explanation": "기본 분류",
                    "requires_auth": False
                }
        except Exception as e:
            print(f"분류 중 오류 발생: {e}")
            return {
                "flow": "general",
                "sub_category": "오류",
                "confidence": 0.5,
                "explanation": f"오류 발생으로 인한 기본 분류: {str(e)}",
                "requires_auth": False
            } 
            