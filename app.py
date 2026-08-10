import streamlit as st
import streamlit.components.v1 as components

# Streamlit 설정
st.set_page_config(layout="wide")

# HTML/CSS/JS 전체 문자열
html_code = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>모바일 맞춤 반응형 달력</title>
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
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
      padding: 0.5rem;
      background-color: #ffffff;
    }

    .calendar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.5rem 0.25rem;
      flex-shrink: 0;
    }

    .calendar-header h2 {
      font-size: clamp(1.1rem, 4vw, 1.5rem);
      font-weight: 700;
    }

    .nav-btn {
      background: none;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 0.3rem 0.8rem;
      font-size: clamp(0.9rem, 3.5vw, 1.1rem);
      cursor: pointer;
      user-select: none;
    }

    .nav-btn:active {
      background-color: #e9ecef;
    }

    .weekdays-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      text-align: center;
      font-weight: 600;
      font-size: clamp(0.75rem, 3vw, 0.95rem);
      padding: 0.4rem 0;
      border-bottom: 1px solid #eee;
      flex-shrink: 0;
    }

    .weekday {
      color: #666;
    }

    .weekday:first-child {
      color: #e63946;
    }

    .weekday:last-child {
      color: #1d3557;
    }

    .days-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      grid-template-rows: repeat(6, 1fr);
      flex: 1;
      gap: 1px;
      background-color: #f1f3f5;
      border: 1px solid #f1f3f5;
      margin-top: 0.25rem;
    }

    .day-cell {
      background-color: #ffffff;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      padding-top: 0.2rem;
      font-size: clamp(0.8rem, 3.2vw, 1rem);
      cursor: pointer;
      position: relative;
      user-select: none;
    }

    .day-cell.today .day-number {
      background-color: #3b82f6;
      color: #ffffff;
      border-radius: 50%;
      width: clamp(1.4rem, 5vw, 1.8rem);
      height: clamp(1.4rem, 5vw, 1.8rem);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }

    .day-cell.other-month {
      color: #ccc;
      background-color: #fafafa;
    }

    .day-cell:nth-child(7n+1):not(.other-month) {
      color: #e63946;
    }

    .day-cell:nth-child(7n):not(.other-month) {
      color: #1d3557;
    }

    .day-cell.selected {
      outline: 2px solid #3b82f6;
      outline-offset: -2px;
      z-index: 1;
    }
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

  <script>
    let currentDate = new Date();
    let selectedCell = null;

    const monthYearTitle = document.getElementById('month-year-title');
    const daysContainer = document.getElementById('days-container');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

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

        let dayNumber;

        if (i < startDayOfWeek) {
          dayNumber = prevMonthLastDay - startDayOfWeek + i + 1;
          cell.classList.add('other-month');
        } else if (i >= startDayOfWeek + totalDaysInMonth) {
          dayNumber = i - (startDayOfWeek + totalDaysInMonth) + 1;
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

        const daySpan = document.createElement('span');
        daySpan.classList.add('day-number');
        daySpan.textContent = dayNumber;
        cell.appendChild(daySpan);

        cell.addEventListener('click', () => {
          if (selectedCell) {
            selectedCell.classList.remove('selected');
          }
          cell.classList.add('selected');
          selectedCell = cell;
        });

        daysContainer.appendChild(cell);
      }
    }

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

# Streamlit 앱에서 HTML 컴포넌트로 렌더링
components.html(html_code, height=650, scrolling=False)
