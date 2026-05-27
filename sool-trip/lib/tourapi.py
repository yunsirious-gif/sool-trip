"""한국관광공사 TourAPI 4.0 클라이언트 (areaBasedList2).

콘텐츠 타입:
  12 관광지 · 14 문화시설 · 15 축제/행사 · 28 레포츠 · 39 음식점
"""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"


def _load_key() -> str:
    """env > st.secrets 순으로 키 조회. Streamlit Cloud는 secrets가 env로 안 들어옴."""
    v = os.getenv("PUBLIC_DATA_API_KEY", "")
    if v:
        return v
    try:
        return st.secrets.get("PUBLIC_DATA_API_KEY", "")
    except Exception:
        return ""


API_KEY = _load_key()

CONTENT_TYPES = {
    "관광지": 12,
    "문화시설": 14,
    "축제": 15,
    "레포츠": 28,
    "맛집": 39,
}


class TourAPIError(RuntimeError):
    pass


def _request(endpoint: str, params: dict[str, Any]) -> list[dict]:
    if not API_KEY:
        raise TourAPIError("PUBLIC_DATA_API_KEY가 설정되지 않았습니다.")
    full_params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "SoolTrip",
        "_type": "json",
        "numOfRows": 30,
        "pageNo": 1,
        **params,
    }
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=full_params, timeout=2.5)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise TourAPIError(f"TourAPI 호출 실패: {e}") from e
    except ValueError as e:
        raise TourAPIError(f"TourAPI 응답 파싱 실패 (XML 에러일 수 있음): {e}") from e

    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "0000":
        msg = header.get("resultMsg", "unknown")
        raise TourAPIError(f"TourAPI 에러: {msg}")

    body = data.get("response", {}).get("body", {})
    items = body.get("items")
    if not items:
        return []
    item_list = items.get("item", [])
    return item_list if isinstance(item_list, list) else [item_list]


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_by_area(area_code: int, content_type: int, rows: int = 30) -> list[dict]:
    """지역 + 콘텐츠 타입으로 목록 조회."""
    return _request("areaBasedList2", {
        "areaCode": area_code,
        "contentTypeId": content_type,
        "arrange": "Q",
        "numOfRows": rows,
    })


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_festivals(area_code: int, year_month: str = "") -> list[dict]:
    """진행중/예정 축제. year_month: YYYYMMDD 형식."""
    params = {"areaCode": area_code, "arrange": "R", "numOfRows": 30}
    if year_month:
        params["eventStartDate"] = year_month
    return _request("searchFestival2", params)
