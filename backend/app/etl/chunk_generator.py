import json
import os
from typing import List, Dict, Any, Optional

def extract_chunks_from_course(course: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    단일 과목 데이터에서 활동, 과제, 공지사항, 동영상 강의 청크를 추출합니다.
    """
    chunks = []
    course_title = course.get("title", "강의명 미지정")
    weeks_data = course.get("weeks", {}).get("weeks", [])
    processed_weeks_for_video = set() # 동영상 강의 중복 처리 방지

    # 주차별 활동 및 과제 청크 생성
    for week in weeks_data:
        week_title = week.get("title", "주차 미지정")
        activities = week.get("activities", [])
        assignment_status = week.get("assignment_status", None)

        # 활동 청크
        if activities:
            # 빈 문자열이나 공백만 있는 활동은 제외
            valid_activities = [act for act in activities if act and act.strip()]
            if valid_activities:
                activity_content = f"{week_title} 수업 활동은 {', '.join(valid_activities)}입니다."
                activity_value = f"{course_title} 강의의 {week_title}에는 다음과 같은 수업 활동이 있습니다: {', '.join(valid_activities)}."
                chunks.append({
                    "chunk_type": "activity",
                    "course": course_title,
                    "week": week_title,
                    "content": activity_content,
                    "value": activity_value,
                    "metadata": {
                        "date": week.get("date"),
                        "day_of_week": week.get("day_of_week"),
                        "start_time": week.get("start_time"),
                        "end_time": week.get("end_time")
                    }
                })

        # 과제 청크
        if assignment_status and isinstance(assignment_status, dict) and "제출 여부" in assignment_status:
            submit_status = assignment_status.get("제출 여부")
            deadline = assignment_status.get("종료 일시", "정보 없음")
            
            # 과제 제목을 activities 리스트의 첫 번째 항목으로 시도, 없으면 주차명 사용
            assignment_title_candidate = next((act for act in activities if act and act.strip()), week_title)
            
            # '과제', '제출' 등의 키워드가 포함된 활동을 과제명으로 우선 사용
            assignment_keywords = ["과제", "제출", "리포트", "보고서", "퀴즈", "시험"]
            specific_assignment_activity = next((act for act in activities if any(kw in act for kw in assignment_keywords) and act.strip()), None)
            
            if specific_assignment_activity:
                assignment_title = specific_assignment_activity
            else:
                assignment_title = assignment_title_candidate

            content_text = ""
            value_text = ""

            if submit_status == "제출 안 함":
                content_text = f"'{assignment_title}' 과제가 아직 제출되지 않았습니다. 마감일은 {deadline}까지입니다."
                value_text = f"{course_title} 강의의 '{assignment_title}' 과제를 아직 제출하지 않으셨습니다. 마감일은 {deadline}이니 잊지 말고 제출해주세요."
            elif submit_status == "제출 완료":
                content_text = f"'{assignment_title}' 과제는 '{submit_status}' 상태이며, 마감일은 {deadline}였습니다."
                value_text = f"{course_title} 강의의 '{assignment_title}' 과제를 제출하셨군요! 잘 하셨습니다. 마감일은 {deadline}였습니다."
            elif isinstance(assignment_status, dict) and "status" in assignment_status and "error" in assignment_status["status"].lower():
                 content_text = f"'{assignment_title}' 과제 정보를 가져오는 중 오류가 발생했습니다: {assignment_status.get('message', '')}"
                 value_text = f"{course_title} 강의의 '{assignment_title}' 과제 상태를 확인하는 데 문제가 발생했습니다. ({assignment_status.get('message', '')}). 해당 주차의 활동 내용을 참고해주세요."
            else:
                content_text = f"'{assignment_title}' 과제는 '{submit_status}' 상태입니다. 마감일은 {deadline}였습니다."
                value_text = f"{course_title} 강의의 '{assignment_title}' 과제는 '{submit_status}' 상태이며, 마감일은 {deadline}였습니다."
            
            chunks.append({
                "chunk_type": "assignment",
                "course": course_title,
                "week": week_title, 
                "assignment_title": assignment_title,
                "content": content_text,
                "value": value_text,
                "metadata": {
                    "제출 여부": submit_status,
                    "마감일시": deadline,
                    "original_week_title": week_title, # 과제명으로 활동명이 사용될 경우를 대비해 원래 주차명 저장
                    "date": week.get("date"),
                    "day_of_week": week.get("day_of_week")
                }
            })

    # 공지사항 청크 생성
    notices = course.get("notices", [])
    if notices:
        for notice in notices:
            notice_title = notice.get("title", "제목 없음")
            notice_link = notice.get("link", "#")
            notice_content = f"공지사항: '{notice_title}'."
            notice_value = f"{course_title} 강의에 새로운 공지사항이 등록되었습니다: '{notice_title}'. 확인이 필요합니다."
            chunks.append({
                "chunk_type": "notice",
                "course": course_title,
                "content": notice_content,
                "value": notice_value,
                "metadata": {
                    "link": notice_link,
                    "title": notice_title
                }
            })
            
    # 동영상 강의 출석 청크 생성 (course 최상위의 video_attendance 사용)
    video_attendance_list = course.get("weeks", {}).get("video_attendance", [])
    if video_attendance_list:
        for video in video_attendance_list:
            # video_title을 기준으로 중복 추가 방지 (이미 추가된 video_title인지 확인)
            video_title = video.get("title", "제목 없음")
            if video_title in processed_weeks_for_video:
                continue # 이미 처리된 동영상 강의면 건너뛰기
            
            period = video.get("period", "기간 정보 없음")
            start_date = video.get("start_date", "정보 없음")
            end_date = video.get("end_date", "정보 없음")
            late_date = video.get("late_date", "정보 없음")
            video_url = video.get("url", "#")
            
            video_content = f"온라인 강의 '{video_title}'의 수강 기간은 {period}입니다."
            video_value = f"{course_title} 강의의 온라인 학습 콘텐츠 '{video_title}'를 수강해야 합니다. 수강 인정 기간은 {start_date}부터 {end_date}까지이며, 지각 처리 마감은 {late_date}입니다."
            
            chunks.append({
                "chunk_type": "video_lecture",
                "course": course_title,
                "video_title": video_title,
                "content": video_content,
                "value": video_value,
                "metadata": {
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "late_date": late_date,
                    "url": video_url
                }
            })
            processed_weeks_for_video.add(video_title)


    # 주차별 출석 요약 정보 (예시, 실제 출석 상태에 따라 value 문구 다양화 필요)
    attendance_summary = course.get("weeks", {}).get("attendance_summary", [])
    if attendance_summary:
        for summary_item in attendance_summary:
            week_num = summary_item.get("week", "알 수 없는 주차")
            status = summary_item.get("status", "정보 없음")
            
            # 단순 정보 제공형 청크
            summary_content = f"{week_num}주차 출석 상태: {status}."
            summary_value = f"{course_title} 강의의 {week_num}주차 출석 상태는 '{status}'입니다."
            
            # status 값에 따라 다른 value 생성 가능 (예: "결석"일 경우 주의 환기)
            if status == "결석":
                summary_value = f"{course_title} 강의 {week_num}주차에 결석 기록이 있습니다. 확인이 필요합니다."
            elif status == "-": # 아직 수업 전이거나 데이터가 없는 경우
                 summary_value = f"{course_title} 강의 {week_num}주차 출석 정보는 아직 업데이트되지 않았거나 수업 전입니다."


            chunks.append({
                "chunk_type": "attendance_summary",
                "course": course_title,
                "week": f"{week_num}주차", # 일관성을 위해 "주차" 텍스트 추가
                "content": summary_content,
                "value": summary_value,
                "metadata": {
                    "status": status
                }
            })

    return chunks

def generate_chunks_from_processed_data(processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    전처리된 데이터에서 청크를 생성합니다.
    
    Args:
        processed_data: CoursePreprocessor로 처리된 데이터
        
    Returns:
        List[Dict[str, Any]]: 생성된 청크 목록
    """
    all_chunks = []
    
    # 각 과목에 대해 청크 생성
    for course_data in processed_data.get("courses", []):
        course_chunks = extract_chunks_from_course(course_data)
        all_chunks.extend(course_chunks)
    
    return all_chunks

def save_chunks_to_file(chunks: List[Dict[str, Any]], output_path: str) -> Optional[str]:
    """
    생성된 청크를 파일로 저장합니다.
    
    Args:
        chunks: 생성된 청크 목록
        output_path: 저장할 파일 경로
        
    Returns:
        Optional[str]: 저장 성공 시 파일 경로, 실패 시 None
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        return output_path
    except Exception as e:
        print(f"청크 데이터 저장 실패: {e}")
        return None 