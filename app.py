import calendar
from datetime import datetime, timedelta
import html

import pandas as pd
import streamlit as st
from supabase import create_client, Client


# ================================================================
# 1. 페이지 설정 및 Supabase 연결
# ================================================================

st.set_page_config(
    page_title="Xave's Family Scheduler",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]


@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()
TABLE_NAME = "schedule"


# ================================================================
# 2. 기본 설정
# ================================================================

AUTHORS = ["Xave", "Tina", "Rosa", "Jina", "Rina"]
CATEGORIES = ["약속", "행사", "기타"]

AUTHOR_COLORS = {
    "Xave": "#2B59C3",
    "Tina": "#9B51E0",
    "Rosa": "#E0519B",
    "Jina": "#27AE60",
    "Rina": "#E67E22",
}

CATEGORY_COLORS = {
    "약속": "#FF4D4D",
    "행사": "#20B2AA",
    "기타": "#FFC107",
}


# ================================================================
# 3. 데이터 처리
# ================================================================

def load_schedules():
    """Supabase에서 일정을 가져오고 한국 시간으로 변환한다."""
    try:
        response = (
            supabase
            .table(TABLE_NAME)
            .select("*")
            .order("start_time")
            .execute()
        )

        df = pd.DataFrame(response.data)

        if not df.empty:
            df["start_time"] = (
                pd.to_datetime(df["start_time"], utc=True)
                .dt.tz_convert("Asia/Seoul")
            )
            df["end_time"] = (
                pd.to_datetime(df["end_time"], utc=True)
                .dt.tz_convert("Asia/Seoul")
            )

        return df

    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()


def save_schedule(data):
    """일정을 신규 등록하거나 수정한다."""
    try:
        data = data.copy()

        if data.get("id"):
            post_id = data.pop("id")

            (
                supabase
                .table(TABLE_NAME)
                .update(data)
                .eq("id", post_id)
                .execute()
            )
        else:
            data.pop("id", None)

            (
                supabase
                .table(TABLE_NAME)
                .insert(data)
                .execute()
            )

        return True

    except Exception as e:
        st.error(f"저장 중 오류: {e}")
        return False


def delete_schedule(post_id):
    """일정을 삭제한다."""
    try:
        (
            supabase
            .table(TABLE_NAME)
            .delete()
            .eq("id", post_id)
            .execute()
        )
        return True

    except Exception as e:
        st.error(f"삭제 중 오류: {e}")
        return False


# ================================================================
# 4. 달력 CSS
#
# 핵심 변경사항
# - min-width 제거
# - overflow-x 제거
# - 항상 화면 폭 100%
# - 7개 열을 각각 14.2857%로 고정
# - 모바일에서는 글자와 셀 높이를 축소
# ================================================================

st.markdown(
    """
    <style>
    .calendar-container {
        width: 100%;
        max-width: 100%;
        overflow: hidden;
        margin-top: 5px;
    }

    .calendar-table {
        width: 100%;
        max-width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }

    .calendar-table th {
        width: 14.2857%;
        height: 30px;
        padding: 5px 2px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        text-align: center;
        font-size: 14px;
        font-weight: bold;
        box-sizing: border-box;
    }

    .calendar-table td {
        width: 14.2857%;
        height: 110px;
        padding: 4px 3px;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        vertical-align: top;
        box-sizing: border-box;
        overflow: hidden;
    }

    .calendar-table td.today {
        background-color: #e8f4fe !important;
        border: 2px solid #339af0 !important;
    }

    .calendar-table td.other-month {
        background-color: #f8f9fa;
        opacity: 0.35;
    }

    .date-num {
        margin-bottom: 4px;
        color: #333333;
        font-size: 14px;
        font-weight: bold;
        line-height: 1.2;
    }

    .schedule-item {
        width: 100%;
        min-width: 0;
        margin-bottom: 3px;
        padding: 2px 3px;
        border-radius: 3px;
        background-color: #f1f3f5;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        overflow: hidden;
        line-height: 1.25;
        font-size: 11px;
    }

    .circle-badge {
        display: inline-block;
        width: 7px;
        min-width: 7px;
        height: 7px;
        margin-right: 3px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .schedule-text {
        display: block;
        min-width: 0;
        flex: 1;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    /* 태블릿 */
    @media (max-width: 768px) {
        .calendar-table th {
            height: 27px;
            padding: 4px 1px;
            font-size: 11px;
        }

        .calendar-table td {
            height: 85px;
            padding: 3px 2px;
        }

        .date-num {
            margin-bottom: 3px;
            font-size: 11px;
        }

        .schedule-item {
            margin-bottom: 2px;
            padding: 2px 1px;
            font-size: 8px;
        }

        .circle-badge {
            width: 5px;
            min-width: 5px;
            height: 5px;
            margin-right: 2px;
        }
    }

    /* 휴대폰 */
    @media (max-width: 480px) {
        .calendar-table th {
            height: 24px;
            padding: 3px 0;
            font-size: 9px;
        }

        .calendar-table td {
            height: 70px;
            padding: 2px 1px;
        }

        .date-num {
            margin-bottom: 2px;
            font-size: 10px;
        }

        .schedule-item {
            margin-bottom: 1px;
            padding: 1px;
            font-size: 7px;
            line-height: 1.15;
        }

        .circle-badge {
            width: 4px;
            min-width: 4px;
            height: 4px;
            margin-right: 1px;
        }
    }

    /* 아주 작은 휴대폰 */
    @media (max-width: 360px) {
        .calendar-table th {
            font-size: 8px;
        }

        .calendar-table td {
            height: 64px;
        }

        .date-num {
            font-size: 9px;
        }

        .schedule-item {
            font-size: 6px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ================================================================
# 5. 일정 작성 / 수정 Dialog
# ================================================================

@st.dialog("일정 작성 및 수정")
def schedule_dialog(target_data=None):
    is_edit = target_data is not None

    now_kst = datetime.now()

    def_cat = target_data["category"] if is_edit else CATEGORIES[0]
    def_auth = target_data["author"] if is_edit else AUTHORS[0]

    def_start_dt = (
        target_data["start_time"].date()
        if is_edit
        else now_kst.date()
    )

    def_start_tm = (
        target_data["start_time"].time()
        if is_edit
        else now_kst.time()
    )

    def_end_dt = (
        target_data["end_time"].date()
        if is_edit
        else now_kst.date()
    )

    def_end_tm = (
        target_data["end_time"].time()
        if is_edit
        else (now_kst + timedelta(hours=1)).time()
    )

    def_content = target_data["content"] if is_edit else ""

    category = st.selectbox(
        "일정 종류",
        CATEGORIES,
        index=CATEGORIES.index(def_cat) if def_cat in CATEGORIES else 0,
    )

    author = st.selectbox(
        "작성자",
        AUTHORS,
        index=AUTHORS.index(def_auth) if def_auth in AUTHORS else 0,
    )

    col1, col2 = st.columns(2)

    with col1:
        start_dt = st.date_input("시작일", def_start_dt)
        start_tm = st.time_input("시작 시간 (KST)", def_start_tm)

    with col2:
        end_dt = st.date_input("종료일", def_end_dt)
        end_tm = st.time_input("종료 시간 (KST)", def_end_tm)

    content = st.text_area(
        "내용",
        value=def_content,
        placeholder="일정 내용을 입력하세요",
    )

    start_time_obj = (
        datetime.combine(start_dt, start_tm)
        .strftime("%Y-%m-%dT%H:%M:%S+09:00")
    )

    end_time_obj = (
        datetime.combine(end_dt, end_tm)
        .strftime("%Y-%m-%dT%H:%M:%S+09:00")
    )

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button(
            "💾 저장",
            type="primary",
            use_container_width=True,
        ):
            if not content.strip():
                st.error("내용을 입력해주세요.")
                return

            payload = {
                "category": category,
                "author": author,
                "start_time": start_time_obj,
                "end_time": end_time_obj,
                "content": content,
            }

            if is_edit:
                payload["id"] = target_data["id"]

            if save_schedule(payload):
                st.success("저장되었습니다!")
                st.rerun()

    with col_btn2:
        if is_edit:
            if st.button(
                "🗑️ 삭제",
                type="secondary",
                use_container_width=True,
            ):
                if delete_schedule(target_data["id"]):
                    st.success("삭제되었습니다!")
                    st.rerun()


# ================================================================
# 6. 메인 화면
# ================================================================

st.title("📅 Xave's Family Scheduler")

now_dt = datetime.now()

col_ctrl1, col_ctrl2, col_btn = st.columns([2, 2, 2])

with col_ctrl1:
    selected_year = st.selectbox(
        "연도",
        range(now_dt.year - 2, now_dt.year + 3),
        index=2,
        label_visibility="collapsed",
    )

with col_ctrl2:
    selected_month = st.selectbox(
        "월",
        range(1, 13),
        index=now_dt.month - 1,
        label_visibility="collapsed",
    )

with col_btn:
    if st.button(
        "➕ 일정 추가",
        type="primary",
        use_container_width=True,
    ):
        schedule_dialog()


# ================================================================
# 7. 범례
# ================================================================

legend_html = """
<div style="font-size:12px; margin-bottom:8px; line-height:1.8;">
"""

legend_html += "<b>[종류]</b> "

for cat, color in CATEGORY_COLORS.items():
    legend_html += (
        f'<span style="margin-right:10px;">'
        f'<span class="circle-badge" '
        f'style="background-color:{color};"></span>'
        f'{html.escape(cat)}'
        f'</span>'
    )

legend_html += "<br><b>[작성자]</b> "

for auth, color in AUTHOR_COLORS.items():
    legend_html += (
        f'<span style="margin-right:10px; '
        f'color:{color}; font-weight:bold;">'
        f'{html.escape(auth)}'
        f'</span>'
    )

legend_html += "</div>"

st.markdown(legend_html, unsafe_allow_html=True)

st.divider()


# ================================================================
# 8. 데이터 로드
# ================================================================

df = load_schedules()

schedules_by_day = {}
schedules_by_id = {}

if not df.empty:
    for _, row in df.iterrows():
        st_dt = row["start_time"]

        if (
            st_dt.year == selected_year
            and st_dt.month == selected_month
        ):
            day = st_dt.day

            if day not in schedules_by_day:
                schedules_by_day[day] = []

            schedules_by_day[day].append(row)
            schedules_by_id[row["id"]] = row


# ================================================================
# 9. 월 달력 생성
# ================================================================

cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdayscalendar(
    selected_year,
    selected_month,
)


# ================================================================
# 10. 달력 HTML 생성
# ================================================================

html_code = """
<div class="calendar-container">
<table class="calendar-table">
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

    for day in week:

        if day == 0:
            html_code += '<td class="other-month"></td>'
            continue

        is_today = (
            selected_year == now_dt.year
            and selected_month == now_dt.month
            and day == now_dt.day
        )

        td_class = "today" if is_today else ""

        html_code += f"""
        <td class="{td_class}">
            <div class="date-num">{day}</div>
        """

        if day in schedules_by_day:
            for item in schedules_by_day[day]:

                cat_color = CATEGORY_COLORS.get(
                    item["category"],
                    "#888888",
                )

                auth_color = AUTHOR_COLORS.get(
                    item["author"],
                    "#333333",
                )

                time_str = item["start_time"].strftime("%H:%M")

                author_text = html.escape(str(item["author"]))
                content_text = html.escape(str(item["content"]))

                html_code += f"""
                <div
                    class="schedule-item"
                    title="{content_text}"
                >
                    <span
                        class="circle-badge"
                        style="background-color:{cat_color};"
                    ></span>

                    <span
                        class="schedule-text"
                        style="color:{auth_color}; font-weight:600;"
                    >
                        [{author_text}] {time_str} {content_text}
                    </span>
                </div>
                """

        html_code += "</td>"

    html_code += "</tr>"

html_code += """
</tbody>
</table>
</div>
"""


# ================================================================
# 11. 달력 출력
# ================================================================

st.markdown(
    html_code,
    unsafe_allow_html=True,
)


# ================================================================
# 12. 일정 수정 / 삭제
# ================================================================

if schedules_by_id:
    st.markdown("##### ✏️ 일정 클릭하여 수정 및 삭제")

    select_cols = st.columns(2)

    for idx, (s_id, item) in enumerate(schedules_by_id.items()):

        col_idx = idx % 2

        time_str = item["start_time"].strftime("%m/%d %H:%M")
        content_short = str(item["content"])[:15]

        btn_label = (
            f"[{time_str}] "
            f"{item['author']} - "
            f"{content_short}"
        )

        with select_cols[col_idx]:
            if st.button(
                btn_label,
                key=f"quick_edit_{s_id}",
                use_container_width=True,
            ):
                schedule_dialog(item)
# 2. 색상 및 기본 설정값 정의
# =================================================================

AUTHORS = ["Xave", "Tina", "Rosa", "Jina", "Rina"]
CATEGORIES = ["약속", "행사", "기타"]


# 작성자별 색상
AUTHOR_COLORS = {
    "Xave": "#2B59C3",
    "Tina": "#9B51E0",
    "Rosa": "#E0519B",
    "Jina": "#27AE60",
    "Rina": "#E67E22"
}


# 일정 종류별 색상
CATEGORY_COLORS = {
    "약속": "#FF4D4D",
    "행사": "#20B2AA",
    "기타": "#FFC107"
}


# =================================================================
# 3. 데이터 처리 함수
# =================================================================

def load_schedules():
    """DB에서 일정을 가져와 Asia/Seoul 타임존으로 변환"""

    try:
        response = (
            supabase
            .table(TABLE_NAME)
            .select("*")
            .order("start_time")
            .execute()
        )

        df = pd.DataFrame(response.data)

        if not df.empty:
            df["start_time"] = (
                pd.to_datetime(df["start_time"], utc=True)
                .dt.tz_convert("Asia/Seoul")
            )

            df["end_time"] = (
                pd.to_datetime(df["end_time"], utc=True)
                .dt.tz_convert("Asia/Seoul")
            )

        return df

    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()


def save_schedule(data):
    """일정 저장 - 신규 등록 및 수정"""

    try:
        if "id" in data and data["id"]:
            post_id = data.pop("id")

            (
                supabase
                .table(TABLE_NAME)
                .update(data)
                .eq("id", post_id)
                .execute()
            )

        else:
            if "id" in data:
                data.pop("id")

            (
                supabase
                .table(TABLE_NAME)
                .insert(data)
                .execute()
            )

        return True

    except Exception as e:
        st.error(f"저장 중 오류: {e}")
        return False


def delete_schedule(post_id):
    """일정 삭제"""

    try:
        (
            supabase
            .table(TABLE_NAME)
            .delete()
            .eq("id", post_id)
            .execute()
        )

        return True

    except Exception as e:
        st.error(f"삭제 중 오류: {e}")
        return False


# =================================================================
# 4. 반응형 CSS
#
# 핵심:
# - PC / Phone 모두 7열 전체 표시
# - 가로 스크롤 제거
# - 각 열은 화면 폭의 1/7
# - 모바일에서는 글자 크기 자동 축소
# =================================================================

st.markdown(
    """
    <style>

    /* ---------------------------------------------------------
       전체 페이지
       --------------------------------------------------------- */

    .calendar-container {
        width: 100%;
        max-width: 100%;
        overflow: hidden;
        margin-top: 5px;
    }


    /* ---------------------------------------------------------
       달력 테이블
       --------------------------------------------------------- */

    .calendar-table {
        width: 100%;
        max-width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }


    /* ---------------------------------------------------------
       요일 헤더
       --------------------------------------------------------- */

    .calendar-table th {
        background-color: #f8f9fa;
        text-align: center;
        padding: 6px 2px;
        font-size: clamp(10px, 1.4vw, 14px);
        font-weight: bold;
        border: 1px solid #dee2e6;
        height: 30px;
    }


    /* ---------------------------------------------------------
       날짜 셀
       --------------------------------------------------------- */

    .calendar-table td {
        border: 1px solid #dee2e6;
        vertical-align: top;

        padding: clamp(2px, 0.5vw, 6px);

        height: clamp(75px, 10vw, 125px);

        width: 14.2857%;

        background-color: #ffffff;

        overflow: hidden;
    }


    /* ---------------------------------------------------------
       날짜 숫자
       --------------------------------------------------------- */

    .date-num {
        font-weight: bold;

        font-size: clamp(10px, 1.5vw, 15px);

        margin-bottom: clamp(2px, 0.4vw, 5px);

        color: #333;

        line-height: 1.2;
    }


    /* ---------------------------------------------------------
       오늘 날짜
       --------------------------------------------------------- */

    .today {
        background-color: #e8f4fe !important;

        border: 2px solid #339af0 !important;
    }


    /* ---------------------------------------------------------
       이전 / 다음 달 날짜
       --------------------------------------------------------- */

    .other-month {
        background-color: #f8f9fa;

        opacity: 0.35;
    }


    /* ---------------------------------------------------------
       일정 항목
       --------------------------------------------------------- */

    .schedule-item {
        font-size: clamp(7px, 1.15vw, 12px);

        line-height: 1.25;

        margin-bottom: clamp(1px, 0.3vw, 4px);

        padding: clamp(1px, 0.3vw, 3px);

        border-radius: 3px;

        background-color: #f1f3f5;

        white-space: nowrap;

        overflow: hidden;

        text-overflow: ellipsis;

        display: flex;

        align-items: center;

        width: 100%;

        box-sizing: border-box;
    }


    /* ---------------------------------------------------------
       일정 내용
       --------------------------------------------------------- */

    .schedule-text {
        overflow: hidden;

        text-overflow: ellipsis;

        white-space: nowrap;

        min-width: 0;

        display: block;

        flex: 1;
    }


    /* ---------------------------------------------------------
       일정 종류 원형 표시
       --------------------------------------------------------- */

    .circle-badge {
        display: inline-block;

        width: clamp(4px, 0.7vw, 7px);

        height: clamp(4px, 0.7vw, 7px);

        min-width: clamp(4px, 0.7vw, 7px);

        border-radius: 50%;

        margin-right: clamp(1px, 0.3vw, 4px);

        flex-shrink: 0;
    }


    /* ---------------------------------------------------------
       Streamlit 기본 여백 조정
       --------------------------------------------------------- */

    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }


    /* ---------------------------------------------------------
       태블릿
       --------------------------------------------------------- */

    @media (max-width: 768px) {

        .calendar-table th {
            padding: 4px 1px;

            font-size: 11px;
        }

        .calendar-table td {
            padding: 3px 2px;

            height: 82px;
        }

        .date-num {
            font-size: 11px;

            margin-bottom: 3px;
        }

        .schedule-item {
            font-size: 8px;

            padding: 2px 1px;

            margin-bottom: 2px;
        }

        .circle-badge {
            width: 5px;

            height: 5px;

            min-width: 5px;

            margin-right: 2px;
        }
    }


    /* ---------------------------------------------------------
       휴대폰
       --------------------------------------------------------- */

    @media (max-width: 480px) {

        .calendar-container {
            width: 100%;

            overflow: hidden;
        }

        .calendar-table {
            width: 100%;
        }

        .calendar-table th {
            height: 25px;

            padding: 3px 0;

            font-size: 9px;
        }

        .calendar-table td {
            padding: 2px 1px;

            height: 72px;
        }

        .date-num {
            font-size: 10px;

            margin-bottom: 2px;
        }

        .schedule-item {
            font-size: 7px;

            line-height: 1.2;

            padding: 1px;

            margin-bottom: 1px;

            border-radius: 2px;
        }

        .circle-badge {
            width: 4px;

            height: 4px;

            min-width: 4px;

            margin-right: 1px;
        }
    }


    /* ---------------------------------------------------------
       아주 작은 휴대폰
       --------------------------------------------------------- */

    @media (max-width: 360px) {

        .calendar-table th {
            font-size: 8px;
        }

        .calendar-table td {
            height: 65px;

            padding: 1px;
        }

        .date-num {
            font-size: 9px;
        }

        .schedule-item {
            font-size: 6px;

            padding: 1px 0;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =================================================================
# 5. 일정 등록 / 수정 / 삭제 Dialog
# =================================================================

@st.dialog("일정 작성 및 수정")
def schedule_dialog(target_data=None):

    is_edit = target_data is not None

    # -------------------------------------------------------------
    # 기본값
    # -------------------------------------------------------------

    def_cat = (
        target_data["category"]
        if is_edit
        else CATEGORIES[0]
    )

    def_auth = (
        target_data["author"]
        if is_edit
        else AUTHORS[0]
    )

    now_kst = datetime.now()

    def_start_dt = (
        target_data["start_time"].date()
        if is_edit
        else now_kst.date()
    )

    def_start_tm = (
        target_data["start_time"].time()
        if is_edit
        else now_kst.time()
    )

    def_end_dt = (
        target_data["end_time"].date()
        if is_edit
        else now_kst.date()
    )

    def_end_tm = (
        target_data["end_time"].time()
        if is_edit
        else (now_kst + timedelta(hours=1)).time()
    )

    def_content = (
        target_data["content"]
        if is_edit
        else ""
    )


    # -------------------------------------------------------------
    # 일정 종류 / 작성자
    # -------------------------------------------------------------

    category = st.selectbox(
        "일정 종류",
        CATEGORIES,
        index=(
            CATEGORIES.index(def_cat)
            if def_cat in CATEGORIES
            else 0
        )
    )


    author = st.selectbox(
        "작성자",
        AUTHORS,
        index=(
            AUTHORS.index(def_auth)
            if def_auth in AUTHORS
            else 0
        )
    )


    # -------------------------------------------------------------
    # 시작 / 종료
    # -------------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        start_dt = st.date_input(
            "시작일",
            def_start_dt
        )

        start_tm = st.time_input(
            "시작 시간 (KST)",
            def_start_tm
        )


    with col2:

        end_dt = st.date_input(
            "종료일",
            def_end_dt
        )

        end_tm = st.time_input(
            "종료 시간 (KST)",
            def_end_tm
        )


    # -------------------------------------------------------------
    # 내용
    # -------------------------------------------------------------

    content = st.text_area(
        "내용",
        value=def_content,
        placeholder="일정 내용을 입력하세요"
    )


    # -------------------------------------------------------------
    # KST 시간 문자열
    # -------------------------------------------------------------

    start_time_obj = (
        datetime.combine(start_dt, start_tm)
        .strftime("%Y-%m-%dT%H:%M:%S+09:00")
    )

    end_time_obj = (
        datetime.combine(end_dt, end_tm)
        .strftime("%Y-%m-%dT%H:%M:%S+09:00")
    )


    # -------------------------------------------------------------
    # 저장 / 삭제 버튼
    # -------------------------------------------------------------

    col_btn1, col_btn2 = st.columns(2)


    with col_btn1:

        if st.button(
            "💾 저장",
            type="primary",
            use_container_width=True
        ):

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

                payload["id"] = target_data["id"]


            if save_schedule(payload):

                st.success("저장되었습니다!")

                st.rerun()


    with col_btn2:

        if is_edit:

            if st.button(
                "🗑️ 삭제",
                type="secondary",
                use_container_width=True
            ):

                if delete_schedule(target_data["id"]):

                    st.success("삭제되었습니다!")

                    st.rerun()


# =================================================================
# 6. 메인 화면
# =================================================================

st.title("📅 Xave's Family Scheduler")


# =================================================================
# 7. 상단 컨트롤
# =================================================================

col_ctrl1, col_ctrl2, col_btn = st.columns([2, 2, 2])

now_dt = datetime.now()


with col_ctrl1:

    selected_year = st.selectbox(
        "연도",
        range(
            now_dt.year - 2,
            now_dt.year + 3
        ),
        index=2,
        label_visibility="collapsed"
    )


with col_ctrl2:

    selected_month = st.selectbox(
        "월",
        range(1, 13),
        index=now_dt.month - 1,
        label_visibility="collapsed"
    )


with col_btn:

    if st.button(
        "➕ 일정 추가",
        type="primary",
        use_container_width=True
    ):

        schedule_dialog()


# =================================================================
# 8. 범례
# =================================================================

legend_html = """
<div
    style="
        font-size:12px;
        margin-bottom:8px;
        line-height:1.8;
    "
>
"""

legend_html += "<b>[종류]</b> "


for cat, color in CATEGORY_COLORS.items():

    legend_html += f"""
    <span style="margin-right:10px;">
        <span
            class="circle-badge"
            style="background-color:{color};"
        ></span>
        {html.escape(cat)}
    </span>
    """


legend_html += "<br><b>[작성자]</b> "


for auth, color in AUTHOR_COLORS.items():

    legend_html += f"""
    <span
        style="
            margin-right:10px;
            color:{color};
            font-weight:bold;
        "
    >
        {html.escape(auth)}
    </span>
    """


legend_html += "</div>"


st.markdown(
    legend_html,
    unsafe_allow_html=True
)


st.divider()


# =================================================================
# 9. 데이터 로드
# =================================================================

df = load_schedules()


# =================================================================
# 10. 선택한 월의 일정만 날짜별로 정리
# =================================================================

schedules_by_day = {}

schedules_by_id = {}


if not df.empty:

    for _, row in df.iterrows():

        st_dt = row["start_time"]

        if (
            st_dt.year == selected_year
            and st_dt.month == selected_month
        ):

            day = st_dt.day

            if day not in schedules_by_day:

                schedules_by_day[day] = []


            schedules_by_day[day].append(row)


            schedules_by_id[row["id"]] = row


# =================================================================
# 11. 월 달력 생성
# =================================================================

cal = calendar.Calendar(
    firstweekday=6
)

month_days = cal.monthdayscalendar(
    selected_year,
    selected_month
)


# =================================================================
# 12. HTML 달력 렌더링
# =================================================================

html_code = """
<div class="calendar-container">
<table class="calendar-table">

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


    for day in week:

        # ---------------------------------------------------------
        # 빈 날짜
        # ---------------------------------------------------------

        if day == 0:

            html_code += """
            <td class="other-month"></td>
            """

            continue


        # ---------------------------------------------------------
        # 오늘 여부
        # ---------------------------------------------------------

        is_today = (
            selected_year == now_dt.year
            and selected_month == now_dt.month
            and day == now_dt.day
        )


        td_class = "today" if is_today else ""


        html_code += f"""
        <td class="{td_class}">

            <div class="date-num">
                {day}
            </div>
        """


        # ---------------------------------------------------------
        # 일정 표시
        # ---------------------------------------------------------

        if day in schedules_by_day:

            for item in schedules_by_day[day]:

                cat_color = CATEGORY_COLORS.get(
                    item["category"],
                    "#888888"
                )

                auth_color = AUTHOR_COLORS.get(
                    item["author"],
                    "#333333"
                )


                time_str = item["start_time"].strftime(
                    "%H:%M"
                )


                # HTML 특수문자 안전 처리
                author_text = html.escape(
                    str(item["author"])
                )

                content_text = html.escape(
                    str(item["content"])
                )

                category_text = html.escape(
                    str(item["category"])
                )


                html_code += f"""
                <div
                    class="schedule-item"
                    title="{category_text}: {content_text}"
                >

                    <span
                        class="circle-badge"
                        style="
                            background-color:{cat_color};
                        "
                    ></span>

                    <span
                        class="schedule-text"
                        style="
                            color:{auth_color};
                            font-weight:600;
                        "
                    >
                        [{author_text}]
                        {time_str}
                        {content_text}
                    </span>

                </div>
                """


        html_code += "</td>"


    html_code += "</tr>"


html_code += """
</tbody>
</table>
</div>
"""


# =================================================================
# 13. 달력 출력
# =================================================================

st.markdown(
    html_code,
    unsafe_allow_html=True
)


# =================================================================
# 14. 일정 수정 / 삭제
# =================================================================

if schedules_by_id:

    st.markdown(
        "##### ✏️ 일정 클릭하여 수정 및 삭제"
    )


    # 모바일에서도 2열
    select_cols = st.columns(2)


    for idx, (s_id, item) in enumerate(
        schedules_by_id.items()
    ):

        col_idx = idx % 2


        time_str = item["start_time"].strftime(
            "%m/%d %H:%M"
        )


        content_short = str(
            item["content"]
        )[:15]


        btn_label = (
            f"[{time_str}] "
            f"{item['author']} - "
            f"{content_short}"
        )


        with select_cols[col_idx]:

            if st.button(
                btn_label,
                key=f"quick_edit_{s_id}",
                use_container_width=True
            ):

                schedule_dialog(item)
