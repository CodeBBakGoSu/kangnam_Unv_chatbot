# 강남대학교 RAG 챗봇 시스템

Vertex AI RAG Engine을 활용한 강남대학교 졸업이수학점 정보 검색 시스템

## 📁 프로젝트 구조

```
goole_adk/
├── config/
│   └── __init__.py              # 설정 (PROJECT_ID, CORPUS_ID, 임베딩 모델 등)
│
├── data/                        # 데이터 관리
│   ├── *.json                   # 원본 졸업이수학점 JSON 데이터
│   ├── result/                  # 생성된 JSONL 파일 (확인용)
│   ├── upload_to_rag.py         # GCS 업로드 + Vertex AI import
│   ├── delete_corpus_files.py  # 코퍼스 파일 삭제
│   └── test_corpus_query.py    # 직접 쿼리 테스트
│
├── tools/                       # AI Agent용 검색 도구
│   ├── __init__.py
│   └── search_tools.py          # 3개의 검색 함수 + FunctionTool
│
├── agent.py                     # AI Agent 정의
├── test_search_tools.py         # 도구 테스트 스크립트
└── __init__.py
```

## 🎯 핵심 개념

### 1. RAG (Retrieval-Augmented Generation)

```
사용자 질문 → 관련 문서 검색 → 컨텍스트 제공 → AI 답변 생성
```

### 2. 임베딩 (Embedding)

텍스트를 숫자 벡터로 변환:
```
"졸업 요건" → [0.23, -0.45, 0.67, 0.12, ...]
```

### 3. 벡터 유사도

두 벡터 간의 유사성 측정 (0~1):
- `1.0` = 완전 동일
- `0.7~0.9` = 매우 유사
- `0.5~0.7` = 관련 있음
- `0.3~0.5` = 약간 관련
- `< 0.3` = 관련 없음

## 🔧 설정 파일

### `config/__init__.py`

```python
# Vertex AI 설정
PROJECT_ID = "kangnam-backend"
VERTEX_AI_LOCATION = "us-east4"
KANGNAM_CORPUS_ID = "6917529027641081856"

# 임베딩 모델
RAG_DEFAULT_EMBEDDING_MODEL = "text-multilingual-embedding-002"

# 검색 설정
RAG_DEFAULT_TOP_K = 10
RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD = 0.5
```

## 📚 검색 도구 (tools/search_tools.py)

### 1. `search_graduation_requirements(query, top_k, similarity_threshold)`

**기본 검색 함수** - 자유로운 질문

```python
result = search_graduation_requirements(
    query="2024년 입학생 복지융합대학 졸업 요건",
    top_k=5,                    # 상위 5개 결과
    similarity_threshold=0.3    # 30% 이상 유사도
)
```

**내부 동작:**
1. `query`를 임베딩으로 변환 (text-multilingual-embedding-002)
2. 코퍼스 내 모든 chunk와 벡터 유사도 계산
3. `similarity_threshold` 이상인 것만 필터링
4. 유사도 순으로 정렬하여 `top_k`개 반환

**반환값:**
```python
{
    "status": "success",
    "results": [
        {
            "rank": 1,
            "text": "[졸업요건 정보]\n대학: 복지융합대학\n...",
            "source_uri": "gs://kangnam-univ/...",
            "relevance_score": 0.85,
            "relevance_percentage": "85.0%"
        },
        ...
    ],
    "count": 5,
    "query": "2024년 입학생 복지융합대학 졸업 요건",
    "message": "..."
}
```

### 2. `search_by_year_and_college(year, college, category)`

**구조화된 검색** - 명확한 조건

```python
result = search_by_year_and_college(
    year="2024",              # 입학 연도
    college="복지융합대학",     # 대학 이름
    category="졸업요건",       # 카테고리
    top_k=3
)
```

**내부 동작:**
1. `year`를 `year_range`로 매핑
   - 2017~2020 → "2017~2020"
   - 2021~2024 → "2021~2024"
   - 2025+ → "2025 이후"
2. 구조화된 쿼리 생성: "2021~2024 복지융합대학 졸업요건"
3. `search_graduation_requirements()` 호출

### 3. `get_available_information()`

**사용 가능한 정보 확인**

```python
info = get_available_information()
```

**반환값:**
```python
{
    "available_data": {
        "colleges": ["복지융합대학", "경영관리대학", ...],
        "year_ranges": ["2017~2020", "2021~2024", "2025+"],
        "categories": ["졸업요건", "교양이수표"]
    },
    "search_examples": [...]
}
```

## 🧪 테스트 방법

### 1. 검색 도구 테스트

```bash
uv run python goole_adk/test_search_tools.py
```

**테스트 내용:**
- 사용 가능한 정보 확인
- 기본 검색 테스트 (3가지 질문)
- 구조화된 검색 테스트 (3가지 케이스)
- 유사도 임계값 비교
- 전체 텍스트 출력 예시

### 2. 직접 쿼리 테스트

```bash
uv run python goole_adk/data/test_corpus_query.py
```

**특징:**
- 자동 테스트 질문 4개
- 대화형 모드 (직접 질문 가능)

## 🤖 AI Agent 통합

### `agent.py` 예시

```python
from google.adk.agents.llm_agent import Agent
from goole_adk.tools.search_tools import ALL_SEARCH_TOOLS

kangnam_agent = Agent(
    model='gemini-2.0-flash',
    name='kangnam_graduation_assistant',
    description='강남대학교 졸업이수학점 정보 도우미',
    instruction='''
    당신은 강남대학교 학생들을 위한 졸업이수학점 정보 검색 봇입니다.
    
    - 학년도별, 대학별, 계열별 졸업 요건을 안내합니다.
    - 항상 정확한 정보를 제공하고, 출처를 명시합니다.
    - 검색 결과가 없으면 솔직하게 모른다고 말합니다.
    ''',
    tools=ALL_SEARCH_TOOLS  # 3개의 검색 도구
)
```

### Agent 작동 방식

```
사용자: "2024년 입학생인데 복지융합대학 졸업 요건 알려줘"
    ↓
Agent: search_by_year_and_college() 자동 선택 및 호출
    ↓
검색 결과: [...]
    ↓
Agent: 결과를 자연어로 변환
    ↓
답변: "2024년 입학생(2021~2024학년도)의 복지융합대학 졸업 요건은 다음과 같습니다:
       - 기초교양: 14학점
       - 균형교양: 15학점 (5개 영역에서 각 1개)
       - 심화전공자: 66학점
       - 최소졸업학점: 130학점
       
       [출처: gs://kangnam-univ/...]"
```

## 📊 데이터 업로드 프로세스

### 1. JSON → JSONL 변환 및 업로드

```bash
uv run python goole_adk/data/upload_to_rag.py
```

**동작:**
1. JSON 파일 읽기
2. Chunk 생성 (메타데이터 포함)
3. `result/` 폴더에 JSONL 저장 (확인용)
4. 사용자 확인 요청
5. GCS 업로드
6. Vertex AI import

### 2. 코퍼스 파일 삭제

```bash
uv run python goole_adk/data/delete_corpus_files.py
```

## 🔑 핵심 파라미터 튜닝

### `top_k` (결과 개수)

```python
top_k=3   # 간결한 답변 (상위 3개만)
top_k=5   # 균형 잡힌 답변 (기본값)
top_k=10  # 상세한 답변 (많은 컨텍스트)
```

### `similarity_threshold` (유사도 임계값)

```python
threshold=0.2  # 많은 결과, 낮은 정확도
threshold=0.3  # 균형 (기본값)
threshold=0.5  # 적은 결과, 높은 정확도
threshold=0.7  # 매우 정확한 결과만
```

**권장 조합:**
- 일반 질문: `top_k=5, threshold=0.3`
- 정확한 정보 필요: `top_k=3, threshold=0.5`
- 탐색적 검색: `top_k=10, threshold=0.2`

## 📌 주요 메타데이터

각 chunk에 포함된 메타데이터:

```python
{
    "college": "복지융합대학",
    "division": "인문사회",
    "department": "사회복지학부, 사회복지학전공(주), ...",
    "year_range": "2021~2024",
    "category": "졸업요건",
    "language": "ko",
    "source_file": "2017_2025_통합_졸업이수학점.json"
}
```

## 🚀 다음 단계

1. **Agent 통합**: `agent.py`에 검색 도구 추가
2. **프론트엔드 연결**: API 엔드포인트 생성
3. **로깅 추가**: 검색 쿼리 및 결과 로깅
4. **캐싱**: 자주 검색되는 질문 캐싱
5. **피드백 시스템**: 검색 결과 평가

## 💡 트러블슈팅

### 검색 결과가 없을 때

1. `similarity_threshold` 낮추기 (0.3 → 0.2)
2. `top_k` 늘리기 (5 → 10)
3. 쿼리 변경 (더 일반적인 용어 사용)

### 관련 없는 결과가 나올 때

1. `similarity_threshold` 높이기 (0.3 → 0.5)
2. `top_k` 줄이기 (10 → 3)
3. 쿼리를 더 구체적으로 변경

### 코퍼스 연결 실패

1. `KANGNAM_CORPUS_ID` 확인
2. `VERTEX_AI_LOCATION` 확인 (us-east4)
3. 인증: `gcloud auth application-default login`
4. 권한: Vertex AI User 역할

## 📞 문의

강남대학교 RAG 챗봇 시스템 개발팀

