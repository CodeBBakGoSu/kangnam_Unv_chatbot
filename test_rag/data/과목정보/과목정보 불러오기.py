import requests
from bs4 import BeautifulSoup

# 세션 생성 및 기본 헤더 설정
session = requests.Session()
base_url = "https://app.kangnam.ac.kr/knumis/sbr"

# 1. init.jsp 또는 main.jsp 호출 (선택 사항, 쿠키 선점)
# session.get("https://app.kangnam.ac.kr/knumis/jsp/init.jsp")

# 2. 'sbr1010.jsp' (검색 폼 페이지) GET 요청
# 이 단계가 서버 세션에 'frm1' Bean을 생성하고,
# HTML에 'hidden' 필드를 심어주는 핵심 과정입니다.
form_page_url = f"{base_url}/sbr1010.jsp"
try:
    r_form = session.get(form_page_url)
    r_form.raise_for_status()
    # 인코딩 강제 지정 (필수)
    r_form.encoding = 'euc-kr' 
    soup = BeautifulSoup(r_form.text, 'html.parser')

    # 3. 폼 데이터(payload) 준비
    payload = {}

    # 3-1. 페이지에 있는 모든 'hidden' input 값을 추출
    # 이 값들이 'frm1' 세션과 요청을 연결하는 고리입니다.
    hidden_inputs = soup.find_all("input", {"type": "hidden"})
    for input_tag in hidden_inputs:
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            payload[name] = value
            print(f"Found hidden field: {name} = {value}")

    payload = {
    # hidden 필드
    "empl_numb": "",
    "schl_year": "2025",
    "schl_smst": "2",
    "subj_numb": "",
    "lctr_clas": "",
    "save_gubn": "",
    
    # 검색 관련 필드
    "dept_srch": "",
    "srch_gubn": "11",       # 검색 구분 (11 = 과목명 검색)
    "subj_knam": "소프트",  # 과목명 키워드
    "subj_knam2": "",
    "dept_code1": "",
    "grad_area1": "H1"       # 학부 구분 (H1 = 학사)
}


    # 4. EUC-KR로 페이로드 인코딩
    # (주의: 딕셔너리 전체가 아닌, 값(value)만 인코딩해야 함)
    payload_encoded = {}
    for key, value in payload.items():
        # BeautifulSoup이 유니코드로 변환했으므로, 
        # 다시 euc-kr 바이트로 인코딩합니다.
        payload_encoded[key] = value.encode('euc-kr')

    # 5. 'sbr1010L.jsp' (결과 페이지)로 POST 요청
    post_url = f"{base_url}/sbr1010L.jsp"
    
    # 'Referer' 헤더는 필수입니다.
    # 서버는 이 요청이 'sbr1010.jsp'에서 왔는지 검사합니다.
    headers = {
        "Referer": form_page_url,
        "Origin": "https://app.kangnam.ac.kr",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r_post = session.post(post_url, data=payload_encoded, headers=headers)
    r_post.raise_for_status()
    r_post.encoding = 'euc-kr'

    # 6. 결과 확인
    print("\n--- Success! ---")
    print(r_post.text)

except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code}")
    # 500 오류 시 서버가 반환하는 HTML을 확인해 볼 수 있습니다.
    # print(e.response.text) 
except Exception as e:
    print(f"An error occurred: {e}")