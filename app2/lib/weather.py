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


@st.cache_resource(ttl=3600, show_spinner=False)
def forecast(lat: float, lon: float, start: date, end: date) -> list[DailyWeather]:
    """좌표 + 날짜 범위 → 일별 예보 리스트.

    Open-Meteo는 오늘부터 16일까지 지원. 과거/너무 먼 미래는 자동 클램프됨.
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
        data = r.json().get("daily", {})
    except Exception:
        return []

    days = data.get("time", [])
    out = []
    for i, dt in enumerate(days):
        out.append(DailyWeather(
            date=dt,
            tmin=float(data["temperature_2m_min"][i] or 0),
            tmax=float(data["temperature_2m_max"][i] or 0),
            precip_mm=float(data["precipitation_sum"][i] or 0),
            precip_prob=int(data["precipitation_probability_max"][i] or 0),
            code=int(data["weather_code"][i] or 0),
        ))
    return out


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
