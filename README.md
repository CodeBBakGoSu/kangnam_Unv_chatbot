# 강남대학교 챗봇

강남대학교 소프트웨어응용학부 학생들을 위한 AI 챗봇입니다. LangGraph를 사용하여 구현된 이 챗봇은 학생들의 다양한 질문에 대해 개인화된 응답을 제공합니다.

## 주요 기능

<details>
<summary>🎯 개인 맞춤형 정보 제공</summary>

- 수강 중인 과목 정보
- 과제 제출 현황
- 출석 현황
- 개인별 공지사항
- 성적 정보
</details>

<details>
<summary>🏫 학교 공통 정보 제공</summary>

- 학사 제도
- 졸업 요건
- 수강신청 방법
- 학과 공지사항
- 교수 정보
- 시설 정보
</details>

<details>
<summary>💬 일반 질문 응답</summary>

- 학교 생활 일반
- 동아리 정보
- 장학금 정보
- 기숙사 정보
- 기타 잡담
</details>

## 개발 진행 상황 (Development Progress)
### 2025-04-21: 시스템 기본 골조 구성

 기본 에이전트 구조 구현
 메시지 분류 시스템 구현
 LangGraph 워크플로우 구현


### 2025-05-08: RAG 시스템 구현 및 개선

<details>
<summary>📝 데이터 전처리 및 청크 생성</summary>

- 강의 데이터 JSON 파일 전처리
- 의미 있는 단위로 청크 분할
- 메타데이터 추가 (날짜, 시간, 주차 정보 등)
- 과목별 컨텍스트 정보 추가
</details>

<details>
<summary>🗄️ 벡터 데이터베이스 구축</summary>

- Supabase + pgvector 사용
- 청크별 임베딩 생성 및 저장
- 벡터 유사도 검색 기능 구현
- 메타데이터 기반 필터링 구현
</details>

<details>
<summary>🔄 과목명 정규화 시스템 개발 과정</summary>

1. 규칙 기반 접근 시도 (초기 버전)
   - 하드코딩된 매핑 테이블 사용
   - 한계점:
     - 새로운 패턴 추가 시 수동 업데이트 필요
     - 학교/학과별 다른 매핑 테이블 필요
     - 유지보수 비용 증가

2. 임베딩 기반 유사도 검색 시도
   - 과목명 벡터화 및 코사인 유사도 계산
   - 문제점:
     - 축약어와 원래 과목명 간 유사도 낮음
     - 예: "데수처" vs "데이터수집과처리" 유사도 < 0.2
     - 동음이의어 처리 어려움
     - 컨텍스트 고려 불가능

3. LLM 기반 제로샷 학습 방식 채택 ✅
   - 장점:
     - 특정 학교/학과에 종속되지 않는 범용성
     - 다양한 축약 패턴 자동 인식
     - 새로운 과목 추가 시 자동 적응
     - 컨텍스트 기반 정확한 매칭
     - 자연스러운 오타 처리
   - 구현:
     - Gemini Pro 모델 활용
     - 사용자의 수강 과목 컨텍스트 제공
     - 자연어 이해를 통한 과목명 매칭
   - 성능:
     - 축약어 매칭 정확도 95% 이상
     - 다양한 입력 패턴 처리 가능
     - 실시간 처리 가능한 응답 속도
</details>

<details>
<summary>🔄 데이터 처리 파이프라인</summary>

1. 데이터 수집
   - 강의계획서 데이터 수집
   - 학생 수강 정보 연동
   - 실시간 공지사항 수집

2. 데이터 전처리
   - 텍스트 정규화
   - 메타데이터 추출
   - 청크 생성
   - 임베딩 생성

3. 데이터 저장
   - Supabase 벡터 데이터베이스 저장
   - 메타데이터 인덱싱
   - 캐시 레이어 구현

4. 검색 및 추론
   - 하이브리드 검색 (키워드 + 벡터)
   - LLM 기반 컨텍스트 이해
   - 응답 생성 및 검증
</details>

### 다음 개발 계획

<details>
<summary>🎯 에이전트 시스템 통합</summary>

- 개선된 RAG 시스템을 기존 에이전트에 통합
- 과목 관련 질의응답 기능 강화
- 컨텍스트 기반 대화 관리 개선
</details>

<details>
<summary>⚡ 성능 최적화</summary>

- 캐싱 시스템 도입
- 응답 시간 개선
- 토큰 사용량 최적화
</details>

<details>
<summary>🎨 사용자 경험 개선</summary>

- 다중 과목 매칭 시 사용자 선택 UI
- 응답 신뢰도 표시
- 오류 피드백 시스템
</details>

<details>
<summary>📋 개발 현황</summary>

- [x] 기본 에이전트 구조 구현
- [x] 메시지 분류 시스템 구현
- [x] LangGraph 워크플로우 구현
- [x] 데이터 전처리 파이프라인 구축
- [x] 벡터 데이터베이스 연동
- [x] RAG 시스템 구현
- [x] 과목명 정규화 시스템 개발
- [ ] 에이전트-RAG 시스템 통합
- [ ] FastAPI 백엔드 구현
- [ ] Streamlit 프론트엔드 구현
- [ ] 사용자 인증 시스템
</details>

<details>
<summary>🛠️ 기술 스택</summary>

- Python 3.9+
- Google Gemini API
- LangGraph
- FastAPI (예정)
- Streamlit (예정)
</details>

<details>
<summary>📥 설치 방법</summary>

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:
```
GOOGLE_API_KEY=your_api_key_here
```
</details>

<details>
<summary>📂 프로젝트 구조</summary>

```
src/
├── agents/              # 에이전트 관련 모듈
│   ├── __init__.py
│   ├── base_agent.py
│   ├── router_agent.py
│   ├── personal_agent.py
│   ├── common_agent.py
│   └── general_agent.py
├── utils/              # 유틸리티 모듈
│   ├── course_preprocessor.py  # 과목 데이터 전처리
│   ├── chunk_generator.py      # 청크 생성
│   ├── similarity_test.py      # 유사도 테스트
│   └── gemini_rag_test.py      # RAG 시스템 테스트
├── etl/                # 데이터 파이프라인
│   ├── supabase_pipeline.py    # 벡터 DB 업로드
│   └── course_name_mapping.sql # DB 스키마
└── test/              # 테스트 코드
```
</details>

## 라이선스

MIT License

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 