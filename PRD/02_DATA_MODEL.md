# 부산브리핑 — 데이터 모델

> 기존 `bptc_realestate.db`(공공데이터 11테이블)는 **읽기 전용**.
> 중개인 영역(손님·브리핑·리포트)만 **새 테이블** 4개로 추가.
> 개발자가 아니어도 이해할 수 있는 "개념적 ERD".

---

## 전체 구조

```
┌─────────────────────────────────────────────┐
│  [공공데이터 영역 — 읽기 전용]                │
│  bptc_realestate.db  (149MB, 약 60만 행)     │
├─────────────────────────────────────────────┤
│  apt_trade(165K)    apt_rent(351K)           │
│  apt_complex(4.2K)  schools(615)             │
│  medical(5.6K)      pharmacy(1.7K)           │
│  population_gu(960) academies(6.7K + 65K)    │
│  gu_codes_realty(16) gu_centers(16)          │
└──────────────┬──────────────────────────────┘
               │ apt_name / gu_name (JOIN 키)
               ↓
┌─────────────────────────────────────────────┐
│  [중개인 영역 — 새 테이블 4개]                │
│  briefing_app.db  (별도 파일)                │
├─────────────────────────────────────────────┤
│                                              │
│  customer ───1:N─→ briefing ─ N:M ─ 단지     │
│      │                                       │
│      └────1:N─→ match_result ── 단지         │
│                                              │
│  daily_report  (독립 — 영업구별 일일 자동)   │
│                                              │
└─────────────────────────────────────────────┘
```

> **왜 DB 파일을 분리하나**: 공공데이터는 월별로 통째 재생성되므로, 중개인이 만든 데이터(손님·메모)와 같은 파일에 두면 업데이트 시 충돌 위험. `ATTACH DATABASE`로 같이 조회 가능.

---

## 엔티티 상세

### customer (내 손님)
중개인이 상담한 손님 1명. 다음 상담 때 다시 꺼내 보기 위해 저장.

| 필드 | 설명 | 예시 | 필수 |
|------|------|------|------|
| id | 고유 식별자 (자동) | 1, 2, 3… | O |
| name | 손님 이름 | '김철수' | O |
| phone | 연락처 | '010-1234-5678' | X |
| wanted_gu | 원하는 자치구 | '해운대구' | X |
| budget_min | 예산 하한 (만원) | 50000 (5억) | X |
| budget_max | 예산 상한 (만원) | 80000 (8억) | X |
| area_min | 평형 하한 (㎡) | 84 | X |
| area_max | 평형 상한 (㎡) | 110 | X |
| deal_type | 매매 / 전세 / 월세 | '매매' | X |
| has_kids | 아이 동반 여부 | true | X |
| has_parents | 부모 동반 여부 | false | X |
| memo | 상담 메모 (자유) | '학군 1순위, 역세권 선호' | X |
| broker_memo | 중개인용 프라이빗 메모 | '결정권자는 와이프' | X |
| last_contact_at | 마지막 연락일 | 2026-05-20 | X |
| created_at | 등록일 (자동) | 2026-05-27 | O |

---

### briefing (상담 브리핑)
손님 한 명에게 특정 단지(들)로 만든 브리핑 1건. 어느 손님에게 무엇을 보여줬는지 이력 보존 + PDF 재다운로드.

| 필드 | 설명 | 예시 | 필수 |
|------|------|------|------|
| id | 고유 식별자 (자동) | 1, 2, 3… | O |
| customer_id | 어느 손님? (customer FK) | 5 | X (손님 없이 단발성 브리핑 가능) |
| apt_names | 포함된 단지명 (JSON 배열) | `["엘시티","해운대 I PARK"]` | O |
| mode | 단일 / 비교 / 매칭 | '비교' | O |
| sections | 어떤 섹션을 넣었나 (JSON) | `["시세","전세","학군","인구"]` | O |
| pdf_path | 저장된 PDF 파일 경로 | './pdfs/2026-05-27_브리핑_5.pdf' | X |
| share_url | Phase 3 공유 링크 토큰 | 'a3f9b2…' | X |
| viewed_at | 손님이 링크 연 시각 | 2026-05-27 14:32 | X |
| created_at | 생성일 (자동) | 2026-05-27 | O |

---

### match_result (매칭 기록)
손님 조건으로 DB를 점수화해 추출한 후보 단지 1개. 같은 매칭 실행에서 N개 row 생성.

| 필드 | 설명 | 예시 | 필수 |
|------|------|------|------|
| id | 고유 식별자 (자동) | 1, 2, 3… | O |
| customer_id | 어느 손님 (customer FK) | 5 | O |
| run_id | 같은 실행 묶음 ID | 'run_abc123' | O |
| apt_name | 추천 단지명 | '엘시티' | O |
| gu_name | 자치구 | '해운대구' | O |
| score | 매칭 점수 0~100 | 87 | O |
| reason | 점수 산정 이유 (JSON) | `{"예산":"적합","평형":"적합","학군":"강세"}` | O |
| matched_at | 매칭 실행 시각 | 2026-05-27 15:00 | O |

---

### daily_report (일일 리포트 — Phase 3)
중개인이 등록한 '영업 자치구'에 대해 매일 아침 자동 생성되는 어제 시장 요약.

| 필드 | 설명 | 예시 | 필수 |
|------|------|------|------|
| id | 고유 식별자 (자동) | 1, 2, 3… | O |
| report_date | 리포트 대상일 | 2026-05-26 | O |
| target_gu | 대상 자치구 | '해운대구' | O |
| top_trades | 상위 거래 TOP 5 (JSON) | `[{"apt":"엘시티","price":498000},...]` | O |
| max_price | 어제 최고가 | 498000 | X |
| total_count | 어제 거래 건수 | 23 | O |
| anomalies | 이상거래 자동 탐지 (JSON) | `[{"apt":"…","reason":"평균 +25%"}]` | X |
| pdf_path | 리포트 PDF 경로 | './pdfs/daily_해운대_2026-05-27.pdf' | X |
| created_at | 생성 시각 (자동) | 2026-05-27 07:00 | O |

---

## 관계

- `customer` 1명이 여러 개의 `briefing`을 가질 수 있음 (이력 누적)
- `customer` 1명이 여러 번 매칭 실행 가능 — 각 실행이 `run_id`로 묶인 N개 `match_result` 생성
- `briefing.apt_names`는 `apt_complex.apt_name`을 참조 (정식 FK 아닌 JSON, 단지 삭제 위험 없음)
- `daily_report`는 독립 — `target_gu`만 `gu_codes_realty.gu_name`을 참조

---

## 인덱스 (성능)

| 테이블 | 인덱스 컬럼 | 이유 |
|--------|-------------|------|
| customer | wanted_gu | 매칭 시 구 필터 |
| briefing | customer_id, created_at | 손님별 이력 조회 |
| match_result | customer_id, run_id, score DESC | 점수순 추천 |
| daily_report | target_gu, report_date DESC | 최신 리포트 조회 |

---

## 왜 이 구조인가

- **공공데이터 분리**: 매월 갱신되는 공공 DB와 사용자 데이터를 같은 파일에 두면 마이그레이션 충돌. 별도 파일 + `ATTACH DATABASE`로 해결.
- **briefing.apt_names를 JSON으로**: 단일 브리핑·비교 브리핑·매칭 브리핑을 한 테이블로 처리. 단지 1개든 5개든 동일 구조.
- **match_result를 row로 펼침**: 점수·이유 추적이 쉽고, 나중에 "이 손님에게 추천했던 단지" 통계 추출 용이.
- **broker_memo 분리**: 손님 본인에게 공유될 PDF에 노출되면 안 되는 영업 메모는 별도 필드.
- **확장성**: Phase 2 매칭 → Phase 3 공유 URL 추가 시, 기존 컬럼 변경 없이 `share_url`, `viewed_at` 컬럼만 추가하면 됨.

---

## [NEEDS CLARIFICATION]

- [ ] `customer.phone`을 PK로 쓸지 (중복 등록 방지) vs `id` AUTOINCREMENT
- [ ] `apt_complex.apt_name` 표준화 — 같은 단지인데 '엘시티'와 '엘시티 더샵'으로 두 row 있는 경우 처리
- [ ] PDF 파일 보관 기간 (디스크 용량 관리)
- [ ] `share_url`의 만료 정책 (7일? 30일? 무기한?)
