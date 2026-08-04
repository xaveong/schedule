import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
from supabase import create_client
import calendar

# =================================================================
# [설정] Supabase 연결 정보 (st.secrets 사용 권장)
# =================================================================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()
TABLE_NAME = "schedule"

# 기본 고정 리스트 (앱에서 사용할 카테고리/작성자 목록 — 필요시 DB로 따로 관리 가능)
AUTHORS = ["Xave","Tina","Rosa","Jina","Rina"]
CATEGORIES = ["약속", "기타"]

# 기본 색상 (마이그레이션을 통해 DB에도 삽입되는 기본값)
DEFAULT_CATEGORY_COLORS = {
    "약속": "#FF8A65",
    "기타": "#90CAF9",
}
DEFAULT_AUTHOR_COLORS = {
    "Xave": "#6A1B9A",
    "Tina": "#2E7D32",
    "Rosa": "#C62828",
    "Jina": "#F9A825",
    "Rina": "#1565C0",
}

# -----------------------------------------------------------------
# 유틸리티
# -----------------------------------------------------------------
def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def text_color_for_bg(hex_color: str):
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.299*r + 0.587*g + 0.114*b) / 255
    return "#000000" if luminance > 0.6 else "#FFFFFF"

def blend_colors(hex1: str, hex2: str, ratio=0.65):
    # ratio: category 비중, (1-ratio) : author 비중
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    r = int(r1*ratio + r2*(1-ratio))
    g = int(g1*ratio + g2*(1-ratio))
    b = int(b1*ratio + b2*(1-ratio))
    return f"#{r:02x}{g:02x}{b:02x}"

# -----------------------------------------------------------------
# DB 색상 매핑 로드 / 저장 함수
# -----------------------------------------------------------------
def load_color_mappings():
    """DB에서 category_colors, author_colors를 읽어와 dict 반환.
       테이블이 없거나 읽기 실패하면 기본값 반환(사용자에게 안내 표시)."""
    cat_colors = {}
    auth_colors = {}
    try:
        resp_c = supabase.table("category_colors").select("*").execute()
        if resp_c and resp_c.data:
            for r in resp_c.data:
                # 컬럼명이 'category'와 'color'로 가정
                cat_colors[r.get("category")] = r.get("color")
        # if no rows, fallback to defaults but try to insert defaults later
        resp_a = supabase.table("author_colors").select("*").execute()
        if resp_a and resp_a.data:
            for r in resp_a.data:
                auth_colors[r.get("author")] = r.get("color")
    except Exception as e:
        st.warning("카테고리/작성자 색상 테이블(category_colors, author_colors)이 Supabase에 없거나 읽을 수 없습니다. "
                   "먼저 SQL 마이그레이션을 실행해주세요. (앱은 기본 색상으로 동작합니다.)")
        # 빈 dict을 반환하면 아래에서 기본값으로 채웁니다.

    # 보완: 없는 항목은 기본값으로 채움 (DB에 삽입하는 과정은 별도 함수에서 처리)
    for c in CATEGORIES:
        if c not in cat_colors:
            cat_colors[c] = DEFAULT_CATEGORY_COLORS.get(c, "#cccccc")
    for a in AUTHORS:
        if a not in auth_colors:
            auth_colors[a] = DEFAULT_AUTHOR_COLORS.get(a, "#888888")
    return cat_colors, auth_colors

def persist_color_mappings(cat_colors: dict, auth_colors: dict):
    """DB에 현재 세팅을 upsert(업데이트/삽입) 시도합니다. 실패해도 앱 동작엔 영향 없도록 예외 처리."""
    try:
        # category_colors upsert
        cat_rows = [{"category": k, "color": v} for k, v in cat_colors.items()]
        if cat_rows:
            # supabase-py는 .upsert()를 지원합니다.
            supabase.table("category_colors").upsert(cat_rows).execute()
        # author_colors upsert
        auth_rows = [{"author": k, "color": v} for k, v in auth_colors.items()]
        if auth_rows:
            supabase.table("author_colors").upsert(auth_rows).execute()
        return True
    except Exception as e:
        st.error(f"색상 정보를 DB에 저장하지 못했습니다: {e}")
        return False

# -----------------------------------------------------------------
# 데이터 처리 함수
# -----------------------------------------------------------------
def load_schedules():
    """DB에서 모든 일정을 가져와 pandas 데이터프레임으로 변환"""
    try:
        response = supabase.table(TABLE_NAME).select("*").order("start_time").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # ISO -> timezone-aware 변환
            df['start_time'] = pd.to_datetime(df['start_time'], utc=True, errors='coerce')
            df['end_time'] = pd.to_datetime(df['end_time'], utc=True, errors='coerce')
            df['start_date'] = df['start_time'].dt.date
            df['end_date'] = df['end_time'].dt.date
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()

def save_schedule(data):
    """일정 저장 (추가 또는 수정)"""
    try:
        if 'id' in data:
            post_id = data.pop('id')
            supabase.table(TABLE_NAME).update(data).eq("id", post_id).execute()
        else:
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

# -----------------------------------------------------------------
# UI 컴포넌트 (Dialog) - 일정 입력/수정 (기존 유지)
# -----------------------------------------------------------------
@st.dialog("일정 입력 및 수정")
def schedule_dialog(target_data=None):
    is_edit = target_data is not None
    title = "일정 수정하기" if is_edit else "새 일정 등록하기"
    st.subheader(title)

    if "dialog_data" not in st.session_state or is_edit:
        if is_edit:
            st.session_state.dialog_data = {
                "category": target_data['category'],
                "author": target_data['author'],
                "start_dt": target_data['start_time'].date(),
                "start_tm": target_data['start_time'].time(),
                "end_dt": target_data['end_time'].date(),
                "end_tm": target_data['end_time'].time(),
                "content": target_data['content']
            }
        else:
            st.session_state.dialog_data = {
                "category": CATEGORIES[0],
                "author": AUTHORS[0],
                "start_dt": datetime.now().date(),
                "start_tm": datetime.now().time(),
                "end_dt": datetime.now().date(),
                "end_tm": datetime.now().time(),
                "content": ""
            }

    category = st.selectbox("종류", CATEGORIES,
                            index=CATEGORIES.index(st.session_state.dialog_data["category"]))
    author = st.selectbox("작성자", AUTHORS,
                          index=AUTHORS.index(st.session_state.dialog_data["author"]))

    col1, col2 = st.columns(2)
    with col1:
        start_dt = st.date_input("시작일", value=st.session_state.dialog_data["start_dt"])
        start_tm = st.time_input("시작 시간", value=st.session_state.dialog_data["start_tm"])
    with col2:
        end_dt = st.date_input("종료일", value=st.session_state.dialog_data["end_dt"])
        end_tm = st.time_input("종료 시간", value=st.session_state.dialog_data["end_tm"])

    content = st.text_area("내용", value=st.session_state.dialog_data["content"], placeholder="내용을 입력하세요")

    st.session_state.dialog_data.update({
        "category": category,
        "author": author,
        "start_dt": start_dt,
        "start_tm": start_tm,
        "end_dt": end_dt,
        "end_tm": end_tm,
        "content": content
    })

    start_time = datetime.combine(start_dt, start_tm)
    end_time = datetime.combine(end_dt, end_tm)

    if st.button("저장", type="primary"):
        payload = {
            "category": category,
            "author": author,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "content": content
        }
        if is_edit:
            payload['id'] = target_data['id']

        if save_schedule(payload):
            st.success("저장되었습니다!")
            if "dialog_data" in st.session_state:
                del st.session_state.dialog_data
            st.rerun()

# -----------------------------------------------------------------
# 메인 화면 구성 (월 달력 전용)
# -----------------------------------------------------------------
st.set_page_config(page_title="Xave's Family Scheduler", layout="wide")
st.title("📅 Xave's Family Scheduler")

# 로드: 색상 매핑 (DB 또는 기본값)
category_colors, author_colors = load_color_mappings()

# 사이드바: 색상 편집 UI (변경 시 DB에 저장)
st.sidebar.header("달력 색상 설정 (고정값 — DB에 저장됨)")
st.sidebar.markdown("종류 및 작성자 색상을 변경하면 아래 [색상 저장]을 눌러 DB에 반영하세요. "
                    "설정은 모든 사용자에 적용됩니다.")

# 세션에 보관해 편집 중인 값 유지
if "edit_category_colors" not in st.session_state:
    st.session_state.edit_category_colors = category_colors.copy()
if "edit_author_colors" not in st.session_state:
    st.session_state.edit_author_colors = author_colors.copy()

st.sidebar.subheader("종류별 색상")
for c in CATEGORIES:
    col = st.sidebar.color_picker(f"{c} 색", st.session_state.edit_category_colors.get(c, DEFAULT_CATEGORY_COLORS.get(c, "#cccccc")), key=f"catcol_{c}")
    st.session_state.edit_category_colors[c] = col

st.sidebar.subheader("작성자별 색상")
for a in AUTHORS:
    acol = st.sidebar.color_picker(f"{a} 색", st.session_state.edit_author_colors.get(a, DEFAULT_AUTHOR_COLORS.get(a, "#888888")), key=f"authcol_{a}")
    st.session_state.edit_author_colors[a] = acol

if st.sidebar.button("색상 저장 (DB에 반영)"):
    ok = persist_color_mappings(st.session_state.edit_category_colors, st.session_state.edit_author_colors)
    if ok:
        st.success("색상 정보가 DB에 저장되었습니다. 달력을 갱신합니다.")
        # 갱신: 로컬 매핑도 업데이트하고 화면 갱신
        category_colors = st.session_state.edit_category_colors.copy()
        author_colors = st.session_state.edit_author_colors.copy()
        st.experimental_rerun()

st.sidebar.divider()
st.sidebar.markdown("데이터베이스에 테이블이 없다는 경고가 표시되면, 위의 SQL 마이그레이션을 Supabase SQL 에디터에서 실행하세요.")

# 상단: 달력 년/월 선택
today = datetime.now().date()
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month

col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 2])
with col_nav1:
    if st.button("◀ 이전 달"):
        y, m = st.session_state.cal_year, st.session_state.cal_month
        if m == 1:
            st.session_state.cal_year -= 1
            st.session_state.cal_month = 12
        else:
            st.session_state.cal_month -= 1
        st.experimental_rerun()
with col_nav2:
    year = st.number_input("연도", min_value=1970, max_value=2100, value=st.session_state.cal_year, key="sel_year")
    st.session_state.cal_year = int(year)
with col_nav3:
    month = st.selectbox("월", list(range(1,13)), index=st.session_state.cal_month-1, key="sel_month")
    st.session_state.cal_month = int(month)

# 일정 추가 버튼
if st.button("➕ 일정 추가", type="primary"):
    schedule_dialog()

st.divider()

# 일정 로드
df = load_schedules()

# 달력 렌더링
year = st.session_state.cal_year
month = st.session_state.cal_month
st.subheader(f"📅 {year}년 {month}월 달력")
cal = calendar.Calendar(firstweekday=0)  # Monday=0
month_weeks = cal.monthdayscalendar(year, month)  # 행별 날짜 배열 (0은 빈칸)

# 헤더 (월~일)
weekdays = ["월", "화", "수", "목", "금", "토", "일"]
hd_cols = st.columns(7)
for i, dname in enumerate(weekdays):
    with hd_cols[i]:
        st.markdown(f"**{dname}**")

# 각 날짜 칸을 채움
for week in month_weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.write("")  # 빈 칸
                continue
            cell_date = date(year, month, day)
            st.markdown(f"**{day}**")
            # 날짜에 포함되는 이벤트: start_date <= cell_date <= end_date
            if df.empty:
                continue
            day_events = df[(df['start_date'] <= cell_date) & (df['end_date'] >= cell_date)].copy()
            if day_events.empty:
                continue
            # 시간 기준 정렬
            day_events = day_events.sort_values(by='start_time')
            # 출력: 시간, 작성자, 내용 요약, 편집/삭제 버튼
            for idx, ev in day_events.iterrows():
                cat = ev.get('category', CATEGORIES[0])
                auth = ev.get('author', AUTHORS[0])
                cat_col = category_colors.get(cat, DEFAULT_CATEGORY_COLORS.get(cat, "#cccccc"))
                auth_col = author_colors.get(auth, DEFAULT_AUTHOR_COLORS.get(auth, "#888888"))
                bg = blend_colors(cat_col, auth_col, ratio=0.65)
                fg = text_color_for_bg(bg)
                # 시간 문자열 (로컬 시간 포맷)
                try:
                    time_str = ev['start_time'].astimezone(timezone.utc).strftime("%H:%M")
                except Exception:
                    time_str = ev['start_time'].strftime("%H:%M") if not pd.isna(ev['start_time']) else ""
                summary = ev['content'] if isinstance(ev['content'], str) else ""
                summary_short = summary if len(summary) <= 30 else summary[:27] + "..."
                badge_html = f"""
                <div style="background:{bg};color:{fg};padding:6px;border-radius:6px;margin-bottom:6px;">
                    <div style="font-size:12px;font-weight:600;">{time_str} {ev['author']} | {ev['category']}</div>
                    <div style="font-size:12px;">{summary_short}</div>
                </div>
                """
                st.markdown(badge_html, unsafe_allow_html=True)
                c1, c2 = st.columns([1,1])
                with c1:
                    if st.button("✏️", key=f"edit_{ev['id']}_{day}"):
                        # schedule_dialog expects the event dict with id, start_time/end_time as datetimes
                        schedule_dialog(ev)
                with c2:
                    if st.button("🗑️", key=f"del_{ev['id']}_{day}"):
                        if delete_schedule(ev['id']):
                            st.rerun()

# 하단 안내
st.divider()
st.caption("참고: 색상 설정은 '색상 저장 (DB에 반영)' 버튼을 누르면 category_colors/author_colors 테이블에 반영됩니다. "
           "테이블이 없다면 Supabase SQL 에디터에서 제공된 SQL을 먼저 실행하세요.")
