"""이동 시간 추정 — 1단계 Gemini, 2단계 카카오 길찾기로 스왑 가능한 인터페이스.

추후 카카오 길찾기 키가 생기면 `estimate_travel`의 구현부만 갈아끼우면 된다.
페이지 코드는 시그니처에 의존하므로 변경 불필요.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from typing import Literal

import streamlit as st
from dotenv import load_dotenv

from lib.gemini import _generate

load_dotenv()
_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")


@dataclass
class TravelEstimate:
    origin: str
    destination: str
    minutes: int
    distance_km: float
    mode: Literal["driving", "transit"]
    source: Literal["gemini", "kakao"]
    note: str = ""

    @property
    def hours_label(self) -> str:
        h, m = divmod(self.minutes, 60)
        if h and m:
            return f"{h}시간 {m}분"
        if h:
            return f"{h}시간"
        return f"{m}분"


_PROMPT = """당신은 한국 지리·교통에 정통한 어시스턴트입니다.
다음 두 지점 사이를 '{mode_kor}'으로 이동할 때
예상 소요 시간(분)과 직선 가까운 도로 거리(km)를 추정해 주세요.
교통체증은 평일 한낮 기준으로 보수적으로 잡아 주세요.

출발: {origin}
도착: {destination}

반드시 다음 JSON 한 줄만 출력하세요. 다른 텍스트 금지:
{{"minutes": <정수>, "distance_km": <소수1자리>, "note": "<한 줄 코멘트>"}}
"""


@st.cache_data(ttl=3600, show_spinner=False)
def estimate_travel(origin: str, destination: str,
                     mode: Literal["driving", "transit"] = "driving") -> TravelEstimate:
    """Gemini로 이동 시간 추정 (1단계). 카카오 스왑 시 이 함수만 교체."""
    if not _GEMINI_KEY:
        return TravelEstimate(origin, destination, 0, 0.0, mode, "gemini",
                              note="GEMINI_API_KEY 미설정")
    mode_kor = "자동차" if mode == "driving" else "대중교통"
    prompt = _PROMPT.format(mode_kor=mode_kor, origin=origin, destination=destination)
    try:
        text = (_generate(prompt) or "").strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"JSON 미발견: {text[:120]}")
        payload = json.loads(text[start:end + 1])
        return TravelEstimate(
            origin=origin,
            destination=destination,
            minutes=int(payload["minutes"]),
            distance_km=float(payload["distance_km"]),
            mode=mode,
            source="gemini",
            note=payload.get("note", "") or "Gemini 추정 (±20%)",
        )
    except Exception as e:
        return TravelEstimate(origin, destination, 0, 0.0, mode, "gemini",
                              note=f"추정 실패: {e}")


def to_dict(est: TravelEstimate) -> dict:
    return asdict(est)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 사이 지구 표면 거리(km). 직선거리 — 실제 도로거리보다 짧음."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def quick_drive_estimate(distance_km: float) -> int:
    """직선거리로부터 자동차 소요분 거친 추정 — Gemini 호출 없이.

    도로 거리는 직선의 약 1.3배, 평균 시속 60km/h로 보수적으로 잡음.
    """
    road_km = distance_km * 1.3
    return int(road_km / 60 * 60)  # km / (km/h) * 60min
