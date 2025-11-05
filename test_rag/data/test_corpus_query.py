"""
Vertex AI RAG 코퍼스 검색 테스트 스크립트

강남대학교 졸업이수학점 데이터에 대한 간단한 질의 테스트

사용법:
    python test_rag/data/test_corpus_query.py
"""

import vertexai
from vertexai.preview import rag

# ==============================
# 설정
# ==============================
PROJECT_ID = "kangnam-backend"
LOCATION = "us-east4"
CORPUS_ID = "6917529027641081856"
CORPUS_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_ID}"

# ==============================
# 초기화
# ==============================
print("🔄 Vertex AI 초기화...")
print(f"   프로젝트: {PROJECT_ID}")
print(f"   리전: {LOCATION}")
print(f"   코퍼스: {CORPUS_ID}\n")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# ==============================
# 코퍼스 정보 확인
# ==============================
print("📦 코퍼스 정보 조회 중...\n")

try:
    corpus = rag.get_corpus(name=CORPUS_NAME)
    print(f"✅ 코퍼스 연결 성공!")
    print(f"   이름: {corpus.display_name}")
    print(f"   설명: {getattr(corpus, 'description', 'N/A')}\n")
    
    # 파일 목록 확인
    print("📄 코퍼스 내 파일 목록:")
    files_response = rag.list_files(corpus_name=CORPUS_NAME)
    
    if hasattr(files_response, 'rag_files'):
        files = files_response.rag_files
        if files:
            for i, file in enumerate(files, 1):
                display_name = getattr(file, 'display_name', 'N/A')
                source_uri = getattr(file, 'source_uri', 'N/A')
                print(f"   {i}. {display_name}")
                print(f"      📎 {source_uri}")
        else:
            print("   ⚠️  파일이 없습니다. 먼저 upload_to_rag.py를 실행하세요.")
            exit(1)
    print()
    
except Exception as e:
    print(f"❌ 코퍼스 접근 실패: {e}")
    exit(1)

# ==============================
# 테스트 질문들
# ==============================
test_queries = [
    "복지융합대학 졸업 요건이 뭐야?",
    "기초교양 학점은 몇 학점이야?",
    "공과대학 자연과학 계열 교양 과목 알려줘",
    "최소 졸업학점은?",
]

print("=" * 60)
print("🔍 검색 테스트 시작")
print("=" * 60)

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*60}")
    print(f"질문 {i}: {query}")
    print(f"{'='*60}\n")
    
    try:
        # RAG 리소스 설정
        rag_resource = rag.RagResource(rag_corpus=CORPUS_NAME)
        
        # 검색 설정
        retrieval_config = rag.RagRetrievalConfig(
            top_k=3,  # 상위 3개 결과
            filter=rag.Filter(
                vector_distance_threshold=0.3  # 유사도 30% 이상
            )
        )
        
        # 검색 실행
        response = rag.retrieval_query(
            rag_resources=[rag_resource],
            text=query,
            rag_retrieval_config=retrieval_config
        )
        
        # 결과 처리
        if hasattr(response, 'contexts'):
            contexts = response.contexts
            if hasattr(contexts, 'contexts'):
                contexts = contexts.contexts
            
            if contexts:
                print(f"📊 {len(contexts)}개의 결과를 찾았습니다:\n")
                
                for j, context in enumerate(contexts, 1):
                    text = getattr(context, 'text', '')
                    source_uri = getattr(context, 'source_uri', 'N/A')
                    relevance_score = getattr(context, 'relevance_score', None)
                    
                    print(f"결과 {j}:")
                    print(f"{'─' * 60}")
                    print(text[:300])  # 처음 300자만
                    if len(text) > 300:
                        print("...")
                    print(f"\n📎 출처: {source_uri}")
                    if relevance_score is not None:
                        print(f"📊 유사도: {relevance_score:.2%}")
                    print()
            else:
                print("⚠️  검색 결과가 없습니다.")
        else:
            print("⚠️  응답에 컨텍스트가 없습니다.")
    
    except Exception as e:
        print(f"❌ 검색 실패: {e}")

print("\n" + "=" * 60)
print("✅ 테스트 완료!")
print("=" * 60)

# ==============================
# 사용자 입력 모드 (선택)
# ==============================
print("\n💬 직접 질문하기 (종료하려면 'quit' 입력)")
print("─" * 60)

while True:
    try:
        user_query = input("\n질문: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q', '종료']:
            print("👋 종료합니다.")
            break
        
        if not user_query:
            continue
        
        print(f"\n🔍 검색 중...\n")
        
        # 검색
        rag_resource = rag.RagResource(rag_corpus=CORPUS_NAME)
        retrieval_config = rag.RagRetrievalConfig(
            top_k=3,
            filter=rag.Filter(vector_distance_threshold=0.3)
        )
        
        response = rag.retrieval_query(
            rag_resources=[rag_resource],
            text=user_query,
            rag_retrieval_config=retrieval_config
        )
        
        # 결과 출력
        if hasattr(response, 'contexts'):
            contexts = response.contexts
            if hasattr(contexts, 'contexts'):
                contexts = contexts.contexts
            
            if contexts:
                print(f"📊 {len(contexts)}개의 결과:\n")
                for j, context in enumerate(contexts, 1):
                    text = getattr(context, 'text', '')
                    relevance_score = getattr(context, 'relevance_score', None)
                    
                    print(f"결과 {j}:")
                    print(text[:200])
                    if len(text) > 200:
                        print("...")
                    if relevance_score:
                        print(f"유사도: {relevance_score:.2%}")
                    print()
            else:
                print("⚠️  검색 결과가 없습니다.")
        
    except KeyboardInterrupt:
        print("\n\n👋 종료합니다.")
        break
    except Exception as e:
        print(f"❌ 오류: {e}")

