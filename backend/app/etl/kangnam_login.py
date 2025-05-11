import requests
from bs4 import BeautifulSoup
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional

async def login_ecampus(username: str, password: str) -> Optional[aiohttp.ClientSession]:
    """강남대학교 이러닝 시스템에 로그인하고 세션 반환"""
    try:
        session = aiohttp.ClientSession()
        login_url = "https://ecampus.kangnam.ac.kr/login/index.php"
        
        # 로그인 POST 요청
        payload = {
            'username': username,
            'password': password
        }
        async with session.post(login_url, data=payload) as res:
            if res.status != 200:
                print("로그인 실패: 서버 오류")
                await session.close()
                return None
                
            html = await res.text()
            if "로그아웃" not in html:
                print("로그인 실패: 자격 증명 오류")
                await session.close()
                return None
                
        return session
    except Exception as e:
        print(f"로그인 중 오류 발생: {str(e)}")
        return None

async def get_user_info(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """사용자 정보(이름, 학부) 가져오기"""
    course_list_url = "https://ecampus.kangnam.ac.kr/"
    async with session.get(course_list_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
    user_info = {"name": "이름 없음", "department": "학부 정보 없음", "username": ""}
    
    user_info_tag = soup.select_one("div.user-info-picture")
    if user_info_tag:
        user_name_tag = user_info_tag.select_one("h4")
        user_dept_tag = user_info_tag.select_one("p.department")
        user_name = user_name_tag.text.strip() if user_name_tag else "이름 없음"
        user_dept = user_dept_tag.text.strip() if user_dept_tag else "학부 정보 없음"
        user_info["name"] = user_name
        user_info["department"] = user_dept
    
    return user_info

async def get_course_list(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """수강 중인 강좌 목록 가져오기"""
    course_list_url = "https://ecampus.kangnam.ac.kr/"
    async with session.get(course_list_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
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
            
    return courses

async def fetch_assignment_status(session: aiohttp.ClientSession, assign_url: str) -> Dict[str, Any]:
    """과제 상태 정보 가져오기"""
    async with session.get(assign_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
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

async def fetch_attendance_summary(session: aiohttp.ClientSession, course_url: str) -> List[Dict[str, str]]:
    """출석 정보 요약 가져오기"""
    async with session.get(course_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
    summary = soup.select("ul.attendance li.attendance_section")
    attendance_info = []

    for week in summary:
        week_num = week.select_one("p.sname").text.strip()
        status = week.text.replace(week_num, "").strip()
        attendance_info.append({"week": week_num, "status": status if status else '결석 또는 미기록'})

    return attendance_info

async def fetch_video_attendance_status(session: aiohttp.ClientSession, course_url: str) -> List[Dict[str, str]]:
    """동영상 출석 상태 가져오기"""
    async with session.get(course_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
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

async def fetch_course_notices(session: aiohttp.ClientSession, course_url: str) -> List[Dict[str, str]]:
    """강좌의 공지사항 목록 가져오기"""
    async with session.get(course_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
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

async def fetch_notice_detail(session: aiohttp.ClientSession, notice_url: str) -> Dict[str, Any]:
    """공지사항 상세 내용 가져오기"""
    async with session.get(notice_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")

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

async def fetch_course_weeks(session: aiohttp.ClientSession, course_url: str) -> Dict[str, Any]:
    """강좌의 주차별 활동 정보 가져오기"""
    async with session.get(course_url) as res:
        html = await res.text()
        
    soup = BeautifulSoup(html, "html.parser")
    weeks = soup.select("ul.weeks li.section.main.clearfix")
    week_info = []
    
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
                assignment_status = await fetch_assignment_status(session, href)
                week_info[-1]["assignment_status"] = assignment_status

    video_attendance_status = await fetch_video_attendance_status(session, course_url)
    attendance_summary = await fetch_attendance_summary(session, course_url)
    
    return {"weeks": week_info, "video_attendance": video_attendance_status, "attendance_summary": attendance_summary}

async def fetch_course_data(session: aiohttp.ClientSession, course: Dict[str, str]) -> Dict[str, Any]:
    """강좌 데이터 종합"""
    course_data = {
        "title": course['title'],
        "professor": course['professor'],
        "weeks": None,
        "notices": []
    }
    
    # 주차별 정보 가져오기
    course_weeks_info = await fetch_course_weeks(session, course['url'])
    course_data["weeks"] = course_weeks_info
    
    # 공지사항 가져오기
    course_notices_info = await fetch_course_notices(session, course['url'])
    detailed_notices = []
    for notice in course_notices_info:
        detail = await fetch_notice_detail(session, notice["link"])
        detailed_notices.append({**notice, "detail": detail})
    course_data["notices"] = detailed_notices
    
    return course_data

async def fetch_all_course_data(username: str, password: str) -> Dict[str, Any]:
    """사용자 로그인 및 모든 강좌 데이터 가져오기"""
    results = {"user": {}, "courses": []}
    
    # 로그인
    session = await login_ecampus(username, password)
    if not session:
        return {"error": "로그인 실패"}
    
    try:
        # 사용자 정보 가져오기
        user_info = await get_user_info(session)
        results["user"] = user_info
        
        # 과목 목록 가져오기
        courses = await get_course_list(session)
        
        # 각 과목 상세 정보 가져오기
        course_results = []
        for course in courses:
            course_data = await fetch_course_data(session, course)
            course_results.append(course_data)
        
        results["courses"] = course_results
        
        return results
    finally:
        # 세션 닫기
        await session.close()

# CLI로 직접 실행 시 테스트 코드
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = input("학교 아이디: ")
        password = input("학교 비밀번호: ")
    
    async def main():
        results = await fetch_all_course_data(username, password)
        if "error" in results:
            print(f"오류: {results['error']}")
        else:
            # JSON 파일로 저장
            with open("kangnam_courses.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"데이터 수집 완료: {len(results['courses'])}개 강좌")
    
    asyncio.run(main()) 