-- bptc_realestate.db — 샘플 쿼리 10개
-- 난이도: ★(기본) → ★★(집계/시계열) → ★★★(JOIN/CTE/윈도우)

-- ============================================================
-- ★ Q1. 부산 16개 자치구 마스터 확인
-- ============================================================
SELECT * FROM gu_codes_realty ORDER BY gu_name;

-- ============================================================
-- ★ Q2. 해운대구 2025년 매매 TOP 5 (가장 비싼 거래)
-- ============================================================
SELECT
    aptNm as 단지,
    deal_date as 거래일,
    ROUND(dealAmount / 10000.0, 1) as 거래금액_억원,
    excluUseAr as 전용면적,
    floor as 층
FROM apt_trade
WHERE gu_name = '해운대구'
  AND deal_date LIKE '2025%'
ORDER BY dealAmount DESC
LIMIT 5;

-- ============================================================
-- ★★ Q3. 부산 자치구별 거래 횟수 — 어디가 가장 활발할까?
-- ============================================================
-- (의외의 결과: 부산진구가 1위)
SELECT
    gu_name,
    COUNT(*) as 거래수,
    ROUND(AVG(dealAmount) / 10000.0, 1) as 평균_억원,
    ROUND(MAX(dealAmount) / 10000.0, 1) as 최고가_억원
FROM apt_trade
GROUP BY gu_name
ORDER BY 거래수 DESC;

-- ============================================================
-- ★★ Q4. 연도별 부산 평균 거래금액 (5년 추이)
-- ============================================================
-- "5년 동안 얼마나 올랐어?"
SELECT
    SUBSTR(deal_date, 1, 4) as 연도,
    COUNT(*) as 거래수,
    ROUND(AVG(dealAmount) / 10000.0, 2) as 평균_억원,
    ROUND(MEDIAN(dealAmount) / 10000.0, 2) as 중간값_억원
FROM apt_trade
WHERE deal_date >= '2021-01-01'
GROUP BY 연도
ORDER BY 연도;

-- ============================================================
-- ★★ Q5. 평당 가격 계산 → 자치구별 평당가 순위
-- ============================================================
-- 전용면적 1㎡당 가격 = dealAmount / excluUseAr (만원/㎡)
-- 평당 가격 (3.3㎡당)
SELECT
    gu_name,
    COUNT(*) as 거래수,
    ROUND(AVG(dealAmount * 3.3 / excluUseAr), 0) as 평당가_만원
FROM apt_trade
WHERE excluUseAr > 0
  AND deal_date >= '2025-01-01'
GROUP BY gu_name
ORDER BY 평당가_만원 DESC;

-- ============================================================
-- ★★ Q6. "1억 이하 아파트는 어디에?" — 가성비 단지 찾기
-- ============================================================
SELECT
    gu_name,
    aptNm,
    deal_date,
    ROUND(dealAmount / 10000.0, 2) as 거래금액_억원,
    excluUseAr as 면적,
    buildYear as 준공년
FROM apt_trade
WHERE dealAmount < 10000        -- 1억 = 10,000만원
  AND deal_date >= '2025-01-01'
ORDER BY dealAmount DESC
LIMIT 20;

-- ============================================================
-- ★★ Q7. 같은 단지 5년 가격 변동 추적 (엘시티 예시)
-- ============================================================
-- "엘시티 가격 5년 동안 어떻게 변했어?"
SELECT
    SUBSTR(deal_date, 1, 4) as 연도,
    COUNT(*) as 거래수,
    ROUND(MIN(dealAmount) / 10000.0, 1) as 최저_억원,
    ROUND(AVG(dealAmount) / 10000.0, 1) as 평균_억원,
    ROUND(MAX(dealAmount) / 10000.0, 1) as 최고_억원
FROM apt_trade
WHERE aptNm LIKE '%엘시티%'
GROUP BY 연도
ORDER BY 연도;

-- ============================================================
-- ★★★ Q8. 단지 마스터와 JOIN — 거래 많은 인기 단지 TOP 10
-- ============================================================
SELECT
    c.apt_name,
    c.gu_name,
    c.trade_count as 거래수,
    c.build_year as 준공년,
    ROUND(c.min_area, 1) as 최소면적,
    ROUND(c.max_area, 1) as 최대면적,
    ROUND(AVG(t.dealAmount) / 10000.0, 1) as 평균거래_억원
FROM apt_complex c
JOIN apt_trade t ON c.apt_name = t.aptNm AND c.gu_name = t.gu_name
GROUP BY c.apt_name, c.gu_name
ORDER BY c.trade_count DESC
LIMIT 10;

-- ============================================================
-- ★★★ Q9. 매매 vs 전세 가격 비교 (해운대구 단지별)
-- ============================================================
-- "이 단지 매매가 vs 전세가" — 갭투자 가능성 분석
WITH 매매 AS (
    SELECT aptNm,
           AVG(dealAmount) as avg_sale
    FROM apt_trade
    WHERE gu_name = '해운대구'
      AND deal_date >= '2025-01-01'
    GROUP BY aptNm
),
전세 AS (
    SELECT aptNm,
           AVG(deposit) as avg_jeonse
    FROM apt_rent
    WHERE gu_name = '해운대구'
      AND deal_date >= '2025-01-01'
      AND monthlyRent = 0          -- 순수 전세만
      AND deposit > 0
    GROUP BY aptNm
)
SELECT
    매매.aptNm,
    ROUND(매매.avg_sale / 10000.0, 1) as 평균매매_억원,
    ROUND(전세.avg_jeonse / 10000.0, 1) as 평균전세_억원,
    ROUND(전세.avg_jeonse * 100.0 / 매매.avg_sale, 1) as 전세가율_pct,
    ROUND((매매.avg_sale - 전세.avg_jeonse) / 10000.0, 1) as 갭_억원
FROM 매매 JOIN 전세 ON 매매.aptNm = 전세.aptNm
WHERE 매매.avg_sale > 0 AND 전세.avg_jeonse > 0
ORDER BY 전세가율_pct DESC
LIMIT 15;

-- ============================================================
-- ★★★ Q10. 건축년도별 가격 패턴 — 신축이 진짜 비싸?
-- ============================================================
WITH 연식_그룹 AS (
    SELECT *,
        CASE
            WHEN CAST(buildYear AS INTEGER) >= 2020 THEN '신축 (2020~)'
            WHEN CAST(buildYear AS INTEGER) >= 2010 THEN '준신축 (2010~)'
            WHEN CAST(buildYear AS INTEGER) >= 2000 THEN '구축 (2000~)'
            WHEN CAST(buildYear AS INTEGER) >= 1990 THEN '오래된 구축 (1990~)'
            ELSE '90년 이전'
        END as 연식
    FROM apt_trade
    WHERE buildYear IS NOT NULL AND buildYear != ''
      AND deal_date >= '2025-01-01'
)
SELECT
    연식,
    COUNT(*) as 거래수,
    ROUND(AVG(dealAmount * 3.3 / excluUseAr), 0) as 평당가_만원,
    ROUND(AVG(dealAmount) / 10000.0, 1) as 평균_억원
FROM 연식_그룹
WHERE excluUseAr > 0
GROUP BY 연식
ORDER BY 평당가_만원 DESC;

-- ============================================================
-- ★★★ Q11. 자치구 종합 인프라 지수 (5-테이블 JOIN — 강의 클라이맥스)
-- ============================================================
SELECT
    g.gu_name as 자치구,
    (SELECT COUNT(*) FROM medical    WHERE gu_name = g.gu_name) as 병원수,
    (SELECT COUNT(*) FROM pharmacy   WHERE gu_name = g.gu_name) as 약국수,
    (SELECT COUNT(*) FROM schools    WHERE gu_name = g.gu_name) as 학교수,
    (SELECT COUNT(*) FROM academies  WHERE gu_name = g.gu_name) as 학원수,
    (SELECT total_pop FROM population_gu WHERE gu_name = g.gu_name AND ref_date = '2026-04') as 인구,
    (SELECT ROUND(AVG(dealAmount) / 10000.0, 1) FROM apt_trade
       WHERE gu_name = g.gu_name AND deal_date >= '2025-01-01') as 평균_억원
FROM gu_codes_realty g
ORDER BY 평균_억원 DESC;

-- ============================================================
-- ★★★ Q12. "동래구는 진짜 학군 1위인가?" — 입시강좌·교습비·평균거래 비교
-- ============================================================
SELECT
    a.gu_name,
    COUNT(DISTINCT a.academy_name) as 학원수,
    SUM(a.ipsi_count) as 입시강좌수,
    ROUND(AVG(a.avg_tuition), 0) as 평균교습비_원,
    (SELECT ROUND(AVG(dealAmount) / 10000.0, 1)
       FROM apt_trade WHERE gu_name = a.gu_name AND deal_date >= '2025-01-01') as 평균거래_억원
FROM academies a
GROUP BY a.gu_name
ORDER BY 입시강좌수 DESC;

-- ============================================================
-- ★★★ Q13. 학군 좋은 단지 찾기 — 같은 자치구 + 입시강좌 많은 동네
-- ============================================================
WITH 학군_좋은_구 AS (
    SELECT gu_name, SUM(ipsi_count) as 입시강좌
    FROM academies
    GROUP BY gu_name
    HAVING 입시강좌 >= 4000
)
SELECT
    t.gu_name,
    t.aptNm,
    COUNT(*) as 거래수,
    ROUND(AVG(t.dealAmount) / 10000.0, 1) as 평균_억원,
    ROUND(MIN(t.dealAmount) / 10000.0, 1) as 최저_억원
FROM apt_trade t
JOIN 학군_좋은_구 g ON t.gu_name = g.gu_name
WHERE t.deal_date >= '2025-01-01'
GROUP BY t.gu_name, t.aptNm
HAVING 거래수 >= 5
ORDER BY t.gu_name, 평균_억원 DESC
LIMIT 30;

-- ============================================================
-- ★★★ Q14. 인구 변화 vs 집값 추이 (population_gu + apt_trade)
-- ============================================================
WITH 인구_변화 AS (
    SELECT
        gu_name,
        MAX(CASE WHEN ref_date = '2021-05' THEN total_pop END) as 인구_2021,
        MAX(CASE WHEN ref_date = '2026-04' THEN total_pop END) as 인구_2026
    FROM population_gu
    GROUP BY gu_name
),
거래_변화 AS (
    SELECT
        gu_name,
        AVG(CASE WHEN deal_date BETWEEN '2021-01-01' AND '2021-12-31'
                 THEN dealAmount END) as 평균_2021,
        AVG(CASE WHEN deal_date BETWEEN '2025-01-01' AND '2025-12-31'
                 THEN dealAmount END) as 평균_2025
    FROM apt_trade
    GROUP BY gu_name
)
SELECT
    p.gu_name,
    p.인구_2021, p.인구_2026,
    ROUND((p.인구_2026 - p.인구_2021) * 100.0 / p.인구_2021, 1) as 인구_변화_pct,
    ROUND(d.평균_2021 / 10000.0, 1) as 집값_2021_억,
    ROUND(d.평균_2025 / 10000.0, 1) as 집값_2025_억,
    ROUND((d.평균_2025 - d.평균_2021) * 100.0 / d.평균_2021, 1) as 집값_변화_pct
FROM 인구_변화 p
JOIN 거래_변화 d ON p.gu_name = d.gu_name
ORDER BY 집값_변화_pct DESC;

-- ============================================================
-- ★★★ Q15. 가성비 학군 자치구 — 학원 많고 평균 거래가 낮은 곳
-- ============================================================
-- "학원가 + 인프라 있고 집값 안 비싼 곳"
SELECT
    g.gu_name,
    (SELECT SUM(ipsi_count) FROM academies WHERE gu_name = g.gu_name) as 입시강좌,
    (SELECT COUNT(*) FROM medical WHERE gu_name = g.gu_name) as 병원수,
    (SELECT ROUND(AVG(dealAmount) / 10000.0, 1) FROM apt_trade
       WHERE gu_name = g.gu_name AND deal_date >= '2025-01-01') as 평균_억원,
    -- 가성비 점수: 입시강좌수 / 평균거래가
    ROUND(
        (SELECT SUM(ipsi_count) FROM academies WHERE gu_name = g.gu_name) * 1.0 /
        (SELECT AVG(dealAmount) FROM apt_trade WHERE gu_name = g.gu_name AND deal_date >= '2025-01-01' AND AVG IS NOT NULL) * 10000,
    2) as 가성비_점수
FROM gu_codes_realty g
ORDER BY 가성비_점수 DESC NULLS LAST;

-- ============================================================
-- 추가 도전 과제 (수강생 자유 실습)
-- ============================================================
-- 1) 본인이 사는 자치구의 아파트 가격 5년 추이 → Plotly 라인차트
-- 2) "신축 30평대 vs 구축 30평대" 같은 자치구 비교
-- 3) 월별 거래량 + 거래금액 평균 → 부산 부동산 계절성 분석
-- 4) bptc_busan.db와 결합 — 지하철역 인근(자치구) vs 비인근 단지 가격
-- 5) Folium 지도에 자치구별 평당가 색상 표시 (gu_centers 좌표 활용)
-- 6) 매수자/매도자 분석 — 법인 매수 비율 변화 (buyerGbn)
-- 7) 거래 직거래 vs 중개거래 비율 (dealingGbn)
-- 8) 갱신/신규 전세 비율 — 임차인 회전율 (apt_rent.contractType)
