"""
강남대학교 교수정보 전용 RAG 코퍼스 생성 스크립트

사용법:
    python goole_adk/data/교수정보/create_professor_corpus.py
"""

import vertexai
from vertexai.preview import rag

# ==============================
# 설정
# ==============================
PROJECT_ID = "kangnam-backend"
LOCATION = "us-east4"

# ==============================
# 초기화
# ==============================
print("=" * 60)
print("🎓 강남대학교 교수정보 RAG 코퍼스 생성")
print("=" * 60)
print(f"\n프로젝트: {PROJECT_ID}")
print(f"리전: {LOCATION}\n")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# ==============================
# 코퍼스 생성
# ==============================
print("🔄 코퍼스 생성 중...\n")

try:
    corpus = rag.create_corpus(
        display_name="강남대학교_교수정보",
        description="강남대학교 전체 학과 교수 정보 (이름, 연락처, 연구실, 연구분야, 담당과목 등). "
                   "공과대학, 글로벌문화콘텐츠대학, 법행정세무학부, 사범대학, 사회복지학과, 상경학부, "
                   "시니어비즈니스학과, 예체능대학의 교수 정보를 포함합니다."
    )
    
    corpus_id = corpus.name.split('/')[-1]
    
    print("✅ 코퍼스 생성 완료!\n")
    print("=" * 60)
    print("📋 코퍼스 정보")
    print("=" * 60)
    print(f"   이름: {corpus.display_name}")
    print(f"   ID: {corpus_id}")
    print(f"   전체 경로: {corpus.name}")
    print("=" * 60)
    
    print("\n📝 다음 단계:\n")
    print("1️⃣ goole_adk/agents/professor/tools/search_tools.py 파일을 엽니다")
    print("2️⃣ PROFESSOR_CORPUS_ID 변수를 다음 값으로 교체합니다:")
    print(f"\n   PROFESSOR_CORPUS_ID = \"{corpus_id}\"\n")
    print("3️⃣ 교수정보를 업로드합니다:")
    print(f"\n   python goole_adk/data/교수정보/upload_professors_to_rag.py\n")
    
except Exception as e:
    print(f"❌ 코퍼스 생성 실패:")
    print(f"   {str(e)}")
    print(f"\n💡 확인사항:")
    print(f"   1. 인증: gcloud auth application-default login")
    print(f"   2. 권한: Vertex AI User 역할")
    print(f"   3. API 활성화: Vertex AI API")
    exit(1)
