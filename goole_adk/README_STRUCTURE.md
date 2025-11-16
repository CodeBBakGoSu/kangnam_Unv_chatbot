# 강남대학교 RAG 챗봇 - Agent Team 구조

ADK의 Agent Team 패턴을 사용한 Multi-Agent 시스템

## 📁 폴더 구조

```
goole_adk/
├── agent.py                          # Root Agent (delegation)
│
├── agents/                           # Sub-Agents 폴더
│   ├── __init__.py
│   │
│   ├── graduation/                   # 졸업요건 Agent ✅
│   │   ├── __init__.py
│   │   ├── agent.py                  # GraduationAgent
│   │   └── tools/
│   │       ├── __init__.py
│   │       └── search_tools.py       # 졸업요건 검색 도구 3개
│   │
│   ├── professor/                    # 교수 Agent (Placeholder)
│   │   ├── __init__.py
│   │   ├── agent.py                  # ProfessorAgent
│   │   └── tools/
│   │       └── __init__.py
│   │
│   └── admission/                    # 입학 Agent (Placeholder)
│       ├── __init__.py
│       ├── agent.py                  # AdmissionAgent
│       └── tools/
│           └── __init__.py
│
├── config/
│   └── __init__.py                   # 공통 설정 (PROJECT_ID, CORPUS_ID 등)
│
├── data/                             # 공통 데이터 저장소 (백업/참조용)
│   ├── 졸업요건/
│   │   ├── 2017_2025_통합_졸업이수학점.json
│   │   ├── 2017~2020학년도 입학자 졸업이수학점.json
│   │   ├── 2021~2024학년도 입학자 졸업이수학점.json
│   │   └── 2025이상 입학자 졸업이수학점.json
│   ├── 교수정보/                      # 추후
│   └── 입학정보/                      # 추후
│
├── .env                              # 환경 변수
└── README.md
```

## 🤖 Agent Team 구조

```
┌─────────────────────────────────────────┐
│  Root Agent (kangnam_agent)             │
│                                          │
│  역할: 질문 분석 → 적절한 Agent로 위임   │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ▼           ▼           ▼
┌───────────┐ ┌────────────┐ ┌─────────────┐
│Graduation │ │ Professor  │ │ Admission   │
│   Agent   │ │   Agent    │ │   Agent     │
│           │ │            │ │             │
│졸업요건 ✅ │ │교수 정보 ⏳│ │입학 정보 ⏳ │
└─────┬─────┘ └──────┬─────┘ └──────┬──────┘
      │              │              │
      │              │              │
  ┌───┴────┐     (추후)         (추후)
  │ Tools  │
  │  (3개) │
  └────────┘
```

## 🔄 동작 방식 (ADK Delegation Pattern)

### 1. 사용자 질문
```
"2024년 입학생 복지융합대학 졸업 요건 알려줘"
```

### 2. Root Agent 분석
```python
Root Agent (kangnam_agent)
    ↓
질문 분석: "졸업 요건" 키워드 감지
    ↓
판단: GraduationAgent가 적합
```

### 3. GraduationAgent 호출
```python
graduation_agent.query("2024년 입학생 복지융합대학 졸업 요건")
    ↓
Tool 선택: search_by_year_and_college()
    ↓
Vertex AI RAG 검색
    ↓
검색 결과 반환
```

### 4. Root Agent → 사용자
```python
Root Agent가 GraduationAgent의 답변을 사용자에게 전달
```

## 📊 Agent별 역할

### Root Agent (kangnam_agent)
- **파일**: `agent.py`
- **역할**: Delegation (위임)
- **Tools**: 없음 (Sub-agents만 사용)
- **Instruction**: 질문 분석 후 적절한 agent 호출

### GraduationAgent ✅
- **파일**: `agents/graduation/agent.py`
- **역할**: 졸업요건 정보 검색
- **Tools**: 
  1. `search_graduation_requirements()` - 자유 검색
  2. `search_by_year_and_college()` - 구조화 검색
  3. `get_available_information()` - 정보 확인
- **Data**: Vertex AI RAG Corpus (ID: 6917529027641081856)

### ProfessorAgent ⏳ (Placeholder)
- **파일**: `agents/professor/agent.py`
- **역할**: 교수 정보 검색
- **Tools**: 추후 추가
- **Data**: 추후 추가

### AdmissionAgent ⏳ (Placeholder)
- **파일**: `agents/admission/agent.py`
- **역할**: 입학 정보 검색
- **Tools**: 추후 추가
- **Data**: 추후 추가

## 🚀 실행 방법

### ADK Web UI로 실행
```bash
cd /Users/hong-gihyeon/Desktop/cap
uv run python -m google.adk serve goole_adk
```

### CLI로 실행
```bash
uv run python -m google.adk run goole_adk
```

### API Server로 실행
```bash
uv run python -m google.adk api_server goole_adk
```

## 💡 ADK Agent Delegation의 장점

### 1. 자동 라우팅
```python
# Root Agent가 자동으로 판단
agents=[graduation_agent, professor_agent, admission_agent]

# AI가 agent.description을 보고 자동 선택!
graduation_agent.description = "졸업요건 정보를 검색하는 전문 에이전트"
```

### 2. 모듈화
- 각 Agent가 독립적
- 새 Agent 추가 쉬움
- 유지보수 편리

### 3. 전문화
- 각 Agent가 특정 도메인 전문
- Tool도 분리되어 관리
- 명확한 책임 분리

### 4. 확장성
```python
# 새 Agent 추가 시:
1. agents/new_domain/ 폴더 생성
2. agent.py + tools/ 작성
3. Root Agent의 agents=[] 리스트에 추가
```

## 📝 다음 단계

### ProfessorAgent 추가
1. 교수 정보 데이터 수집
2. Vertex AI RAG Corpus 생성
3. search_tools.py 작성
4. agent.py 완성
5. Root Agent에 등록

### AdmissionAgent 추가
1. 입학 정보 데이터 수집
2. Vertex AI RAG Corpus 생성
3. search_tools.py 작성
4. agent.py 완성
5. Root Agent에 등록

## 🔗 참고 자료

- [ADK Agent Team Tutorial](https://google.github.io/adk-docs/tutorials/agent-team/)
- [ADK Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agent-systems/)
- [Vertex AI RAG Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/rag-api)

## ⚙️ 환경 변수 (.env)

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=kangnam-backend
GOOGLE_CLOUD_LOCATION=us-east4  # Gemini 모델 위치
VERTEX_AI_LOCATION=us-east4     # RAG 엔진 위치

# RAG Corpus
KANGNAM_CORPUS_ID=6917529027641081856

# GCS
GCS_BUCKET_NAME=kangnam-univ
GCS_BUCKET_LOCATION=asia-northeast3  # 데이터 저장 위치
```

---

**Status**: 
- ✅ Root Agent 구조 완성
- ✅ GraduationAgent 완성
- ⏳ ProfessorAgent (Placeholder)
- ⏳ AdmissionAgent (Placeholder)

