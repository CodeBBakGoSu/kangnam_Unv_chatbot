FROM python:3.9-slim

WORKDIR /app

# 캐시 무효화를 위한 환경변수 추가
ARG CACHEBUST=1

# 먼저 필요한 패키지만 설치
COPY requirements.txt .
RUN pip install --no-cache-dir huggingface_hub==0.16.4
RUN pip install --no-cache-dir transformers==4.30.2
RUN pip install --no-cache-dir -r requirements.txt

# 모델 사전 다운로드를 위한 스크립트 생성
RUN echo 'from sentence_transformers import SentenceTransformer\n\
# all-MiniLM-L6-v2 모델 미리 다운로드\n\
model1 = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")\n\
# 한국어 모델 미리 다운로드\n\
model2 = SentenceTransformer("jhgan/ko-sroberta-multitask")\n\
print("모델 다운로드 완료")' > /app/download_models.py

# 모델 사전 다운로드 실행
RUN python /app/download_models.py

# 나머지 코드 복사
COPY . .

# Cloud Run은 PORT 환경변수를 자동으로 제공함
ENV HOST=0.0.0.0
# $PORT 환경변수 사용
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]