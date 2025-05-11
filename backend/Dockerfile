FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run은 PORT 환경변수를 자동으로 제공함
ENV HOST=0.0.0.0
# $PORT 환경변수 사용
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"] 