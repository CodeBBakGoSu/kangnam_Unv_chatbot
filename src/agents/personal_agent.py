from typing import Dict, Any
import json
import os
from .base_agent import BaseAgent
from ..utils.course_preprocessor import CoursePreprocessor
from datetime import datetime

class PersonalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.system_prompt = """당신은 강남대학교 학생들을 위한 개인 맞춤형 정보를 제공하는 챗봇입니다.
        학생의 수강 과목, 과제 현황, 출석 상태, 개인 공지사항, 성적 등의 정보를 제공할 수 있습니다.
        항상 공손하고 정확한 정보를 제공하세요."""
        
        # 사용자 데이터 로드 및 전처리
        self.user_data = self._load_user_data()
    
    def _load_user_data(self) -> Dict[str, Any]:
        """사용자 데이터 로드 및 전처리"""
        try:
            data_path = os.path.join(os.path.dirname(__file__), '../../user_data/kangnam_courses.json')
            processed_path = os.path.join(os.path.dirname(__file__), '../../user_data/kangnam_courses_processed.json')
            
            # 전처리된 파일이 있으면 그것을 사용
            if os.path.exists(processed_path):
                with open(processed_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 전처리된 파일이 없으면 전처리 실행
            preprocessor = CoursePreprocessor(data_path)
            processed_data = preprocessor.process()
            preprocessor.save_processed_data()
            
            return processed_data
            
        except Exception as e:
            print(f"사용자 데이터 로드 실패: {e}")
            return {}
    
    def _get_relevant_info(self, message: str, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """질문과 관련된 정보만 추출"""
        relevant_info = {}
        
        # 기본 정보는 항상 포함
        if "user" in student_data:
            relevant_info["name"] = student_data["user"].get("name", "알 수 없음")
            relevant_info["department"] = student_data["user"].get("department", "알 수 없음")
        
        # 현재 날짜 기준으로 이번 주 정보 추출
        current_date = datetime.now()
        
        # 질문 내용에 따라 관련 정보만 포함
        if any(keyword in message for keyword in ["이번주", "이번 주", "이번 주차"]):
            # 이번 주 과제 정보만 추출
            current_week_assignments = []
            for course in student_data.get("courses", []):
                for week in course.get("weeks", {}).get("weeks", []):
                    if "date" in week and "assignment_status" in week:
                        week_date = datetime.strptime(week["date"], "%Y-%m-%d")
                        # 이번 주에 해당하는 과제만 포함
                        if (week_date - current_date).days >= -7 and (week_date - current_date).days <= 7:
                            current_week_assignments.append({
                                "course": course["title"],
                                "week": week["title"],
                                "date": week["date"],
                                "assignment": week["assignment_status"]
                            })
            relevant_info["current_week_assignments"] = current_week_assignments
            
        elif any(keyword in message for keyword in ["수강", "과목", "강의"]):
            # 수강 과목 목록만 간단히 추출
            relevant_info["courses"] = [
                {
                    "title": course["title"],
                    "professor": course["professor"]
                }
                for course in student_data.get("courses", [])
            ]
        
        elif any(keyword in message for keyword in ["과제", "제출"]):
            # 과제 정보만 간단히 추출
            assignments = []
            for course in student_data.get("courses", []):
                for week in course.get("weeks", {}).get("weeks", []):
                    if "assignment_status" in week:
                        assignments.append({
                            "course": course["title"],
                            "week": week["title"],
                            "date": week.get("date", ""),
                            "status": week["assignment_status"].get("제출 여부", ""),
                            "deadline": week["assignment_status"].get("종료 일시", "")
                        })
            relevant_info["assignments"] = assignments
        
        elif any(keyword in message for keyword in ["출석", "결석"]):
            # 출석 정보만 간단히 추출
            attendance = []
            for course in student_data.get("courses", []):
                if "weeks" in course and "attendance_summary" in course["weeks"]:
                    attendance.append({
                        "course": course["title"],
                        "summary": course["weeks"]["attendance_summary"]
                    })
            relevant_info["attendance"] = attendance
        
        elif any(keyword in message for keyword in ["공지", "알림"]):
            # 공지사항만 간단히 추출
            notices = []
            for course in student_data.get("courses", []):
                for notice in course.get("notices", []):
                    notices.append({
                        "course": course["title"],
                        "title": notice["title"]
                    })
            relevant_info["notices"] = notices
            
        return relevant_info
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """개인 정보 관련 메시지 처리"""
        if not context:
            return {
                "response": "로그인이 필요한 서비스입니다. 먼저 로그인해주세요.",
                "requires_auth": True
            }
        
        try:
            # 사용자 컨텍스트에서 학번 추출
            student_id = context.get("student_id")
            if not student_id:
                return {
                    "response": "학생 정보를 찾을 수 없습니다. 다시 로그인해주세요.",
                    "requires_auth": True
                }
            
            # 사용자 데이터에서 해당 학생 정보 찾기
            student_data = self.user_data.get(student_id, {})
            if not student_data:
                return {
                    "response": "학생 정보를 찾을 수 없습니다.",
                    "requires_auth": True
                }
            
            # 질문과 관련된 정보만 추출
            relevant_info = self._get_relevant_info(message, student_data)
            
            # 프롬프트 구성
            prompt = f"""시스템: {self.system_prompt}

사용자 정보:
- 이름: {relevant_info.get('name')}
- 학과: {relevant_info.get('department')}
{self._format_relevant_info(relevant_info)}

사용자 질문: {message}

위 정보를 바탕으로 사용자의 질문에 답변해주세요."""

            # Gemini API 호출
            response = self.client.models.generate_content(prompt)
            
            # 응답 저장
            self.add_to_memory({
                "role": "user",
                "content": message,
                "context": context
            })
            
            self.add_to_memory({
                "role": "assistant",
                "content": response.text
            })
            
            return {
                "response": response.text,
                "requires_auth": False
            }
            
        except Exception as e:
            return {
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "requires_auth": False
            }
    
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