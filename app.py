import streamlit as st
import pandas as pd
from datetime import datetime, timezone, date
from supabase import create_client
import calendar
import html

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

# 기본 고정 리스트
AUTHORS = ["Xave","Tina","Rosa","Jina","Rina"]
CATEGORIES = ["약속", "기타"]

# 기본 색상 (DB 마이그레이션에서 동일한 기본값을 넣어두세요)
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
    hex_color = (hex_color or "").lstrip('#')
    if len(hex_color) != 6:
        return (200, 200, 200)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (200, 200, 200)

def text_color_for_bg(hex_color: str):
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.299*r + 0.587*g + 0.114*b) / 255
    return "#000000" if luminance > 0.6 else "#FFFFFF"

def blend_colors(hex1: str, hex2: str, ratio=0.65):
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
    cat_colors = {}
    auth_colors = {}
    try:
        resp_c = supabase.table("category_colors").select("*").execute()
        if resp_c and getattr(resp_c, "data", None):
            for r in resp_c.data:
                cat_colors[r.get("category")] = r.get("color")
        resp_a = supabase.table("author_colors").select("*").execute()
        if resp_a and getattr(resp_a, "data", None):
            for r in resp_a.data:
                auth_colors[r.get("author")] = r.get("color")
    except Exception:
        st.warning("카테고리/작성자 색상 테이블을 읽을 수 없습니다. (category_colors, author_colors) — 기본값으로 동작합니다.")
    for c in CATEGORIES:
        if c not in cat_colors:
            cat_colors[c] = DEFAULT_CATEGORY_COLORS.get(c, "#cccccc")
    for a in AUTHORS:
        if a not in auth_colors:
            auth_colors[a] = DEFAULT_AUTHOR_COLORS.get(a, "#888888")
    return cat_colors, auth_colors

def persist_color_mappings(cat_colors: dict, auth_colors: dict):
    try:
        cat_rows = [{"category": k, "color": v} for k, v in cat_colors.items()]
        if cat_rows:
            supabase.table("category_colors").upsert(cat_rows).execute()
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
    try:
        response = supabase.table(TABLE_NAME).select("*").order("start_time").execute()
        df = pd.DataFrame(response.data)
        if df is None or df.empty:
            return pd.DataFrame()
        # 안전하게 파싱: ISO 문자열을 UTC로 변환 (errors='coerce'로 잘못된 값은 NaT)
        df['start_time'] = pd.to_datetime(df.get('start_time'), utc=True, errors='coerce')
        df['end_time'] = pd.to_datetime(df.get('end_time'), utc=True, errors='coerce')
        # fallback: 만약 end_time이 비어있으면 start_time 사용
        df['end_time'] = df['end_time'].fillna(df['start_time'])
        # date 컬럼 추가 (날짜 범위 비교 용)
        df['start_date'] = df['start_time'].dt.date
        df['end_date'] = df['end_time'].dt.date
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()

def save_schedule(data):
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
    try:
        supabase.table(TABLE_NAME).delete().eq("id", post_id).execute()
        return True
    except Exception as e:
        st.error(f"삭제 중 오류: {e}")
        return False

# -----------------------------------------------------------------
# 일정 입력/수정 Dialog
# -----------------------------------------------------------------
@st.dialog("일정 입력 및 수정")
def schedule_dialog(target_data=None):
    is_edit = target_data is not None
    title = "일정 수정하기" if is_edit else "새 일정 등록하기"
    st.subheader(title)

    # 안전하게 인덱스 계산 (값이 목록에 없을 수 있음)
    def safe_index(lst, val, default=0):
        try:
            return lst.index(val)
        except Exception:
            return default

    if "dialog_data" not in st.session_state or is_edit:
        if is_edit:
            st.session_state.dialog_data = {
                "category": target_data.get('category'),
                "author": target_data.get('author'),
                "start_dt": target_data.get('start_time').date() if target_data.get('start_time') is not None else datetime.now().date(),
                "start_tm": target_data.get('start_time').time() if target_data.get('start_time') is not None else datetime.now().time(),
                "end_dt": target_data.get('end_time').date() if target_data.get('end_time') is not None else datetime.now().date(),
                "end_tm": target_data.get('end_time').time() if target_data.get('end_time') is not None else datetime.now().time(),
                "content": target_data.get('content', "")
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

    category = st.selectbox("종류", CATEGORIES, index=safe_index(CATEGORIES, st.session_state.dialog_data["category"]))
    author = st.selectbox("작성자", AUTHORS, index=safe_index(AUTHORS, st.session_state.dialog_data["author"]))

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
            payload['id'] = target_data.get('id')
        if save_schedule(payload):
            st.success("저장되었습니다!")
            if "dialog_data" in st.session_state:
                del st.session_state.dialog_data
            st.rerun()

# -----------------------------------------------------------------
# Streamlit query-param 호환성 래퍼 (호환성 문제로 인한 AttributeError 방지)
# -----------------------------------------------------------------
def get_query_params_safe():
    """가능한 query-get API를 사용해 파라미터를 얻고, 없으면 빈 dict 반환."""
    try:
        if hasattr(st, "experimental_get_query_params"):
            return st.experimental_get_query_params()
        if hasattr(st, "get_query_params"):
            return st.get_query_params()
    except Exception:
        pass
    return {}

def clear_query_params_safe():
    """가능한 query-set API를 사용해 파라미터를 지움(없으면 무시)."""
    try:
        if hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params()
            return
        if hasattr(st, "set_query_params"):
            st.set_query_params()
            return
    except Exception:
        pass
    # 아무 것도 못하면 그냥 무시

# -----------------------------------------------------------------
# 메인 화면 (월 달력 전용)
# -----------------------------------------------------------------
st.set_page_config(page_title="Xave's Family Scheduler", layout="wide")
st.title("📅 Xave's Family Scheduler")

# 색상 매핑 로드
category_colors, author_colors = load_color_mappings()

# 사이드바: 색상 편집 (DB에 저장 가능)
st.sidebar.header("달력 색상 설정 (고정값 - DB 저장)")
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
        st.success("색상 정보가 DB에 저장되었습니다.")
        category_colors = st.session_state.edit_category_colors.copy()
        author_colors = st.session_state.edit_author_colors.copy()
        st.rerun()

st.sidebar.divider()
st.sidebar.markdown("DB에 테이블이 없으면 제공된 SQL을 Supabase SQL 에디터에서 실행하세요.")

# 상단: 년/월 선택 (이전 / 중앙 입력 / 다음)
today = datetime.now().date()
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month

def prev_month():
    y = st.session_state["cal_year"]
    m = st.session_state["cal_month"]
    if m == 1:
        st.session_state["cal_year"] = y - 1
        st.session_state["cal_month"] = 12
    else:
        st.session_state["cal_month"] = m - 1

def next_month():
    y = st.session_state["cal_year"]
    m = st.session_state["cal_month"]
    if m == 12:
        st.session_state["cal_year"] = y + 1
        st.session_state["cal_month"] = 1
    else:
        st.session_state["cal_month"] = m + 1

col_nav_prev, col_nav_mid, col_nav_next = st.columns([1,6,1])
with col_nav_prev:
    st.button("◀ 이전 달", on_click=prev_month)
with col_nav_mid:
    # 중앙 컨트롤에 바로 session_state 키를 바인딩하면 prev/next에서 변경 시 자동 반영됩니다.
    year = st.number_input("연도", min_value=1970, max_value=2100, value=st.session_state.cal_year, key="cal_year")
    month = st.selectbox("월", list(range(1,13)), index=st.session_state.cal_month-1, key="cal_month")
with col_nav_next:
    st.button("다음 달 ▶", on_click=next_month)

# 일정 추가
if st.button("➕ 일정 추가", type="primary"):
    schedule_dialog()

st.divider()

# 일정 로드
df = load_schedules()

# 편집 쿼리 파라미터 처리: ?edit_id=<id>
query_params = get_query_params_safe()
if "edit_id" in query_params and query_params["edit_id"]:
    edit_id_val = query_params["edit_id"][0]
    # find event in df (cast id to str for matching)
    if not df.empty:
        match = df[df['id'].astype(str) == str(edit_id_val)]
        if not match.empty:
            # take first match and open dialog
            row = match.iloc[0].to_dict()
            # convert Timestamp to python datetime for schedule_dialog expectations
            for k in ("start_time", "end_time"):
                if k in row and pd.notna(row[k]):
                    # pandas Timestamp -> python datetime
                    try:
                        row[k] = pd.to_datetime(row[k]).to_pydatetime()
                    except Exception:
                        pass
            schedule_dialog(row)
    # clear the param to avoid re-opening repeatedly
    clear_query_params_safe()

# 달력 렌더링
year = st.session_state.cal_year
month = st.session_state.cal_month
st.subheader(f"📅 {year}년 {month}월 달력")
cal = calendar.Calendar(firstweekday=0)  # Monday=0
month_weeks = cal.monthdayscalendar(year, month)

# 헤더
weekdays = ["월","화","수","목","금","토","일"]
hd_cols = st.columns(7)
for i, dname in enumerate(weekdays):
    with hd_cols[i]:
        st.markdown(f"**{dname}**")

# 칸 채우기
for week in month_weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.write("")
                continue
            cell_date = date(year, month, day)
            st.markdown(f"**{day}**")
            if df.empty:
                continue
            # start_date <= cell_date <= end_date
            day_events = df[(df['start_date'] <= cell_date) & (df['end_date'] >= cell_date)].copy()
            if day_events.empty:
                continue
            day_events = day_events.sort_values(by='start_time')
            # 각 이벤트를 한 줄씩 표시 (간결하게), 텍스트 색으로 category/author를 표시
            for idx_local, (idx, ev) in enumerate(day_events.iterrows()):
                ev_id = ev.get('id', f"{idx}_{day}")
                cat = ev.get('category', CATEGORIES[0])
                auth = ev.get('author', AUTHORS[0])
                cat_col = category_colors.get(cat, DEFAULT_CATEGORY_COLORS.get(cat, "#000000"))
                auth_col = author_colors.get(auth, DEFAULT_AUTHOR_COLORS.get(auth, "#000000"))
                # 라벨 HTML: 종류(카테고리 컬러) | 작성자(작성자 컬러)
                escaped_cat = html.escape(str(cat))
                escaped_auth = html.escape(str(auth))
                label_html = (f'<span style="color:{cat_col};font-weight:600;">{escaped_cat}</span>'
                              f' <span style="color:#888888;">|</span> '
                              f'<span style="color:{auth_col};">{escaped_auth}</span>')
                # 링크로 감싸서 클릭시 ?edit_id=<id> 로 이동 -> 페이지 로드 시 dialog 오픈
                label_link = f'<a href="?edit_id={html.escape(str(ev_id))}" style="text-decoration:none;">{label_html}</a>'
                # 한 줄에 (라벨(링크) | 삭제 버튼)
                c_label, c_del = st.columns([9,1])
                with c_label:
                    st.markdown(label_link, unsafe_allow_html=True)
                del_key = f"del_{ev_id}_{day}_{idx_local}"
                with c_del:
                    if st.button("🗑️", key=del_key):
                        if delete_schedule(ev.get('id')):
                            st.rerun()

st.divider()
st.caption("참고: 일정 항목은 '종류 | 작성자' 텍스트로 표시됩니다. 텍스트 클릭하면 수정(모달)이 열리고, 삭제는 우측 아이콘으로 가능합니다. 색상 저장은 사이드바에서 수행하세요.")
