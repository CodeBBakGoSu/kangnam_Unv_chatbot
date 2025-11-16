# 강남대학교 교수정보 RAG 설정 가이드

교수 정보 Agent가 작동하도록 RAG 코퍼스를 설정하는 방법입니다.

---

## 📋 목차
1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [설정 단계](#설정-단계)
4. [테스트](#테스트)
5. [문제 해결](#문제-해결)

---

## 🎯 개요

교수정보 Agent는 다음 정보를 검색할 수 있습니다:
- ✅ 교수 이름, 소속 대학/학과
- ✅ 연락처 (이메일, 전화번호)
- ✅ 연구실 위치
- ✅ 연구분야 및 키워드
- ✅ 담당 과목
- ✅ 학위 정보

**8개 대학 데이터:**
- 공과대학, 글로벌문화콘텐츠대학, 법행정세무학부
- 사범대학, 사회복지학과, 상경학부
- 시니어비즈니스학과, 예체능대학

---

## 🔧 사전 준비

### 1. GCP 인증
```bash
gcloud auth application-default login
```

### 2. 필요한 권한
- Vertex AI User
- Storage Object Admin

### 3. API 활성화 확인
- Vertex AI API
- Cloud Storage API

---

## 🚀 설정 단계

### Step 1: 코퍼스 생성

```bash
cd /Users/hong-gihyeon/Desktop/cap
python goole_adk/data/교수정보/create_professor_corpus.py
```

**출력 예시:**
```
✅ 코퍼스 생성 완료!

📋 코퍼스 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   이름: 강남대학교_교수정보
   ID: 1234567890123456789
   전체 경로: projects/kangnam-backend/locations/us-east4/ragCorpora/1234567890123456789
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 2: 코퍼스 ID 설정 (2곳)

#### 2-1. `upload_professors_to_rag.py` 파일 수정
```python
# 🔴 이 줄을 찾아서
CORPUS_ID = "YOUR_NEW_CORPUS_ID"

# ✅ 복사한 ID로 변경
CORPUS_ID = "1234567890123456789"
```

#### 2-2. `goole_adk/agents/professor/tools/search_tools.py` 파일 수정
```python
# 🔴 이 줄을 찾아서
PROFESSOR_CORPUS_ID = "YOUR_PROFESSOR_CORPUS_ID"

# ✅ 복사한 ID로 변경
PROFESSOR_CORPUS_ID = "1234567890123456789"
```

### Step 3: 교수정보 업로드

```bash
python goole_adk/data/교수정보/upload_professors_to_rag.py
```

**처리 과정:**
1. 8개 JSONL 파일 확인 및 통계 수집
2. GCS `gs://kangnam-univ/rag_data/professors/`에 업로드
3. Vertex AI RAG 코퍼스에 import
4. 임베딩 생성 (5-10분 소요)

**출력 예시:**
```
📊 데이터 통계 수집 중...
   공과대학:
      교수: 54명
      인덱스: 11개
      합계: 65개
   ...
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   전체 교수: 200명
   전체 인덱스: 30개
   총 항목: 230개
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 4: 완료 대기

⏳ **5-10분** 대기 (임베딩 생성 시간)

---

## 🧪 테스트

### Agent 실행

```bash
cd /Users/hong-gihyeon/Desktop/cap
adk run goole_adk
```

### 테스트 쿼리

```
💬 사용자: 인공지능 교수님 알려줘

🤖 Agent: [professor_agent가 검색 수행]
   공과대학 인공지능전공 교수님들:
   
   1. 양재형 교수님
      - 이메일: jhyang@kangnam.ac.kr
      - 전화: 031-280-3757
      - 연구실: 이공관519
      ...
```

### 다양한 검색 예시

| 질문 유형 | 예시 쿼리 |
|----------|----------|
| 이름 검색 | "김철주 교수님 알려줘" |
| 학과 검색 | "공과대학 교수님들 누구야?" |
| 연구분야 검색 | "VR 연구하시는 교수님 찾아줘" |
| 연락처 문의 | "양재형 교수님 연구실 어디야?" |
| 전공 검색 | "인공지능전공 교수님 누구세요?" |

---

## 🔍 데이터 구조

### JSONL 파일 형식

```json
{
  "id": "prof-ai-0000",
  "title": "김철주 교수 | 인공지능전공 | 종합 정보",
  "text": "김철주 교수. 연락처: 031-280-3684, ...",
  "metadata": {
    "name_ko": "김철주",
    "email": "kcjoo@kangnam.ac.kr",
    "phone": "031-280-3684",
    "office": "천은관 503호",
    "college": "공과대학",
    "department": "인공지능전공",
    "keywords": ["인공지능", "딥러닝"],
    "courses": ["AI개론", "딥러닝"],
    "professor_id": "prof-ai-0000"
  }
}
```

### 인덱스 항목 (org_index)

```json
{
  "id": "org-idx-eng-ai-2025",
  "title": "공과대학 | 인공지능전공 | 교수 명단 인덱스",
  "text": "공과대학 인공지능전공 교수 명단: 김철주, ...",
  "metadata": {
    "entity": "org_index",
    "college": "공과대학",
    "department": "인공지능전공",
    "professor_names": ["김철주", "..."],
    "professor_ids": ["prof-ai-0000", "..."]
  }
}
```

---

## 🛠 문제 해결

### 1. "코퍼스가 설정되지 않았습니다" 에러

**원인:** `PROFESSOR_CORPUS_ID`가 설정되지 않음

**해결:**
1. `create_professor_corpus.py` 실행
2. 출력된 코퍼스 ID 복사
3. `search_tools.py`의 `PROFESSOR_CORPUS_ID` 변수에 입력

### 2. "검색 결과가 없습니다"

**원인:** 임베딩 생성이 완료되지 않음

**해결:**
- 5-10분 대기 후 재시도
- Vertex AI Console에서 코퍼스 상태 확인

### 3. GCS 업로드 실패

**원인:** 권한 또는 버킷 문제

**해결:**
```bash
# 버킷 존재 확인
gsutil ls gs://kangnam-univ/

# 권한 확인
gcloud projects get-iam-policy kangnam-backend
```

### 4. Import 타임아웃

**원인:** 데이터가 많아 처리 시간 초과

**해결:**
- 백그라운드에서 계속 처리 중
- 10-15분 후 다시 확인
- 에러가 아닌 정상 동작

---

## 📊 파일 목록

```
goole_adk/data/교수정보/
├── README.md                       # 이 파일
├── create_professor_corpus.py      # 코퍼스 생성
├── upload_professors_to_rag.py     # 데이터 업로드
├── 공과대학.jsonl                   # 교수 데이터 (65개)
├── 글로벌문화콘텐츠대학.jsonl        # 교수 데이터 (29개)
├── 법행정세무학부.jsonl             # 교수 데이터 (23개)
├── 사범대학.jsonl                   # 교수 데이터 (46개)
├── 사회복지학과.jsonl               # 교수 데이터 (39개)
├── 상경학부.jsonl                   # 교수 데이터 (37개)
├── 시니어비즈니스학과.jsonl         # 교수 데이터 (7개)
└── 예체능대학.jsonl                 # 교수 데이터 (23개)
```

---

## 🔗 관련 파일

- Agent 정의: `goole_adk/agents/professor/agent.py`
- 검색 도구: `goole_adk/agents/professor/tools/search_tools.py`
- Root Agent: `goole_adk/agent.py`

---

## 📝 참고사항

1. **청크 설정**: `chunk_size=2048, chunk_overlap=0`
   - 교수 정보가 이미 최적 청크로 구성되어 있어 분할 최소화

2. **임베딩 모델**: `text-multilingual-embedding-002`
   - 한국어 최적화 모델

3. **검색 설정**:
   - `top_k`: 기본 5개
   - `similarity_threshold`: 0.3-0.5 (낮을수록 더 많은 결과)

---

완료! 🎉

