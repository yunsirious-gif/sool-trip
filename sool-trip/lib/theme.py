"""여행 테마 옵션."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Theme:
    key: str
    label: str
    emoji: str
    description: str
    hint_for_gemini: str


THEMES: list[Theme] = [
    Theme(
        key="healing",
        label="힐링",
        emoji="🌅",
        description="자연·온천·한적한 숙소, 천천히 쉬고 싶을 때",
        hint_for_gemini="자연 풍경이 좋고 한적하며 온천/숙박이 잘 갖춰진 지역. 큰 도시는 피하고 산촌·바닷가 마을·전원형 지역 우선.",
    ),
    Theme(
        key="activity",
        label="액티비티",
        emoji="🏔️",
        description="등산·캠핑·레포츠·별보기 등 야외 활동 중심",
        hint_for_gemini="국립공원·캠핑장·트레킹 코스·별보기 좋은 청정 지역. 야외 활동이 가능한 곳 위주.",
    ),
    Theme(
        key="culture",
        label="문화·역사",
        emoji="🏛️",
        description="한옥·사찰·박물관·전통 마을, 차분한 문화 탐방",
        hint_for_gemini="한옥마을·고도·사찰·박물관 등 역사 자원이 풍부한 지역. 안동·경주·전주·강릉 등.",
    ),
    Theme(
        key="coast",
        label="바다·섬",
        emoji="🌊",
        description="해안 드라이브·해변·항구도시·섬",
        hint_for_gemini="해안선 또는 섬 지역. 동해·남해·서해의 해안 도시·어촌·관광 섬.",
    ),
    Theme(
        key="food",
        label="미식",
        emoji="🍜",
        description="지역 향토음식·시장·맛집 투어",
        hint_for_gemini="향토음식이나 시장·맛집이 유명한 지역. 전주·통영·여수·부산 등.",
    ),
    Theme(
        key="festival",
        label="축제·이벤트",
        emoji="🎉",
        description="시즌 축제·꽃·단풍 등 시기 한정 이벤트",
        hint_for_gemini="이 시즌에 진행되는 축제·꽃·단풍·눈축제 등 시기 한정 콘텐츠가 있는 지역.",
    ),
]


def by_key(key: str) -> Theme | None:
    for t in THEMES:
        if t.key == key:
            return t
    return None
