import calendar
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ================================================================= 
# 1. 페이지 설정 및 Supabase 연결
# ================================================================= 
st.set_page_config(
    page_title="Xave's Family Scheduler",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = st.secrets["supabase_url"] 
SUPABASE_KEY = st.secrets["supabase_key"] 

@st.cache_resource 
def init_supabase() -> Client: 
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase() 
TABLE_NAME = "schedule"

# ================================================================= 
# 2. 색상 및 기본 설정값 정의
# ================================================================= 
AUTHORS = ["Xave", "Tina", "Rosa", "Jina", "Rina"] 
CATEGORIES = ["약속", "행사", "기타"]

# 작성자별 색상 맵 (텍스트 색상)
AUTHOR_COLORS = {
    "Xave": "#2B59C3",   # 파랑
    "Tina": "#9B51E0",   # 보라
    "Rosa": "#E0519B",   # 핑크
    "Jina": "#27AE60",   # 초록
    "Rina": "#E67E22"    # 주황
}

# 일정 종류별 카테고리 색상 (원형 점 마크)
CATEGORY_COLORS = {
    "약속": "#FF4D4D",   # 빨강
    "행사": "#20B2AA",   # 청록
    "기타": "#FFC107"    # 노랑
}

# ================================================================= 
# 3. 데이터 처리 함수 (한국 서울 시간대 Asia/Seoul 기준 적용)
# ================================================================= 
def load_schedules(): 
    """DB에서 일정을 가져와 Asia/Seoul 타임존으로 파싱""" 
    try: 
        response = supabase.table(TABLE_NAME).select("*").order("start_time").execute() 
        df = pd.DataFrame(response.data) 
        if not df.empty: 
            # UTC 시간을 한국 표준시(Asia/Seoul, UTC+9)로 변환
            df['start_time'] = pd.to_datetime(df['start_time'], utc=True).dt.tz_convert('Asia/Seoul') 
            df['end_time'] = pd.to_datetime(df['end_time'], utc=True).dt.tz_convert('Asia/Seoul') 
        return df 
    except Exception as e: 
        st.error(f"데이터 로드 중 오류: {e}") 
        return pd.DataFrame()

def save_schedule(data): 
    """일정 저장 (신규 등록 및 수정)""" 
    try: 
        if 'id' in data and data['id']: 
            post_id = data.pop('id') 
            supabase.table(TABLE_NAME).update(data).eq("id", post_id).execute() 
        else: 
            if 'id' in data:
                data.pop('id')
            supabase.table(TABLE_NAME).insert(data).execute() 
        return True 
    except Exception as e: 
        st.error(f"저장 중 오류: {e}") 
        return False

def delete_schedule(post_id): 
    """일정 삭제""" 
    try: 
        supabase.table(TABLE_NAME).delete().eq("id", post_id).execute() 
        return True 
    except Exception as e: 
        st.error(f"삭제 중 오류: {e}") 
        return False

# ================================================================= 
# 4. 모바일 반응형 CSS (7열 달력 형태 유지 & 스크롤 보장)
# ================================================================= 
st.markdown("""
    <style>
    /* 모바일에서 달력이 찌그러지지 않고 가로 스크롤 가능하게 처리 */
    .calendar-container {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-top: 5px;
    }
    .calendar-table {
        width: 100%;
        min-width: 650px; /* 모바일 폭이 좁아도 650px을 확보하여 7열 그리드 유지 */
        border-collapse: collapse;
        table-layout: fixed;
    }
    .calendar-table th {
        background-color: #f8f9fa;
        text-align: center;
        padding: 6px 2px;
        font-size: 13px;
        font-weight: bold;
        border: 1px solid #dee2e6;
    }
    .calendar-table td {
        border: 1px solid #dee2e6;
        vertical-align: top;
        padding: 4px 2px;
        height: 100px; /* 셀 고정 높이 */
        width: 14.28%;
        background-color: #ffffff;
    }
    .date-num {
        font-weight: bold;
        font-size: 12px;
        margin-bottom: 4px;
        color: #333;
    }
    .today {
        background-color: #e8f4fe !important;
        border: 2px solid #339af0 !important;
    }
    .other-month {
        background-color: #f8f9fa;
        opacity: 0.3;
    }
    
    /* 일자 내부 일정 항목 표시 */
    .schedule-item {
        font-size: 11px;
        line-height: 1.3;
        margin-bottom: 3px;
        padding: 2px 3px;
        border-radius: 3px;
        background-color: #f1f3f5;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: flex;
        align-items: center;
    }
    .circle-badge {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        margin-right: 3px;
        flex-shrink: 0;
    }
    </style>
""", unsafe_allow_html=True)

# ================================================================= 
# 5. 일정 등록 / 수정 / 삭제 모달 (Dialog)
# ================================================================= 
@st.dialog("일정 작성 및 수정") 
def schedule_dialog(target_data=None): 
    is_edit = target_data is not None 
    
    def_cat = target_data['category'] if is_edit else CATEGORIES[0]
    def_auth = target_data['author'] if is_edit else AUTHORS[0]
    
    now_kst = datetime.now()
    def_start_dt = target_data['start_time'].date() if is_edit else now_kst.date()
    def_start_tm = target_data['start_time'].time() if is_edit else now_kst.time()
    def_end_dt = target_data['end_time'].date() if is_edit else now_kst.date()
    def_end_tm = target_data['end_time'].time() if is_edit else (now_kst + timedelta(hours=1)).time()
    def_content = target_data['content'] if is_edit else ""

    category = st.selectbox("일정 종류", CATEGORIES, index=CATEGORIES.index(def_cat) if def_cat in CATEGORIES else 0) 
    author = st.selectbox("작성자", AUTHORS, index=AUTHORS.index(def_auth) if def_auth in AUTHORS else 0) 
     
    col1, col2 = st.columns(2) 
    with col1: 
        start_dt = st.date_input("시작일", def_start_dt) 
        start_tm = st.time_input("시작 시간 (KST)", def_start_tm) 
    with col2: 
        end_dt = st.date_input("종료일", def_end_dt) 
        end_tm = st.time_input("종료 시간 (KST)", def_end_tm) 
         
    content = st.text_area("내용", value=def_content, placeholder="일정 내용을 입력하세요")

    # 한국 표준시(KST +09:00) 정보 부여 후 ISO 문자열 변환
    start_time_obj = datetime.combine(start_dt, start_tm).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    end_time_obj = datetime.combine(end_dt, end_tm).strftime("%Y-%m-%dT%H:%M:%S+09:00")

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("💾 저장", type="primary", use_container_width=True): 
            if not content.strip():
                st.error("내용을 입력해주세요.")
                return

            payload = { 
                "category": category, 
                "author": author, 
                "start_time": start_time_obj, 
                "end_time": end_time_obj, 
                "content": content 
            } 
            if is_edit: 
                payload['id'] = target_data['id'] 
                 
            if save_schedule(payload): 
                st.success("저장되었습니다!") 
                st.rerun()

    with col_btn2:
        if is_edit:
            if st.button("🗑️ 삭제", type="secondary", use_container_width=True):
                if delete_schedule(target_data['id']):
                    st.success("삭제되었습니다!")
                    st.rerun()

# ================================================================= 
# 6. 메인 화면 구성
# ================================================================= 
st.title("📅 Xave's Family Scheduler")

# 상단 컨트롤 바
col_ctrl1, col_ctrl2, col_btn = st.columns([2, 2, 2])
now_dt = datetime.now()

with col_ctrl1:
    selected_year = st.selectbox("연도", range(now_dt.year - 2, now_dt.year + 3), index=2, label_visibility="collapsed")
with col_ctrl2:
    selected_month = st.selectbox("월", range(1, 13), index=now_dt.month - 1, label_visibility="collapsed")
with col_btn:
    if st.button("➕ 일정 추가", type="primary", use_container_width=True): 
        schedule_dialog()

# 범례(Legend) 표시
legend_html = "<div style='font-size: 12px; margin-bottom: 8px; line-height: 1.8;'>"
legend_html += "<b>[종류]</b> "
for cat, color in CATEGORY_COLORS.items():
    legend_html += f"<span style='margin-right: 10px;'><span class='circle-badge' style='background-color:{color};'></span>{cat}</span>"
legend_html += "<br><b>[작성자]</b> "
for auth, color in AUTHOR_COLORS.items():
    legend_html += f"<span style='margin-right: 10px; color:{color}; font-weight:bold;'>{auth}</span>"
legend_html += "</div>"
st.markdown(legend_html, unsafe_allow_html=True)

st.divider()

# 데이터 로드
df = load_schedules()

# 해당 월의 일정 데이터 필터링 및 날짜/ID별 매핑
schedules_by_day = {}
schedules_by_id = {}
if not df.empty:
    for _, row in df.iterrows():
        st_dt = row['start_time']
        if st_dt.year == selected_year and st_dt.month == selected_month:
            day = st_dt.day
            if day not in schedules_by_day:
                schedules_by_day[day] = []
            schedules_by_day[day].append(row)
            schedules_by_id[row['id']] = row

# ================================================================= 
# 7. 월 달력 렌더링 (가로 스크롤 가능 HTML 테이블)
# ================================================================= 
cal = calendar.Calendar(firstweekday=6) # 일요일 시작
month_days = cal.monthdayscalendar(selected_year, selected_month)

html_code = '<div class="calendar-container">'
html_code += '<table class="calendar-table">'
html_code += '<thead><tr><th style="color:red;">일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th style="color:blue;">토</th></tr></thead>'
html_code += '<tbody>'

for week in month_days:
    html_code += '<tr>'
    for day in week:
        if day == 0:
            html_code += '<td class="other-month"></td>'
        else:
            is_today = (selected_year == now_dt.year and selected_month == now_dt.month and day == now_dt.day)
            td_class = 'today' if is_today else ''
            
            html_code += f'<td class="{td_class}">'
            html_code += f'<div class="date-num">{day}</div>'
            
            # 날짜 칸(Cell) 안쪽에 일정을 세로 정렬로 출력
            if day in schedules_by_day:
                for item in schedules_by_day[day]:
                    cat_color = CATEGORY_COLORS.get(item['category'], '#888888')
                    auth_color = AUTHOR_COLORS.get(item['author'], '#333333')
                    time_str = item['start_time'].strftime("%H:%M")
                    
                    html_code += f'''
                    <div class="schedule-item" title="내용: {item['content']}">
                        <span class="circle-badge" style="background-color: {cat_color};"></span>
                        <span style="color: {auth_color}; font-weight: 600;">
                            [{item['author']}] {time_str} {item['content']}
                        </span>
                    </div>
                    '''
            html_code += '</td>'
    html_code += '</tr>'

html_code += '</tbody></table></div>'

# 렌더링
st.markdown(html_code, unsafe_allow_html=True)

# ================================================================= 
# 8. 하단 일정 수정/삭제 선택 버튼
# ================================================================= 
if schedules_by_id:
    st.markdown("##### ✏️ 일정 클릭하여 수정 및 삭제")
    
    # 2열 또는 3열 그리드로 모바일에서도 깔끔하게 배치
    select_cols = st.columns(2)
    for idx, (s_id, item) in enumerate(schedules_by_id.items()):
        col_idx = idx % 2
        time_str = item['start_time'].strftime("%m/%d %H:%M")
        btn_label = f"[{time_str}] {item['author']} - {item['content'][:10]}"
        
        with select_cols[col_idx]:
            if st.button(btn_label, key=f"quick_edit_{s_id}", use_container_width=True):
                schedule_dialog(item)
