"""양조장 · 술 조회 쿼리."""

from __future__ import annotations

import streamlit as st

from lib.db import get_conn


@st.cache_data(ttl=600)
def find_breweries(sido: str, sigungu: str | None = None,
                   visitable_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM breweries WHERE sido = ?"
    params: list = [sido]
    if sigungu:
        sql += " AND sigungu = ?"
        params.append(sigungu)
    if visitable_only:
        sql += " AND visitable = 1"
    sql += " ORDER BY visitable DESC, views DESC"
    rows = get_conn().execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=600)
def get_brewery_products(brewery_id: int) -> list[dict]:
    rows = get_conn().execute(
        "SELECT * FROM products WHERE brewery_id = ? ORDER BY abv",
        (brewery_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=600)
def find_regional_products(sido: str, sigungu: str | None = None,
                            keyword: str = "") -> list[dict]:
    """그 지역 양조장에서 빚는 술 전부 — '지역 한정주' 의미.

    products.brewery_id ↔ breweries.id JOIN으로 양조장 위치 기반 필터.
    """
    sql = """
        SELECT p.*, b.name AS brewery_name, b.sigungu, b.visitable
        FROM products p
        JOIN breweries b ON p.brewery_id = b.id
        WHERE b.sido = ?
    """
    params: list = [sido]
    if sigungu:
        sql += " AND b.sigungu = ?"
        params.append(sigungu)
    if keyword:
        sql += (" AND (p.product_name LIKE ? OR p.features LIKE ? "
                "OR p.description LIKE ? OR p.ingredients LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw, kw])
    sql += " ORDER BY b.visitable DESC, p.abv"
    rows = get_conn().execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=600)
def count_regional_products(sido: str, sigungu: str | None = None) -> int:
    sql = ("SELECT COUNT(*) FROM products p JOIN breweries b ON p.brewery_id=b.id "
           "WHERE b.sido = ?")
    params: list = [sido]
    if sigungu:
        sql += " AND b.sigungu = ?"
        params.append(sigungu)
    return get_conn().execute(sql, params).fetchone()[0]
