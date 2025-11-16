import os
import json
import asyncio
import tempfile
from typing import Dict, Any, Optional, List

from app.etl.kangnam_login import fetch_all_course_data
from app.etl.cache import save_user_data_to_cache
from app.etl.course_preprocessor import CoursePreprocessor
from app.etl.chunk_generator import generate_chunks_from_processed_data, save_chunks_to_file
from app.etl.supabase_pipeline import initialize_supabase_client, insert_chunks_to_supabase

# 향후 추가될 임포트
# from app.etl.course_preprocessor import CoursePreprocessor
# from app.etl.chunk_generator import extract_chunks_from_course
# from app.etl.supabase_pipeline import initialize_supabase_client, generate_embedding, insert_chunks_to_supabase

async def run_etl_pipeline(username: str, password: str) -> Dict[str, Any]:
    """
    로그인 시 실행되는 전체 ETL 파이프라인
    1. 강남대 이러닝에서 데이터 크롤링
    2. 데이터 전처리
    3. 청크 생성
    4. 벡터 DB에 저장
    
    Returns:
        Dict[str, Any]: 파이프라인 실행 결과
    """
    result = {
        "success": False,
        "message": "",
        "step": "init",
        "user_data": None
    }
    
    try:
        # 1. 데이터 크롤링
        result["step"] = "crawling"
        raw_data = await fetch_all_course_data(username, password)
        
        if "error" in raw_data:
            result["message"] = f"크롤링 실패: {raw_data['error']}"
            return result
            
        # 사용자 기본 정보 추출 (API 응답용)
        basic_user_data = {
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
            basic_user_data["courses"].append(course_info)
        
        # 캐시에 저장 (로그인 시 사용)
        save_user_data_to_cache(username, basic_user_data)
        
        # 2. 데이터 전처리
        result["step"] = "preprocessing"
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as raw_file:
            json.dump(raw_data, raw_file, ensure_ascii=False, indent=2)
            raw_file_path = raw_file.name
            
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as processed_file:
            processed_file_path = processed_file.name
        
        # 전처리 실행
        preprocessor = CoursePreprocessor(raw_data)  # 파일 대신 데이터 직접 전달
        processed_data = preprocessor.process()
        
        # 전처리된 데이터 임시 저장
        with open(processed_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
        # 3. 청크 생성
        result["step"] = "chunking"
        all_chunks = generate_chunks_from_processed_data(processed_data)
        
        # 4. 벡터 DB에 저장
        result["step"] = "embedding"
        
        # 청크를 Supabase에 삽입
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as chunks_file:
            json.dump(all_chunks, chunks_file, ensure_ascii=False, indent=2)
            chunks_file_path = chunks_file.name
            
        # Supabase에 청크 삽입
        success = insert_chunks_to_supabase(all_chunks, username)
        
        if not success:
            result["message"] = "벡터 DB 저장 실패"
            result["success"] = False
            result["user_data"] = basic_user_data
            return result
            
        # 임시 파일 삭제
        for file_path in [raw_file_path, processed_file_path, chunks_file_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        # 파이프라인 완료
        result["success"] = True
        result["message"] = "ETL 파이프라인 실행 완료"
        result["user_data"] = basic_user_data
        
        return result
        
    except Exception as e:
        result["message"] = f"ETL 파이프라인 실행 중 오류 발생: {str(e)}"
        return result 