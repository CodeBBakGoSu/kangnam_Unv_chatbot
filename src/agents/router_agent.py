from typing import Dict, Any, List
import json
from .base_agent import BaseAgent

class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.system_prompt = """당신은 강남대학교 소프트웨어응용학부 학생들을 위한 챗봇의 라우터입니다.
        사용자의 질문을 다음 3가지 주요 흐름 중 하나로 분류해주세요:

        1. 개인 맞춤형 정보 흐름
        - 수강 중인 과목 정보
        - 과제 제출 현황
        - 출석 현황
        - 개인별 공지사항
        - 성적 정보

        2. 학교 공통 정보 흐름
        - 학사 제도
        - 졸업 요건
        - 수강신청 방법
        - 학과 공지사항
        - 교수 정보
        - 시설 정보

        3. 기타 일반 질문 흐름
        - 학교 생활 일반
        - 동아리 정보
        - 장학금 정보
        - 기숙사 정보
        - 기타 잡담
        
        응답은 반드시 다음 형식으로 해주세요:
        {
            "flow": "분류된 흐름 (personal/common/general)",
            "sub_category": "세부 카테고리",
            "confidence": 0.0 ~ 1.0 사이의 신뢰도,
            "explanation": "분류 이유",
            "requires_auth": true/false (개인정보 접근 필요 여부)
        }"""
    
    # 메시지 분류 함수
    #async 비동기 처리를 위한 키워드, 사용자의 압력 메시지를 str 로 받는다.
    #반환타입은 딕셔너리
    async def classify(self, message: str) -> Dict[str, Any]: 
        """사용자 메시지를 분류"""
        # 시스템 프롬프트와 사용자 메시지를 결합
        prompt = f"{self.system_prompt}\n\n사용자 메시지: {message}"
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # 기본값 반환
            return {
                "flow": "general",
                "sub_category": "기타",
                "confidence": 0.5,
                "explanation": "응답 파싱 실패로 인한 기본 분류",
                "requires_auth": False
            } 
            