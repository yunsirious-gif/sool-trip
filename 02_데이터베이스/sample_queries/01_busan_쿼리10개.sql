-- bptc_busan.db — 샘플 쿼리 10개
-- 난이도: ★(기본) → ★★(GROUP BY) → ★★★(JOIN)
-- 모든 쿼리는 sqlite3 명령어 또는 DB Browser for SQLite에서 실행 가능

-- ============================================================
-- ★ Q1. 부산 도시철도 1~4호선 정보 보기 (가장 단순)
-- ============================================================
SELECT * FROM lines;

-- ============================================================
-- ★ Q2. 서면역 정보 찾기 (WHERE 필터)
-- ============================================================
SELECT * FROM stations WHERE station_name = '서면';

-- ============================================================
-- ★ Q3. 1호선에 속한 역 전체 보기 (정렬)
-- ============================================================
SELECT station_id, station_name
FROM stations
WHERE line_no = 1
ORDER BY station_id;

-- ============================================================
-- ★★ Q4. 노선별 역 개수 (GROUP BY + COUNT)
-- ============================================================
-- "어느 노선이 역이 가장 많을까?"
SELECT line_no, COUNT(*) as station_count
FROM stations
GROUP BY line_no
ORDER BY station_count DESC;

-- ============================================================
-- ★★ Q5. 서면역 출퇴근 시간대 승차 인원 패턴
-- ============================================================
-- "서면역에서 몇 시에 사람이 가장 많이 타나?"
SELECT hour, ROUND(AVG(passengers), 0) as avg_passengers
FROM daily_passengers
WHERE station_name = '서면'
  AND direction = 'board'
GROUP BY hour
ORDER BY hour;

-- ============================================================
-- ★★ Q6. 1호선 vs 2호선 — 어느 노선이 더 붐비나?
-- ============================================================
SELECT
  line_no,
  ROUND(SUM(passengers) / 1000000.0, 2) as total_million,
  ROUND(AVG(passengers), 0) as avg_per_hour
FROM daily_passengers
WHERE direction = 'board'
GROUP BY line_no
ORDER BY total_million DESC;

-- ============================================================
-- ★★ Q7. 부산에서 가장 붐비는 역 TOP 10 (모든 노선)
-- ============================================================
-- "부산 사람들이 어디서 제일 많이 탈까?"
SELECT
  station_name,
  line_no,
  ROUND(SUM(passengers) / 10000.0, 1) as total_10thousand
FROM daily_passengers
WHERE direction = 'board'
GROUP BY station_name, line_no
ORDER BY total_10thousand DESC
LIMIT 10;

-- ============================================================
-- ★★★ Q8. 평일 vs 주말 출퇴근 패턴 차이 (CASE WHEN)
-- ============================================================
SELECT
  hour,
  CASE
    WHEN weekday IN ('토', '일') THEN '주말'
    ELSE '평일'
  END as day_type,
  ROUND(AVG(passengers), 0) as avg_passengers
FROM daily_passengers
WHERE direction = 'board'
  AND station_name IN ('서면', '해운대', '광안')
GROUP BY hour, day_type
ORDER BY hour, day_type;

-- ============================================================
-- ★★★ Q9. 노선 이름과 함께 보는 노선별 통계 (JOIN)
-- ============================================================
-- 노선번호만 보면 헷갈리니까 노선명 같이 표시
SELECT
  l.line_name,
  l.color,
  COUNT(DISTINCT dp.station_name) as station_count,
  ROUND(SUM(dp.passengers) / 1000000.0, 2) as total_million_riders
FROM daily_passengers dp
JOIN lines l ON dp.line_no = l.line_no
WHERE dp.direction = 'board'
GROUP BY l.line_no, l.line_name, l.color
ORDER BY total_million_riders DESC;

-- ============================================================
-- ★★★ Q10. 해운대 vs 서면 — 시간대별 승차 비교 (피벗 스타일)
-- ============================================================
-- 같은 시간에 두 역 중 어디가 더 붐비나?
SELECT
  hour,
  SUM(CASE WHEN station_name = '해운대' THEN passengers ELSE 0 END) as 해운대,
  SUM(CASE WHEN station_name = '서면' THEN passengers ELSE 0 END) as 서면,
  ROUND(
    SUM(CASE WHEN station_name = '서면' THEN passengers ELSE 0 END) * 1.0 /
    NULLIF(SUM(CASE WHEN station_name = '해운대' THEN passengers ELSE 0 END), 0),
  2) as 서면_해운대_배수
FROM daily_passengers
WHERE direction = 'board'
  AND station_name IN ('해운대', '서면')
GROUP BY hour
ORDER BY hour;

-- ============================================================
-- 추가 도전 과제 (수강생 자유 실습)
-- ============================================================
-- 1) 본인이 자주 이용하는 역 1개를 골라서 시간대별 패턴 분석
-- 2) "비 오는 날 vs 맑은 날" — 날씨 데이터 추가 결합 (외부 CSV 필요)
-- 3) 광안리 불꽃축제 날(특정 날짜) vs 평소 비교
-- 4) 부산국제영화제(BIFF) 9월 중순~말 해운대역 승하차 평소 대비
-- 5) 시간대 + 요일 매트릭스 히트맵 (Plotly로 시각화)
