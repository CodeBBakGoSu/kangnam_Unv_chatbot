# list_corpus_metadata_fixed.py
import vertexai
from vertexai.preview import rag

PROJECT_ID = "kangnam-backend"
LOCATION = "us-east4"
CORPUS_ID = "6917529027641081856"

vertexai.init(project=PROJECT_ID, location=LOCATION)

corpus_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_ID}"

print("============================================================")
print("📦 Vertex AI RAG Corpus Metadata Inspector")
print("============================================================\n")

try:
    corpus = rag.get_corpus(name=corpus_name)
    print(f"✅ 코퍼스 확인됨: {corpus.display_name}\n")

    print("📁 업로드된 파일 목록:")
    files = list(rag.list_files(corpus_name=corpus_name))
    if not files:
        print("   (업로드된 파일 없음)")
    for i, f in enumerate(files, 1):
        print(f"   [{i}] {f.display_name} (ID: {f.name.split('/')[-1]})")
    print("\n============================================================")

    print("🔍 샘플 청크 및 메타데이터 확인 (검색 기반):")

    if not files:
        print("❌ 확인할 파일이 없습니다.")
    else:
        # 테스트를 위해 첫 번째 파일만 사용
        target_file = files[0]
        target_file_resource_name = target_file.name
        
        # ❗️ 이 파일의 내용과 관련 있을 법한 매우 일반적인 테스트 쿼리
        # (예: JSONL 파일이므로 '학과'나 '졸업요건' 같은 단어)
        TEST_QUERY = "졸업요건" 

        print(f"\n--- 📄 파일 '{target_file.display_name}'에 테스트 쿼리 전송 중 ---")
        print(f"   쿼리 내용: \"{TEST_QUERY}\"")
    
        try:
            # ✅ 'list_chunks' 대신 'retrieval_query' 사용
            response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=corpus_name,
                    rag_file_ids=[target_file.name.split('/')[-1]]
                )
            ],
            text=TEST_QUERY,
            rag_retrieval_config=rag.RagRetrievalConfig(
                top_k=5  # 여기에 top_k 지정
            )
        )
            
            # 전체 응답 객체를 직접 출력
            print("\n============================================================")
            print("🧾 Raw Retrieval Query Response:")
            print("============================================================")
            print(response)
            print("============================================================\n")

        except Exception as e:
            print(f"   ⚠️  검색 쿼리 중 에러 발생: {e}")

except Exception as e:
    print(f"❌ 스크립트 실행 중 에러 발생: {e}")