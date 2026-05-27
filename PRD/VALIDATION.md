# VALIDATION: 부산브리핑 Phase 2

## Required Checks

다음 명령은 골 완료로 마크하기 전 반드시 실행한다.

```bash
# 1. 임포트 — Phase 2 신규 모듈 포함
cd app && python3 -c "import app, lib.db, lib.matching, lib.customer, lib.queries, lib.charts, lib.pdf, lib.auth; print('OK')"

# 2. 전체 pytest (Phase 1 회귀 + Phase 2 신규)
cd app && python3 -m pytest tests/ -v

# 3. Streamlit health
cd app && streamlit run app.py --server.headless true & sleep 5 && curl -fsS http://localhost:8501/_stcore/health && kill %1

# 4. briefing_app.db 스키마 무결성
cd app && python3 -c "import sqlite3; c=sqlite3.connect('briefing_app.db'); print(sorted(r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()))"
# 기대값: ['briefing', 'customer', 'match_result']

# 5. bptc_realestate.db 읽기 전용 재확인 (md5 시작/종료 비교)
cd app && python3 -c "import hashlib; print(hashlib.md5(open('../02_데이터베이스/bptc_realestate.db','rb').read()).hexdigest())"
# 골 시작 시 md5 기록 후 종료 시 동일성 확인
```

## Targeted Checks

각 마일스톤 종료 시 실행한다.

```bash
# M1: briefing_app.db ATTACH + customer CRUD
cd app && python3 -m pytest tests/test_customer.py -v
# 손님 100명 INSERT + 전체 SELECT ≤ 2초

# M2: 단지 2개 비교
cd app && python3 -m pytest tests/test_compare.py::test_compare_render_under_3s -v
# 스크린샷 screenshots/compare_엘시티_아이파크.png 저장

# M3: 매칭 엔진
cd app && python3 -m pytest tests/test_matching.py -v
# 100명 등록 상태에서 매칭 ≤ 2초 + match_result row 생성 + run_id 묶음 확인

# M4: 브리핑 이력 + Phase 1 회귀
cd app && python3 -m pytest tests/ -v
# Phase 1 (test_queries / test_briefing / test_pdf) 모두 PASS 유지
```

## Manual Verification

1. `cd app && streamlit run app.py` 실행
2. 비밀번호 입력 후 진입
3. **손님 관리**: "김철수" 등록 → 일반 메모 + broker_memo 작성 → 다시 조회 시 두 필드 모두 보임
4. **단지 비교**: "엘시티" vs "해운대 I PARK" 선택 → 좌우 대조표 + 시세 오버레이 차트 + 학군·인프라 점수 카드 비교
5. **매물 매칭**: 손님 김철수 선택 → "추천 단지 보기" 클릭 → 점수순 상위 5개 + 이유 JSON 표시 → match_result 저장 확인
6. **브리핑 이력**: 손님 페이지에서 "이전 브리핑" 클릭 → 기존 PDF 재다운로드 성공
7. **Phase 1 회귀**: "엘시티" 검색 → 6섹션 브리핑 여전히 3초 이내 + PDF 정상
8. **broker_memo 격리**: 단지 비교 / 매칭 결과 / 공유 PDF 어디에도 broker_memo 텍스트 미노출 확인
9. 1280×800 해상도에서 신규 페이지(2/3/4) 가로 스크롤 없음

## Visual Verification

- [ ] 단지 비교 페이지 1280×800 가로 스크롤 없음
- [ ] 매칭 결과 카드 한글 깨짐 없음
- [ ] 모든 신규 차트에 출처 워터마크
- [ ] 스크린샷 저장:
  - `./screenshots/customer_김철수.png`
  - `./screenshots/compare_엘시티_아이파크.png`
  - `./screenshots/match_김철수.png`
  - `./screenshots/history_김철수.png`

## Acceptance Criteria Mapping

| PRD criterion | Validation method | Status |
| --- | --- | --- |
| Phase 1 단지 브리핑 회귀 정상 | `pytest tests/test_queries.py tests/test_briefing.py tests/test_pdf.py` | PENDING |
| 손님 100명 등록 후 매칭 ≤ 2s | `tests/test_matching.py::test_match_under_2s` | PENDING |
| briefing customer_id NULL 허용 (단발성) | `tests/test_briefing_history.py` | PENDING |
| broker_memo 공유 영역 미노출 | `tests/test_privacy.py` + 수동 8번 | PENDING |
| 매칭 가중치 config 외부화 | `tests/test_matching.py::test_weights_from_config` | PENDING |
| bptc_realestate.db 0회 수정 | md5 시작/종료 비교 | PENDING |
| briefing_app.db 스키마 = 02_DATA_MODEL.md | Required Check #4 + 인덱스 4종 존재 | PENDING |

## Not Done If

- Any required check fails
- Scope changed (Phase 3 daily_report / share_url / Phase 4 진입)
- bptc_realestate.db md5 변경 (공공 DB 수정)
- briefing_app.db 스키마가 02_DATA_MODEL.md와 불일치
- broker_memo가 단지 비교 / 매칭 / 공유 PDF 어디든 노출
- Phase 1 회귀 테스트 1개라도 깨짐
- 매칭 가중치가 코드에 하드코딩 (config/match_weights.toml 누락)
- 자치구명·단지명 하드코딩
- Test 삭제·skip으로 통과
- Error silenced without diagnosis
- Artifact 생성됐는데 열어본 적 없음 (PDF 재다운로드 미확인 등)
- Public API 변경 (Phase 1 모듈 함수 시그니처 변경)
