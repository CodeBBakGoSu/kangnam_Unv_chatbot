import asyncio
import json
import os
import sys

# src 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot_graph import process_message

async def test_chatbot():
    # 테스트 케이스들
    test_cases = [
        {
            "message": "내가 듣고 있는 과목들의 과제 현황을 알려줘",
            "description": "개인 맞춤형 정보 흐름 테스트 - 과제 현황"
        },
        {
            "message": "졸업요건이 어떻게 되나요?",
            "description": "공통 정보 흐름 테스트 - 졸업요건"
        },
        {
            "message": "학교 근처 맛집 추천해줘",
            "description": "일반 질문 흐름 테스트 - 맛집 추천"
        }
    ]
    
    # 테스트 실행
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"테스트: {test['description']}")
        print(f"질문: {test['message']}")
        
        try:
            # 사용자 컨텍스트 설정 (테스트용)
            user_context = {
                "name": "홍기현",
                "department": "소프트웨어응용학부",
                "courses": [
                    {
                        "title": "캡스톤디자인(SW)I",
                        "professor": "최인엽"
                    }
                ]
            }
            
            # 메시지 처리
            response = await process_message(test['message'], user_context)
            
            
            # 응답 출력
            print("\n응답:")
            print(json.dumps(response, ensure_ascii=False, indent=2))
            
        except Exception as e:
            print(f"에러 발생: {str(e)}")
        
        print(f"{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(test_chatbot()) 