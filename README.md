# 강남대학교 챗봇

강남대학교 소프트웨어응용학부 학생들을 위한 AI 챗봇입니다. LangGraph를 사용하여 구현된 이 챗봇은 학생들의 다양한 질문에 대해 개인화된 응답을 제공합니다.

## 주요 기능

- **개인 맞춤형 정보 제공**
  - 수강 중인 과목 정보
  - 과제 제출 현황
  - 출석 현황
  - 개인별 공지사항
  - 성적 정보

- **학교 공통 정보 제공**
  - 학사 제도
  - 졸업 요건
  - 수강신청 방법
  - 학과 공지사항
  - 교수 정보
  - 시설 정보

- **일반 질문 응답**
  - 학교 생활 일반
  - 동아리 정보
  - 장학금 정보
  - 기숙사 정보
  - 기타 잡담

## 기술 스택

- Python 3.9+
- Google Gemini API
- LangGraph
- FastAPI (예정)
- Streamlit (예정)

## 설치 방법

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

## 프로젝트 구조

```
src/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── router_agent.py
│   ├── personal_agent.py
│   ├── common_agent.py
│   └── general_agent.py
├── __init__.py
├── chatbot_graph.py
└── test_chatbot.py
```

## 사용 방법

1. 테스트 실행
```bash
python src/test_chatbot.py
```

## 개발 현황

- [x] 기본 에이전트 구조 구현
- [x] 메시지 분류 시스템 구현
- [x] LangGraph 워크플로우 구현
- [ ] FastAPI 백엔드 구현
- [ ] Streamlit 프론트엔드 구현
- [ ] 데이터베이스 연동
- [ ] 사용자 인증 시스템

## 라이선스

MIT License

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 