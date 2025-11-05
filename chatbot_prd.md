강남대학교 소프트웨어응용학부 AI 챗봇 프로젝트 정리

🎯 프로젝트 개요

목표: 강남대학교 소프트웨어응용학부 학생들이 학교생활 관련 궁금증을 24시간 빠르게 해결할 수 있는 AI 챗봇 개발

문제점: 기존 챗봇은 키워드 기반으로 문맥 파악 불가능, 실시간 문의 어려움, 퇴근 이후 정보 접근 제한 등

해결 방안: RAG + LLM(Gemini) 기반 자연어 이해 챗봇 개발

🧠 기술 스택

계층

기술

프론트엔드

Streamlit (챗봇 UI), React + Tailwind (로그인 화면)

백엔드

FastAPI

데이터베이스

Supabase (pgvector 포함)

LLM

Gemini 2.0 Flash (genai.GenerativeModel('gemini-2.0-flash-001'))

임베딩 및 검색

벡터 DB 기반 RAG 시스템

인증 방식

강남대 이러닝 SSO 로그인 후 JWT 발급

🧩 주요 기능

SSO 로그인 및 ETL

로그인 성공 시 학번, 이름, 학과, 수강과목, 주차별 과제/출석/영상/공지 등 크롤링

Supabase에 청크 단위로 저장 및 임베딩

Router 기반 대화 흐름 제어

personal, common, general 3가지 Agent로 라우팅

personal: 개인 LMS 정보 기반 응답

common: 졸업요건, 교수 정보, 시설 이용 등 학교 생활 전반 FAQ

general: 일반 질문 응답 (LLM 기반)

Fallback 시나리오

정보가 없을 경우 교학팀 전화번호 안내

챗봇 인터페이스

Streamlit 기반 chat_input, chat_message 사용

JWT 세션 없으면 /login 리다이렉트

✅ 주요 사용자 페르소나

유형

특징 및 니즈

신·편입생

학사일정, 졸업요건, 교수연락처를 빠르게 찾고 싶음

재학생 (3~4학년)

퇴근 이후 과제 마감/출석 등 실시간 정보 필요

🛠️ 운영/DevOps

CI/CD: GitHub Actions + Fly.io 배포 (Blue-Green)

로깅: Supabase 로그 + Grafana (제안)

ETL: 로그인 시 자동 실행

데이터 모델: UUID 기반 청크 저장, 768-d 벡터 포함

🔐 보안 및 세션 관리

학번/성적/출석 데이터는 PIPA 준수 → AES-256, TLS 1.3 사용 권장

JWT 발급 시 학번, 이름 포함하여 14일 유지

Supabase RLS 설정 및 접근 로그 기록

📅 개발 일정 (2025.03.20 ~ 2025.05 예정)

주차

주요 작업

W1

SSO + JWT 연동, 초기 ETL 구축

W2

personal agent 완성

W3

common agent FAQ 데이터 수집

W4

Streamlit UI 및 fallback 화면 구성

W5

부하 테스트 및 보안 점검

W6

베타 서비스 오픈 및 피드백 수집

📊 KPI

챗봇 MAU ≥ 50% (학부 재학생 기준)

평균 응답 시간 ≤ 4초

교학팀 전화 문의 20% 감소

사용자 만족도 ≥ 4.0 / 5.0

📌 기타

향후 기능 확장 계획:

모바일 PWA

영어/중국어 대응 다국어 응답

음성 인터페이스

Slack / Kakao 채널 연동

이 요약본은 Cursor AI, Notion, GitHub README 등에 그대로 활용 가능하며, 프롬프트 또는 초기 문맥 제공용으로 최적화되었습니다.

