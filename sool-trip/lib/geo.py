"""시/도 · 시/군/구 옵션 + TourAPI 지역코드 매핑."""

from __future__ import annotations

import streamlit as st

from lib.db import get_conn

TOURAPI_AREA_CODE = {
    "서울특별시": 1,
    "인천광역시": 2,
    "대전광역시": 3,
    "대구광역시": 4,
    "광주광역시": 5,
    "부산광역시": 6,
    "울산광역시": 7,
    "세종특별자치시": 8,
    "경기도": 31,
    "강원특별자치도": 32,
    "충청북도": 33,
    "충청남도": 34,
    "경상북도": 35,
    "경상남도": 36,
    "전북특별자치도": 37,
    "전라남도": 38,
    "제주특별자치도": 39,
}


@st.cache_data(ttl=3600)
def list_sido() -> list[str]:
    rows = get_conn().execute(
        "SELECT sido, COUNT(*) AS n FROM breweries WHERE sido != '' "
        "GROUP BY sido ORDER BY n DESC"
    ).fetchall()
    return [r["sido"] for r in rows]


@st.cache_data(ttl=3600)
def list_sigungu(sido: str) -> list[str]:
    rows = get_conn().execute(
        "SELECT DISTINCT sigungu FROM breweries WHERE sido = ? AND sigungu != '' "
        "ORDER BY sigungu",
        (sido,),
    ).fetchall()
    return [r["sigungu"] for r in rows]
