# bptc_stocks.db — 한국 주식 데이터베이스

> KRX 정보데이터시스템 + 네이버 금융 (pykrx 경유) 수집
> 강의 실습용 · "참고용" 표시 (KRX 약관)

## 한눈에 보기

| 테이블 | 행수 | 무엇이 들어있나 |
|--------|------|--------------|
| `stocks_master` | 200 | 시가총액 TOP 200 종목 마스터 |
| `daily_price` | 250,547 | 일별 OHLCV (5년) |
| `daily_marcap` | 250,547 | 일별 시가총액 + **외국인 보유율** |
| `fundamental_monthly` | ~12,000 | 월말 PER/PBR/EPS/BPS/배당 |
| `investor_flow` | 249,795 | 일별 **투자자별 매매** (개인/기관/외국인) |
| `indexes` | 163 | 모든 지수 마스터 (KOSPI/KOSDAQ/KRX 시리즈) |
| `index_ohlcv` | 207,773 | 지수 일별 OHLCV |

## ERD

```
┌─────────────────┐
│  stocks_master  │  (삼성전자·SK하이닉스·…200종목)
│─────────────────│
│ code      PK    │  ─┬→ daily_price
│ name            │   ├→ daily_marcap
│ market          │   ├→ fundamental_monthly
└─────────────────┘   └→ investor_flow

┌─────────────────────────┐
│  daily_price            │  ★ 시세
│─────────────────────────│
│ code FK | date          │
│ open | high | low | close│
│ volume | change_pct     │
└─────────────────────────┘

┌──────────────────────────────┐
│  daily_marcap                │  ★ 시총 + 외국인
│──────────────────────────────│
│ code FK | date               │
│ marcap (시가총액)            │
│ shares (상장주식수)          │
│ foreign_shares (외국인보유수)│
│ foreign_rate  (외국인보유율%)│
└──────────────────────────────┘

┌─────────────────────────┐
│  fundamental_monthly    │  ★ 밸류에이션
│─────────────────────────│
│ code FK | date (월말)   │
│ per | pbr | eps | bps   │
│ div_yield | dps         │
└─────────────────────────┘

┌─────────────────────────────┐
│  investor_flow              │  ★ 수급 (순매수액)
│─────────────────────────────│
│ code FK | date              │
│ individual    (개인)        │
│ foreign       (외국인 합계) │
│ institution   (기관 합계)   │
│ other_corp    (기타법인)    │
│ total         (전체)        │
└─────────────────────────────┘

┌──────────────────┐         ┌──────────────────────┐
│  indexes         │         │  index_ohlcv         │
│──────────────────│         │──────────────────────│
│ index_code  PK   │ 1:N ──→ │ index_code FK | date │
│ index_name       │         │ open|high|low|close  │
│ market           │         │ volume               │
└──────────────────┘         └──────────────────────┘
```

## 주요 컬럼 상세

### daily_price
| 컬럼 | 예시 | 설명 |
|------|------|------|
| code | '005930' | 종목코드 |
| date | '2026-05-21' | 거래일 |
| open / high / low / close | 282000 | 시가/고가/저가/종가 (원) |
| volume | 39314752 | 거래량 (주) |
| change_pct | 4.225352 | 등락률 (%) |

### daily_marcap
| 컬럼 | 예시 | 설명 |
|------|------|------|
| code | '005930' | 종목코드 |
| marcap | 1555110109728000 | 시가총액 (원) — **1,555조** |
| shares | 5846278608 | 상장주식수 |
| foreign_shares | 2886478875 | 외국인 보유주식수 |
| foreign_rate | **49.375** | 외국인 보유율 (%) |

### fundamental_monthly
| 컬럼 | 예시 | 설명 |
|------|------|------|
| date | '2021-01-31' | 월말 기준일 |
| per | 26.22 | 주가수익비율 |
| pbr | 2.21 | 주가순자산비율 |
| eps | 3166 | 주당순이익 (원) |
| div_yield | 1.71 | 배당수익률 (%) |
| dps | 1416 | 주당배당금 (원) |

### investor_flow (순매수 단위: 원)
| 컬럼 | 의미 |
|------|------|
| individual | 개인 순매수 (양수=순매수, 음수=순매도) |
| foreign | 외국인 합계 |
| institution | 기관 합계 (금융투자+보험+투신+사모+은행+연기금) |
| other_corp | 기타법인 |

## 데이터 범위

- **기간**: 2021-01-04 ~ 2026-05-21 (약 5년)
- **종목**: 시총 TOP 200 (KOSPI + KOSDAQ)
- **갱신**: 일별 (재빌드 시 END_DATE 수정)
- **빠진 데이터**: 공매도 거래량/잔고 (KRX IP 차단으로 미수집 — 별도 자료 참조)

## 라이선스

KRX "참고용" 표시. 강의·교육 목적 무방, 상업적 재배포 시 KRX 약관 확인.
