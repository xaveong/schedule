import streamlit as st  
import pandas as pd  
from datetime import datetime, timezone, date  
from supabase import create_client  
import calendar  
import html

# =================================================================  
# [설정] Supabase 연결 정보  
# =================================================================  
SUPABASE_URL = st.secrets["supabase_url"]  
SUPABASE_KEY = st.secrets["supabase_key"]

@st.cache_resource  
def init_supabase():  
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()  
TABLE_NAME = "schedule"

AUTHORS = ["Xave","Tina","Rosa","Jina","Rina"]  
CATEGORIES = ["약속", "기타"]

DEFAULT_CATEGORY_COLORS = {"약속": "#FF8A65", "기타": "#90CAF9"}  
DEFAULT_AUTHOR_COLORS = {  
    "Xave": "#6A1B9A", "Tina": "#2E7D32", "Rosa": "#C62828", "Jina": "#F9A825", "Rina": "#1565C0",  
}

# -----------------------------------------------------------------  
# 유틸리티  
# -----------------------------------------------------------------  
def hex_to_rgb(hex_color: str):  
    hex_color = (hex_color or "").lstrip('#')  
    if len(hex_color) != 6: return (200, 200, 200)  
    try: return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  
    except: return (200, 200, 200)

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

def ev_series_to_dialog_dict(ev_series):  
    ev = ev_series.to_dict()  
    for k in ("start_time", "end_time"):  
        if k in ev and pd.notna(ev[k]):  
            try: ev[k] = pd.to_datetime(ev[k]).to_pydatetime()  
            except: pass  
    return ev

# -----------------------------------------------------------------  
# DB 연동 함수  
# -----------------------------------------------------------------  
def load_color_mappings():  
    cat_colors, auth_colors = {}, {}  
    try:  
        resp_c = supabase.table("category_colors").select("*").execute()  
        if resp_c and resp_c.data:  
            for r in resp_c.data: cat_colors[r.get("category")] = r.get("color")  
        resp_a = supabase.table("author_colors").select("*").execute()  
        if resp_a and resp_a.data:  
            for r in resp_a.data: auth_colors[r.get("author")] = r.get("color")  
    except:  
        st.warning("색상 테이블 로드 실패 - 기본값 사용")  
      
    for c in CATEGORIES: cat_colors.setdefault(c, DEFAULT_CATEGORY_COLORS.get(c, "#cccccc"))  
    for a in AUTHORS: auth_colors.setdefault(a, DEFAULT_AUTHOR_COLORS.get(a, "#888888"))  
    return cat_colors, auth_colors

def persist_color_mappings(cat_colors, auth_colors):  
    try:  
        supabase.table("category_colors").upsert([{"category": k, "color": v} for k, v in cat_colors.items()]).execute()  
        supabase.table("author_colors").upsert([{"author": k, "color": v} for k, v in auth_colors.items()]).execute()  
        return True  
    except Exception as e:  
        st.error(f"색상 저장 실패: {e}")  
        return False

def load_schedules():  
    try:  
        response = supabase.table(TABLE_NAME).select("*").order("start_time").execute()  
        df = pd.DataFrame(response.data)  
        if df.empty: return df  
        df['start_time'] = pd.to_datetime(df['start_time'], utc=True, errors='coerce')  
        df['end_time'] = pd.to_datetime(df['end_time'], utc=True, errors='coerce').fillna(df['start_time'])  
        df['start_date'] = df['start_time'].dt.date  
        df['end_date'] = df['end_time'].dt.date  
        return df  
    except Exception as e:  
        st.error(f"데이터 로드 오류: {e}")  
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
        st.error(f"저장 오류: {e}")  
        return False

def delete_schedule(post_id):  
    try:  
        supabase.table(TABLE_NAME).delete().eq("id", post_id).execute()  
        return True  
    except Exception as e:  
        st.error(f"삭제 오류: {e}")  
        return False

# -----------------------------------------------------------------  
# 일정 입력/수정/삭제 Dialog  
# -----------------------------------------------------------------  
@st.dialog("일정 상세 정보")  
def schedule_dialog(target_data=None):  
    is_edit = target_data is not None  
    title = "일정 수정 및 삭제" if is_edit else "새 일정 등록하기"  
    st.subheader(title)

    def safe_index(lst, val, default=0):  
        try: return lst.index(val)  
        except: return default

    if "dialog_data" not in st.session_state or is_edit:  
        if is_edit:  
            st.session_state.dialog_data = {  
                "id": target_data.get('id'),  
                "category": target_data.get('category'),  
                "author": target_data.get('author'),  
                "start_dt": target_data.get('start_time').date() if target_data.get('start_time') else datetime.now().date(),  
                "start_tm": target_data.get('start_time').time() if target_data.get('start_time') else datetime.now().time(),  
                "end_dt": target_data.get('end_time').date() if target_data.get('end_time') else datetime.now().date(),  
                "end_tm": target_data.get('end_time').time() if target_data.get('end_time') else datetime.now().time(),  
                "content": target_data.get('content', "")  
            }  
        else:  
            st.session_state.dialog_data = {  
                "category": CATEGORIES[0], "author": AUTHORS[0],  
                "start_dt": datetime.now().date(), "start_tm": datetime.now().time(),  
                "end_dt": datetime.now().date(), "end_tm": datetime.now().time(),  
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

    st.divider()  
      
    col_save, col_del = st.columns([1, 1])  
    with col_save:  
        if st.button("저장하기", type="primary", use_container_width=True):  
            payload = {  
                "category": category, "author": author,  
                "start_time": datetime.combine(start_dt, start_tm).isoformat(),  
                "end_time": datetime.combine(end_dt, end_tm).isoformat(),  
                "content": content  
            }  
            if is_edit: payload['id'] = st.session_state.dialog_data.get('id')  
            if save_schedule(payload):  
                st.success("저장되었습니다!")  
                st.rerun()  
      
    with col_del:  
        if is_edit:  
            if st.button("삭제하기", use_container_width=True):  
                if delete_schedule(st.session_state.dialog_data.get('id')):  
                    st.success("삭제되었습니다!")  
                    st.rerun()

# -----------------------------------------------------------------  
# 메인 UI  
# -----------------------------------------------------------------  
st.set_page_config(page_title="Xave's Family Scheduler", layout="wide")  
st.title("📅 Xave's Family Scheduler")

category_colors, author_colors = load_color_mappings()

# 사이드바 설정 (생략 없이 유지)  
st.sidebar.header("🎨 색상 설정")  
if "edit_category_colors" not in st.session_state: st.session_state.edit_category_colors = category_colors.copy()  
if "edit_author_colors" not in st.session_state: st.session_state.edit_author_colors = author_colors.copy()

for c in CATEGORIES:  
    st.session_state.edit_category_colors[c] = st.sidebar.color_picker(f"{c} 색", st.session_state.edit_category_colors.get(c), key=f"cat_{c}")  
for a in AUTHORS:  
    st.session_state.edit_author_colors[a] = st.sidebar.color_picker(f"{a} 색", st.session_state.edit_author_colors.get(a), key=f"auth_{a}")

if st.sidebar.button("색상 DB 저장"):  
    if persist_color_mappings(st.session_state.edit_category_colors, st.session_state.edit_author_colors):  
        st.rerun()

# 날짜 네비게이션  
today = datetime.now().date()  
if "cal_year" not in st.session_state: st.session_state.cal_year = today.year  
if "cal_month" not in st.session_state: st.session_state.cal_month = today.month

def prev_month():  
    if st.session_state.cal_month == 1:  
        st.session_state.cal_year -= 1  
        st.session_state.cal_month = 12  
    else: st.session_state.cal_month -= 1

def next_month():  
    if st.session_state.cal_month == 12:  
        st.session_state.cal_year += 1  
        st.session_state.cal_month = 1  
    else: st.session_state.cal_month += 1

col_prev, col_mid, col_next = st.columns([1,6,1])  
with col_prev: st.button("◀", on_click=prev_month)  
with col_mid:  
    st.markdown(f"<h3 style='text-align: center;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)  
with col_next: st.button("▶", on_click=next_month)

if st.button("➕ 새 일정 추가", type="primary", use_container_width=True):  
    schedule_dialog()

st.divider()

# 달력 렌더링 부분  
df = load_schedules()  
year, month = st.session_state.cal_year, st.session_state.cal_month  
cal = calendar.Calendar(firstweekday=0)  
month_weeks = cal.monthdayscalendar(year, month)

weekdays = ["월","화","수","목","금","토","일"]  
hd_cols = st.columns(7)  
for i, dname in enumerate(weekdays):  
    hd_cols[i].markdown(f"**{dname}**")

for week in month_weeks:  
    cols = st.columns(7)  
    for i, day in enumerate(week):  
        with cols[i]:  
            if day == 0: continue  
            st.markdown(f"**{day}**")  
            cell_date = date(year, month, day)  
              
            if not df.empty:  
                # 해당 날짜의 일정 필터링 및 시간순 정렬  
                day_events = df[(df['start_date'] <= cell_date) & (df['end_date'] >= cell_date)].sort_values(by='start_time')  
                  
                for idx_local, (idx, ev) in enumerate(day_events.iterrows()):  
                    cat = ev.get('category', CATEGORIES[0])  
                    auth = ev.get('author', AUTHORS[0])  
                      
                    # 설정된 색상 가져오기  
                    cat_col = category_colors.get(cat, "#000000")  
                    auth_col = author_colors.get(auth, "#000000")  
                      
                    try:  
                        time_str = ev['start_time'].astimezone(timezone.utc).strftime("%H:%M")  
                    except:  
                        time_str = ev['start_time'].strftime("%H:%M") if not pd.isna(ev['start_time']) else ""

                    # [개선] 텍스트 컬러 적용을 위한 HTML 스타일 버튼  
                    # Streamlit 버튼은 색상 변경이 안되므로,   
                    # HTML/CSS를 사용하여 버튼처럼 보이게 하고,   
                    # st.button의 key를 활용해 클릭 이벤트를 처리합니다.  
                      
                    # 텍스트 레이블 생성: 시간 (종류색|작성자색)  
                    label_html = f"""  
                        <div style="margin-bottom: 2px; font-size: 0.85rem; line-height: 1.2;">  
                            <span style="color: #666;">{time_str}</span>   
                            <span style="color: {cat_col}; font-weight: bold;">{cat}</span>|  
                            <span style="color: {auth_col}; font-weight: bold;">{auth}</span>  
                        </div>  
                    """  
                    st.markdown(label_html, unsafe_allow_html=True)  
                      
                    # 클릭 시 다이얼로그를 띄우기 위한 투명 버튼 (텍스트 바로 아래 배치)  
                    if st.button(f" Details", key=f"btn_{ev.get('id')}_{day}_{idx_local}",   
                                 help="상세보기 및 수정",   
                                 use_container_width=True,  
                                 type="secondary"):  
                        schedule_dialog(ev_series_to_dialog_dict(ev))  
                      
                    # 일정 간 구분을 위한 작은 공백  
                    st.markdown("<br>", unsafe_allow_html=True)

st.divider()  
st.caption("💡 'Details' 버튼을 클릭하면 상세 내용을 확인하고 수정하거나 삭제할 수 있습니다.")  
