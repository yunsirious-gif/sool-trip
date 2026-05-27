"""브리핑 페이지 렌더링 시간 측정 — VALIDATION.md M2 대응."""

import time

import pytest

from lib import charts, queries


def _render_all(apt_name: str):
    info = queries.complex_info.__wrapped__(apt_name)
    if info is None:
        return None
    trade = queries.trade_history.__wrapped__(apt_name)
    rent = queries.rent_history.__wrapped__(apt_name)
    ranking = queries.gu_ranking.__wrapped__(info["gu_name"], limit=10)
    infra = queries.gu_infra.__wrapped__(info["gu_name"])
    pop = queries.gu_population.__wrapped__(info["gu_name"])
    charts.line_chart_trade(trade)
    charts.line_chart_rent(rent)
    charts.bar_ranking(ranking, highlight_apt=apt_name)
    charts.line_population(pop)
    return info


@pytest.fixture(scope="module", autouse=True)
def _warmup_sqlite_page_cache():
    """첫 콜드 콜 페널티 회피 — production은 OS 페이지 캐시가 항상 hot."""
    _render_all("엘시티")
    yield


@pytest.mark.parametrize("apt_name", ["엘시티", "해운대 I PARK", "장산마을"])
def test_render_under_3s(apt_name):
    """PRD §5: 단지명 입력 → 브리핑 렌더링 3초 이내.

    queries 6개 + charts 4개 호출 시간 합산 측정. SQLite OS 페이지 캐시가
    웜업된 상태(=streamlit run 후 두 번째 사용자부터의 상태) 기준.
    """
    t0 = time.perf_counter()
    info = _render_all(apt_name)
    if info is None:
        pytest.skip(f"단지 없음: {apt_name}")
    elapsed = time.perf_counter() - t0
    assert elapsed < 3.0, f"{apt_name} 렌더링 {elapsed:.2f}s > 3.0s"


def test_six_sections_complete():
    """브리핑 페이지가 PRD §3 명시 6개 섹션 데이터를 모두 반환."""
    apt = "엘시티"
    info = queries.complex_info.__wrapped__(apt)
    assert info is not None
    gu = info["gu_name"]

    sections = {
        "단지 정보": info,
        "매매 시세": queries.trade_history.__wrapped__(apt),
        "전월세": queries.rent_history.__wrapped__(apt),
        "구 거래량 순위": queries.gu_ranking.__wrapped__(gu),
        "인프라": queries.gu_infra.__wrapped__(gu),
        "인구 추이": queries.gu_population.__wrapped__(gu),
    }
    for name, data in sections.items():
        assert data is not None and (
            (hasattr(data, "empty") and not data.empty) or (isinstance(data, dict) and len(data) > 0)
        ), f"섹션 누락 또는 비어 있음: {name}"
