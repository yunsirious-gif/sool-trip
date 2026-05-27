# bptc 강의 데이터베이스 — AI 컨텍스트 가이드

> 이 파일에는 데이터베이스의 표·컬럼 구조가 정리돼 있습니다.
> AI에 먼저 읽히면 DB 구조를 파악해서, 질문에 맞는 데이터를 정확히 가져옵니다.
> 새 대화 첫 메시지에 첨부하세요. (수강생이 SQL을 직접 짤 필요는 없습니다)

## 패키지 개요

3개의 SQLite 데이터베이스 파일로 구성된 강의 실습 패키지.

```
bptc_data_pack/
├── bptc_busan.db       (66MB)  부산 도시철도 — 5테이블, 660K행
├── bptc_stocks.db      (83MB)  한국 주식 — 7테이블, 1.2M행
└── bptc_realestate.db  (149MB) 부산 부동산 + 학군/의료/인구 — 11테이블, 60만행
```

총 약 240만 행 · 23개 테이블.

## SQL 작성 시 절대 규칙

1. **컬럼명에 한글 있으면 큰따옴표로 감싸기** — `"무임"`, `"청소년"`
2. **SQLite 예약어 컬럼은 큰따옴표 필수** — `i."foreign"`, `"order"`
3. **모든 쿼리에 `LIMIT 100` 기본** — 60만 행 통째로 SELECT 금지
4. **날짜는 작은따옴표 문자열** — `WHERE deal_date >= '2025-01-01'`
5. **금액 단위 주의** — `dealAmount`는 **만원 단위** (10000 = 1억)
6. **컬럼명 추측 금지** — 모르면 `PRAGMA table_info(테이블명)` 먼저 확인

## DB 1: bptc_busan.db (부산 도시철도)

### lines (4행) — 노선 마스터
| 컬럼 | 타입 | 예시 | 설명 |
|------|------|------|------|
| line_no | INTEGER | 1, 2, 3, 4 | 노선 번호 |
| line_name | TEXT | '1호선' | |
| color | TEXT | '#F37423' | HEX 색상 |
| open_year | INTEGER | 1985 | 개통연도 |

### stations (112행) — 역 마스터
| 컬럼 | 예시 | 설명 |
|------|------|------|
| station_id | 95, 222, 313 | 역번호 (앞자리=노선) |
| station_name | '서면', '해운대' | |
| line_no | 1, 2, 3, 4 | |
| lat, lng | NULL | ⚠ 좌표 비어있음 |

### daily_passengers (645,120행) ★ 메인
| 컬럼 | 예시 | 설명 |
|------|------|------|
| date | '2026-05-21' | YYYY-MM-DD |
| weekday | '월', '화' | 요일 |
| hour | 1~24 | 시간대 |
| direction | 'board', 'alight' | 승차/하차 |
| passengers | 1523 | 인원 (명) |

### monthly_passport (14,784행)
| 컬럼 | 설명 |
|------|------|
| 연월 | "2025-04" 등 (한글 컬럼 주의) |
| board_cnt, alight_cnt | 승하차 수 |
| 무임, 어린이, 청소년 | 권종별 (한글 컬럼) |

### gu_codes (16행) — 부산 자치구
| gu_code | gu_name | type |
|---------|---------|------|
| 26350 | 해운대구 | 구 |
| 26710 | 기장군 | 군 |

---

## DB 2: bptc_stocks.db (한국 주식)

### stocks_master (200행)
| 컬럼 | 예시 |
|------|------|
| code | '005930' (삼성전자), '000660' (SK하이닉스) |
| name | '삼성전자' |
| market | 'KOSPI', 'KOSDAQ' |

### daily_price (250,547행) ★ 시세
| 컬럼 | 예시 | 설명 |
|------|------|------|
| code | '005930' | FK → stocks_master |
| date | '2026-05-21' | |
| open, high, low, close | 282000 | 원 단위 |
| volume | 39314752 | 주 |
| change_pct | 4.225352 | 등락률 % |

### daily_marcap (250,547행) ★ 시총 + 외국인
| 컬럼 | 예시 | 설명 |
|------|------|------|
| date, code | | FK |
| marcap | 1555110109728000 | 시가총액 원 단위 |
| foreign_rate | **49.375** | 외국인 보유율 % |
| foreign_shares, shares | | |

### fundamental_monthly (12,236행)
| 컬럼 | 의미 |
|------|------|
| date | 월말 |
| per, pbr, eps, bps | 밸류에이션 |
| div_yield | 배당수익률 % |
| dps | 주당 배당금 원 |

### investor_flow (249,795행) ★ 수급
⚠ **`foreign`은 예약어 — 반드시 `"foreign"` 큰따옴표로 감싸기**
| 컬럼 | 의미 |
|------|------|
| date, code | |
| individual | 개인 순매수 (원) |
| **"foreign"** | 외국인 순매수 (양수=매수) |
| institution | 기관 |
| other_corp | 기타법인 |
| total | 전체 합계 |

### indexes (163행) + index_ohlcv (207,773행)
- 코스피·코스닥·KRX 시리즈 지수
- `index_code = '1001'` = 코스피, `'2001'` = 코스닥

---

## DB 3: bptc_realestate.db (부산 부동산 + 학군 + 인프라)

### apt_trade (165,386행) ★ 매매
| 컬럼 | 예시 | 설명 |
|------|------|------|
| aptNm | '엘시티', '센텀리슈빌2단지' | 단지명 |
| gu_name | '해운대구' | 자치구 |
| deal_date | '2025-04-02' | YYYY-MM-DD |
| **dealAmount** | 498000 | **만원 단위** (49.8억) |
| excluUseAr | 186.0063 | 전용면적 ㎡ |
| floor | '12' | 층 |
| buildYear | '2019' | 건축년도 |
| roadNm, umdNm | '해운대로76번길', '우동' | 도로/법정동 |
| dealingGbn | '중개거래' | 거래유형 |
| buyerGbn, slerGbn | '개인' | 매수/매도자 |

### apt_rent (351,186행) ★ 전월세
| 컬럼 | 예시 | 설명 |
|------|------|------|
| deposit | 50000 | 보증금 **만원** (5억) |
| monthlyRent | 100 | 월세 **만원** (0이면 순수 전세) |
| contractType | '신규', '갱신' | |

### apt_complex (4,278행) — 단지 마스터
- apt_name (PK), gu_name, build_year, min_area, max_area, trade_count

### gu_codes_realty (16) + gu_centers (16)
- gu_centers에 lat/lng 있음 → Folium 지도용

### schools (615행) — 부산 초·중·고
| 컬럼 | 예시 |
|------|------|
| school_name, school_type ('초등학교') |
| gu_name, road_name_addr |
| lat, lng | ★ 위경도 있음 |

### medical (5,623행) + pharmacy (1,732행)
| 컬럼 | 의미 |
|------|------|
| name, category ('의원', '치과의원', '한의원') |
| gu_name |
| address, phone |
| lat, lng |

### population_gu (960행 — 16구 × 60개월)
| 컬럼 | 예시 |
|------|------|
| gu_name | '해운대구' |
| ref_date | '2026-04' (YYYY-MM) |
| total_pop, male_pop, female_pop | 371143 |
| households | 세대수 |

### academies (6,725행) ★ 학원 마스터
| 컬럼 | 의미 |
|------|------|
| academy_name, gu_name |
| course_count | 운영 강좌 수 |
| **ipsi_count** | 입시 강좌 수 (학군 강도) |
| avg_tuition | 평균 교습비 |

### academies_courses (65,349행) — 강좌별
| 컬럼 | 의미 |
|------|------|
| academy_name, gu_name |
| field, series, course | 분야/계열/과정 |
| tuition, total_fee | 교습비 (원) |
| **is_ipsi** | 입시계열 boolean |

---

## JOIN 가능한 키

```
gu_name (자치구) — 부산 16개 표준
  ├─ bptc_busan.db:        gu_codes
  └─ bptc_realestate.db:   apt_trade, apt_rent, schools, medical,
                            pharmacy, population_gu, academies, gu_codes_realty

code (종목코드) — bptc_stocks.db 내부
  └─ stocks_master ← daily_price, daily_marcap, fundamental_monthly, investor_flow

aptNm (단지명) — bptc_realestate.db 내부
  └─ apt_complex ← apt_trade, apt_rent

station_name — bptc_busan.db 내부
  └─ stations ← daily_passengers, monthly_passport
```

## Cross-DB JOIN

```sql
ATTACH DATABASE 'bptc_busan.db' AS busan;
SELECT ar.gu_name, AVG(ar.dealAmount) as avg_price
FROM apt_trade ar
WHERE ar.gu_name IN (SELECT DISTINCT gu_name FROM busan.gu_codes)
GROUP BY ar.gu_name;
```

## 검증된 인사이트 (강의 참고)

- 부산 거래 1위: **부산진구** 18,993건 (해운대 아님)
- 평당가 1위: **수영구** 2,931만원/평
- 학원 입시강좌 1위: **동래구** 6,228개
- 인구 vs 집값 역상관: 동구 인구 -5.2% / 집값 +60%
- 삼성전자 외국인 보유율: 49.375%

## AI에게 SQL 부탁할 때 좋은 프롬프트 패턴

```
이 파일(CLAUDE.md)을 읽었어. 
이제 bptc_realestate.db에서
"해운대구 2025년 단지별 평균 거래금액 TOP 10 + 입시강좌 수"
를 가져오는 SQL 짜줘. 
- 한글 컬럼은 큰따옴표
- foreign 같은 예약어 처리
- LIMIT 10
```
