import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
KST = ZoneInfo("Asia/Seoul")

AUTHORS = ["Xave", "Tina", "Rosa", "Jina", "Rina"] 
CATEGORIES = ["약속", "행사", "기타"]

CATEGORY_COLORS = {
    "약속": "🔴", 
    "행사": "🟢", 
    "기타": "🟡"  
}

# Session State를 이용한 연도/월 상태 관리 (이전/다음 버튼 작동용)
now_kst = datetime.now(KST)
if "curr_year" not in st.session_state:
    st.session_state.curr_year = now_kst.year
if "curr_month" not in st.session_state:
    st.session_state.curr_month = now_kst.month

# ================================================================= 
# 2. 데이터 처리 함수
# ================================================================= 
def load_schedules(): 
    try: 
        response = supabase.table(TABLE_NAME).select("*").order("start_time").execute() 
        df = pd.DataFrame(response.data) 
        if not df.empty: 
            df['start_time'] = pd.to_datetime(df['start_time'], utc=True).dt.tz_convert(KST) 
            df['end_time'] = pd.to_datetime(df['end_time'], utc=True).dt.tz_convert(KST) 
        return df 
    except Exception as e: 
        st.error(f"데이터 로드 중 오류: {e}") 
        return pd.DataFrame()

def save_schedule(data): 
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
    try: 
        supabase.table(TABLE_NAME).delete().eq("id", post_id).execute() 
        return True 
    except Exception as e: 
        st.error(f"삭제 중 오류: {e}") 
        return False

# ================================================================= 
# 3. 일정 등록/수정 Modal Dialog
# ================================================================= 
@st.dialog("일정 상세 및 수정") 
def schedule_dialog(target_data=None): 
    is_edit = target_data is not None 
    
    def_cat = target_data['category'] if is_edit else CATEGORIES[0]
    def_auth = target_data['author'] if is_edit else AUTHORS[0]
    
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
        start_tm = st.time_input("시작 시간", def_start_tm) 
    with col2: 
        end_dt = st.date_input("종료일", def_end_dt) 
        end_tm = st.time_input("종료 시간", def_end_tm) 
         
    content = st.text_area("내용", value=def_content, placeholder="일정 내용을 입력하세요")

    start_time_kst = datetime.combine(start_dt, start_tm, tzinfo=KST)
    end_time_kst = datetime.combine(end_dt, end_tm, tzinfo=KST)

    start_time_obj = start_time_kst.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_time_obj = end_time_kst.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("💾 저장", type="primary", use_container_width=True): 
            if not content.strip():
                st.error("내용을 입력해주세요.")
                return

            payload = { 
                "category": category, 
                "author": author, 
                "start_time": start_time_obj.isoformat(), 
                "end_time": end_time_obj.isoformat(), 
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
# 4. 모바일 최적화 CSS
# ================================================================= 
st.markdown("""
    <style>
    .block-container {
        padding: 0.2rem 0.2rem !important;
        max-width: 100% !important;
    }
    header, footer { visibility: hidden; height: 0; }
    
    /* 상단 버튼/조작바 높이 축소 */
    div[data-testid="stHorizontalBlock"] {
        gap: 2px !important;
        align-items: center !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        min-height: 28px !important;
        font-size: 11px !important;
    }
    button {
        min-height: 28px !important;
        padding: 0px 4px !important;
        font-size: 11px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ================================================================= 
# 5. 상단 이동 및 조작 바 (이전 / 연·월 선택 / 다음 / 일정추가)
# ================================================================= 
def prev_month():
    if st.session_state.curr_month == 1:
        st.session_state.curr_month = 12
        st.session_state.curr_year -= 1
    else:
        st.session_state.curr_month -= 1

def next_month():
    if st.session_state.curr_month == 12:
        st.session_state.curr_month = 1
        st.session_state.curr_year += 1
    else:
        st.session_state.curr_month += 1

c_prev, c_yr, c_mth, c_next, c_add = st.columns([1, 2, 1.5, 1, 2.5])

with c_prev:
    st.button("◀", on_click=prev_month, use_container_width=True)

with c_yr:
    selected_year = st.selectbox(
        "Y", 
        range(now_kst.year - 3, now_kst.year + 4), 
        index=range(now_kst.year - 3, now_kst.year + 4).index(st.session_state.curr_year), 
        label_visibility="collapsed",
        key="year_select"
    )
    st.session_state.curr_year = selected_year

with c_mth:
    selected_month = st.selectbox(
        "M", 
        range(1, 13), 
        index=st.session_state.curr_month - 1, 
        label_visibility="collapsed",
        key="month_select"
    )
    st.session_state.curr_month = selected_month

with c_next:
    st.button("▶", on_click=next_month, use_container_width=True)

with c_add:
    if st.button("➕ 추가", type="primary", use_container_width=True): 
        schedule_dialog()

# 데이터 로드
df = load_schedules()

schedules_by_day = {}
if not df.empty:
    for _, row in df.iterrows():
        st_dt = row['start_time']
        if st_dt.year == st.session_state.curr_year and st_dt.month == st.session_state.curr_month:
            day = st_dt.day
            if day not in schedules_by_day:
                schedules_by_day[day] = []
            schedules_by_day[day].append(row)

# ================================================================= 
# 6. 배경색 없는 깔끔한 HTML 노스크롤 달력
# ================================================================= 
cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdayscalendar(st.session_state.curr_year, st.session_state.curr_month)

html_code = """
<style>
.cal-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    margin-top: 2px;
}
.cal-table th {
    background-color: #f1f3f5;
    font-size: 10px;
    padding: 2px 0;
    text-align: center;
    border: 1px solid #dee2e6;
}
.cal-table td {
    border: 1px solid #e9ecef;
    vertical-align: top;
    padding: 1px;
    height: calc((100vh - 85px) / 6); /* 한 화면 분할 최적화 */
    background: #ffffff;
    overflow: hidden;
}
.day-title {
    font-size: 9px;
    font-weight: bold;
    color: #495057;
    line-height: 1;
    margin-bottom: 2px;
}
.today-title {
    color: #1c7ed6;
    font-weight: 900;
}
/* 배경색 제거 및 투명 깔끔 텍스트 바 */
.item-text {
    display: block;
    font-size: 8px;
    line-height: 1.1;
    padding: 0px;
    margin-bottom: 1px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #212529;
    background: transparent;
}
</style>

<table class="cal-table">
  <thead>
    <tr>
      <th style="color:red;">일</th>
      <th>월</th>
      <th>화</th>
      <th>수</th>
      <th>목</th>
      <th>금</th>
      <th style="color:blue;">토</th>
    </tr>
  </thead>
  <tbody>
"""

for week in month_days:
    html_code += "<tr>"
    for idx, day in enumerate(week):
        if day == 0:
            html_code += "<td style='background:#f8f9fa;'></td>"
        else:
            is_today = (st.session_state.curr_year == now_kst.year and st.session_state.curr_month == now_kst.month and day == now_kst.day)
            t_cls = "day-title today-title" if is_today else "day-title"
            t_txt = f"{day}★" if is_today else f"{day}"
            
            html_code += f"<td><div class='{t_cls}'>{t_txt}</div>"
            
            if day in schedules_by_day:
                for item in schedules_by_day[day]:
                    icon = CATEGORY_COLORS.get(item['category'], '⚪')
                    t_str = item['start_time'].strftime("%H:%M")
                    
                    # 배경색 제거: 아이콘 + 작성자 + 시간 순서의 깔끔한 텍스트 렌더링
                    html_code += f"<div class='item-text'>"
                    html_code += f"{icon}<b>{item['author']}</b> {t_str}"
                    html_code += "</div>"
            
            html_code += "</td>"
    html_code += "</tr>"

html_code += "</tbody></table>"

# 화면 출력 (노스크롤)
st.html(html_code)

# ================================================================= 
# 7. 하단 일정 선택 메뉴 (수정/삭제용)
# ================================================================= 
if not df.empty:
    with st.expander("🔍 일정 상세 보기 / 수정 / 삭제"):
        month_items = [
            f"[{row['start_time'].strftime('%m/%d %H:%M')}] {row['author']} - {row['content']}" 
            for _, row in df.iterrows() 
            if row['start_time'].year == st.session_state.curr_year and row['start_time'].month == st.session_state.curr_month
        ]
        if month_items:
            selected_item_str = st.selectbox("일정 선택", month_items)
            if selected_item_str:
                for _, row in df.iterrows():
                    match_str = f"[{row['start_time'].strftime('%m/%d %H:%M')}] {row['author']} - {row['content']}"
                    if match_str == selected_item_str:
                        if st.button("✏️ 이 일정 수정 / 삭제하기", use_container_width=True):
                            schedule_dialog(row)
                        break
        else:
            st.write("이번 달에 등록된 일정이 없습니다.")
