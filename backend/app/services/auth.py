from typing import Dict, Any, Optional
from app.utils.jwt import create_access_token
from app.etl.kangnam_login import login_ecampus, get_user_info, get_course_list, fetch_all_course_data
from app.etl.cache import get_user_data_from_cache, save_user_data_to_cache, clear_user_cache
from app.etl.pipeline import run_etl_pipeline
from app.etl.supabase_pipeline import clean_user_data, get_user_chunks_count
import json
import os
import asyncio
from datetime import datetime, timedelta
from app.config import settings
from app.utils.logger import logger

async def authenticate_user(username: str, password: str, run_etl: bool = False):
    """
    사용자 인증 및 토큰 발급
    
    - username: 학번
    - password: 비밀번호
    - run_etl: ETL 파이프라인 실행 여부
    
    반환: 사용자 정보 (dict) 또는 None (인증 실패 시)
    """
    try:
        # 캐시 디렉토리 확인
        cache_dir = os.path.join(settings.BACKEND_DIR, "app", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # 사용자 캐시 파일 경로
        cache_file = os.path.join(cache_dir, f"user_{username}.json")
        
        # 캐시 파일이 존재하고 최신 상태인지 확인
        cache_valid = False
        user_data = None
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    
                # 캐시 타임스탬프 확인 (24시간 이내)
                timestamp = cached_data.get("timestamp")
                if timestamp:
                    cache_time = datetime.fromisoformat(timestamp)
                    if datetime.now() - cache_time < timedelta(hours=24):
                        cache_valid = True
                        user_data = cached_data.get("data")
                        logger.info(f"캐시된 사용자 데이터를 사용합니다: {username}")
            except Exception as e:
                logger.error(f"캐시 파일 읽기 오류: {str(e)}")
        
        # 캐시가 유효하지 않은 경우 LMS에서 데이터 가져오기
        if not cache_valid:
            # LMS 로그인 및 데이터 수집
            logger.info(f"LMS에 로그인합니다: {username}")
            
            # kangnam_login.py의 함수 사용하여 로그인
            session = await login_ecampus(username, password)
            
            if not session:
                logger.error(f"LMS 로그인 실패: {username}")
                return None
            
            # 사용자 정보 및 과목 정보 가져오기
            user_info = await get_user_info(session)
            courses = await get_course_list(session)
            
            # 세션 종료
            await session.close()
            
            # 사용자 데이터 구성
            user_data = {
                "username": username,
                "name": user_info.get("name", ""),
                "department": user_info.get("department", ""),
                "courses": courses
            }
            
            # 캐시에 저장
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"timestamp": datetime.now().isoformat(), "data": user_data}, f, ensure_ascii=False)
            
            logger.info(f"사용자 {username}의 데이터가 캐시되었습니다.")
        
        # 새 사용자 여부 확인 (상세 데이터 파일 존재 확인)
        user_data_dir = os.path.join(settings.BASE_DIR, "user_data")
        detailed_data_file = os.path.join(user_data_dir, f"kangnam_courses_{username}.json")
        is_new_user = not os.path.exists(detailed_data_file)
        
        # 청크 수 확인 (벡터 DB에 데이터가 있는지)
        chunks_count = get_user_chunks_count(username)
        has_vector_data = chunks_count > 0
        
        logger.info(f"사용자 {username} - 파일 존재: {not is_new_user}, 벡터 데이터: {has_vector_data}, 청크 수: {chunks_count}")
        
        # 새 사용자이거나 벡터 데이터가 없는 경우 또는 명시적 ETL 요청이 있는 경우 - 동기적으로 처리
        if (is_new_user or not has_vector_data or run_etl) and (run_etl or settings.AUTO_RUN_ETL_FOR_NEW_USERS):
            logger.info(f"사용자 {username}의 ETL 파이프라인을 시작합니다.")
            
            # ETL 파이프라인 동기적으로 실행
            etl_result = await run_etl_pipeline(username, password)
            
            logger.info(f"ETL 파이프라인 결과: {etl_result}")
            
            # 이 시점에서 다시 벡터 데이터 체크
            chunks_count = get_user_chunks_count(username)
            has_vector_data = chunks_count > 0
            
            # 사용자에게 보여줄 상태 정보 추가
            if user_data:
                user_data["etl_status"] = "ready" if has_vector_data else "error"
                user_data["has_vector_data"] = has_vector_data
                user_data["chunks_count"] = chunks_count
                
        elif has_vector_data:
            # 이미 데이터가 있는 경우
            if user_data:
                user_data["etl_status"] = "ready"
                user_data["has_vector_data"] = True
                user_data["chunks_count"] = chunks_count
        
        return user_data
    except Exception as e:
        logger.error(f"사용자 인증 중 오류 발생: {str(e)}")
        logger.exception(e)  # 스택 트레이스 로깅
        return None

async def run_etl_pipeline(username: str, password: str):
    """ETL 파이프라인 실행 - 동기적으로 모든 단계 완료"""
    try:
        logger.info(f"ETL 파이프라인 시작: {username}")
        
        # 1. 상세 데이터 크롤링
        logger.info(f"[1/3] 사용자 {username}의 데이터 크롤링 시작")
        user_data_dir = os.path.join(settings.BASE_DIR, "user_data")
        os.makedirs(user_data_dir, exist_ok=True)
        
        # 크롤링 실행 - 직접 fetch_all_course_data 함수 호출
        raw_data = await fetch_all_course_data(username, password)
        
        if "error" in raw_data:
            logger.error(f"크롤링 실패: {raw_data['error']}")
            return {"success": False, "message": f"크롤링 오류: {raw_data['error']}", "step": "crawling"}
        
        # 크롤링 데이터 저장
        output_file = os.path.join(user_data_dir, f"kangnam_courses_{username}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"크롤링 데이터 저장 완료: {output_file}")
        
        # 2. 데이터 전처리 및 청크 생성
        logger.info(f"[2/3] 사용자 {username}의 데이터 전처리 및 청크 생성 시작")
        from app.etl.supabase_pipeline import process_user_data
        
        # 생성된 파일에서 데이터 처리
        if os.path.exists(output_file):
            # 기존 벡터 데이터 삭제 (새로 생성하기 위해)
            clean_user_data(username)
            
            # 데이터 처리 및 청크 생성, Supabase에 저장
            process_result = process_user_data(username, output_file)
            
            if not process_result:
                logger.error(f"데이터 처리 실패")
                return {"success": False, "message": "데이터 처리 실패", "step": "processing"}
                
            # 처리 후 청크 수 확인
            chunks_count = get_user_chunks_count(username)
            logger.info(f"사용자 {username}의 데이터 처리 완료. 생성된 청크 수: {chunks_count}")
            
            return {
                "success": True, 
                "message": f"ETL 파이프라인 완료. 생성된 청크 수: {chunks_count}", 
                "step": "complete",
                "chunks_count": chunks_count
            }
        else:
            logger.error(f"크롤링된 데이터 파일을 찾을 수 없음: {output_file}")
            return {"success": False, "message": "크롤링 데이터 파일 없음", "step": "processing"}
                
    except Exception as e:
        logger.error(f"ETL 파이프라인 실행 중 오류: {str(e)}")
        logger.exception(e)  # 스택 트레이스 로깅
        return {"success": False, "message": f"ETL 오류: {str(e)}", "step": "unknown"}

async def get_user_courses(username: str) -> list:
    """
    사용자의 수강 과목 정보 조회 (캐시된 정보 활용)
    """
    # 캐시된 정보 확인 (로그인 시 이미 가져온 정보)
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "cache", f"user_{username}_courses.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"캐시된 과목 정보 로드 중 오류: {str(e)}")
    
    # 캐시가 없으면 기본 정보 반환
    test_courses = [
        {
            "title": "캡스톤디자인(SW)I",
            "professor": "최인엽",
            "class_time": "화 13:00-15:50",
            "room": "이공관 401호"
        },
        {
            "title": "AIoT소프트웨어[00]",
            "professor": "김교수",
            "class_time": "금 11:50-14:30",
            "room": "이공관 305호"
        }
    ]
    
    return test_courses

async def refresh_user_data(username: str, password: str, run_full_etl: bool = True) -> Dict[str, Any]:
    """
    사용자 데이터 강제 갱신 (캐시 삭제 후 재로그인)
    
    Args:
        username: 학번
        password: 비밀번호
        run_full_etl: 전체 ETL 파이프라인 실행 여부 (True: 청크 생성 및 벡터DB 저장까지, False: 사용자 정보만 갱신)
    
    Returns:
        Dict[str, Any]: 갱신 결과 정보
    """
    try:
        logger.info(f"사용자 {username}의 데이터 갱신 시작")
        
        # 기존 캐시 삭제
        clear_user_cache(username)
        
        # 데이터 관리 정책: 갱신 전 기존 벡터 데이터 삭제
        if run_full_etl:
            try:
                logger.info(f"데이터 갱신 전 기존 벡터 데이터 정리 시도...")
                clean_user_data(username)
            except Exception as e:
                logger.error(f"기존 데이터 정리 중 오류 (계속 진행): {str(e)}")
        
        if run_full_etl:
            logger.info(f"사용자 {username}의 전체 ETL 파이프라인 실행 시작")
            
            # 전체 ETL 파이프라인 동기적으로 실행
            etl_result = await run_etl_pipeline(username, password)
            
            # ETL 실패한 경우
            if not etl_result["success"]:
                error_msg = f"ETL 파이프라인 실패: {etl_result['message']} (단계: {etl_result['step']})"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "step": etl_result["step"]
                }
            
            # 처리 결과
            logger.info(f"ETL 파이프라인 실행 완료: {etl_result['message']}")
            return {
                "success": True,
                "message": etl_result["message"],
                "chunks_count": etl_result.get("chunks_count", 0)
            }
        else:
            logger.info(f"사용자 {username}의 기본 정보만 갱신 시작")
            
            # 사용자 정보만 갱신 - 크롤링만 수행
            raw_data = await fetch_all_course_data(username, password)
            
            if "error" in raw_data:
                error_msg = f"사용자 데이터 조회 실패: {raw_data['error']}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # 사용자 정보 구성
            user_data = {
                "username": username,
                "name": raw_data["user"]["name"],
                "department": raw_data["user"]["department"],
                "courses": []
            }
            
            # 과목 정보 가공
            for course in raw_data["courses"]:
                course_info = {
                    "title": course["title"],
                    "professor": course["professor"]
                }
                user_data["courses"].append(course_info)
            
            # 결과 캐시에 저장
            save_user_data_to_cache(username, user_data)
            logger.info(f"사용자 {username}의 기본 정보 갱신 완료")
            
            return {
                "success": True,
                "message": "기본 정보 갱신 완료"
            }
        
    except Exception as e:
        logger.error(f"데이터 갱신 중 오류 발생: {str(e)}")
        logger.exception(e)
        # 오류 정보 반환
        return {
            "success": False,
            "message": f"데이터 갱신 중 오류: {str(e)}"
        } 