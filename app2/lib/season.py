"""오늘 날짜로 계절·월별 컨텍스트 생성."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

SEASON_BY_MONTH = {
    3: "초봄", 4: "봄", 5: "늦봄",
    6: "초여름", 7: "한여름", 8: "늦여름",
    9: "초가을", 10: "가을", 11: "늦가을",
    12: "초겨울", 1: "한겨울", 2: "늦겨울",
}

SEASON_MOOD = {
    "초봄": {
        "drinks": ["꽃잎주", "이화주", "햇막걸리"],
        "vibe": "꽃놀이, 봄나물, 가벼운 산책",
        "regions_hint": "남도(전남) 꽃축제, 경기 양조장 봄나들이",
    },
    "봄": {
        "drinks": ["청주", "막걸리", "벚꽃주"],
        "vibe": "벚꽃, 들꽃, 한낮 피크닉",
        "regions_hint": "경주, 진해, 화개장터 일대",
    },
    "늦봄": {
        "drinks": ["청주", "약주", "쌀막걸리"],
        "vibe": "신록, 야외 테라스, 가벼운 트레킹",
        "regions_hint": "경기 북부 양조장 투어, 강원 평창·홍천, 충청 산촌",
    },
    "초여름": {
        "drinks": ["동동주", "탁주", "차가운 청주"],
        "vibe": "계곡, 펜션, 농촌 체험",
        "regions_hint": "강원 영월·정선, 충북 단양, 전북 무주",
    },
    "한여름": {
        "drinks": ["탄산막걸리", "동동주", "온더록 청주"],
        "vibe": "바다, 계곡, 시원한 안주",
        "regions_hint": "동해안(강릉·속초), 거제·통영, 제주",
    },
    "늦여름": {
        "drinks": ["과실주", "동동주", "유자/매실주"],
        "vibe": "휴양, 여름 끝자락 캠핑",
        "regions_hint": "지리산 자락, 남해, 영덕",
    },
    "초가을": {
        "drinks": ["햅쌀막걸리", "맑은 청주", "햇과실주"],
        "vibe": "추수, 단풍 시작, 시골 풍경",
        "regions_hint": "경북 안동·예천, 충남 공주·부여, 강원 평창",
    },
    "가을": {
        "drinks": ["청주", "약주", "오미자주"],
        "vibe": "단풍, 사찰, 가을 미식",
        "regions_hint": "전남 담양·순천, 충북 단양·제천, 경북 봉화",
    },
    "늦가을": {
        "drinks": ["진하게 빚은 약주", "도라지/인삼주", "묵은 청주"],
        "vibe": "온천, 늦단풍, 따뜻한 안주",
        "regions_hint": "충남 아산 온천, 강원 횡성, 경북 청송",
    },
    "초겨울": {
        "drinks": ["따뜻하게 데운 청주", "약주", "전통 소주"],
        "vibe": "온천, 첫눈, 실내 풍경",
        "regions_hint": "강원 평창·정선, 전북 무주, 충북 단양",
    },
    "한겨울": {
        "drinks": ["데운 정종", "안동소주", "고도주"],
        "vibe": "스키, 온천, 실내 양조장 체험",
        "regions_hint": "강원 스키권, 경북 안동, 제주 동백",
    },
    "늦겨울": {
        "drinks": ["고도주", "약주", "전통 소주"],
        "vibe": "겨울 끝자락, 실내 시음",
        "regions_hint": "수도권 양조장 체험, 안동 소주마을",
    },
}


@dataclass
class SeasonContext:
    today: date
    season: str
    month: int
    drinks: list[str]
    vibe: str
    regions_hint: str

    def summary(self) -> str:
        return (
            f"{self.today.isoformat()} ({self.season}, {self.month}월) — "
            f"분위기: {self.vibe}. 어울리는 술: {', '.join(self.drinks)}."
        )


def current_context(today: date | None = None) -> SeasonContext:
    today = today or date.today()
    season = SEASON_BY_MONTH[today.month]
    mood = SEASON_MOOD[season]
    return SeasonContext(
        today=today,
        season=season,
        month=today.month,
        drinks=mood["drinks"],
        vibe=mood["vibe"],
        regions_hint=mood["regions_hint"],
    )
