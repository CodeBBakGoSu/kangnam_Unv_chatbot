# test_rag/config/__init__.py

"""
Configuration settings for the RAG Agent.

These settings are used by the various RAG tools.
Vertex AI initialization is performed in the package's __init__.py
"""

import os
from dotenv import load_dotenv

# Load environment variables (this is redundant if __init__.py is imported first,
# but included for safety when importing config directly)
load_dotenv()

# Project and location settings
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "kangnam-backend")  # ✅ 프로젝트 이름

# Vertex AI location (RAG Engine, Embeddings, LLM)
# Note: Vertex AI RAG Engine is only available in limited regions
VERTEX_AI_LOCATION = os.environ.get("VERTEX_AI_LOCATION", "us-east4")  # ✅ us-east4로 변경!
LOCATION = VERTEX_AI_LOCATION  # Alias for backward compatibility

# GCS Bucket settings (can be in different region from Vertex AI)
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "kangnam-univ")  # RAG documents bucket
GCS_BUCKET_LOCATION = os.environ.get("GCS_BUCKET_LOCATION", "asia-northeast3")  # Seoul region

# RAG Corpus settings - 강남대 코퍼스
KANGNAM_CORPUS_ID = os.environ.get("KANGNAM_CORPUS_ID", "6917529027641081856")  # ✅ 코퍼스 ID
KANGNAM_CORPUS_NAME = "kangnamUniv"

# RAG configuration defaults
RAG_DEFAULT_EMBEDDING_MODEL = "text-multilingual-embedding-002"  # ✅ 다국어 임베딩 모델!
RAG_DEFAULT_TOP_K = 10  # Number of results to return for a single query
RAG_DEFAULT_SEARCH_TOP_K = 5  # Number of results per corpus for multi-corpus search
RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD = 0.5  # Similarity threshold
RAG_DEFAULT_PAGE_SIZE = 50  # Default pagination size for listing operations

# RAG settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-multilingual-embedding-002"  # ✅ 변경!
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = 1000

# GCS configuration defaults
GCS_DEFAULT_STORAGE_CLASS = "STANDARD"  # Standard storage class for buckets
GCS_DEFAULT_LOCATION = GCS_BUCKET_LOCATION  # Seoul region for data storage
GCS_DEFAULT_CONTENT_TYPE = "application/pdf"  # Default content type for uploads
GCS_LIST_BUCKETS_MAX_RESULTS = 50  # Max results for bucket listing
GCS_LIST_BLOBS_MAX_RESULTS = 100  # Max results for blob listing

# Logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"