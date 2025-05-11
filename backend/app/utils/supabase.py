from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import os

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 임베딩 모델 초기화
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def get_relevant_chunks(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """벡터 DB에서 관련 청크 검색"""
    try:
        # 쿼리 텍스트를 임베딩으로 변환
        query_embedding = embedding_model.encode(query).tolist()
        
        # 벡터 검색 쿼리
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

def find_most_similar_course(query: str) -> str:
    """유사도 기반으로 가장 유사한 과목명 찾기"""
    if not query:
        return None
        
    try:
        # 임베딩 기반 검색
        query_embedding = embedding_model.encode(query).tolist()
        
        response = supabase.rpc(
            'match_course_name',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': 1
            }
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['original_name']
        
        return None
    except Exception as e:
        print(f"과목명 검색 중 오류 발생: {e}")
        return None 