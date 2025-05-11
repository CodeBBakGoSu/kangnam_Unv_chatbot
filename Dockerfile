FROM python:3.9-slim

WORKDIR /app

# 의존성 복사 및 설치
COPY backend/requirements.txt backend-requirements.txt
COPY streamlit/requirements.txt streamlit-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt -r streamlit-requirements.txt

# 백엔드 복사
COPY backend/ backend/

# 스트림릿 복사
COPY streamlit/ streamlit/

# Supervisor 설치 및 설정
RUN apt-get update && apt-get install -y supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 환경변수 설정
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 포트 노출
EXPOSE 8000 8501

# Supervisor로 두 서비스 동시 실행
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 