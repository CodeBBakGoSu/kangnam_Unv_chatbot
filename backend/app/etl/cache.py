import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# 캐시 디렉토리 설정
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def save_user_data_to_cache(username: str, data: Dict[str, Any]) -> None:
    """사용자 데이터를 캐시에 저장"""
    try:
        # 저장할 파일 경로
        filepath = os.path.join(CACHE_DIR, f"user_{username}.json")
        
        # 타임스탬프 추가
        data_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # JSON으로 저장
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_with_timestamp, f, ensure_ascii=False, indent=2)
            
        # 과목 정보 별도 저장 (빠른 조회용)
        if "courses" in data:
            courses_filepath = os.path.join(CACHE_DIR, f"user_{username}_courses.json")
            with open(courses_filepath, "w", encoding="utf-8") as f:
                json.dump(data["courses"], f, ensure_ascii=False, indent=2)
                
        print(f"사용자 {username}의 데이터가 캐시되었습니다.")
    except Exception as e:
        print(f"캐시 저장 중 오류 발생: {str(e)}")

def get_user_data_from_cache(username: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
    """캐시에서 사용자 데이터 조회 (최대 나이 제한)"""
    try:
        filepath = os.path.join(CACHE_DIR, f"user_{username}.json")
        
        # 파일이 없으면 None 반환
        if not os.path.exists(filepath):
            return None
            
        # 파일 읽기
        with open(filepath, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
            
        # 타임스탬프 확인
        timestamp = datetime.fromisoformat(cached_data["timestamp"])
        now = datetime.now()
        age = now - timestamp
        
        # 최대 나이 확인
        if age > timedelta(hours=max_age_hours):
            print(f"캐시된 데이터가 너무 오래됨: {age.total_seconds() / 3600:.1f}시간")
            return None
            
        return cached_data["data"]
    except Exception as e:
        print(f"캐시 조회 중 오류 발생: {str(e)}")
        return None

def clear_user_cache(username: str) -> bool:
    """사용자 캐시 삭제"""
    try:
        filepath = os.path.join(CACHE_DIR, f"user_{username}.json")
        courses_filepath = os.path.join(CACHE_DIR, f"user_{username}_courses.json")
        
        # 파일 삭제
        if os.path.exists(filepath):
            os.remove(filepath)
            
        if os.path.exists(courses_filepath):
            os.remove(courses_filepath)
            
        return True
    except Exception as e:
        print(f"캐시 삭제 중 오류 발생: {str(e)}")
        return False 