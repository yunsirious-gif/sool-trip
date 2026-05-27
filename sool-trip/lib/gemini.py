"""Gemini 기반 술여행 코스 추천."""

from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()


def _load_key() -> str:
    """env > st.secrets 순으로 키 조회. Streamlit Cloud secrets는 env로 안 들어옴."""
    v = os.getenv("GEMINI_API_KEY", "")
    if v:
        return v
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


API_KEY = _load_key()
_client = genai.Client(api_key=API_KEY) if API_KEY else None


# 모델 fallback — 한 모델 실패 시 자동으로 다음 모델 시도
# 실재하는 최신 모델만 (Gemini 3.x는 존재하지 않음)
MODELS_FALLBACK = [
    "gemini-flash-latest",      # 항상 최신 flash로 자동 갱신
    "gemini-2.5-flash",         # 현 최신 flash 고정 버전
    "gemini-flash-lite-latest", # 빠르고 저렴
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def _generate(prompt: str) -> str:
    """모델 fallback으로 응답을 받는다. 모두 실패하면 빈 문자열 + 마지막 에러 저장."""
    if not API_KEY:
        st.session_state["_last_curate_error"] = "GEMINI_API_KEY 미설정"
        return ""
    last_err = ""
    for model_name in MODELS_FALLBACK:
        try:
            resp = _client.models.generate_content(model=model_name, contents=prompt)
            text = resp.text or ""
            if text:
                return text
            last_err = f"{model_name}: 빈 응답"
            continue
        except Exception as e:
            msg = str(e)
            last_err = f"{model_name}: {msg[:200]}"
            # 인증 에러는 다른 모델 시도해도 똑같이 실패 → 즉시 중단
            if any(k in msg.lower() for k in (
                "api key", "permission_denied", "unauthenticated", "invalid_argument",
            )):
                break
            # 그 외 에러(404/모델 없음, 429/quota, 5xx 등)는 다음 모델 시도
            continue
    st.session_state["_last_curate_error"] = last_err
    return ""
def _format_brewery(b: dict) -> str:
    visit = "체험 가능" if b.get("visitable") else "방문 불가"
    return f"- {b['name']} ({b.get('sigungu','')}, {visit})"


def _format_spot(item: dict, kind: str) -> str:
    title = item.get("title", "")
    addr = item.get("addr1") or item.get("addr2") or ""
    return f"- [{kind}] {title} — {addr}"


def build_prompt(region_label: str, taste: str, duration: str,
                  breweries: list[dict], spots: list[dict], foods: list[dict],
                  festivals: list[dict]) -> str:
    lines = [
        f"당신은 한국 전통주와 지역 여행에 정통한 큐레이터입니다.",
        f"사용자가 '{region_label}' 지역에서 '{duration}' 일정으로 술여행을 가고 싶어합니다.",
        f"사용자 취향: {taste}",
        "",
        "아래 후보 중에서 적절히 선별하여, 시간 순서대로 코스를 짜주세요.",
        "각 단계마다 '왜 이걸 추천했는지' 한 줄로 설명하고,",
        "양조장에서는 어떤 술을 어떤 안주와 페어링하면 좋을지 한 줄 곁들여 주세요.",
        "마지막에 '한 줄 총평'으로 마무리하세요.",
        "",
        "## 후보 양조장",
    ]
    lines.extend(_format_brewery(b) for b in breweries[:10])
    lines.append("\n## 후보 관광지")
    lines.extend(_format_spot(s, "관광") for s in spots[:10])
    lines.append("\n## 후보 맛집")
    lines.extend(_format_spot(s, "맛집") for s in foods[:10])
    if festivals:
        lines.append("\n## 진행 중/예정 축제")
        lines.extend(_format_spot(s, "축제") for s in festivals[:5])
    return "\n".join(lines)


def generate_course(prompt: str, model_name: str = "gemini-2.5-flash-lite") -> str:
    if not API_KEY:
        return "⚠️ GEMINI_API_KEY가 설정되지 않았습니다."
    _g_text = _generate(prompt)
    return _g_text or "(빈 응답)"


def curate_destinations(season_ctx, themes: list, candidate_regions: list[dict],
                          top_n: int = 5, origins: list[str] | None = None,
                          restrict_sido: str = "") -> list[dict]:
    """계절 + 다중 테마 + 다중 출발지를 종합해 시군구 단위로 여행지를 큐레이션.

    Args:
        season_ctx: SeasonContext
        themes: Theme 리스트 (빈 리스트면 자동 계절 모드)
        candidate_regions: 후보 시군구 목록
        top_n: 추천 개수
        origins: 출발지 후보들 (이 중 가장 가까운 곳에서 출발 가능)
    """
    if not API_KEY:
        return []

    region_lines = []
    for r in candidate_regions[:130]:
        n_v = r.get("n_visitable", 0)
        region_lines.append(
            f"- {r['sido']} {r['sigungu']} (양조장 {r['n_breweries']}곳, 체험 가능 {n_v}곳)"
        )

    if origins:
        origin_clause = (f"여행 출발지 후보: {', '.join(origins)}. "
                          f"이 중 한 곳에서 출발하므로, 이 중 어느 한 곳에서라도 가까우면 가산점.\n")
    else:
        origin_clause = ""

    if themes:
        theme_label = " + ".join(t.label for t in themes)
        theme_desc = " / ".join(t.description for t in themes)
        theme_hint = "\n".join(f"- {t.label}: {t.hint_for_gemini}" for t in themes)
        theme_block = (f"사용자가 고른 테마(여러 개): {theme_label}\n"
                        f"테마 설명: {theme_desc}\n"
                        f"테마별 힌트:\n{theme_hint}\n"
                        "여러 테마가 모두 어느 정도 충족되는 곳을 우선시하세요.\n")
    else:
        theme_block = "테마 미지정 — 오늘 계절 분위기에 가장 잘 맞는 곳을 골라주세요.\n"

    if restrict_sido:
        restrict_clause = (f"⚠️ **반드시 지킬 것**: '{restrict_sido}' 시/도 **안의** 시/군/구만 골라주세요. "
                            f"'{restrict_sido}'가 아닌 다른 시/도는 **절대로** 추천하지 마세요.\n\n")
    else:
        restrict_clause = ""

    prompt = f"""당신은 한국 여행 큐레이터입니다.
오늘은 {season_ctx.today.isoformat()} ({season_ctx.season}, {season_ctx.month}월)입니다.
계절 분위기: {season_ctx.vibe}
계절 권역 힌트: {season_ctx.regions_hint}

{theme_block}
{origin_clause}{restrict_clause}'이번 계절·테마에 가장 잘 맞는 여행지' {top_n}곳을 골라주세요.
**여행지 매력을 최우선**으로 평가하세요. 양조장 유무는 중요하지 않습니다.
아래 후보 시/군/구는 참고용이며, 후보에 없는 시/군/구라도 더 좋다면 추천해도 됩니다.
(단, 실재하는 한국 행정구역명만 사용 — 시/도와 시/군/구가 정확히 일치해야 합니다.)

JSON 배열만 출력하세요. 다른 텍스트 금지.
형식:
[
  {{"sido":"전라남도","sigungu":"담양군","reason":"늦봄 죽녹원·메타세콰이어 길의 신록이 절정","highlights":"죽녹원, 메타세콰이어길, 죽순요리"}},
  ...
]

## 후보 시/군/구
{chr(10).join(region_lines)}
"""
    import streamlit as st
    try:
        _g_text = _generate(prompt)
        text = (_g_text or "").strip()
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            st.session_state["_last_curate_error"] = f"JSON 미발견: {text[:200]}"
            return []
        picks = json.loads(text[start:end + 1])
        if restrict_sido:
            # Gemini가 약식 표기(경북, 강원도, 경기 등)로 응답해도 정상 인식
            sido_alias = {
                "경기": "경기도",
                "강원": "강원특별자치도", "강원도": "강원특별자치도",
                "충북": "충청북도", "충남": "충청남도",
                "전북": "전북특별자치도", "전라북도": "전북특별자치도",
                "전남": "전라남도",
                "경북": "경상북도", "경남": "경상남도",
                "제주": "제주특별자치도", "제주도": "제주특별자치도",
                "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
                "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
                "울산": "울산광역시", "세종": "세종특별자치시",
            }
            normalized = []
            for p in picks:
                ps = p.get("sido", "")
                ps_n = sido_alias.get(ps, ps)
                if ps_n == restrict_sido:
                    p["sido"] = restrict_sido  # 정식 명칭으로 통일
                    normalized.append(p)
            if not normalized and picks:
                seen = ", ".join(set(p.get("sido", "?") for p in picks))
                st.session_state["_last_curate_error"] = (
                    f"Gemini가 '{restrict_sido}' 외 시/도({seen})만 출력해서 필터 후 0건."
                )
                return []
            picks = normalized
        return picks
    except Exception as e:
        st.session_state["_last_curate_error"] = f"{type(e).__name__}: {str(e)[:300]}"
        return []


def curate_seasonal_picks(season_ctx, breweries: list[dict], top_n: int = 5,
                            origin: str = "") -> str:
    """오늘 계절 + 후보 양조장 → '왜 이 계절에 어울리는지'와 함께 추천 N곳."""
    if not API_KEY:
        return "⚠️ GEMINI_API_KEY가 설정되지 않았습니다."

    candidate_lines = []
    for b in breweries[:60]:
        visit = "체험" if b.get("visitable") else "비체험"
        candidate_lines.append(
            f"- {b['name']} | {b.get('sido','')} {b.get('sigungu','')} | {visit}"
        )

    origin_clause = f"여행 출발지는 '{origin}'입니다. 너무 먼 곳은 후순위로 두세요.\n" if origin else ""

    prompt = f"""당신은 한국 전통주와 지역 여행 큐레이터입니다.
오늘은 {season_ctx.today.isoformat()} ({season_ctx.season}, {season_ctx.month}월)입니다.
이 계절의 분위기: {season_ctx.vibe}
이 계절에 어울리는 술 키워드: {', '.join(season_ctx.drinks)}
참고할 만한 지역 힌트: {season_ctx.regions_hint}

{origin_clause}아래 후보 양조장 중에서 '이번 계절 술여행지'로 가장 잘 맞는 곳 {top_n}곳을 골라주세요.
체험 가능한 곳을 우선 고려하고, 지역이 너무 한쪽으로 쏠리지 않게 다양화하세요.

각 추천은 다음 형식으로 작성:

### {top_n}개 추천

**1. [양조장명] — [시/도 시/군/구]**
- 왜 이 계절에 어울리는지 (1~2줄)
- 함께 즐기면 좋은 안주/풍경 (1줄)

마지막에 "💡 이번 계절 한 줄 총평"으로 마무리.

## 후보 양조장
{chr(10).join(candidate_lines)}
"""
    _g_text = _generate(prompt)
    return _g_text or "(빈 응답)"


def weather_aware_plan(brewery: dict, daily_weather: list, dates_label: str,
                         products: list[dict]) -> str:
    """양조장 + 일자별 날씨 → '어떻게 즐기면 좋을지' 가이드.

    날씨가 나쁘면 실내 시음/박물관/체험, 좋으면 야외 캠핑/풍경/별보기 등 조정.
    """
    if not API_KEY:
        return "⚠️ GEMINI_API_KEY가 설정되지 않았습니다."

    weather_lines = []
    for d in daily_weather:
        weather_lines.append(
            f"- {d.date}: {d.label} ({d.tmin:.0f}~{d.tmax:.0f}°C, "
            f"강수확률 {d.precip_prob}%, 강수량 {d.precip_mm:.1f}mm)"
        )

    product_lines = []
    for p in (products or [])[:6]:
        product_lines.append(
            f"- {p.get('product_name','?')} ({p.get('abv','?')}도): "
            f"{p.get('features') or (p.get('description','')[:60])}"
        )

    prompt = f"""당신은 한국 전통주와 지역여행에 정통한 큐레이터입니다.
사용자는 '{dates_label}' 기간에 아래 양조장을 중심으로 술여행을 갑니다.
일자별 날씨와 그 양조장에서 빚는 술 정보를 종합해서,
'각 날을 어떻게 즐기면 좋을지' 짧고 구체적으로 알려주세요.

특히 다음을 반영해 주세요:
- 비/궂은 날: 양조장 시음·체험·박물관·실내 식당 등 실내 위주
- 맑은 날: 야외 풍경·캠핑·별보기·산책 등 야외 활동
- 술 페어링은 그 양조장에서 실제로 빚는 술 이름을 인용
- 사용자가 영천 캠핑 예시처럼 비 오는 날 별 보기 같은 낭패를 피하도록

## 양조장
{brewery['name']} ({brewery.get('sido','')} {brewery.get('sigungu','')})

## 일자별 날씨
{chr(10).join(weather_lines)}

## 이 양조장의 술
{chr(10).join(product_lines) or '(데이터 없음)'}

출력 형식:

### 📋 여행 가이드

**기간 한 줄 요약**: (한 줄)

**Day 1 ({{날짜}}, {{날씨}})**:
- 추천 활동: (한두 줄)
- 추천 술 + 페어링: (한 줄)

**Day 2 ... (있으면 반복)**

**⚠️ 주의/대안**: 비 오는 날 야외 활동 대신 무엇으로? 등
"""
    _g_text = _generate(prompt)
    return _g_text or "(빈 응답)"


def local_drink_recommendation(sido: str, sigungu: str) -> str:
    """양조장이 없는 지역에서 즐길 수 있는 술 추천.

    그 지역의 시장·식당·바·축제 등에서 마실 만한 술이 있으면 추천.
    아예 없으면 빈 문자열.
    """
    if not API_KEY:
        return ""
    prompt = f"""당신은 한국 지역 술 큐레이터입니다.
'{sido} {sigungu}'에 양조장은 없거나 거의 없지만, 그 지역에서 여행자가 즐길 수 있는
**그 지역만의 술**(이웃 지역 양조장의 술이라도 그 지역과 강하게 연관되어 있는 것,
지역 시장·식당·축제에서 즐기는 향토주 등)을 알려주세요.

**중요 규칙**:
- 한국 어디서나 흔한 술(소주·맥주·청하 등 대중주)은 적지 마세요.
- 정말 그 지역과 연관성 있는 술만 적으세요. 억지로 만들지 마세요.
- 아무것도 없으면 정확히 "없음"이라고만 답하세요.

있으면 다음 형식으로 (간결하게, 2~3종 이내):
- **술 이름**: 어디서 마실 수 있고 어떤 매력이 있는지 (한두 줄)

없으면 정확히 다음만 출력:
없음
"""
    _g_text = _generate(prompt)
    text = (_g_text or "").strip()
    if not text:
        return ""
    last_line = text.split("\n")[-1].strip()
    if text == "없음" or last_line == "없음" or last_line.endswith("없음"):
        return ""
    return text


def regional_specialty(sido: str, sigungu: str) -> str:
    """그 지역의 특산품 + 향토 먹거리. 유명한 게 없으면 빈 문자열 반환.

    "없음" 응답을 받으면 억지로 끼워넣지 않는다.
    """
    if not API_KEY:
        return ""
    prompt = f"""당신은 한국 지역 미식 전문가입니다.
'{sido} {sigungu}'의 지역 특산품(농수산물·과일·임산물 등)과
그 특산품을 이용한 대표적인 향토 음식을 알려주세요.

**중요 규칙 — 반드시 지켜주세요**:
- 정말 그 지역에서 유명하고 특화된 것만 적으세요.
- 한국 어디서나 흔한 음식(예: 일반 삼겹살, 일반 비빔밥)은 적지 마세요.
- 그 지역만의 시그니처(예: 청도 미나리 삼겹살, 안동 간고등어, 영광 굴비, 횡성 한우)만 적으세요.
- 특별히 내세울 만한 게 없으면 정확히 "없음"이라고만 답하세요. 억지로 만들지 마세요.

특산품이 있으면 다음 형식으로:
**🌾 특산품**: ...
**🍴 꼭 먹어봐야 할 음식**: ...
**💡 한 줄 팁**: 어디서·어떻게 먹으면 좋은지 (1줄)

특산품이 없으면 정확히 다음만 출력:
없음
"""
    try:
        _g_text = _generate(prompt)
        text = (_g_text or "").strip()
    except Exception:
        return ""
    stripped = text.strip()
    if stripped == "없음":
        return ""
    last_line = stripped.split("\n")[-1].strip()
    if last_line == "없음" or last_line.endswith("없음"):
        return ""
    return text


def sort_drinks_recommended(drinks: list[dict]) -> list[dict]:
    """술 리스트를 '유명한·먹어봐야 할 순서'로 재정렬.

    Gemini가 인덱스 순서 배열을 반환. 실패 시 원본 그대로.
    """
    if not drinks or len(drinks) <= 1 or not API_KEY:
        return drinks

    lines = []
    for i, d in enumerate(drinks):
        feat = d.get("features") or (d.get("description", "")[:60])
        awards = d.get("awards") or ""
        lines.append(
            f"{i}. {d.get('product_name','?')} "
            f"({d.get('abv','?')}도, {d.get('brewery_name','')}) "
            f"— {feat} {('| 수상: ' + awards) if awards else ''}"
        )

    prompt = f"""당신은 한국 전통주 소믈리에입니다.
아래 술 목록을 '유명한 정도'와 '한 번은 꼭 마셔봐야 할 추천도'를 종합해서
다시 정렬해주세요. **대표·시그니처 술이 앞**, 그 다음 추천도 높은 것, 마지막에 일반.
수상 경력, 양조장의 인지도, 도수의 입문 적합도를 고려하세요.

JSON 배열로 인덱스만 출력하세요. 다른 텍스트·설명 금지.
예: [3, 0, 5, 1, 4, 2]
인덱스 누락·중복 없이 0부터 {len(drinks)-1}까지 정확히 모두 포함하세요.

## 술 목록
{chr(10).join(lines)}
"""
    try:
        _g_text = _generate(prompt)
        text = (_g_text or "").strip()
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return drinks
        order = json.loads(text[start:end + 1])
        seen = set()
        sorted_list = []
        for idx in order:
            if isinstance(idx, int) and 0 <= idx < len(drinks) and idx not in seen:
                sorted_list.append(drinks[idx])
                seen.add(idx)
        # 누락된 인덱스 뒤에 추가
        for i, d in enumerate(drinks):
            if i not in seen:
                sorted_list.append(d)
        return sorted_list
    except Exception:
        return drinks


def drink_experience_guide(brewery: dict, products: list[dict]) -> str:
    """양조장의 술 목록 → 어떤 순서로 무엇을 마셔야 하는지 가이드."""
    if not API_KEY:
        return "⚠️ GEMINI_API_KEY가 설정되지 않았습니다."
    if not products:
        return "이 양조장의 술 정보가 데이터에 없습니다."

    product_lines = []
    for p in products[:10]:
        product_lines.append(
            f"- {p['product_name']} ({p.get('abv','?')}도, {p.get('volume','?')}) — "
            f"{p.get('features') or p.get('description','')[:80]}"
        )

    prompt = f"""당신은 한국 전통주 소믈리에입니다.
사용자가 '{brewery['name']}' 양조장({brewery.get('sido','')} {brewery.get('sigungu','')})을
방문하려고 합니다. 아래 술 목록을 보고:

1. 초보자가 첫 잔으로 마셔보면 좋은 술
2. 중급자/매니아용 술
3. 함께 즐기면 좋은 안주 페어링 (최대 2가지)
4. 시음 순서 추천 (도수 낮은 것 → 높은 것 또는 단맛 흐름)

위 4가지를 짧고 명료하게(각 한두 줄) 알려주세요.
실제 술 이름을 그대로 인용해서 답하세요.

## 술 목록
{chr(10).join(product_lines)}
"""
    _g_text = _generate(prompt)
    return _g_text or "(빈 응답)"
