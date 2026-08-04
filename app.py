import streamlit as st    
import pandas as pd    
from datetime import datetime, timedelta, timezone   
from supabase import create_client, Client

# =================================================================    
# [설정] Supabase 연결 정보 (st.secrets 사용 권장)    
# =================================================================    
# Streamlit Cloud 배포 시 Settings -> Secrets에 입력하세요.    
SUPABASE_URL = st.secrets["supabase_url"]    
SUPABASE_KEY = st.secrets["supabase_key"] 

@st.cache_resource    
def init_supabase():    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()    
TABLE_NAME = "schedule"

# 기본 설정값    
AUTHORS = ["Xave","Tina","Rosa","Jina","Rina"]     
CATEGORIES = ["약속", "기타"]

# -----------------------------------------------------------------    
# 데이터 처리 함수    
# -----------------------------------------------------------------    
def load_schedules():    
    """DB에서 모든 일정을 가져와 pandas 데이터프레임으로 변환"""    
    try:    
        response = supabase.table(TABLE_NAME).select("*").order("start_time").execute()    
        df = pd.DataFrame(response.data)    
        if not df.empty:    
            # format='ISO8601'을 추가하여 다양한 ISO 형식의 날짜 문자열을 모두 처리합니다.  
            df['start_time'] = pd.to_datetime(df['start_time'], format='ISO8601')    
            df['end_time'] = pd.to_datetime(df['end_time'], format='ISO8601')  
        return df    
    except Exception as e:    
        st.error(f"데이터 로드 중 오류: {e}")    
        return pd.DataFrame()

def save_schedule(data):    
    """일정 저장 (추가 또는 수정)"""    
    try:    
        if 'id' in data: # 수정 모드    
            post_id = data.pop('id')    
            supabase.table(TABLE_NAME).update(data).eq("id", post_id).execute()    
        else: # 신규 등록 모드    
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
# UI 컴포넌트 (Dialog) - 시간 유지 개선 버전  
# -----------------------------------------------------------------    
@st.dialog("일정 입력 및 수정")    
def schedule_dialog(target_data=None):    
    is_edit = target_data is not None    
    title = "일정 수정하기" if is_edit else "새 일정 등록하기"  
    st.subheader(title)  
        
    # [핵심] 세션 상태를 이용하여 입력 값 유지  
    # target_data가 있거나, 세션에 저장된 데이터가 없을 때 초기값 설정  
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

    # 입력 폼 (value를 session_state와 연결)  
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

    # 사용자가 값을 변경할 때마다 세션 상태를 업데이트하여 유지시킴  
    st.session_state.dialog_data.update({  
        "category": category,  
        "author": author,  
        "start_dt": start_dt,  
        "start_tm": start_tm,  
        "end_dt": end_dt,  
        "end_tm": end_tm,  
        "content": content  
    })

    # 시간 결합    
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
            # 저장 후 세션 상태 초기화하여 다음 입력 시 영향 없게 함  
            if "dialog_data" in st.session_state:  
                del st.session_state.dialog_data  
            st.rerun()

# -----------------------------------------------------------------    
# 메인 화면 구성    
# -----------------------------------------------------------------    
st.set_page_config(page_title="Xave's Family Scheduler", layout="wide")    
st.title("📅 Xave's Family Scheduler")

# 상단 컨트롤 바    
col_view, col_btn = st.columns([4, 1])    
with col_view:    
    view_mode = st.radio("보기 모드", ["주 단위", "월 단위"], horizontal=True)    
with col_btn:    
    if st.button("➕ 일정 추가", type="primary", use_container_width=True):    
        schedule_dialog()

st.divider()

# 데이터 로드    
df = load_schedules()

if not df.empty:    
    # 현재 시간을 UTC 시간대로 설정    
    now = datetime.now(timezone.utc)   
      
    if view_mode == "주 단위":    
        # 이번 주 월요일 00:00:00 기준  
        start_view = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())    
        end_view = start_view + timedelta(days=7)    
            
        filtered_df = df[(df['start_time'] >= start_view) & (df['start_time'] < end_view)]    
        st.subheader(f"📅 이번 주 일정 ({start_view.date()} ~ {end_view.date()})")  
      
    else:    
        # 이번 달 1일 00:00:00 기준  
        start_view = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)    
        next_month = (start_view + timedelta(days=32)).replace(day=1)    
        end_view = next_month    
            
        filtered_df = df[(df['start_time'] >= start_view) & (df['start_time'] < end_view)]    
        st.subheader(f"📅 {start_view.strftime('%Y년 %m월')} 일정")  

    # 일정 리스트 표시    
    for _, row in filtered_df.iterrows():    
        with st.container():    
            col_info, col_action = st.columns([9, 1])    
                
            # 표시용 텍스트 구성    
            time_range = f"{row['start_time'].strftime('%m/%d %H:%M')} ~ {row['end_time'].strftime('%m/%d %H:%M')}"    
            summary_text = f"[{row['author']}] {row['category']} : {row['content'][:20]}..."    
                
            with col_info:    
                with st.expander(f"🕒 {time_range} | {summary_text}"):    
                    st.markdown(f"**종류:** {row['category']} | **작성자:** {row['author']}")    
                    st.markdown(f"**기간:** {row['start_time']} ~ {row['end_time']}")    
                    st.write(f"**내용:**\n{row['content']}")    
                        
                    c1, c2 = st.columns(2)    
                    with c1:    
                        if st.button("✏️ 수정", key=f"edit_{row['id']}"):    
                            schedule_dialog(row)    
                    with c2:    
                        if st.button("🗑️ 삭제", key=f"del_{row['id']}", type="secondary"):    
                            if delete_schedule(row['id']):    
                                st.rerun()

            with col_action:    
                if st.button("❌", key=f"quick_del_{row['id']}"):    
                    if delete_schedule(row['id']):    
                        st.rerun()    
else:    
    st.info("일정이 없습니다. 상단의 버튼을 눌러 일정을 추가하세요!")  
