import requests
from bs4 import BeautifulSoup
import json

# 1️⃣ 사용자 입력 (보안을 위해 input으로 받기)
username = input("학교 아이디: ")
password = input("학교 비밀번호: ")

# 2️⃣ 로그인 세션 준비
session = requests.Session()
login_url = "https://ecampus.kangnam.ac.kr/login/index.php"

# 3️⃣ 로그인 POST 요청
payload = {
    'username': username,
    'password': password
}
res = session.post(login_url, data=payload)
if res.status_code != 200 or "로그아웃" not in res.text:
    print("로그인 실패 ❌")
    exit()

print("✅ 로그인 성공!")

# 4️⃣ 강의 리스트 페이지 요청
course_list_url = "https://ecampus.kangnam.ac.kr/"
res = session.get(course_list_url)
soup = BeautifulSoup(res.text, "html.parser")

# 5️⃣ 강의 정보 수집
courses = []
for course_div in soup.select("ul.my-course-lists > li.course_label_re_03"):
    title_tag = course_div.select_one(".course-title h3")
    prof_tag = course_div.select_one(".course-title p.prof")
    link_tag = course_div.select_one("a.course_link")

    if title_tag and link_tag:
        courses.append({
            "title": title_tag.text.strip(),
            "professor": prof_tag.text.strip() if prof_tag else "",
            "url": link_tag['href']
        })

# 결과 저장을 위한 딕셔너리
results = {"user": {}, "courses": []}

# 6️⃣ 사용자 이름 및 학부 정보 수집
user_info_tag = soup.select_one("div.user-info-picture")
if user_info_tag:
    user_name_tag = user_info_tag.select_one("h4")
    user_dept_tag = user_info_tag.select_one("p.department")
    user_name = user_name_tag.text.strip() if user_name_tag else "이름 없음"
    user_dept = user_dept_tag.text.strip() if user_dept_tag else "학부 정보 없음"
    results["user"] = {"name": user_name, "department": user_dept}
    print(f"\n👤 사용자: {user_name}")
    print(f"🏫 학부: {user_dept}")
else:
    print("❗ 사용자 정보를 찾을 수 없습니다.")

# ✅ 특정 강의 페이지에서 주차별 활동 정보 수집 (예: 데이터수집과처리)
def fetch_course_weeks(course_url):
    week_info = []
    res = session.get(course_url)
    soup = BeautifulSoup(res.text, "html.parser")
    weeks = soup.select("ul.weeks li.section.main.clearfix")
    
    for week in weeks:
        title = week.get("aria-label", "").strip()
        activities = []
        for act in week.select("li.activity"):
            name = act.select_one(".instancename")
            if name:
                activities.append(name.text.strip().replace("파일", "").replace("게시판", "").replace("과제", "").strip())
        week_info.append({"title": title, "activities": activities})
        
        # 과제가 있다면 링크를 가져와 상태 확인
        for act in week.select("li.activity.assign a"):
            href = act.get("href")
            if href:
                assignment_status = fetch_assignment_status(href)
                week_info[-1]["assignment_status"] = assignment_status

    video_attendance_status = fetch_video_attendance_status(course_url)
    attendance_summary = fetch_attendance_summary(course_url)
    
    return {"weeks": week_info, "video_attendance": video_attendance_status, "attendance_summary": attendance_summary}

def fetch_assignment_status(assign_url):
    res = session.get(assign_url)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.select_one(".submissionstatustable table")
    
    if not table:
        return {"error": "과제 제출 정보 테이블을 찾을 수 없습니다."}
    
    rows = table.select("tr")
    status_info = {}
    for row in rows:
        cells = row.select("td")
        if len(cells) == 2:
            key = cells[0].text.strip()
            val = cells[1].text.strip()
            status_info[key] = val
    
    return status_info

def fetch_attendance_summary(course_url):
    res = session.get(course_url)
    soup = BeautifulSoup(res.text, "html.parser")
    summary = soup.select("ul.attendance li.attendance_section")
    attendance_info = []

    for week in summary:
        week_num = week.select_one("p.sname").text.strip()
        status = week.text.replace(week_num, "").strip()
        attendance_info.append({"week": week_num, "status": status if status else '결석 또는 미기록'})

    return attendance_info

def fetch_video_attendance_status(course_url):
    res = session.get(course_url)
    soup = BeautifulSoup(res.text, "html.parser")
    video_blocks = soup.select("li.activity.vod .activityinstance")
    video_info = []

    for video in video_blocks:
        title_tag = video.select_one("span.instancename")
        time_tag = video.select_one("span.text-info")
        period_tag = video.select_one("span.text-ubstrap")
        video_url_tag = video.select_one("a")

        title = title_tag.text.strip() if title_tag else "(제목 없음)"
        time = time_tag.text.strip() if time_tag else "재생 시간 정보 없음"
        period = period_tag.text.strip() if period_tag else "수강 기간 정보 없음"
        url = video_url_tag["href"] if video_url_tag else "링크 없음"

        video_info.append({"title": title, "url": url, "time": time, "period": period})

    return video_info

def fetch_course_notices(course_url):
    res = session.get(course_url)
    soup = BeautifulSoup(res.text, "html.parser")
    notice_box = soup.select_one("div.upcommings ul")
    notices_info = []

    if not notice_box:
        return notices_info

    notices = notice_box.select("li > a")
    for notice in notices:
        title = notice.select_one("h5").get("title", "").strip()
        link = notice["href"]
        notices_info.append({"title": title, "link": link})

    return notices_info

def fetch_notice_detail(notice_url):
    res = session.get(notice_url)
    soup = BeautifulSoup(res.text, "html.parser")

    subject = soup.select_one("div.subject h3")
    writer = soup.select_one("div.writer")
    date = soup.select_one("div.date")
    views = soup.select_one("div.hit")
    content = soup.select_one("div.content .text_to_html")

    notice_detail = {
        "subject": subject.text.strip() if subject else 'N/A',
        "writer": writer.text.strip().replace('작성자 :', '').strip() if writer else 'N/A',
        "date": date.text.strip().replace('작성일 :', '').strip() if date else 'N/A',
        "views": views.text.strip().replace('조회수 :', '').strip() if views else 'N/A',
        "content": [line for line in content.stripped_strings] if content else []
    }
    
    return notice_detail

# 🔄 모든 강의에서 주차별 활동 정보 수집
course_results = []
for course in courses:
    course_data = {
        "title": course['title'],
        "professor": course['professor'],
        "weeks": [],
        "notices": []
    }
    course_weeks_info = fetch_course_weeks(course['url'])
    course_data["weeks"] = course_weeks_info
    course_notices_info = fetch_course_notices(course['url'])
    detailed_notices = []
    for notice in course_notices_info:
        detail = fetch_notice_detail(notice["link"])
        detailed_notices.append({**notice, "detail": detail})
    course_data["notices"] = detailed_notices
    course_results.append(course_data)

results["courses"] = course_results

# JSON 파일로 저장
with open("kangnam_courses.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)