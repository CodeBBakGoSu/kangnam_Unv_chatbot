import logging
import os
import sys
from datetime import datetime

# 로그 디렉토리 설정
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

# 로그 파일 경로
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

# 로거 설정
logger = logging.getLogger("kangnam_chatbot")
logger.setLevel(logging.DEBUG)

# 파일 핸들러
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 로그 포맷 설정
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# 핸들러 추가
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 로깅 함수 (편의를 위해)
def info(msg, *args, **kwargs):
    return logger.info(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    return logger.error(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    return logger.debug(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    return logger.warning(msg, *args, **kwargs) 