# PLAN: 부산브리핑 Phase 2

## Goal

Phase 1 위에 손님 관리 + 단지 2개 비교 + 매칭 엔진 + 브리핑 이력을 추가하되, Phase 1 회귀 0건을 유지한다.

## Source Documents

- PRD: PRD/01_PRD.md, 02_DATA_MODEL.md, 03_PHASES.md (§Phase 2), 04_PROJECT_SPEC.md
- VALIDATION.md
- RECOVERY.md

## Milestone 1: briefing_app.db ATTACH + customer CRUD
- Scope:
  - `app/scripts/init_briefing_app_db.py`: customer / briefing / match_result 테이블 + 인덱스 4종 (02_DATA_MODEL.md §인덱스 표 그대로)
  - `lib/db.py`에 `ATTACH DATABASE` 추가 — 기존 `get_conn()` 함수 시그니처는 유지, 내부에서 ATTACH (`@st.cache_resource`)
  - `lib/customer.py` (신규): create / read / update / delete + 검색 by 이름·연락처. broker_memo 분리 SELECT 함수 별도 제공
  - `pages/2_손님_관리.py`: 등록 폼, 손님 목록 테이블, 상세 페이지(일반 메모 / broker_memo 별도 표시)
  - `tests/test_customer.py`: 등록·조회·수정·삭제 + 100명 성능 케이스 5+
- Completion: 비밀번호 통과 후 손님 페이지에서 CRUD 전부 동작 + Phase 1 회귀 0건
- Validation:
  - `tests/test_customer.py` 통과
  - 100명 INSERT 후 전체 SELECT ≤ 2s
  - `tests/test_queries.py / test_briefing.py / test_pdf.py` 전부 PASS 유지
  - briefing_app.db 스키마 = Required Check #4 기대값

## Milestone 2: 단지 2개 나란히 비교
- Scope:
  - `pages/3_단지_비교.py`: 좌·우 selectbox(자치구·거래수 함께 표시) + 가격/평형/건축년도/거래량 대조표
  - `lib/charts.py`에 `line_chart_overlay(name1, name2)` 신규 함수 추가 — Phase 1 함수 시그니처 변경 금지
  - 학군·인프라 점수 카드 좌우 비교 (자치구 단위 집계, "자치구 단위" 라벨 명시)
  - 모든 차트에 출처 워터마크
  - `tests/test_compare.py::test_compare_render_under_3s`
- Completion: 임의 단지 2개 비교 페이지 ≤ 3s 렌더링 + 스크린샷 저장
- Validation:
  - `tests/test_compare.py` 통과
  - 수동: 엘시티 vs 해운대 I PARK 비교 화면 정상
  - 스크린샷 `screenshots/compare_엘시티_아이파크.png` 저장

## Milestone 3: 매칭 엔진
- Scope:
  - `config/match_weights.toml`: 예산30 / 평형20 / 학군20 / 거래15 / 신축15 (합 100)
  - `lib/matching.py`: `compute_scores(customer_dict, weights) -> List[{apt_name, gu_name, score, reason}]`
  - `pages/4_매물_매칭.py`: 손님 selectbox → 조건 자동 채움 → "추천 단지 보기" → 점수순 상위 N개 + 이유 JSON 카드 표시
  - `match_result` 자동 저장 — run_id = `uuid4().hex`. 같은 손님 이전 run_id 결과는 새 실행 시 삭제 (보관 정책 PROGRESS.md에 기록)
  - `tests/test_matching.py`: 점수 산정 / run_id 묶음 / 가중치 외부화 / 100명 성능
- Completion: 100명 등록 상태에서 매칭 ≤ 2s + match_result row 정상 생성
- Validation:
  - `tests/test_matching.py::test_match_under_2s` 통과
  - `tests/test_matching.py::test_weights_from_config` 통과 (코드 하드코딩 0 확인)
  - 수동: 자치구·예산 다른 손님 3명에게 각각 다른 추천 결과
  - 가중치 변경(config 편집) → 매칭 결과 즉시 반영

## Milestone 4: 브리핑 이력 + Phase 1 회귀 테스트
- Scope:
  - Phase 1 브리핑 페이지에 "손님 선택(옵션)" 드롭다운 추가 — 선택 시 `briefing` row 저장(customer_id 옵션)
  - `briefing.apt_names`는 JSON 배열로 저장, `mode` = 단일 / 비교 / 매칭 구분
  - 손님 페이지에 "이전 브리핑" 섹션 + `pdf_path` 재사용 재다운로드 버튼
  - 매칭 결과에서 단지 클릭 → 브리핑으로 이동 (`mode='매칭'`)
  - `tests/test_briefing_history.py` (customer_id NULL 허용, 재다운로드)
  - `tests/test_privacy.py` (broker_memo가 비교/매칭/공유 영역에 없음)
  - 최종 회귀: `pytest tests/` 전체
- Completion: Phase 1 전체 + Phase 2 신규 테스트 모두 PASS + bptc_realestate.db md5 불변
- Validation:
  - 전체 pytest 통과 (Phase 1 16개+ 회귀 유지)
  - 수동: 손님 페이지 이전 PDF 재다운로드 성공
  - bptc_realestate.db md5: 골 시작/종료 동일

## Final Completion Criteria

- [ ] M1~M4 모두 완료
- [ ] VALIDATION.md의 Required + Targeted Check 전부 통과
- [ ] Phase 1 회귀 0건 (test_queries / test_briefing / test_pdf 유지)
- [ ] Phase 3 / Phase 4 기능 0개 (daily_report / share_url / auto refresh 금지)
- [ ] briefing_app.db 스키마 = 02_DATA_MODEL.md (테이블 3 + 인덱스 4)
- [ ] bptc_realestate.db INSERT/UPDATE/DELETE 0회 (md5 검증)
- [ ] broker_memo 공유 영역 미노출 (`tests/test_privacy.py` + 수동 점검)
- [ ] 매칭 가중치 = `config/match_weights.toml` (코드 하드코딩 0)
- [ ] PROGRESS.md updated
- [ ] 사무실 PC 인수인계 가능 (Phase 1 README 갱신 또는 Phase 2 페이지 사용법 추가)
