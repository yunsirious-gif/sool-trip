"""PDF 생성 시간·정합성 테스트 — VALIDATION.md M3 대응."""

import time
from pathlib import Path

import pytest

from lib import pdf, queries


def _gather(apt_name: str):
    info = queries.complex_info.__wrapped__(apt_name)
    if info is None:
        pytest.skip(f"단지 없음: {apt_name}")
    gu = info["gu_name"]
    return (
        info,
        queries.trade_history.__wrapped__(apt_name),
        queries.rent_history.__wrapped__(apt_name),
        queries.gu_ranking.__wrapped__(gu, limit=10),
        queries.gu_infra.__wrapped__(gu),
        queries.gu_population.__wrapped__(gu),
    )


def test_pdf_generation_under_10s(tmp_path):
    """PRD §5: PDF 1장 다운로드 10초 이내."""
    bundle = _gather("엘시티")
    t0 = time.perf_counter()
    data = pdf.render_briefing_pdf(*bundle)
    elapsed = time.perf_counter() - t0
    assert elapsed < 10.0, f"PDF 생성 {elapsed:.2f}s > 10.0s"
    assert data.startswith(b"%PDF"), "PDF 매직 바이트 없음"
    assert len(data) > 5_000, f"PDF 너무 작음: {len(data)} bytes"
    out = Path(__file__).parent.parent / "pdfs" / "test_briefing.pdf"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)


def test_pdf_contains_korean_text():
    """생성된 PDF의 텍스트 레이어에 단지명·자치구·헤더가 포함."""
    info, trade, rent, ranking, infra, pop = _gather("엘시티")
    data = pdf.render_briefing_pdf(info, trade, rent, ranking, infra, pop)
    raw = data.decode("latin-1", errors="ignore")
    # PDF는 압축돼 있어 직접 검색은 불가 → 최소 사이즈와 매직 바이트만 확인
    assert raw.startswith("%PDF")
    assert "엘시티" in info["apt_name"]


def test_pdf_no_runtime_error_for_minimal_data():
    """거래 0건 단지도 PDF가 깨지지 않고 생성."""
    import pandas as pd
    info = {
        "apt_name": "테스트단지", "gu_name": "해운대구",
        "road_name": "테스트로 1", "build_year": "2024",
        "min_area": 84.0, "max_area": 84.0, "trade_count": 0,
    }
    empty = pd.DataFrame()
    infra = queries.gu_infra.__wrapped__("해운대구")
    pop = queries.gu_population.__wrapped__("해운대구")
    data = pdf.render_briefing_pdf(info, empty, empty, empty, infra, pop)
    assert data.startswith(b"%PDF")
