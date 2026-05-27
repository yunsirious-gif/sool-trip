"""주소/지역명 → 좌표 변환. Nominatim(OpenStreetMap) + SQLite 캐시.

Nominatim 정책: 최대 1 req/sec, User-Agent 필수. 캐시로 재호출을 최소화한다.
"""

from __future__ import annotations

import time
from typing import Optional

import requests
import streamlit as st

from lib.db import get_conn

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "sool-trip-app/0.1 (https://example.local)"
_last_call_ts = 0.0


def _ensure_cache_table() -> None:
    get_conn().execute("""
        CREATE TABLE IF NOT EXISTS geocache (
            query TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            ts INTEGER
        )
    """)


def _cache_get(query: str) -> tuple[float, float] | None:
    _ensure_cache_table()
    row = get_conn().execute(
        "SELECT lat, lon FROM geocache WHERE query = ?", (query,)
    ).fetchone()
    if row and row["lat"] is not None:
        return float(row["lat"]), float(row["lon"])
    return None


def _cache_put(query: str, latlon: tuple[float, float] | None) -> None:
    lat, lon = latlon if latlon else (None, None)
    get_conn().execute(
        "INSERT OR REPLACE INTO geocache(query, lat, lon, ts) VALUES (?, ?, ?, strftime('%s','now'))",
        (query, lat, lon),
    )
    get_conn().commit()


def _throttle() -> None:
    global _last_call_ts
    elapsed = time.time() - _last_call_ts
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_call_ts = time.time()


def geocode(query: str) -> tuple[float, float] | None:
    """주소/지역명을 좌표로. 캐시 우선, 미스시 Nominatim 호출 + 캐시."""
    query = query.strip()
    if not query:
        return None
    cached = _cache_get(query)
    if cached is not None:
        return cached

    _throttle()
    try:
        r = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1,
                    "countrycodes": "kr", "accept-language": "ko"},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        _cache_put(query, None)
        return None

    if not data:
        _cache_put(query, None)
        return None
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    _cache_put(query, (lat, lon))
    return lat, lon


@st.cache_data(ttl=86400, show_spinner=False)
def geocode_sigungu(sido: str, sigungu: str) -> tuple[float, float] | None:
    """시/도 + 시/군/구 조합으로 좌표 조회 (Streamlit 캐시 + DB 캐시 2중)."""
    if not sigungu:
        return geocode(sido)
    return geocode(f"{sigungu} {sido}")
