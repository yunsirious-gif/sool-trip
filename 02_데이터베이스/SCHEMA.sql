-- ============================================================
-- bptc 강의 데이터베이스 — 전체 스키마 (CREATE TABLE 모음)
-- AI에게 이 파일 그대로 붙여넣으면 모든 테이블 구조 인식
-- ============================================================

-- ============================================================
-- bptc_busan.db — 부산 도시철도 (5테이블, 660K행)
-- ============================================================

CREATE TABLE "lines" (
    "line_no"   INTEGER,    -- 1, 2, 3, 4
    "line_name" TEXT,        -- '1호선'
    "color"     TEXT,        -- '#F37423'
    "operator"  TEXT,        -- '부산교통공사'
    "open_year" INTEGER      -- 1985
);

CREATE TABLE "stations" (
    "line_no"      INTEGER,   -- FK → lines.line_no
    "station_id"   INTEGER,   -- 95, 222 (앞자리=노선)
    "station_name" TEXT,       -- '서면', '해운대'
    "lat"          TEXT,       -- 비어있음
    "lng"          TEXT        -- 비어있음
);

CREATE TABLE "daily_passengers" (   -- ★ 메인, 645,120행
    "line_no"      INTEGER,
    "station_id"   INTEGER,
    "station_name" TEXT,
    "date"         TEXT,       -- 'YYYY-MM-DD'
    "weekday"      TEXT,       -- '월'~'일'
    "hour"         INTEGER,    -- 1~24
    "direction"    TEXT,       -- 'board' | 'alight'
    "passengers"   INTEGER     -- 명
);

CREATE TABLE "monthly_passport" (
    "station_name" TEXT,
    "연월"         TEXT,        -- ⚠ 한글 컬럼 — "연월" 큰따옴표
    "board_cnt"    INTEGER,
    "alight_cnt"   INTEGER,
    "무임"         INTEGER,      -- ⚠ 한글
    "어린이"       INTEGER,      -- ⚠ 한글
    "청소년"       INTEGER       -- ⚠ 한글
);

CREATE TABLE "gu_codes" (   -- 부산 16개 자치구
    "gu_code" TEXT,    -- '26350'
    "gu_name" TEXT,    -- '해운대구'
    "type"    TEXT     -- '구' | '군'
);


-- ============================================================
-- bptc_stocks.db — 한국 주식 (7테이블, 1.2M행)
-- ============================================================

CREATE TABLE "stocks_master" (
    "code"   TEXT,    -- '005930' (삼성전자), PK 역할
    "name"   TEXT,    -- '삼성전자'
    "market" TEXT     -- 'KOSPI' | 'KOSDAQ'
);

CREATE TABLE "daily_price" (   -- 250,547행
    "code"       TEXT,
    "date"       TEXT,        -- 'YYYY-MM-DD'
    "open"       INTEGER,     -- 원
    "high"       INTEGER,
    "low"        INTEGER,
    "close"      INTEGER,
    "volume"     INTEGER,     -- 주
    "change_pct" REAL          -- %
);

CREATE TABLE "daily_marcap" (   -- 시가총액 + 외국인 보유율
    "date"           TEXT,
    "code"           TEXT,
    "marcap"         INTEGER,   -- 원 (1555110109728000 = 1,555조)
    "shares"         INTEGER,   -- 상장주식수
    "foreign_shares" INTEGER,
    "foreign_rate"   REAL,      -- ★ 외국인 보유율 %
    "volume"         INTEGER,
    "amount"         INTEGER
);

CREATE TABLE "fundamental_monthly" (   -- 월말 펀더멘털
    "code"      TEXT,
    "date"      TEXT,      -- 월말 'YYYY-MM-DD'
    "per"       REAL,      -- PER
    "pbr"       REAL,      -- PBR
    "eps"       INTEGER,
    "bps"       INTEGER,
    "div_yield" REAL,      -- 배당수익률 %
    "dps"       INTEGER    -- 주당 배당금
);

CREATE TABLE "investor_flow" (   -- 투자자별 일별 순매수
    "code"        TEXT,
    "date"        TEXT,
    "individual"  INTEGER,    -- 개인 순매수 (원)
    "foreign"     INTEGER,    -- ⚠ 예약어 — i."foreign" 형식 필수
    "institution" INTEGER,    -- 기관
    "other_corp"  INTEGER,
    "total"       INTEGER
);

CREATE TABLE "indexes" (
    "index_code" TEXT,    -- '1001' = 코스피
    "index_name" TEXT,    -- '코스피'
    "market"     TEXT     -- 'KOSPI' | 'KOSDAQ' | 'KRX'
);

CREATE TABLE "index_ohlcv" (   -- 지수 일별 OHLCV
    "index_code" TEXT,
    "date"       TEXT,
    "open"       REAL,
    "high"       REAL,
    "low"        REAL,
    "close"      REAL,
    "volume"     INTEGER,
    "amount"     INTEGER,
    "상장시가총액" INTEGER     -- ⚠ 한글 컬럼
);


-- ============================================================
-- bptc_realestate.db — 부산 부동산 + 학군 + 인프라 (11테이블)
-- ============================================================

CREATE TABLE "apt_trade" (   -- ★ 165,386 매매
    "aptNm"       TEXT,       -- 단지명
    "gu_name"     TEXT,       -- '해운대구'
    "deal_date"   TEXT,       -- 'YYYY-MM-DD'
    "dealAmount"  INTEGER,    -- ★ 만원 단위 (10000 = 1억)
    "excluUseAr"  REAL,       -- 전용면적 ㎡
    "floor"       TEXT,
    "buildYear"   TEXT,       -- 건축년도
    "roadNm"      TEXT,
    "umdNm"       TEXT,       -- 법정동
    "dealingGbn"  TEXT,       -- '중개거래' | '직거래'
    "buyerGbn"    TEXT,       -- '개인' | '법인'
    "slerGbn"     TEXT,
    "aptDong"     TEXT,
    "jibun"       TEXT
    -- 외 35컬럼
);

CREATE TABLE "apt_rent" (   -- 351,186 전월세
    "aptNm"        TEXT,
    "gu_name"      TEXT,
    "deal_date"    TEXT,
    "deposit"      INTEGER,    -- 보증금 만원
    "monthlyRent"  INTEGER,    -- 월세 만원 (0이면 순수 전세)
    "excluUseAr"   REAL,
    "floor"        TEXT,
    "buildYear"    TEXT,
    "contractType" TEXT,        -- '신규' | '갱신'
    "contractTerm" TEXT
);

CREATE TABLE "apt_complex" (   -- 4,278 단지 마스터
    "apt_name"    TEXT,        -- PK
    "gu_name"     TEXT,
    "road_name"   TEXT,
    "build_year"  TEXT,
    "min_area"    REAL,
    "max_area"    REAL,
    "trade_count" INTEGER       -- 총 거래 횟수
);

CREATE TABLE "gu_codes_realty" (   -- 16
    "lawd_cd" TEXT,    -- '26350'
    "gu_name" TEXT     -- '해운대구'
);

CREATE TABLE "gu_centers" (   -- 16, ★ 좌표 있음
    "lawd_cd" TEXT,
    "gu_name" TEXT,
    "lat"     REAL,
    "lng"     REAL
);

CREATE TABLE "schools" (   -- 615 부산 초·중·고
    "school_name"     TEXT,
    "school_type"     TEXT,    -- '초등학교' | '중학교' | '고등학교'
    "gu_name"         TEXT,
    "road_name_addr"  TEXT,
    "lat"             REAL,
    "lng"             REAL,
    "founded_date"    TEXT,
    "founded_type"    TEXT
);

CREATE TABLE "medical" (   -- 5,623 부산 병원
    "name"          TEXT,
    "category"      TEXT,     -- '의원' | '치과의원' | '한의원' | '병원' | '종합병원'
    "gu_name"       TEXT,
    "address"       TEXT,
    "phone"         TEXT,
    "doctor_count"  INTEGER,
    "lat"           REAL,
    "lng"           REAL
);

CREATE TABLE "pharmacy" (   -- 1,732 부산 약국
    "name"     TEXT,
    "category" TEXT,
    "gu_name"  TEXT,
    "address"  TEXT,
    "phone"    TEXT,
    "lat"      REAL,
    "lng"      REAL
);

CREATE TABLE "population_gu" (   -- 960 = 16구 × 60개월
    "gu_name"           TEXT,
    "ref_date"          TEXT,     -- 'YYYY-MM'
    "total_pop"         INTEGER,  -- 총인구
    "male_pop"          INTEGER,
    "female_pop"        INTEGER,
    "households"        INTEGER,  -- 세대수
    "pop_per_household" REAL,
    "gender_ratio"      REAL
);

CREATE TABLE "academies" (   -- 6,725 학원 마스터
    "academy_name"  TEXT,
    "gu_name"       TEXT,
    "address"       TEXT,
    "academy_type"  TEXT,
    "phone"         TEXT,
    "course_count"  INTEGER,
    "ipsi_count"    INTEGER,    -- ★ 입시 강좌 수 (학군 지표)
    "avg_tuition"   REAL         -- 평균 교습비 (원)
);

CREATE TABLE "academies_courses" (   -- 65,349 강좌별
    "academy_name"   TEXT,
    "gu_name"        TEXT,
    "edu_district"   TEXT,
    "academy_type"   TEXT,
    "field"          TEXT,
    "series"         TEXT,
    "course"         TEXT,
    "class_name"     TEXT,
    "capacity"       REAL,
    "hours"          REAL,
    "tuition"        REAL,
    "total_fee"      REAL,
    "is_ipsi"        BOOLEAN,   -- ★ 입시계열 여부
    "address"        TEXT,
    "phone"          TEXT
);
