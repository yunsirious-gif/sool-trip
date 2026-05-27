# bptc_busan.db — 부산 도시철도 데이터베이스

> 부산교통공사 공공데이터 기반 SQLite 데이터베이스
> 강의 실습용 · 공공누리 1유형 (출처표시 시 자유 이용)

## 한눈에 보기

| 테이블 | 행수 | 무엇이 들어있나 |
|--------|------|--------------|
| `lines` | 4 | 부산 도시철도 1~4호선 마스터 |
| `stations` | 112 | 모든 역 정보 (역번호·역명·노선) |
| `daily_passengers` | **645,120** | 일별·시간대별 승하차 인원 (메인) |
| `monthly_passport` | 14,784 | 월별·역별 권종별 (무임·어린이·청소년) |
| `gu_codes` | 16 | 부산 16개 자치구·군 코드 |

## ERD (Entity Relationship)

```
┌─────────────┐
│   lines     │  (1호선·2호선·3호선·4호선)
│─────────────│
│ line_no  PK │
│ line_name   │
│ color       │
│ operator    │
│ open_year   │
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐
│  stations   │  (다대포해수욕장·서면·해운대 등 112개)
│─────────────│
│ station_id  │ PK
│ station_name│
│ line_no  FK │ ──→ lines.line_no
│ lat / lng   │ (좌표는 비어있음, 지도 시각화 필요 시 추가 수집)
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────────────┐
│ daily_passengers    │  ★ 메인 테이블 645K행
│─────────────────────│
│ station_id    FK    │
│ station_name        │
│ line_no       FK    │
│ date  (YYYY-MM-DD)  │
│ weekday (월~일)     │
│ hour  (1~24)        │
│ direction           │  'board' (승차) | 'alight' (하차)
│ passengers          │  명
└─────────────────────┘

┌─────────────────────┐
│ monthly_passport    │  권종별 (어린이/청소년/무임 등)
│─────────────────────│
│ station_name        │
│ 연월                │
│ board_cnt           │
│ alight_cnt          │
│ 무임 / 어린이 / 청소년│
└─────────────────────┘

┌─────────────┐
│  gu_codes   │  (중구·서구·동구·…해운대구·기장군)
│─────────────│
│ gu_code PK  │ (예: 26350 = 해운대구)
│ gu_name     │
│ type        │ '구' | '군'
└─────────────┘
```

## 컬럼 상세

### lines
| 컬럼 | 타입 | 예시 | 설명 |
|------|------|------|------|
| line_no | INTEGER | 1, 2, 3, 4 | 노선 번호 |
| line_name | TEXT | '1호선' | 노선명 |
| color | TEXT | '#F37423' | 노선 색상 (HEX) |
| operator | TEXT | '부산교통공사' | 운영기관 |
| open_year | INTEGER | 1985 | 개통연도 |

### stations
| 컬럼 | 타입 | 예시 | 설명 |
|------|------|------|------|
| station_id | INTEGER | 95, 222, 313 | 역번호 (앞자리=노선) |
| station_name | TEXT | '다대포해수욕장', '서면', '해운대' | 역명 |
| line_no | INTEGER | 1 | 노선번호 |

### daily_passengers (메인)
| 컬럼 | 타입 | 예시 | 설명 |
|------|------|------|------|
| date | TEXT | '2026-05-21' | YYYY-MM-DD |
| weekday | TEXT | '월', '화' | 요일 |
| hour | INTEGER | 1~24 | 시간대 (1시-2시 → 1) |
| direction | TEXT | 'board', 'alight' | 승차/하차 |
| passengers | INTEGER | 1523 | 인원 |

## 데이터 범위

- **기간**: 2026년 1월 ~ 5월 (확장 가능)
- **노선**: 부산교통공사 1~4호선 (사하·해운대·범어사·노포·반송 포함)
- **시간단위**: 1시간
- **누락**: 좌표(lat/lng)는 별도 수집 필요 — 지도 시각화 시 추가
- **사기업 구간**: 동해선·부산김해경전철 미포함

## 라이선스

공공누리 1유형 (출처표시) — 상업적 사용 가능
출처: 부산교통공사 (data.go.kr/data/3057229)
