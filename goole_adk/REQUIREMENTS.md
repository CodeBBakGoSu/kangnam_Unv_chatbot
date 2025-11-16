# goole_adk 의존성 요약

## 배포 시 자동 설치되는 패키지

Agent Engine 배포 시 `deploy.py`의 `requirements` 파라미터에 명시된 패키지들이 자동으로 설치됩니다.

### 필수 의존성

```python
requirements = [
    "google-cloud-aiplatform[adk,agent_engines]",  # Vertex AI + ADK + Agent Engine
    "requests",                                     # HTTP 클라이언트
    "beautifulsoup4",                              # HTML 파싱
    "python-dotenv",                               # 환경 변수
]
```

## 의존성 사용처

### 1. google-cloud-aiplatform[adk,agent_engines]
**사용 위치:**
- `goole_adk/agent.py`: Root Agent 정의
- `goole_adk/agents/*/agent.py`: 모든 Sub-Agent 정의
- `goole_adk/config/__init__.py`: Vertex AI 초기화

**포함 기능:**
- `google.adk.agents`: Agent 클래스
- `google.adk.tools`: FunctionTool 클래스
- `vertexai`: Vertex AI 초기화
- `vertexai.agent_engines`: Agent Engine 배포/관리
- `vertexai.preview.reasoning_engines`: AdkApp 래핑

### 2. requests
**사용 위치:**
- `goole_adk/agents/graduation/tools/search_tools.py`
  - Vertex AI Search API 호출
  - `gcloud auth print-access-token`으로 토큰 획득 후 HTTP 요청
  
- `goole_adk/agents/professor/tools/search_tools.py`
  - Vertex AI Search API 호출
  
- `goole_adk/agents/subject/tools/subject_tools.py`
  - 강남대학교 강의계획서 시스템 크롤링
  - HTTP POST 요청으로 과목 목록 조회
  - 강의계획서 상세 페이지 조회

**API 엔드포인트:**
```python
# Graduation Agent
VERTEX_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-univ-graduation-re_1762133185323/"
    "servingConfigs/default_search:search"
)

# Professor Agent
VERTEX_SEARCH_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1alpha/"
    "projects/88199591627/locations/global/collections/default_collection/"
    "engines/kangnam-professor-search-a_1761497936584/"
    "servingConfigs/default_search:search"
)

# Subject Agent (크롤링)
BASE_URL = "https://app.kangnam.ac.kr/knumis/sbr"
```

### 3. beautifulsoup4
**사용 위치:**
- `goole_adk/agents/subject/tools/subject_tools.py`

**사용 목적:**
1. 과목 목록 HTML 파싱
   - `parse_course_list()`: 검색 결과에서 과목 정보 추출
   - 학수번호, 분반, 과목명, 담당교수, 학점, 시수, 강의시간 파싱

2. 강의계획서 HTML 파싱
   - `parse_syllabus_html()`: 강의계획서 상세 페이지 파싱
   - 교과목 개요, 수업목표, 평가방법, 주차별 계획 등 추출

**파싱 구조:**
```python
soup = BeautifulSoup(html, "html.parser")
rows = soup.select("div#list table.grid_list tr[id^='row']")
# <table>, <tr>, <td>, <th> 태그 탐색
# 체크박스, 중첩 테이블 처리
```

### 4. python-dotenv
**사용 위치:**
- `goole_adk/config/__init__.py`
- `goole_adk/deploy.py`
- `goole_adk/create_staging_bucket.py`

**환경 변수 로드:**
```python
from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-east4")
```

## Python 내장 라이브러리 (설치 불필요)

다음 모듈들은 Python 표준 라이브러리이므로 별도 설치가 필요 없습니다:

- `subprocess`: gcloud 명령 실행, access token 획득
- `json`: JSON 데이터 처리
- `re`: 정규표현식 (HTML 파싱 보조)
- `datetime`: 날짜/시간 처리 (과목 검색 시 학기 자동 판단)
- `typing`: 타입 힌팅 (Dict, Any, Optional, List)
- `os`: 환경 변수, 파일 경로
- `sys`: 시스템 인터페이스

## 의존성 트리

```
goole_adk (배포 패키지)
├── google-cloud-aiplatform[adk,agent_engines]
│   ├── Agent, FunctionTool 클래스
│   ├── vertexai 초기화
│   └── agent_engines 배포/관리
│
├── requests
│   ├── Vertex AI Search API 호출
│   │   ├── Graduation Agent (졸업요건)
│   │   └── Professor Agent (교수 정보)
│   └── 강의계획서 크롤링
│       └── Subject Agent (과목 정보)
│
├── beautifulsoup4
│   └── HTML 파싱
│       └── Subject Agent (강의계획서)
│
└── python-dotenv
    └── 환경 변수 로드 (.env 파일)
```

## 버전 호환성

### Python 버전
- 최소 요구: Python 3.9+
- 권장: Python 3.10 이상

### 주요 패키지 버전 (자동 설치됨)
```
google-cloud-aiplatform >= 1.38.0
requests >= 2.28.0
beautifulsoup4 >= 4.11.0
python-dotenv >= 0.21.0
```

## 로컬 개발 환경 설정

로컬에서 개발/테스트 시:

```bash
# uv 사용 (권장)
uv pip install google-cloud-aiplatform[adk,agent_engines] requests beautifulsoup4 python-dotenv

# 또는 pip 사용
pip install google-cloud-aiplatform[adk,agent_engines] requests beautifulsoup4 python-dotenv
```

## 추가 의존성 (향후)

현재 Admission Agent는 placeholder로 tools가 없지만, 향후 추가 시 필요할 수 있는 의존성:

- `pandas`: 데이터 분석
- `openpyxl`: Excel 파일 처리
- `PyPDF2`: PDF 파싱

## 참고사항

### RAG 관련 의존성 (현재 미사용)
과거에는 Vertex AI RAG를 사용했으나, 현재는 Vertex AI Search로 전환하여 다음 의존성들은 **사용하지 않습니다**:

- `vertexai.preview.rag`: RAG Corpus 관련 (백업용으로 코드는 남아있음)
- 관련 파일: `goole_adk/agents/graduation/tools/rag_search_tools.py` (사용 안 함)

### 네트워크 의존성
배포 환경에서 다음 엔드포인트에 접근 가능해야 합니다:

1. **Vertex AI API**: `aiplatform.googleapis.com`
2. **Discovery Engine API**: `discoveryengine.googleapis.com`
3. **강남대 시스템**: `app.kangnam.ac.kr`

방화벽이나 VPC 설정 시 이를 고려하세요.

