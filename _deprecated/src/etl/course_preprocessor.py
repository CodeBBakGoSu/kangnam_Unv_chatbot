import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import numpy as np
import re
from collections import Counter

class CoursePreprocessor:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.raw_data = self._load_json()
        self.processed_data = None
        # 2025년 3월 4일을 기준일로 설정
        self.base_date = datetime(2025, 3, 4)
    
    def _extract_time_info(self, title: str) -> Dict[str, Any]:
        """과목명에서 요일과 시간 정보 추출"""
        time_info = {
            "day": None,
            "start_time": None,
            "end_time": None
        }
        
        # 요일 매핑
        day_map = {
            "월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6
        }
        
        try:
            # 괄호 안의 시간 정보 추출
            if "(" in title and ")" in title:
                time_str = title[title.find("(")+1:title.find(")")]
                parts = time_str.split()
                
                # 요일 추출
                for day in day_map.keys():
                    if day in time_str:
                        time_info["day"] = day_map[day]
                        break
                
                # 시간 추출
                if len(parts) >= 2:
                    time_parts = parts[1].split("-")
                    if len(time_parts) == 2:
                        time_info["start_time"] = time_parts[0].strip()
                        time_info["end_time"] = time_parts[1].strip()
        except:
            pass
        
        return time_info
    
    def _calculate_week_dates(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """주차별 실제 날짜 계산"""
        time_info = self._extract_time_info(course["title"])
        if time_info["day"] is None:
            return course
        
        # 해당 요일의 첫 수업일 계산
        first_class_date = self.base_date + timedelta(days=(time_info["day"] - self.base_date.weekday()) % 7)
        
        # 주차별 날짜 계산 및 weeks 통합
        if "weeks" in course and "weeks" in course["weeks"]:
            updated_weeks = []
            for week in course["weeks"]["weeks"]:
                if "주차" in week["title"]:
                    try:
                        week_num = int(week["title"].split("주차")[0].strip())
                        # (주차 - 1) * 7일을 더해서 해당 주차의 날짜 계산
                        week_date = first_class_date + timedelta(days=(week_num - 1) * 7)
                        
                        # 주차 정보에 날짜 정보 추가
                        week["date"] = week_date.strftime("%Y-%m-%d")
                        week["day_of_week"] = ["월", "화", "수", "목", "금", "토", "일"][week_date.weekday()]
                        week["start_time"] = time_info["start_time"]
                        week["end_time"] = time_info["end_time"]
                    except:
                        pass
                updated_weeks.append(week)
            
            course["weeks"]["weeks"] = updated_weeks
        
        return course
    
    def _load_json(self) -> Dict[str, Any]:
        """JSON 파일 로드"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"JSON 파일 로드 실패: {e}")
            return {}
    
    def _sort_weeks(self, weeks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """주차 정보 정렬"""
        # 주차 번호 추출 함수
        def get_week_number(week_title: str) -> int:
            if "주차" in week_title:
                try:
                    return int(week_title.split("주차")[0].strip())
                except:
                    return 0
            return 0
        
        # 주차별로 정렬
        sorted_weeks = sorted(weeks, key=lambda x: get_week_number(x["title"]))
        
        # 강의 개요는 항상 첫 번째로
        overview = next((week for week in sorted_weeks if week["title"] == "강의 개요"), None)
        if overview:
            sorted_weeks.remove(overview)
            sorted_weeks.insert(0, overview)
        
        return sorted_weeks
    
    def _clean_activities(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """활동 정보 정리"""
        if "weeks" in course and "weeks" in course["weeks"]:
            for week in course["weeks"]["weeks"]:
                # 빈 활동 제거
                week["activities"] = [activity for activity in week["activities"] if activity]
                
                # 과제 상태 정보 정리
                if "assignment_status" in week:
                    if isinstance(week["assignment_status"], dict) and "error" in week["assignment_status"]:
                        week["assignment_status"] = {
                            "status": "error",
                            "message": week["assignment_status"]["error"]
                        }
        
        return course
    
    def _process_video_attendance(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """동영상 출석 정보 처리"""
        if "weeks" in course and "video_attendance" in course["weeks"]:
            for video in course["weeks"]["video_attendance"]:
                # 기간 정보 파싱
                if "period" in video:
                    try:
                        period_parts = video["period"].split("~")
                        if len(period_parts) == 2:
                            start_date = period_parts[0].strip()
                            end_parts = period_parts[1].split("(")
                            end_date = end_parts[0].strip()
                            
                            video["start_date"] = start_date
                            video["end_date"] = end_date
                            
                            if len(end_parts) > 1:
                                late_date = end_parts[1].replace("지각 :", "").replace(")", "").strip()
                                video["late_date"] = late_date
                    except:
                        pass
        
        return course
    
    def _process_notices(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """공지사항 처리"""
        if "notices" in course:
            # 공지사항 정렬 (최신순)
            course["notices"].sort(key=lambda x: x.get("title", ""), reverse=True)
            
            # 중복 제거
            seen_titles = set()
            course["notices"] = [
                notice for notice in course["notices"]
                if notice["title"] not in seen_titles and not seen_titles.add(notice["title"])
            ]
        
        return course
    
    def process(self) -> Dict[str, Any]:
        """전체 데이터 처리"""
        if not self.raw_data:
            return {}
        
        processed_data = {
            "user": self.raw_data.get("user", {}),
            "courses": []
        }
        
        for course in self.raw_data.get("courses", []):
            # 주차 정보 정렬
            if "weeks" in course and "weeks" in course["weeks"]:
                course["weeks"]["weeks"] = self._sort_weeks(course["weeks"]["weeks"])
            
            # 활동 정보 정리
            course = self._clean_activities(course)
            
            # 동영상 출석 정보 처리
            course = self._process_video_attendance(course)
            
            # 공지사항 처리
            course = self._process_notices(course)
            
            # 주차별 날짜 계산
            course = self._calculate_week_dates(course)
            
            processed_data["courses"].append(course)
        
        self.processed_data = processed_data
        return processed_data
    
    def save_processed_data(self, output_path: str = None):
        """처리된 데이터 저장"""
        if not self.processed_data:
            self.process()
        
        if not output_path:
            # 원본 파일명에 _processed 추가
            base, ext = os.path.splitext(self.json_path)
            output_path = f"{base}_processed{ext}"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data, f, ensure_ascii=False, indent=2)
            print(f"처리된 데이터가 저장되었습니다: {output_path}")
        except Exception as e:
            print(f"데이터 저장 실패: {e}")

    def load_course_names(self, course_names: List[str]):
        """과목명 데이터 로드"""
        self.course_names = {name: True for name in course_names}
        
    def find_course_by_abbreviation(self, query: str, threshold: float = 0.15) -> List[Tuple[str, float]]:
        """축약어로 과목 검색"""
        if not self.course_names:
            raise ValueError("과목명 데이터가 로드되지 않았습니다.")
            
        matches = self.find_best_matches(query, list(self.course_names.keys()))
        
        # threshold보다 높은 유사도를 가진 결과만 반환
        return [(name, score) for name, score in matches if score > threshold]

class SimilarityMatcher:
    def __init__(self):
        self.course_vectors = {}  # 과목명 벡터 저장
        self.course_names = {}    # 원본 과목명 저장
        
    def get_initials(self, text: str) -> str:
        """한글 문자열에서 초성을 추출"""
        CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        result = ""
        for char in text:
            if '가' <= char <= '힣':
                char_code = ord(char) - ord('가')
                initial_index = char_code // (21 * 28)
                result += CHOSUNG_LIST[initial_index]
            else:
                result += char.lower()
        return result

    def calculate_initial_similarity(self, query: str, target: str) -> float:
        """초성 유사도 계산"""
        query_initials = self.get_initials(query)
        target_initials = self.get_initials(target)
        
        # 초성 길이가 같은 경우 가중치 부여
        length_bonus = 1.0 if len(query_initials) == len(target_initials) else 0.8
        
        # 공통 초성 비율 계산
        common_chars = set(query_initials) & set(target_initials)
        similarity = len(common_chars) / max(len(query_initials), len(target_initials))
        
        return similarity * length_bonus

    def calculate_ngram_similarity(self, query: str, target: str, n: int = 2) -> float:
        """n-gram 유사도 계산"""
        def get_ngrams(text: str, n: int) -> List[str]:
            return [text[i:i+n] for i in range(len(text)-n+1)]
        
        query_ngrams = get_ngrams(query, n)
        target_ngrams = get_ngrams(target, n)
        
        if not query_ngrams or not target_ngrams:
            return 0.0
            
        common_ngrams = set(query_ngrams) & set(target_ngrams)
        return len(common_ngrams) / max(len(query_ngrams), len(target_ngrams))

    def calculate_length_ratio(self, query: str, target: str) -> float:
        """문자열 길이 비율 계산"""
        min_len = min(len(query), len(target))
        max_len = max(len(query), len(target))
        return min_len / max_len

    def calculate_similarity(self, query: str, target: str) -> float:
        """통합 유사도 계산"""
        # 초성 유사도 (높은 가중치)
        initial_sim = self.calculate_initial_similarity(query, target)
        
        # n-gram 유사도
        bigram_sim = self.calculate_ngram_similarity(query, target, n=2)
        trigram_sim = self.calculate_ngram_similarity(query, target, n=3)
        
        # 길이 비율
        length_ratio = self.calculate_length_ratio(query, target)
        
        # 가중치 조정
        weights = {
            'initial': 0.6,    # 초성 매칭 가중치 증가
            'bigram': 0.15,    # 바이그램 유사도
            'trigram': 0.15,   # 트라이그램 유사도
            'length': 0.1      # 길이 비율
        }
        
        # 초성이 정확히 일치하는 경우 보너스 점수
        if initial_sim == 1.0:
            initial_sim *= 1.5
        
        final_score = (
            weights['initial'] * initial_sim +
            weights['bigram'] * bigram_sim +
            weights['trigram'] * trigram_sim +
            weights['length'] * length_ratio
        )
        
        return min(1.0, final_score)  # 최대 1.0으로 제한

    def find_best_matches(self, query: str, course_names: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """주어진 쿼리에 대해 가장 유사한 과목명 찾기"""
        similarities = []
        
        for course_name in course_names:
            score = self.calculate_similarity(query, course_name)
            similarities.append((course_name, score))
        
        # 유사도 점수로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]

if __name__ == "__main__":
    # 사용 예시
    preprocessor = CoursePreprocessor("user_data/kangnam_courses.json")
    processed_data = preprocessor.process()
    preprocessor.save_processed_data() 