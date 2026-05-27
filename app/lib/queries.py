"""apt_complex / apt_trade / apt_rent / schools / medical / pharmacy / academies / population_gu 조회."""

import pandas as pd
import streamlit as st

from lib.db import get_conn


@st.cache_data(ttl=3600, show_spinner=False)
def search_complex(query: str, limit: int = 20) -> pd.DataFrame:
    if not query or not query.strip():
        return pd.DataFrame(columns=["apt_name", "gu_name", "road_name", "build_year", "trade_count"])
    pattern = f"%{query.strip()}%"
    sql = """
        SELECT apt_name, gu_name, road_name, build_year, trade_count
        FROM apt_complex
        WHERE apt_name LIKE ?
        ORDER BY trade_count DESC
        LIMIT ?
    """
    return pd.read_sql_query(sql, get_conn(), params=(pattern, limit))


@st.cache_data(ttl=3600, show_spinner=False)
def complex_info(apt_name: str) -> dict | None:
    sql = """
        SELECT apt_name, gu_name, road_name, build_year, min_area, max_area, trade_count
        FROM apt_complex
        WHERE apt_name = ?
        LIMIT 1
    """
    row = get_conn().execute(sql, (apt_name,)).fetchone()
    return dict(row) if row else None


@st.cache_data(ttl=3600, show_spinner=False)
def trade_history(apt_name: str) -> pd.DataFrame:
    sql = """
        SELECT deal_date, dealAmount, excluUseAr, floor, buildYear
        FROM apt_trade
        WHERE aptNm = ? AND deal_date IS NOT NULL
        ORDER BY deal_date
    """
    df = pd.read_sql_query(sql, get_conn(), params=(apt_name,))
    if not df.empty:
        df["deal_date"] = pd.to_datetime(df["deal_date"], errors="coerce")
        df["price_eok"] = df["dealAmount"] / 10000.0
        df["area_pyeong"] = (df["excluUseAr"] / 3.3058).round(1)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def rent_history(apt_name: str) -> pd.DataFrame:
    sql = """
        SELECT deal_date, deposit, monthlyRent, excluUseAr
        FROM apt_rent
        WHERE aptNm = ? AND deal_date IS NOT NULL
        ORDER BY deal_date
    """
    df = pd.read_sql_query(sql, get_conn(), params=(apt_name,))
    if not df.empty:
        df["deal_date"] = pd.to_datetime(df["deal_date"], errors="coerce")
        df["deposit_eok"] = df["deposit"] / 10000.0
        df["is_jeonse"] = df["monthlyRent"] == 0
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def gu_ranking(gu_name: str, limit: int = 10) -> pd.DataFrame:
    sql = """
        SELECT apt_name, trade_count, build_year
        FROM apt_complex
        WHERE gu_name = ?
        ORDER BY trade_count DESC
        LIMIT ?
    """
    return pd.read_sql_query(sql, get_conn(), params=(gu_name, limit))


@st.cache_data(ttl=3600, show_spinner=False)
def gu_infra(gu_name: str) -> dict:
    conn = get_conn()
    counts = {}
    for label, sql in [
        ("초등학교", "SELECT COUNT(*) FROM schools WHERE gu_name=? AND school_type='초등학교'"),
        ("중학교", "SELECT COUNT(*) FROM schools WHERE gu_name=? AND school_type='중학교'"),
        ("고등학교", "SELECT COUNT(*) FROM schools WHERE gu_name=? AND school_type='고등학교'"),
        ("병원·의원", "SELECT COUNT(*) FROM medical WHERE gu_name=?"),
        ("약국", "SELECT COUNT(*) FROM pharmacy WHERE gu_name=?"),
        ("학원", "SELECT COUNT(*) FROM academies WHERE gu_name=?"),
    ]:
        counts[label] = conn.execute(sql, (gu_name,)).fetchone()[0]
    ipsi = conn.execute(
        "SELECT COALESCE(SUM(ipsi_count),0) FROM academies WHERE gu_name=?", (gu_name,)
    ).fetchone()[0]
    counts["입시 강좌"] = int(ipsi)
    return counts


@st.cache_data(ttl=3600, show_spinner=False)
def gu_population(gu_name: str) -> pd.DataFrame:
    sql = """
        SELECT ref_date, total_pop, households
        FROM population_gu
        WHERE gu_name = ?
        ORDER BY ref_date
    """
    df = pd.read_sql_query(sql, get_conn(), params=(gu_name,))
    if not df.empty:
        df["ref_date"] = pd.to_datetime(df["ref_date"], errors="coerce")
    return df
