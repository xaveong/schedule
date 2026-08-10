import streamlit as st
import streamlit.components.v1 as components

# Streamlit 기본 설정
st.set_page_config(
    page_title="모바일 맞춤 일정 관리 달력",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모바일 UI/UX 최적화를 위해 여백 최소화 CSS 적용
st.markdown("""
    <style>
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# HTML / CSS / JS 통합 코드
html_code = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>반응형 일정 달력</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      width: 100%;
      height: 100%;
      height: 100vh;
      height: 100dvh;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #f8f9fa;
      color: #333;
    }

    .calendar-container {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      max-width: 600px;
      margin: 0 auto;
      padding: 0.4rem;
      background-color: #ffffff;
      position: relative;
    }

    /* 상단 헤더 */
    .calendar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.4rem 0.2rem;
      flex-shrink: 0;
    }

    .calendar-header h2 {
      font-size: clamp(1.1rem, 4vw, 1.4rem);
      font-weight: 700;
    }

    .nav-btn {
      background: #f1f3f5;
      border: none;
      border-radius: 8px;
      padding: 0.3rem 0.8rem;
      font-size: clamp(0.9rem, 3.5vw, 1.1rem);
      cursor: pointer;
      font-weight: bold;
    }

    .nav-btn:active {
      background-color: #e9ecef;
    }

    /* 요일 표시 */
    .weekdays-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      text-align: center;
      font-weight: 600;
      font-size: clamp(0.75rem, 3vw, 0.9rem);
      padding: 0.3rem 0;
      border-bottom: 1px solid #eee;
      flex-shrink: 0;
    }

    .weekday:first-child { color: #e63946; } /* 일요일 */
    .weekday:last-child { color: #1d3557; }  /* 토요일 */

    /* 날짜 그리드 (6주 고정 비율) */
    .days-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      grid-template-rows: repeat(6, 1fr);
      flex: 1;
      gap: 1px;
      background-color: #e9ecef;
      border: 1px solid #e9ecef;
      margin-top: 0.2rem;
      overflow: hidden;
    }

    .day-cell {
      background-color: #ffffff;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      padding: 0.2rem 0.1rem;
      font-size: clamp(0.75rem, 3vw, 0.9rem);
      cursor: pointer;
      position: relative;
      user-select: none;
      overflow: hidden;
    }

    .day-header {
      display: flex;
      justify-content: center;
      align-items: center;
      margin-bottom: 0.1rem;
    }

    /* 오늘 날짜 표시 */
    .day-cell.today .day-number {
      background-color: #3b82f6;
      color: #ffffff;
      border-radius: 50%;
      width: clamp(1.3rem, 4.5vw, 1.6rem);
      height: clamp(1.3rem, 4.5vw, 1.6rem);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }

    /* 이전/다음 달 날짜 */
    .day-cell.other-month {
      background-color: #f8f9fa;
      opacity: 0.4;
    }

    .day-cell:nth-child(7n+1):not(.other-month) .day-number { color: #e63946; }
    .day-cell:nth-child(7n):not(.other-month) .day-number { color: #1d3557; }

    /* 일정 목록 표시 구역 */
    .events-list {
      display: flex;
      flex-direction: column;
      gap: 1px;
      overflow-y: auto;
      flex: 1;
    }

    /* 날짜 셀 안의 일정 바 */
    .event-item {
      background-color: #e0f2fe;
      color: #0369a1;
      font-size: clamp(0.6rem, 2.3vw, 0.75rem);
      padding: 1px 3px;
      border-radius: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }

    /* 일정 추가/수정 모달 팝업 */
    .modal-overlay {
      display: none;
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.4);
      justify-content: center;
      align-items: center;
      z-index: 100;
      padding: 1rem;
    }

    .modal-overlay.active {
      display: flex;
    }

    .modal-content {
      background: #ffffff;
      padding: 1.2rem;
      border-radius: 12px;
      width: 100%;
      max-width: 320px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .modal-title {
      font-size: 1.1rem;
      font-weight: bold;
      margin-bottom: 0.8rem;
    }

    .modal-input {
      width: 100%;
      padding: 0.6rem;
      border: 1px solid #ccc;
      border-radius: 6px;
      font-size: 0.95rem;
      margin-bottom: 0.8rem;
    }

    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }

    .btn {
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 600;
    }

    .btn-primary { background: #3b82f6; color: white; }
    .btn-secondary { background: #e5e7eb; color: #374151; }
    .btn-danger { background: #ef4444; color: white; }
  </style>
</head>
<body>

  <div class="calendar-container">
    <header class="calendar-header">
      <button class="nav-btn" id="prev-btn">&lt;</button>
      <h2 id="month-year-title"></h2>
      <button class="nav-btn" id="next-btn">&gt;</button>
    </header>

    <div class="weekdays-grid">
      <div class="weekday">일</div>
      <div class="weekday">월</div>
      <div class="weekday">화</div>
      <div class="weekday">수</div>
      <div class="weekday">목</div>
      <div class="weekday">금</div>
      <div class="weekday">토</div>
    </div>

    <div class="days-grid" id="days-container"></div>
  </div>

  <!-- 일정 입력/수정 모달 -->
  <div class="modal-overlay" id="modal">
    <div class="modal-content">
      <div class="modal-title" id="modal-date-label">일정 관리</div>
      <input type="text" class="modal-input" id="event-input" placeholder="일정을 입력하세요">
      <div class="modal-actions">
        <button class="btn btn-danger" id="delete-btn" style="display:none;">삭제</button>
        <button class="btn btn-secondary" id="cancel-btn">취소</button>
        <button class="btn btn-primary" id="save-btn">저장</button>
      </div>
    </div>
  </div>

  <script>
    let currentDate = new Date();
    let selectedDateKey = null;

    // 브라우저 로컬 스토리지에서 저장된 일정 가져오기
    let eventsData = JSON.parse(localStorage.getItem('calendarEvents')) || {};

    const monthYearTitle = document.getElementById('month-year-title');
    const daysContainer = document.getElementById('days-container');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    const modal = document.getElementById('modal');
    const modalDateLabel = document.getElementById('modal-date-label');
    const eventInput = document.getElementById('event-input');
    const saveBtn = document.getElementById('save-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const deleteBtn = document.getElementById('delete-btn');

    function saveEventsToStorage() {
      localStorage.setItem('calendarEvents', JSON.stringify(eventsData));
    }

    function formatDateKey(year, month, day) {
      const m = String(month + 1).padStart(2, '0');
      const d = String(day).padStart(2, '0');
      return `${year}-${m}-${d}`;
    }

    function renderCalendar() {
      daysContainer.innerHTML = '';

      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();

      monthYearTitle.textContent = `${year}년 ${month + 1}월`;

      const firstDayOfMonth = new Date(year, month, 1);
      const lastDayOfMonth = new Date(year, month + 1, 0);

      const startDayOfWeek = firstDayOfMonth.getDay();
      const totalDaysInMonth = lastDayOfMonth.getDate();
      const prevMonthLastDay = new Date(year, month, 0).getDate();

      const today = new Date();

      for (let i = 0; i < 42; i++) {
        const cell = document.createElement('div');
        cell.classList.add('day-cell');

        let cellYear = year;
        let cellMonth = month;
        let dayNumber;

        if (i < startDayOfWeek) {
          dayNumber = prevMonthLastDay - startDayOfWeek + i + 1;
          cellMonth = month - 1;
          if (cellMonth < 0) { cellMonth = 11; cellYear--; }
          cell.classList.add('other-month');
        } else if (i >= startDayOfWeek + totalDaysInMonth) {
          dayNumber = i - (startDayOfWeek + totalDaysInMonth) + 1;
          cellMonth = month + 1;
          if (cellMonth > 11) { cellMonth = 0; cellYear++; }
          cell.classList.add('other-month');
        } else {
          dayNumber = i - startDayOfWeek + 1;

          if (
            year === today.getFullYear() &&
            month === today.getMonth() &&
            dayNumber === today.getDate()
          ) {
            cell.classList.add('today');
          }
        }

        const dayHeader = document.createElement('div');
        dayHeader.classList.add('day-header');

        const daySpan = document.createElement('span');
        daySpan.classList.add('day-number');
        daySpan.textContent = dayNumber;
        dayHeader.appendChild(daySpan);
        cell.appendChild(dayHeader);

        // 일정 표출 컨테이너
        const eventsList = document.createElement('div');
        eventsList.classList.add('events-list');

        const dateKey = formatDateKey(cellYear, cellMonth, dayNumber);
        if (eventsData[dateKey]) {
          const eventItem = document.createElement('div');
          eventItem.classList.add('event-item');
          eventItem.textContent = eventsData[dateKey];
          eventsList.appendChild(eventItem);
        }

        cell.appendChild(eventsList);

        // 셀 클릭 시 일정 모달 열기
        cell.addEventListener('click', () => {
          openModal(dateKey);
        });

        daysContainer.appendChild(cell);
      }
    }

    function openModal(dateKey) {
      selectedDateKey = dateKey;
      modalDateLabel.textContent = `${dateKey} 일정`;
      
      const existingEvent = eventsData[dateKey] || '';
      eventInput.value = existingEvent;

      if (existingEvent) {
        deleteBtn.style.display = 'block';
      } else {
        deleteBtn.style.display = 'none';
      }

      modal.classList.add('active');
      eventInput.focus();
    }

    function closeModal() {
      modal.classList.remove('active');
      eventInput.value = '';
      selectedDateKey = null;
    }

    saveBtn.addEventListener('click', () => {
      if (selectedDateKey) {
        const value = eventInput.value.trim();
        if (value) {
          eventsData[selectedDateKey] = value;
        } else {
          delete eventsData[selectedDateKey];
        }
        saveEventsToStorage();
        renderCalendar();
      }
      closeModal();
    });

    deleteBtn.addEventListener('click', () => {
      if (selectedDateKey && eventsData[selectedDateKey]) {
        delete eventsData[selectedDateKey];
        saveEventsToStorage();
        renderCalendar();
      }
      closeModal();
    });

    cancelBtn.addEventListener('click', closeModal);

    prevBtn.addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() - 1);
      renderCalendar();
    });

    nextBtn.addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      renderCalendar();
    });

    renderCalendar();
  </script>
</body>
</html>
"""

# Streamlit 앱 렌더링
components.html(html_code, height=650, scrolling=False)
