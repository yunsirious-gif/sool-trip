"""주소/지역명 → 좌표 변환.

조회 우선순위:
  1. data/sigungu_coords.json (git에 commit된 정적 매핑 — 즉시)
  2. SQLite geocache (런타임 캐시)
  3. Nominatim (OpenStreetMap, 1 req/sec)

Streamlit Cloud는 재배포마다 컨테이너가 새로 떠서 SQLite가 초기화되므로
정적 JSON이 1순위로 와야 한다.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Optional

import requests
import streamlit as st

from lib.db import get_conn

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "sool-trip-app/0.1 (https://example.local)"
_STATIC_PATH = Path(__file__).resolve().parent.parent / "data" / "sigungu_coords.json"

_throttle_lock = threading.Lock()
_last_call_ts = 0.0


def _load_static() -> dict[str, tuple[float, float]]:
    if not _STATIC_PATH.exists():
        return {}
    try:
        raw = json.loads(_STATIC_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, tuple[float, float]] = {}
    for k, v in raw.items():
        if isinstance(v, list) and len(v) == 2 and v[0] is not None:
            out[k] = (float(v[0]), float(v[1]))
    return out


_STATIC: dict[str, tuple[float, float]] = _load_static()


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
    """Nominatim 1 req/sec 정책 준수. 멀티스레드 안전."""
    global _last_call_ts
    with _throttle_lock:
        elapsed = time.time() - _last_call_ts
        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)
        _last_call_ts = time.time()


def geocode(query: str) -> tuple[float, float] | None:
    """주소/지역명을 좌표로. 정적 JSON → DB 캐시 → Nominatim 순."""
    query = query.strip()
    if not query:
        return None

    if query in _STATIC:
        return _STATIC[query]

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
    """시/도 + 시/군/구 조합으로 좌표 조회 (정적 JSON + Streamlit 캐시 + DB 캐시 3중)."""
    if not sigungu:
        return geocode(sido)
    return geocode(f"{sigungu} {sido}")
