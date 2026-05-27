# RECOVERY

## Core Rule

If validation fails, do not immediately make a broad change. Diagnose first.

## Failure Loop

When a validation step fails:

1. Read the full failure output.
2. Identify failure category: implementation bug / incorrect test / missing dependency / environment / unclear requirement / scope conflict.
3. Compare against PRD/01_PRD.md, PRD/02_DATA_MODEL.md, PRD/03_PHASES.md, PRD/PLAN.md, PRD/VALIDATION.md.
4. Make the smallest reversible fix.
5. Re-run the smallest relevant validation first.
6. Update PROGRESS.md.

## Retry Limit

If the same validation fails after 3 distinct attempts:

골이 진단·검토에 진입하고 자체 수정을 멈춘다. `/goal pause`는 Claude Code가 지원하지 않으므로 사람 결정을 기다린다. 필요 시 `/goal clear` 후 재설정.

Report:
- failing command or criterion
- three attempted fixes
- why each failed
- safest next options
- whether user/product guidance is needed

## Scope Control

Do not:
- modify Phase 1 modules (`lib/queries.py`, `lib/charts.py`, `lib/pdf.py`, `lib/db.py` 기존 함수) — Phase 2는 신규 함수 추가만. 시그니처 변경 금지
- modify bptc_realestate.db schema or rows — read-only public data. 골 시작 시 md5 기록 후 종료 시 동일 확인
- store customer / briefing / match_result rows in bptc_realestate.db — 반드시 briefing_app.db
- implement Phase 3 (daily_report, share_url) or Phase 4 (auto refresh)
- hardcode passwords, API keys, 자치구 names, apt names, match weights
- assume dealAmount is in 원 — it is **만원** (498000 = 49.8억)
- expose `broker_memo` on 단지 비교 / 매칭 결과 / 공유 PDF
- change matching weights in code — only via `config/match_weights.toml`
- delete or skip tests to make checks pass
- silence errors without diagnosis
- introduce broad refactors while fixing a narrow issue
- replace the validation command itself
- change public APIs unless PLAN.md says so

## Reorientation Rule

Before changing approach:

1. Reread the goal statement.
2. Reread Non-goals in PRD/01_PRD.md §6 (Out of Scope).
3. Reread PRD/03_PHASES.md §Phase 2 only — Phase 3/4 항목은 무시.
4. Reread current milestone in PRD/PLAN.md.
5. Confirm the next edit directly serves the current milestone.
6. Re-confirm change does not violate PRD/04_PROJECT_SPEC.md "절대 하지 마" list.

## Revert Rule

Only revert your own last failed change if:
- it made validation worse,
- it introduced unrelated changes,
- or it conflicts with PRD / PLAN.

Do not revert user changes unless explicitly instructed.

## Domain-specific Diagnostics

- **briefing_app.db ATTACH 실패** → 경로를 `os.path.abspath`로 절대화. 한 connection에서 두 DB 모두 접근. WSL `/mnt/c` 사용 시 경로에 공백·한글 주의.
- **customer SELECT 후 매칭 느림** → `idx_customer_gu`, `idx_match_run`, `idx_match_score` 인덱스 누락 의심. 02_DATA_MODEL.md §인덱스 표 확인.
- **단지 비교 시 한 단지 데이터 부족** → trade_count=0 단지는 selectbox에서 제외하거나 친절한 한글 안내 ("최근 5년 거래 없음").
- **매칭 결과 항상 같은 단지** → `match_weights.toml` 합이 100인지 + 자치구 필터 적용 여부 + 예산·평형 범위 NULL 처리 확인.
- **broker_memo 누출** → 단지 비교/매칭 페이지의 customer 조회 시 전용 query 함수 사용 (`SELECT id,name,phone,wanted_gu,budget_*,area_*,deal_type,memo` — broker_memo 제외).
- **Phase 1 회귀** → `git diff app/lib/queries.py app/lib/charts.py app/lib/pdf.py` — 기존 함수 시그니처 바뀌었다면 즉시 revert + 신규 파일에서 처리. Phase 1 테스트 먼저 통과시키고 Phase 2 진행.
- **match_result row 폭발** → 같은 손님의 직전 run_id 결과는 새 매칭 실행 시 삭제 (또는 보관 정책 PROGRESS.md에 명시).
- **bptc_realestate.db md5 변경** → 어떤 INSERT/UPDATE/DELETE가 들어갔는지 git diff + sqlite3 dump 비교. 즉시 백업본으로 복원.
- **WeasyPrint 한글 깨짐 재발** → Phase 1과 동일 — Malgun Gothic 시스템 폰트 사용 확인.
