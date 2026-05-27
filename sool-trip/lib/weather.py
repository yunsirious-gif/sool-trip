"""Open-Meteo 일자별 예보 (무료, 키 불필요, 한국 16일까지)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import requests
import streamlit as st

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE = {
    0: ("☀️", "맑음"),
    1: ("🌤️", "대체로 맑음"),
    2: ("⛅", "부분적으로 흐림"),
    3: ("☁️", "흐림"),
    45: ("🌫️", "안개"), 48: ("🌫️", "짙은 안개"),
    51: ("🌦️", "가벼운 이슬비"), 53: ("🌦️", "이슬비"), 55: ("🌧️", "강한 이슬비"),
    61: ("🌧️", "약한 비"), 63: ("🌧️", "비"), 65: ("🌧️", "강한 비"),
    71: ("🌨️", "약한 눈"), 73: ("🌨️", "눈"), 75: ("❄️", "강한 눈"),
    77: ("🌨️", "싸락눈"),
    80: ("🌦️", "소나기"), 81: ("🌧️", "강한 소나기"), 82: ("⛈️", "폭우"),
    85: ("🌨️", "약한 눈 소나기"), 86: ("❄️", "강한 눈 소나기"),
    95: ("⛈️", "뇌우"), 96: ("⛈️", "우박 동반 뇌우"), 99: ("⛈️", "강한 우박 뇌우"),
}


@dataclass
class DailyWeather:
    date: str
    tmin: float
    tmax: float
    precip_mm: float
    precip_prob: int
    code: int

    @property
    def emoji(self) -> str:
        return WEATHER_CODE.get(self.code, ("❓", "알수없음"))[0]

    @property
    def label(self) -> str:
        return WEATHER_CODE.get(self.code, ("❓", "알수없음"))[1]

    @property
    def is_rainy(self) -> bool:
        return self.precip_mm >= 1.0 or self.precip_prob >= 60

    @property
    def is_outdoor_friendly(self) -> bool:
        return not self.is_rainy and self.code in {0, 1, 2}

    def one_line(self) -> str:
        return (f"{self.emoji} {self.label} · "
                f"{self.tmin:.0f}~{self.tmax:.0f}°C · "
                f"강수 {self.precip_prob}% ({self.precip_mm:.1f}mm)")


@st.cache_data(ttl=1800, show_spinner=False)
def forecast(lat: float, lon: float, start: date, end: date) -> list[DailyWeather]:
    """좌표 + 날짜 범위 → 일별 예보 리스트.

    Open-Meteo는 오늘부터 16일까지 지원. 과거/너무 먼 미래는 자동 클램프됨.
    빈 결과는 캐시하지 않음 (API 일시 장애로 인한 영구 공란 방지).
    """
    if start > end:
        start, end = end, start
    try:
        r = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": ("weather_code,temperature_2m_max,temperature_2m_min,"
                          "precipitation_sum,precipitation_probability_max"),
                "timezone": "Asia/Seoul",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
            timeout=8,
        )
        r.raise_for_status()
        data = r.json().get("daily", {}) or {}
    except Exception as e:
        # 빈 결과가 캐시에 박히지 않도록 예외 전파 (forecast_safe가 잡음)
        raise _NoCacheError(f"weather api failed: {e}") from e

    days = data.get("time", []) or []
    if not days:
        raise _NoCacheError("weather api returned empty")

    def _g(key: str) -> list:
        return data.get(key) or [None] * len(days)

    tmin_l, tmax_l = _g("temperature_2m_min"), _g("temperature_2m_max")
    pmm_l, pprob_l = _g("precipitation_sum"), _g("precipitation_probability_max")
    code_l = _g("weather_code")

    out = []
    for i, dt in enumerate(days):
        out.append(DailyWeather(
            date=dt,
            tmin=float(tmin_l[i] if tmin_l[i] is not None else 0),
            tmax=float(tmax_l[i] if tmax_l[i] is not None else 0),
            precip_mm=float(pmm_l[i] if pmm_l[i] is not None else 0),
            precip_prob=int(pprob_l[i] if pprob_l[i] is not None else 0),
            code=int(code_l[i] if code_l[i] is not None else 0),
        ))
    return out


class _NoCacheError(Exception):
    """forecast 빈 결과를 캐시하지 않게 하기 위한 마커 예외."""


def forecast_safe(lat: float, lon: float, start: date, end: date) -> list[DailyWeather]:
    """forecast 래퍼: 실패해도 호출부에는 빈 리스트로 돌려준다."""
    try:
        return forecast(lat, lon, start, end)
    except _NoCacheError:
        return []
    except Exception:
        return []


def summarize_period(days: list[DailyWeather]) -> str:
    """여행 기간 전체 한 줄 요약."""
    if not days:
        return "예보 데이터 없음"
    rainy = [d for d in days if d.is_rainy]
    if len(rainy) == len(days):
        return f"기간 내내 비/궂은 날씨 ({len(days)}일)"
    if not rainy:
        return f"기간 내내 야외 활동 좋음 ({len(days)}일)"
    rainy_dates = ", ".join(d.date[5:] for d in rainy)
    return f"{len(rainy)}/{len(days)}일 비 예보 — {rainy_dates}"
