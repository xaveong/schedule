<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <!-- 모바일 뷰포트 설정: 가로 스크롤 방지 및 화면 맞춤 -->
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>모바일 맞춤 반응형 달력</title>
  <style>
    /* 기본 리셋 및 화면 스크롤 완전 차단 */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      width: 100%;
      height: 100%;
      height: 100dvh; /* Dynamic Viewport Height 사용 */
      overflow: hidden; /* 가로/세로 스크롤 제거 */
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: #f8f9fa;
      color: #333;
    }

    /* 전체 달력 컨테이너: 전체 화면 채우기 */
    .calendar-container {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      max-width: 600px; /* 대화면/데스크톱 대응 한계 너비 */
      margin: 0 auto;
      padding: 0.5rem;
      background-color: #ffffff;
    }

    /* 1. 상단 헤더 (연/월 컨트롤) */
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
      transition: background-color 0.2s;
    }

    .nav-btn:active {
      background-color: #e9ecef;
    }

    /* 2. 요일 헤더 (일~토) */
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
      color: #e63946; /* 일요일 빨간색 */
    }

    .weekday:last-child {
      color: #1d3557; /* 토요일 파란색 */
    }

    /* 3. 날짜 그리드 (남은 남은 높이를 모두 차지) */
    .days-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      grid-template-rows: repeat(6, 1fr); /* 항상 6주 높이 동일 비율 분배 */
      flex: 1; /* 남은 높이 전체 채움 */
      gap: 1px;
      background-color: #f1f3f5; /* 셀 구분선 효과 */
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

    /* 오늘 날짜 표시 */
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

    /* 이전/다음 달 날짜 (옅은 색상) */
    .day-cell.other-month {
      color: #ccc;
      background-color: #fafafa;
    }

    /* 주말 색상 */
    .day-cell:nth-child(7n+1):not(.other-month) {
      color: #e63946; /* 일요일 */
    }

    .day-cell:nth-child(7n):not(.other-month) {
      color: #1d3557; /* 토요일 */
    }

    /* 선택된 날짜 테두리 */
    .day-cell.selected {
      outline: 2px solid #3b82f6;
      outline-offset: -2px;
      z-index: 1;
    }

    /* 간단한 일정 표시 점 (Dot) 예시 */
    .event-dots {
      display: flex;
      gap: 2px;
      margin-top: 2px;
    }

    .dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background-color: #ef4444;
    }
  </style>
</head>
<body>

  <div class="calendar-container">
    <!-- 달력 상단 바 -->
    <header class="calendar-header">
      <button class="nav-btn" id="prev-btn">&lt;</button>
      <h2 id="month-year-title"></h2>
      <button class="nav-btn" id="next-btn">&gt;</button>
    </header>

    <!-- 요일 표시 -->
    <div class="weekdays-grid">
      <div class="weekday">일</div>
      <div class="weekday">월</div>
      <div class="weekday">화</div>
      <div class="weekday">수</div>
      <div class="weekday">목</div>
      <div class="weekday">금</div>
      <div class="weekday">토</div>
    </div>

    <!-- 날짜 그리드 -->
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

      // 헤더 연/월 업데이트
      monthYearTitle.textContent = `${year}년 ${month + 1}월`;

      // 달력 시작일 / 종료일 계산
      const firstDayOfMonth = new Date(year, month, 1);
      const lastDayOfMonth = new Date(year, month + 1, 0);

      const startDayOfWeek = firstDayOfMonth.getDay(); // 0(일) ~ 6(토)
      const totalDaysInMonth = lastDayOfMonth.getDate();

      const prevMonthLastDay = new Date(year, month, 0).getDate();

      const today = new Date();

      // 6주 × 7일 = 총 42개의 셀 생성
      for (let i = 0; i < 42; i++) {
        const cell = document.createElement('div');
        cell.classList.add('day-cell');

        let dayNumber;

        if (i < startDayOfWeek) {
          // 이전 달 날짜
          dayNumber = prevMonthLastDay - startDayOfWeek + i + 1;
          cell.classList.add('other-month');
        } else if (i >= startDayOfWeek + totalDaysInMonth) {
          // 다음 달 날짜
          dayNumber = i - (startDayOfWeek + totalDaysInMonth) + 1;
          cell.classList.add('other-month');
        } else {
          // 현재 달 날짜
          dayNumber = i - startDayOfWeek + 1;

          // 오늘 날짜 확인
          if (
            year === today.getFullYear() &&
            month === today.getMonth() &&
            dayNumber === today.getDate()
          ) {
            cell.classList.add('today');
          }
        }

        // 날짜 텍스트 래퍼
        const daySpan = document.createElement('span');
        daySpan.classList.add('day-number');
        daySpan.textContent = dayNumber;
        cell.appendChild(daySpan);

        // 터치/클릭 이벤트 처리
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

    // 버튼 이벤트 연결
    prevBtn.addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() - 1);
      renderCalendar();
    });

    nextBtn.addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      renderCalendar();
    });

    // 초기 실행
    renderCalendar();
  </script>
</body>
</html>
