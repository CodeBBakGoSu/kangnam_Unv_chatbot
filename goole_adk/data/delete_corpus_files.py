"""
Vertex AI RAG 코퍼스에서 기존 파일을 삭제하는 스크립트

사용법:
    python goole_adk/data/delete_corpus_files.py
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
print(f"   코퍼스: {CORPUS_ID}\n")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# ==============================
# 코퍼스 파일 목록 조회
# ==============================
print("📄 코퍼스 내 파일 목록 조회 중...\n")

try:
    files_response = rag.list_files(corpus_name=CORPUS_NAME)
    
    if hasattr(files_response, 'rag_files'):
        files = files_response.rag_files
        
        if not files:
            print("⚠️  코퍼스에 파일이 없습니다.")
            exit(0)
        
        print(f"📊 총 {len(files)}개 파일 발견:\n")
        
        for i, file in enumerate(files, 1):
            file_id = file.name.split('/')[-1]
            display_name = getattr(file, 'display_name', 'N/A')
            source_uri = getattr(file, 'source_uri', 'N/A')
            
            print(f"{i}. {display_name}")
            print(f"   ID: {file_id}")
            print(f"   URI: {source_uri}")
            print()
        
        # 삭제 확인
        confirm = input("⚠️  모든 파일을 삭제하시겠습니까? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("❌ 취소되었습니다.")
            exit(0)
        
        # 파일 삭제
        print(f"\n🗑️  파일 삭제 중...\n")
        
        for i, file in enumerate(files, 1):
            file_name = file.name
            display_name = getattr(file, 'display_name', 'N/A')
            
            try:
                rag.delete_file(name=file_name)
                print(f"✅ {i}. 삭제 완료: {display_name}")
            except Exception as e:
                print(f"❌ {i}. 삭제 실패: {display_name}")
                print(f"   에러: {str(e)}")
        
        print(f"\n✅ 모든 파일 삭제 완료!")
    
    else:
        print("⚠️  파일 목록을 가져올 수 없습니다.")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print(f"\n💡 확인사항:")
    print(f"   1. 인증: gcloud auth application-default login")
    print(f"   2. 권한: Vertex AI User")
    print(f"   3. 코퍼스 ID: {CORPUS_ID}")

