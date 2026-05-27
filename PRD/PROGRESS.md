# PROGRESS

## Current Goal

Phase 2 of 부산브리핑: 손님 관리 + 단지 2개 비교 + 매칭 엔진 + 브리핑 이력 (Phase 1 회귀 0건 유지).

## Current Milestone

⏳ **M1 — briefing_app.db ATTACH + customer CRUD** (시작 전)

## Completed

(없음 — 골 발사 직후)

## Last Validation

(없음 — 첫 마일스톤 종료 후 기록)

## Failed Attempts

| Attempt | Change | Result | Lesson |
| --- | --- | --- | --- |
| — | — | — | — |

## Current Best State

Phase 1 완료 상태 유지 (이전 골 종료 시점: 16/16 pytest PASS, Streamlit health OK, 4,278 단지 검색 가능). Phase 2 신규 코드 0줄.

## Phase 2 Acceptance Tracking

| 기준 | 측정 | 결과 |
|------|------|------|
| Phase 1 단지 브리핑 회귀 정상 | pytest test_queries / test_briefing / test_pdf | PENDING |
| 손님 100명 등록 후 매칭 ≤ 2s | tests/test_matching.py::test_match_under_2s | PENDING |
| briefing customer_id NULL 허용 | tests/test_briefing_history.py | PENDING |
| broker_memo 공유 영역 미노출 | tests/test_privacy.py + 수동 | PENDING |
| 매칭 가중치 config 외부화 | tests/test_matching.py::test_weights_from_config | PENDING |
| bptc_realestate.db 0회 수정 | md5 시작/종료 비교 | PENDING |
| briefing_app.db 스키마 = 02_DATA_MODEL.md | Required Check #4 | PENDING |

## Next Step

골 발사 직후 첫 작업:
1. bptc_realestate.db md5 기록 (R.md 도메인 진단 참조)
2. `app/scripts/init_briefing_app_db.py` 작성 → 실행 → 테이블 3 + 인덱스 4 확인
3. `lib/db.py`에 ATTACH DATABASE 추가 (기존 시그니처 유지)
4. M1 customer CRUD 진행

## Risks / Blockers

- briefing_app.db와 bptc_realestate.db ATTACH 경로 (WSL `/mnt/c` 절대경로 권장)
- 매칭 가중치 초기값 (PRD §7 NEEDS CLARIFICATION) — 일단 30/20/20/15/15로 시작, 1주 실사용 후 튜닝
- apt_complex 단지명 중복 (엘시티 vs 엘시티 더샵) — 비교 페이지 selectbox에 자치구·거래수 함께 표시로 우회
- match_result row 보관 정책 — 같은 손님 이전 run_id는 새 실행 시 삭제로 시작 (단순화)

## Handoff Notes

- 골 발사 안내 시각: 2026-05-27 (Phase 2 골잡이 출력)
- Phase 1 종료 시점 16/16 테스트 + Streamlit health OK (이전 PROGRESS 기록 보존됨)
- bptc_realestate.db md5 골 시작 시 기록 필수
- 골 완료 조건은 PRD/PLAN.md §Final Completion Criteria 9개 모두 ✓
