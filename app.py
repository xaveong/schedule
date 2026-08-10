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

# ================================================================= 
# 2. 색상 및 기본 설정값 정의
# ================================================================= 
AUTHORS = ["Xave", "Tina", "Rosa", "Jina", "Rina"] 
CATEGORIES = ["약속", "행사", "기타"]

AUTHOR_COLORS = {
    "Xave": "#2B59C3",   # 파랑
    "Tina": "#9B51E0",   # 보라
    "Rosa": "#E0519B",   # 핑크
    "Jina": "#27AE60",   # 초록
    "Rina": "#E67E22"    # 주황
}

CATEGORY_COLORS = {
    "약속": "🔴", 
    "행사": "🟢", 
    "기타": "🟡"  
}

# ================================================================= 
# 3. 데이터 처리 함수 (Supabase CRUD)
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
# 4. UI 커스텀 CSS (모바일 강제 가로 달력 레이아웃 보장)
# ================================================================= 
st.markdown("""
    <style>
    /* 1. 모바일 전체 화면 여백 최소화 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
        max-width: 100% !important;
    }

    /* 2. Streamlit이 컬럼을 세로로 쌓지 못하도록 강제 가로(Row) 고정 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 1px !important;
        width: 100% !important;
    }

    /* 3. 7개 컬럼 너비를 정확히 1/7로 균등 분할 */
    [data-testid="column"] {
        width: calc(100% / 7) !important;
        min-width: calc(100% / 7) !important;
        max-width: calc(100% / 7) !important;
        flex: 1 1 calc(100% / 7) !important;
        padding: 0px !important;
    }

    /* 4. 날짜 카드 컨테이너 여백/패딩 최소화 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 1px !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }

    /* 5. 요일 헤더 */
    .weekday-header {
        text-align: center;
        font-weight: bold;
        padding: 4px 0px;
        background-color: #f1f3f5;
        border-radius: 3px;
        font-size: 11px;
        margin-bottom: 2px;
        border: 1px solid #dee2e6;
    }

    /* 6. 날짜 숫자 스타일 */
    .day-num {
        font-weight: bold;
        font-size: 11px;
        margin-bottom: 2px;
        color: #333;
        line-height: 1.1;
    }
    .today-num {
        color: #1c7ed6 !important;
        font-weight: 900;
    }

    /* 7. popover (일정) 버튼 컴팩트화 */
    div[data-testid="stPopover"] {
        width: 100% !important;
    }
    div[data-testid="stPopover"] > button {
        padding: 1px 2px !important;
        font-size: 9px !important;
        line-height: 1.1 !important;
        min-height: 18px !important;
        height: auto !important;
        margin-bottom: 2px !important;
        width: 100% !important;
        text-align: left !important;
        border: 1px solid #e0e0e0 !important;
        background-color: #ffffff !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        border-radius: 3px !important;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #339af0 !important;
        background-color: #e8f4fe !important;
    }

    /* 8. 아주 좁은 화면(380px 이하)을 위한 미세 조율 */
    @media (max-width: 380px) {
        .weekday-header {
            font-size: 10px;
            padding: 2px 0px;
        }
        .day-num {
            font-size: 10px;
        }
        div[data-testid="stPopover"] > button {
            font-size: 8px !important;
            padding: 1px 1px !important;
            min-height: 16px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ================================================================= 
# 5. UI 컴포넌트 (일정 작성/수정 Dialog)
# ================================================================= 
@st.dialog("일정 작성 및 수정") 
def schedule_dialog(target_data=None): 
    is_edit = target_data is not None 
    
    def_cat = target_data['category'] if is_edit else CATEGORIES[0]
    def_auth = target_data['author'] if is_edit else AUTHORS[0]
    
    now_kst = datetime.now(KST)
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
# 6. 메인 화면 구성
# ================================================================= 
st.title("📅 Xave's Family Scheduler")

# 상단 컨트롤 바
col_ctrl1, col_ctrl2, col_btn = st.columns([2, 2, 2])
now_dt = datetime.now(KST)

with col_ctrl1:
    selected_year = st.selectbox("연도", range(now_dt.year - 2, now_dt.year + 3), index=2, label_visibility="collapsed")
with col_ctrl2:
    selected_month = st.selectbox("월", range(1, 13), index=now_dt.month - 1, label_visibility="collapsed")
with col_btn:
    if st.button("➕ 일정 추가", type="primary", use_container_width=True): 
        schedule_dialog()

# 범례(Legend)
legend_html = "<div style='font-size: 11px; margin-bottom: 6px; line-height: 1.4;'>"
legend_html += "<b>[종류]</b> "
for cat, icon in CATEGORY_COLORS.items():
    legend_html += f"<span style='margin-right: 6px;'>{icon}{cat}</span>"
legend_html += "<br><b>[작성자]</b> "
for auth, color in AUTHOR_COLORS.items():
    legend_html += f"<span style='margin-right: 6px; color:{color}; font-weight:bold;'>● {auth}</span>"
legend_html += "</div>"
st.markdown(legend_html, unsafe_allow_html=True)

st.divider()

# 데이터 로드 및 월별/일별 매핑
df = load_schedules()

schedules_by_day = {}
if not df.empty:
    for _, row in df.iterrows():
        st_dt = row['start_time']
        if st_dt.year == selected_year and st_dt.month == selected_month:
            day = st_dt.day
            if day not in schedules_by_day:
                schedules_by_day[day] = []
            schedules_by_day[day].append(row)

# ================================================================= 
# 7. 월 달력 렌더링
# ================================================================= 

# 요일 헤더 표시 (일요일 시작)
weekdays = ["일", "월", "화", "수", "목", "금", "토"]
cols = st.columns(7)
for idx, day_name in enumerate(weekdays):
    color = "red" if idx == 0 else ("blue" if idx == 6 else "black")
    cols[idx].markdown(f"<div class='weekday-header' style='color:{color};'>{day_name}</div>", unsafe_allow_html=True)

# 주 단위 달력 출력
cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdayscalendar(selected_year, selected_month)

for week in month_days:
    day_cols = st.columns(7)
    for idx, day in enumerate(week):
        with day_cols[idx]:
            with st.container(border=True):
                if day == 0:
                    st.markdown("<div style='min-height: 40px; opacity: 0.2;'>&nbsp;</div>", unsafe_allow_html=True)
                else:
                    is_today = (selected_year == now_dt.year and selected_month == now_dt.month and day == now_dt.day)
                    num_class = "day-num today-num" if is_today else "day-num"
                    
                    # 스마트폰 폭을 고려해 오늘 표시를 간결하게 변경
                    day_label = f"{day} (오늘)" if is_today else f"{day}"
                    
                    st.markdown(f"<div class='{num_class}'>{day_label}</div>", unsafe_allow_html=True)
                    
                    if day in schedules_by_day:
                        for item in schedules_by_day[day]:
                            icon = CATEGORY_COLORS.get(item['category'], '⚪')
                            auth_color = AUTHOR_COLORS.get(item['author'], '#333333')
                            time_str = item['start_time'].strftime("%H:%M")
                            
                            # 버튼 라벨에 성함 앞글자 또는 이름만 출력하여 자리 차지 최소화
                            btn_label = f"{icon}{item['author']} {time_str}"
                            
                            with st.popover(btn_label, use_container_width=True):
                                st.markdown("### 📌 일정 상세 정보")
                                st.markdown(f"**종류:** {icon} {item['category']}")
                                st.markdown(f"**작성자:** <b style='color:{auth_color};'>{item['author']}</b>", unsafe_allow_html=True)
                                st.markdown(f"**시간:** {item['start_time'].strftime('%m/%d %H:%M')} ~ {item['end_time'].strftime('%H:%M')}")
                                st.markdown(f"**내용:**\n{item['content']}")
                                st.divider()
                                
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button("✏️ 수정", key=f"edit_{item['id']}", use_container_width=True):
                                        schedule_dialog(item)
                                with c2:
                                    if st.button("🗑️ 삭제", key=f"del_{item['id']}", type="secondary", use_container_width=True):
                                        if delete_schedule(item['id']):
                                            st.success("삭제되었습니다.")
                                            st.rerun()
                    else:
                        st.markdown("<div style='min-height: 20px;'></div>", unsafe_allow_html=True)
