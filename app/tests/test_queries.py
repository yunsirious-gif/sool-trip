"""SQL 질의 단위 테스트 — VALIDATION.md Targeted Check 대응."""

import pandas as pd

from lib import queries


def test_db_total_complex_count():
    """PRD §5: 부산 16개 자치구 단지 4,278개 검색 가능."""
    from lib.db import get_conn
    n = get_conn().execute("SELECT COUNT(*) FROM apt_complex").fetchone()[0]
    assert n == 4278, f"expected 4278 complexes, got {n}"


def test_search_complex_empty():
    df = queries.search_complex.__wrapped__("")
    assert df.empty


def test_search_complex_엘시티():
    df = queries.search_complex.__wrapped__("엘시티")
    assert not df.empty
    assert any("엘시티" in n for n in df["apt_name"])


def test_complex_info_엘시티():
    info = queries.complex_info.__wrapped__("엘시티")
    assert info is not None
    assert info["gu_name"] == "해운대구"
    assert info["trade_count"] > 0


def test_trade_history_returns_df_with_price_eok():
    df = queries.trade_history.__wrapped__("엘시티")
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "price_eok" in df.columns
        assert (df["price_eok"] > 0).all()


def test_rent_history_jeonse_flag():
    df = queries.rent_history.__wrapped__("엘시티")
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "is_jeonse" in df.columns


def test_gu_ranking_top10():
    df = queries.gu_ranking.__wrapped__("해운대구", limit=10)
    assert len(df) <= 10
    assert (df["trade_count"].diff().dropna() <= 0).all(), "must be sorted DESC"


def test_gu_infra_has_seven_categories():
    infra = queries.gu_infra.__wrapped__("해운대구")
    expected = {"초등학교", "중학교", "고등학교", "병원·의원", "약국", "학원", "입시 강좌"}
    assert set(infra.keys()) == expected
    assert all(v >= 0 for v in infra.values())


def test_gu_population_60_months():
    df = queries.gu_population.__wrapped__("해운대구")
    assert len(df) == 60, f"expected 60 months, got {len(df)}"
    assert df["total_pop"].iloc[-1] > 0


def test_db_is_read_only():
    """RECOVERY.md: bptc_realestate.db는 INSERT/UPDATE/DELETE 금지."""
    import sqlite3
    from lib.db import get_conn
    with __import__("pytest").raises(sqlite3.OperationalError):
        get_conn().execute("INSERT INTO apt_complex(apt_name) VALUES ('테스트')")
