-- bptc_stocks.db — 샘플 쿼리 10개
-- 난이도: ★(기본) → ★★(GROUP BY/WINDOW) → ★★★(JOIN/CTE)

-- ============================================================
-- ★ Q1. 시가총액 TOP 200 중 KOSPI vs KOSDAQ 종목 수
-- ============================================================
SELECT market, COUNT(*) as cnt FROM stocks_master GROUP BY market;

-- ============================================================
-- ★ Q2. 삼성전자 2026-05-06 시세 ("진짜 14% 올랐는지" 검증)
-- ============================================================
SELECT s.name, d.date, d.open, d.close,
       ROUND(d.change_pct, 2) as change_pct,
       d.volume
FROM daily_price d
JOIN stocks_master s ON d.code = s.code
WHERE s.name = '삼성전자'
  AND d.date BETWEEN '2026-05-01' AND '2026-05-10'
ORDER BY d.date;

-- ============================================================
-- ★★ Q3. 외국인 보유율 TOP 10 — 외국인이 가장 많이 가진 종목
-- ============================================================
SELECT s.name, s.market,
       ROUND(m.foreign_rate, 2) as 외국인보유율,
       ROUND(m.marcap / 1000000000000.0, 1) as 시총_조원
FROM daily_marcap m
JOIN stocks_master s ON m.code = s.code
WHERE m.date = '2026-05-21'
ORDER BY m.foreign_rate DESC
LIMIT 10;

-- ============================================================
-- ★★ Q4. 삼성전자 외국인 보유율 5년 추이 (월말만)
-- ============================================================
-- "외국인이 사고 있나 팔고 있나?"
SELECT m.date, ROUND(m.foreign_rate, 2) as 외국인보유율
FROM daily_marcap m
JOIN stocks_master s ON m.code = s.code
WHERE s.name = '삼성전자'
  AND strftime('%d', m.date) = strftime('%d', date(m.date, 'start of month', '+1 month', '-1 day'))
ORDER BY m.date;

-- ============================================================
-- ★★ Q5. "삼성·SK하이닉스 빼면 코스피 진짜 올랐어?"
-- ============================================================
-- 2026-01-02 대비 2026-05-21 종목별 수익률
WITH base AS (
  SELECT code, close as base_close
  FROM daily_price
  WHERE date = (SELECT MIN(date) FROM daily_price WHERE date >= '2026-01-02')
),
recent AS (
  SELECT code, close as recent_close
  FROM daily_price
  WHERE date = (SELECT MAX(date) FROM daily_price)
)
SELECT s.name,
       ROUND((r.recent_close - b.base_close) * 100.0 / b.base_close, 1) as 수익률_pct
FROM stocks_master s
JOIN base b ON s.code = b.code
JOIN recent r ON s.code = r.code
WHERE s.market = 'KOSPI'
ORDER BY 수익률_pct DESC
LIMIT 20;

-- ============================================================
-- ★★ Q6. PER 낮은데 외국인 보유율 높은 "저평가 + 스마트머니" 종목
-- ============================================================
SELECT s.name,
       ROUND(f.per, 1) as PER,
       ROUND(f.pbr, 2) as PBR,
       ROUND(m.foreign_rate, 1) as 외국인_pct,
       ROUND(f.div_yield, 1) as 배당수익률
FROM stocks_master s
JOIN daily_marcap m ON s.code = m.code AND m.date = '2026-05-21'
JOIN fundamental_monthly f ON s.code = f.code
                           AND f.date = (SELECT MAX(date) FROM fundamental_monthly)
WHERE f.per BETWEEN 1 AND 10
  AND m.foreign_rate > 30
ORDER BY m.foreign_rate DESC;

-- ============================================================
-- ★★ Q7. 배당수익률 TOP 10 (월말 기준)
-- ============================================================
SELECT s.name,
       ROUND(f.div_yield, 2) as 배당수익률_pct,
       f.dps as 주당배당금,
       ROUND(f.per, 1) as PER
FROM fundamental_monthly f
JOIN stocks_master s ON f.code = s.code
WHERE f.date = (SELECT MAX(date) FROM fundamental_monthly)
  AND f.div_yield > 0
ORDER BY f.div_yield DESC
LIMIT 10;

-- ============================================================
-- ★★★ Q8. 기관 vs 개인 vs 외국인 — 누가 더 잘 샀나? (1년)
-- ============================================================
-- 각 투자자가 최근 1년 동안 가장 많이 순매수한 종목 TOP 5
SELECT s.name,
       ROUND(SUM(i.individual)  / 100000000.0, 0) as 개인_억원,
       ROUND(SUM(i."foreign")   / 100000000.0, 0) as 외국인_억원,
       ROUND(SUM(i.institution) / 100000000.0, 0) as 기관_억원
FROM investor_flow i
JOIN stocks_master s ON i.code = s.code
WHERE i.date >= '2025-05-22'
GROUP BY s.code, s.name
ORDER BY 외국인_억원 DESC
LIMIT 5;

-- ============================================================
-- ★★★ Q9. 코스피 지수 5년 수익률 vs KOSDAQ150
-- ============================================================
WITH coverage AS (
  SELECT index_code, MIN(date) as min_d, MAX(date) as max_d
  FROM index_ohlcv
  WHERE index_code IN ('1001', '2001')   -- 코스피, KOSDAQ
  GROUP BY index_code
)
SELECT i.index_name,
       ROUND(start_p.close, 2) as 시작가,
       ROUND(end_p.close, 2) as 종가,
       ROUND((end_p.close - start_p.close) * 100.0 / start_p.close, 1) as 5년수익률
FROM coverage c
JOIN indexes i ON c.index_code = i.index_code
JOIN index_ohlcv start_p ON c.index_code = start_p.index_code AND c.min_d = start_p.date
JOIN index_ohlcv end_p   ON c.index_code = end_p.index_code   AND c.max_d = end_p.date;

-- ============================================================
-- ★★★ Q10. 2026-05-06 폭등일 — 외국인 순매수 TOP 5 종목의 등락률
-- ============================================================
SELECT s.name,
       ROUND(i."foreign" / 100000000.0, 1) as 외국인순매수_억원,
       ROUND(d.change_pct, 2) as 당일등락률,
       ROUND(m.foreign_rate, 1) as 외국인보유율
FROM investor_flow i
JOIN stocks_master s ON i.code = s.code
JOIN daily_price d   ON i.code = d.code AND i.date = d.date
JOIN daily_marcap m  ON i.code = m.code AND i.date = m.date
WHERE i.date = '2026-05-06'
  AND i."foreign" > 0
ORDER BY i."foreign" DESC
LIMIT 5;

-- ============================================================
-- 추가 도전 과제
-- ============================================================
-- 1) 본인 보유종목의 1년 수익률 + 외국인 보유율 변화
-- 2) "조방원(조선·방산·원전)" 키워드로 종목 골라서 1년 수익률 비교
--    HD현대중공업·한화에어로스페이스·두산에너빌리티 등
-- 3) 코로나 폭락(2020-03)이 데이터에 없으니 가장 큰 단일일 손실 찾기
-- 4) 기관 순매수 상위 종목의 다음 날 평균 수익률 (LAG 윈도우 함수)
-- 5) PER < 10, PBR < 1, 배당수익률 > 3% 동시 만족 종목 (가치주 스크리닝)
