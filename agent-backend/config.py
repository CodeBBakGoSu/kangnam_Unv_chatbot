"""
환경 변수 설정
"""

import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 개발 시)
load_dotenv()

# Agent Engine 설정
AGENT_RESOURCE_ID = os.getenv(
    "AGENT_RESOURCE_ID",
    "projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664"
)

# Google Cloud 설정
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-east4")

# 환경 확인
def check_config():
    """환경 변수 확인"""
    required_vars = {
        "AGENT_RESOURCE_ID": AGENT_RESOURCE_ID,
        "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
        "VERTEX_AI_LOCATION": VERTEX_AI_LOCATION,
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return required_vars

