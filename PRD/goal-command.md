/goal Implement Phase 2 of 부산브리핑 (customer CRUD + 단지 비교 + 매칭 엔진 + 브리핑 이력) until every Phase 2 acceptance in PRD/V.md passes and Phase 1 regression holds.

[Abbreviations] V.md=VALIDATION.md, R.md=RECOVERY.md, P.md=PLAN.md, PR.md=PROGRESS.md

Read PRD/01_PRD.md, PRD/02_DATA_MODEL.md, PRD/03_PHASES.md (Phase 2 only), PRD/04_PROJECT_SPEC.md, PRD/V.md, PRD/R.md, PRD/P.md before any edit.

Work milestones in order from P.md: M1 briefing_app.db ATTACH + customer CRUD → M2 단지 2-way 비교 → M3 매칭 엔진 (config/match_weights.toml) → M4 briefing 이력 + Phase 1 회귀.

Do not expand scope. Phase 2 only — no Phase 3 (daily_report, share_url) or Phase 4 (auto refresh). Do not modify bptc_realestate.db schema or rows (read-only public data); record its md5 at start and verify identical at end. Store user data ONLY in briefing_app.db. Treat dealAmount as 만원 (498000 = 49.8억). No hardcoded passwords/keys/자치구 names/match weights — weights live in config/match_weights.toml only. broker_memo MUST NOT appear in 단지 비교 / 매칭 결과 / 공유 PDF.

Phase 1 regression: prior tests (test_queries, test_briefing, test_pdf) plus streamlit health must still pass. Add new files; do not change Phase 1 module function signatures.

Follow R.md for all failure handling, scope rules, domain diagnostics, and the 3-attempt pause.

Validate after each milestone using V.md commands. Update PR.md after each milestone with current state, last validation output, and any failed attempts.

If validation fails after 3 attempts or requirements conflict, stop self-edits and pause for human decision (Claude Code does not support /goal pause).
