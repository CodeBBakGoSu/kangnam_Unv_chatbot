#!/bin/bash

# NGINX 시작
service nginx start

# 백엔드 API 서버 시작
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Streamlit 앱 시작
cd /app/streamlit
streamlit run app.py --server.port 8501 --server.enableCORS false &

# 로그 출력을 위해 대기 
tail -f /var/log/nginx/access.log 