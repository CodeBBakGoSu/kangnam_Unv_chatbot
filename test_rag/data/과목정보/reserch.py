import requests
import re
import pprint
from bs4 import BeautifulSoup

# ------------------------------------------------------------------
# [1단계] 강의계획서 "상세 페이지" 파서 (제공해주신 코드)
# ------------------------------------------------------------------
def parse_syllabus_html(html: str):
    """
    강의계획서 상세 HTML을 파싱하여 JSON(dict) 형태로 반환합니다.
    'NoneType' 오류를 해결하고, 유연한(robust) 텍스트 탐색을 적용합니다.
    """
    soup = BeautifulSoup(html, "html.parser")   
    data = {}

    # ---------------------------------------------------------------
    # 1. 메인 정보 테이블 파싱 (첫 번째 <tbody>)
    # ---------------------------------------------------------------
    main_tbody = soup.find("tbody")
    if not main_tbody:
        main_tbody = soup

    # --- 1-1. 기본 정보 파싱 (Helper) ---
    def get_main_text(label):
        """<th> 레이블로 <td> 텍스트를 찾는 헬퍼 (rowspan 대응)"""
        th = main_tbody.find("th", string=lambda s: s and label in s.strip())
        if not th:
            return ""
        
        td = th.find_next_sibling("td")
        if td:
            for br in td.find_all("br"): br.replace_with("\n")
            return td.get_text(strip=True)
        
        tr = th.find_parent("tr")
        if not tr: return ""
        
        all_cells = tr.find_all(["th", "td"])
        found_th = False
        for cell in all_cells:
            if cell == th:
                found_th = True
                continue
            if found_th and cell.name == "td":
                for br in cell.find_all("br"): br.replace_with("\n")
                return cell.get_text(strip=True)
        return ""

    data["년도"] = get_main_text("년 도")
    data["학기"] = get_main_text("학 기")
    data["교과목명_한글"] = get_main_text("한글")
    data["교과목명_영문"] = get_main_text("영문")
    data["담당교수"] = get_main_text("담당교수")
    data["학수번호_분반"] = get_main_text("학수번호-분반")
    data["강의요일교시"] = get_main_text("강의요일교시")
    data["학점_시간수"] = get_main_text("학점")
    data["강의실"] = get_main_text("강의실")
    data["핵심역량"] = get_main_text("핵심역량")
    data["성적평가기준"] = get_main_text("성적평가기준") # '패스강좌'
    data["연구실"] = get_main_text("연구실")
    data["E-Mail"] = get_main_text("E-Mail")
    data["휴대전화"] = get_main_text("휴대전화")
    data["면담가능시간"] = get_main_text("면담가능시간")
    data["연구일"] = get_main_text("연구일")
    data["관리부서"] = get_main_text("관리부서")
    data["선수과목"] = get_main_text("선수과목")
    data["관련_기초과목"] = get_main_text("기초과목")
    data["동시수강_관련과목"] = get_main_text("동시수강")
    data["관련_고급과목"] = get_main_text("고급과목")
    data["교과목_개요"] = get_main_text("교과목") # '교과목\n개요'
    data["수업목표"] = get_main_text("수업목표")
    data["교수학습_세부운영_방법"] = get_main_text("세부운영")
    data["수업운영방식"] = get_main_text("수업운영방식")
    data["주교재"] = get_main_text("주교재")
    data["참고도서"] = get_main_text("참고도서")

    # --- 1-2. 체크박스 항목 파싱 (Helper) [수정됨] ---
    def get_checked_labels(th_label_search):
        """특정 <th> 하위 <td>에서 체크된 항목 텍스트 추출 (Robust Version)"""
        # <br> 태그 등을 고려하여 텍스트 검색
        th_label_search = th_label_search.replace("<br>", "\n").strip()
        th = main_tbody.find("th", string=lambda s: s and th_label_search in s.strip())
        if not th: return []
        
        td = th.find_next_sibling("td", {"class": "displayOn"})
        if not td: 
            td = th.find_next_sibling("td") # Fallback
        if not td: 
            return []
        
        checked_labels = []
        for checkbox in td.find_all("input", {"type": "checkbox", "checked": True}):
            label_node = checkbox.next_sibling
            label_text = ""
            # [오류 수정] 텍스트가 나올 때까지 다음 노드를 탐색 (공백, <b> 등 건너뛰기)
            while label_node:
                if isinstance(label_node, str): # NavigableString
                    label_text = label_node.string.strip()
                elif label_node.name: # Tag (e.g., <b>, <font>)
                    label_text = label_node.get_text(strip=True)
                
                if label_text: # 텍스트를 찾으면
                    checked_labels.append(label_text)
                    break # 다음 체크박스로 이동
                label_node = label_node.next_sibling # 텍스트 못찾았으면 다음 노드 탐색
        return checked_labels

    data["이수구분_교양"] = get_checked_labels("교양")
    data["이수구분_전공"] = get_checked_labels("전공")
    data["이수구분_일반선택"] = get_checked_labels("일반선택")

    # "학부(과)"는 특수 케이스
    td_dept = main_tbody.find("td", string=re.compile(r"학부\(과\) :"))
    if td_dept:
        data["학부(과)"] = td_dept.get_text(strip=True).split(":")[-1].strip()

    # "강좌특성" [수정됨]
    th_feature = main_tbody.find("th", string=lambda s: s and "강좌특성" in s)
    checked_features = []
    if th_feature:
        td_feature = th_feature.find_next_sibling("td", {"class": "displayOn"})
        if not td_feature: td_feature = th_feature.find_next_sibling("td")
        
        if td_feature:
            # [오류 수정] 빡빡한 list comprehension 대신 유연한 while 루프 사용
            for checkbox in td_feature.find_all("input", {"type": "checkbox", "checked": True}):
                label_node = checkbox.next_sibling
                label_text = ""
                while label_node:
                    if isinstance(label_node, str): # NavigableString
                        label_text = label_node.string.strip()
                    elif label_node.name: # Tag
                        label_text = label_node.get_text(strip=True)
                    
                    if label_text: # Found text
                        checked_features.append(label_text)
                        break
                    label_node = label_node.next_sibling # Try the next one
    data["강좌특성"] = checked_features


    # "교수학습방법" (수정된 헬퍼 사용)
    learning_methods = {}
    learning_methods["표준"] = get_checked_labels("표준 교과목운영 <br>기준")
    learning_methods["자기주도식"] = get_checked_labels("학생 자기주도식<br>수업운영")
    learning_methods["현장연계"] = get_checked_labels("현장 연계 방법")
    data["교수학습방법"] = learning_methods
    
    # "장애학생 지원" (수정된 헬퍼 사용)
    data["장애학생_시험시간"] = get_checked_labels("시험시간<br>조정여부")
    data["장애학생_지원사항"] = get_checked_labels("지원사항")

    # --- 1-3. 평가 방법 (중첩 테이블) 파싱 ---
    eval_data = {}
    th_eval = main_tbody.find("th", string="평가방법") # '평가방법' <th>
    if th_eval:
        nested_table = th_eval.find_next("table") # 내부 <table>
        if nested_table:
            labels = []
            values = []
            
            for th in nested_table.find_all("th"):
                label = th.get_text(strip=True)
                if "과제/퀴즈" in label: 
                    desc_td = th.find_next_sibling("td")
                    if desc_td:
                        eval_data["세부사항"] = desc_td.get_text(strip=True)
                    break
                if label:
                    labels.append(label)
            
            for td in nested_table.find_all("td"):
                # "과제/퀴즈"가 포함된 텍스트를 가진 <td>는 세부사항이므로 제외
                if "과제/퀴즈" in td.find_parent("tr").get_text(strip=True):
                    continue
                values.append(td.get_text(strip=True))
            
            eval_data["항목"] = dict(zip(labels, values[:len(labels)]))
    data["평가방법"] = eval_data

    # ---------------------------------------------------------------
    # 2. 주차별 강의 계획 파싱 (두 번째 <tbody>)
    # ---------------------------------------------------------------
    weekly_plan = []
    th_week_header = soup.find("th", string="주차")
    if th_week_header:
        table = th_week_header.find_parent("table")
        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 6: 
                        week_data = {
                            "주차": cols[0].get_text(strip=True),
                            "학습주제": cols[1].get_text(strip=True),
                            "수업방식/이용기재": cols[2].get_text(strip=True),
                            "교수학습자료": cols[3].get_text(strip=True),
                            "과제": cols[4].get_text(strip=True),
                            "수업운영방식": cols[5].get_text(strip=True)
                        }
                        weekly_plan.append(week_data)
    data["주차별강의계획"] = weekly_plan

    return data

    # ---------------------------------------------------------------
    # 2. 주차별 강의 계획 파싱 (두 번째 <tbody>)
    # ---------------------------------------------------------------
    weekly_plan = []
    # "주차" <th>를 포함한 <thead>를 찾아 그 테이블을 특정
    th_week_header = soup.find("th", string="주차")
    if th_week_header:
        table = th_week_header.find_parent("table")
        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 6: # 정확히 6개 열
                        week_data = {
                            "주차": cols[0].get_text(strip=True),
                            "학습주제": cols[1].get_text(strip=True),
                            "수업방식/이용기자재": cols[2].get_text(strip=True),
                            "교수학습자료": cols[3].get_text(strip=True),
                            "과제": cols[4].get_text(strip=True),
                            "수업운영방식": cols[5].get_text(strip=True)
                        }
                        weekly_plan.append(week_data)
    data["주차별강의계획"] = weekly_plan

    return data

# ------------------------------------------------------------------
# [2단계] 과목 "목록" 검색 함수 (제공해주신 코드 기반)
# ------------------------------------------------------------------
def search_courses(session, base_url, year, semester, keyword):
    """특정 키워드로 과목 목록을 검색하고 결과 HTML을 반환합니다."""
    
    # 1. 쿠키 및 기본 세션 확보 (필수)
    #    (이 GET 요청이 없으면 POST가 500 오류를 반환할 수 있음)
    form_page_url = f"{base_url}/sbr1010.jsp"
    try:
        session.get(form_page_url, timeout=10)
    except requests.RequestException as e:
        print(f"Warning: sbr1010.jsp GET 실패 (세션 쿠키 확보 실패 가능성): {e}")
        # 실패해도 일단 진행 (세션이 유효할 수 있으므로)

    # 2. POST 페이로드(데이터) 정의
    #    (제공해주신 성공한 payload 기반으로 구성)
    payload = {
        "empl_numb": "",
        "schl_year": year,       # 파라미터로 받은 년도
        "schl_smst": semester,   # 파라미터로 받은 학기
        "subj_numb": "",
        "lctr_clas": "",
        "save_gubn": "",
        "dept_srch": "",
        "srch_gubn": "11",       # 검색 구분 (11 = 과목명 검색)
        "subj_knam": keyword,    # 파라미터로 받은 키워드
        "subj_knam2": "",
        "dept_code1": "",
        "grad_area1": "H1"       # 학부 구분 (H1 = 학사)
    }

    # 3. EUC-KR로 페이로드 인코딩
    payload_encoded = {}
    for key, value in payload.items():
        payload_encoded[key] = value.encode('euc-kr')

    # 4. 'sbr1010L.jsp' (결과 페이지)로 POST 요청
    post_url = f"{base_url}/sbr1010L.jsp"
    headers = {
        "Referer": form_page_url,
        "Origin": "https://app.kangnam.ac.kr",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    r_post = session.post(post_url, data=payload_encoded, headers=headers)
    r_post.raise_for_status()
    r_post.encoding = 'euc-kr'
    
    return r_post.text

# ------------------------------------------------------------------
# [3단계] 과목 "목록 HTML" 파서
# ------------------------------------------------------------------
def parse_course_list(html: str):
    """과목 목록 HTML을 파싱하여 과목 정보 리스트를 반환합니다."""
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    
    # <div id="list"> 안의 <table> 안의 <tr> 들을 찾음
    rows = soup.select("div#list table.grid_list tr[id^='row']")
    
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue

        # goPrint('1','108165,2025,2,EF14214,00')
        # 위 형태의 문자열에서 파라미터 부분만 추출
        onclick_attr = tds[7].find("div", onclick=True)
        if not onclick_attr:
            continue
            
        # 정규표현식으로 goPrint 내부의 두 번째 파라미터(따옴표 안) 추출
        match = re.search(r"goPrint\([^,]+,'([^']+)'\)", str(onclick_attr))
        if not match:
            continue

        params_str = match.group(1) # '108165,2025,2,EF14214,00'
        
        course_info = {
            "학수번호": tds[0].get_text(strip=True),
            "분반": tds[1].get_text(strip=True),
            "과목명": tds[2].get_text(strip=True),
            "담당교수": tds[3].get_text(strip=True),
            "학점": tds[4].get_text(strip=True),
            "시수": tds[5].get_text(strip=True),
            "강의시간": tds[6].get_text(strip=True),
            "params": params_str  # 강의계획서 URL을 만들 핵심 파라미터
        }
        courses.append(course_info)
        
    return courses

# ------------------------------------------------------------------
# [4단계] 강의계획서 "상세" 정보 요청 함수
# ------------------------------------------------------------------
def get_syllabus_details(session, base_url, params_str):
    """추출한 파라미터로 실제 강의계획서 URL을 조합하고 HTML을 반환합니다."""
    
    # params_str = '108165,2025,2,EF14214,00'
    try:
        val = params_str.split(',')
        empl_numb = val[0]
        schl_year = val[1]
        schl_smst = val[2]
        subj_numb = val[3]
        lctr_clas = val[4]
    except IndexError:
        print(f"Error: 파라미터('{params_str}') 분리 중 오류 발생")
        return None

    # 년도에 따라 URL이 바뀜 (JS 코드 분석 결과)
    temp_year = int(schl_year)
    if temp_year >= 2020:
        url_path = 'syllabus2020.jsp'
    elif temp_year >= 2017:
        url_path = 'syllabus2017.jsp'
    else:
        url_path = 'syllabus.jsp'
        
    # mrd 파일 경로는 JS 코드 분석 결과 고정값으로 보임
    repo_path = '../sbr/sbr3070_New.mrd' if temp_year >= 2014 else '../sbr/sbr3070.mrd'
        
    # 최종 URL 조합
    syllabus_url = (
        f"{base_url}/{url_path}?schl_year={schl_year}&schl_smst={schl_smst}"
        f"&subj_numb={subj_numb}&lctr_clas={lctr_clas}&empl_numb={empl_numb}"
        f"&repo_path={repo_path}&winopt=1010"
    )
    
    print(f"\n[INFO] 강의계획서 URL 요청 중: {syllabus_url}")
    
    try:
        r_syllabus = session.get(syllabus_url)
        r_syllabus.raise_for_status()
        r_syllabus.encoding = 'euc-kr'
        return r_syllabus.text
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# ------------------------------------------------------------------
# [메인 실행]
# ------------------------------------------------------------------
def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
    })
    base_url = "https://app.kangnam.ac.kr/knumis/sbr"

    # --- 사용자 입력 ---
    search_year = input("검색할 년도를 입력하세요 (예: 2024): ")
    search_semester = input("검색할 학기를 입력하세요 (1 또는 2): ")
    search_keyword = input("검색할 과목명을 입력하세요 (예: 데이터): ")
    
    # 1. 과목 목록 검색
    print(f"\n--- '{search_keyword}' 과목 목록 검색 중 ---")
    list_html = search_courses(session, base_url, search_year, search_semester, search_keyword)
    
    # 2. 과목 목록 파싱
    courses = parse_course_list(list_html)
    
    if not courses:
        print("검색 결과가 없습니다.")
        return

    # 3. 사용자에게 목록 보여주기
    print("\n--- 검색 결과 ---")
    for i, course in enumerate(courses):
        print(f"[{i+1}] {course['과목명']} ({course['담당교수']}) - {course['강의시간']}")
        
    # 4. 사용자 선택
    try:
        choice = int(input("\n강의계획서를 볼 과목의 번호를 선택하세요: "))
        if not (1 <= choice <= len(courses)):
            raise ValueError
        
        selected_course = courses[choice - 1]
        
    except ValueError:
        print("잘못된 입력입니다. 프로그램을 종료합니다.")
        return

    # 5. 선택한 과목의 상세 강의계획서 가져오기
    syllabus_html = get_syllabus_details(session, base_url, selected_course['params'])
    
    if syllabus_html:
        # 6. 상세 강의계획서 파싱 (사용자가 만든 함수)
        syllabus_data = parse_syllabus_html(syllabus_html)
        
        # 7. 최종 결과 출력
        print("\n--- 강의계획서 상세 정보 ---")
        pprint.pprint(syllabus_data)

if __name__ == "__main__":
    main()