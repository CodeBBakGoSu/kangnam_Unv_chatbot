# test_check_corpus.py
import vertexai
from vertexai.preview import rag

PROJECT_ID = "kangnam-backend"
LOCATION = "us-east4"
CORPUS_ID = "4532873024948404224"

vertexai.init(project=PROJECT_ID, location=LOCATION)

corpus_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_ID}"

# 코퍼스 정보 확인
try:
    corpus = rag.get_corpus(name=corpus_name)
    print(f"✅ 코퍼스 찾음: {corpus.display_name}")
    
    # 파일 목록 확인
    files = rag.list_files(corpus_name=corpus_name)
    print(f"\n📁 파일 수: {len(list(files))}")
    
    # 검색 테스트 (임계값 완전 제거)
    response = rag.retrieval_query(
        rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
        text="최인엽 교수님 공과대학",
        rag_retrieval_config=rag.RagRetrievalConfig(
            top_k=10,
            filter=rag.Filter(vector_distance_threshold=0.5)  # 임계값 0으로
        )
    )
    
    print(f"\n🔍 검색 결과:")
    if hasattr(response, 'contexts') and response.contexts:
        contexts = response.contexts.contexts if hasattr(response.contexts, 'contexts') else response.contexts
        print(f"   찾은 결과: {len(contexts)}개")
        for i, ctx in enumerate(contexts[:3], 1):
            print(f"\n   [{i}] {ctx.text[:1000]}...")
    else:
        print("   결과 없음 ❌")
        print(f"   Response: {response}")
        
except Exception as e:
    print(f"❌ 에러: {e}")