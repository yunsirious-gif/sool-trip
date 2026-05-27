"""여행 — 단계별 인터뷰 UX 메인 페이지."""

from __future__ import annotations

import base64
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from lib.auth import gate
from lib.brewery import (find_breweries, find_regional_products,
                          get_brewery_products)
from lib.db import get_conn
from lib.gemini import (build_prompt, curate_destinations, generate_course,
                          local_drink_recommendation, regional_specialty,
                          sort_drinks_recommended, weather_aware_plan)
from lib.geo import TOURAPI_AREA_CODE, list_sido, list_sigungu
from lib.geocoding import geocode, geocode_sigungu
from lib.season import current_context
from lib.theme import THEMES, Theme
from lib.tourapi import CONTENT_TYPES, TourAPIError, fetch_by_area, fetch_festivals
from lib.travel import haversine_km, quick_drive_estimate
from lib.weather import forecast_safe, summarize_period

st.set_page_config(
    page_title="여행",
    page_icon="🍶",
    layout="wide",
    initial_sidebar_state="expanded",
)

gate()

st.markdown(
    "<style>[data-testid='stSidebarNav']{display:none;}</style>",
    unsafe_allow_html=True,
)

ctx = current_context()
today = date.today()
max_date = today + timedelta(days=15)
step = st.session_state.get("step", 0)


# ─── Hero 이미지 + 반딧불 + 텍스트 렌더 ─────────────────
HERO_IMG = Path(__file__).parent / "static" / "hero_bg.png"
if HERO_IMG.exists():
    _img_b64 = base64.b64encode(HERO_IMG.read_bytes()).decode()
    _bg_css = f"url(data:image/png;base64,{_img_b64}) center/cover"
else:
    _bg_css = "linear-gradient(180deg, #2a1a4f 0%, #6b3a4f 55%, #d97a4a 100%)"


def apply_hero_page_bg() -> None:
    """페이지 전체에 hero 이미지 배경 + 반딧불 띄움. step 0~3에서 호출."""
    fireflies = "".join(f'<div class="firefly f{i}"></div>' for i in range(1, 13))
    st.markdown(
        f"""
<style>
.stApp {{
    background: {_bg_css};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.stApp::before {{
    content: "";
    position: fixed; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.55) 100%);
    pointer-events: none;
    z-index: 0;
}}
/* 위젯과 텍스트는 배경 위로 */
[data-testid="stMainBlockContainer"] {{ position: relative; z-index: 1; }}

/* 사이드바는 hero 배경 위로 띄우고, 메뉴 보이게 흰 배경 */
[data-testid="stSidebar"] {{
    z-index: 999 !important;
    background-color: rgba(255, 255, 255, 0.96) !important;
    backdrop-filter: blur(4px);
}}
[data-testid="stSidebar"] * {{
    color: #2a2218 !important;
    text-shadow: none !important;
}}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{
    z-index: 1000 !important;
    background: rgba(255,255,255,0.95) !important;
    border-radius: 8px !important;
    padding: 6px 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {{
    color: #2a2218 !important;
    fill: #2a2218 !important;
}}

/* 모든 텍스트 흰색 + 그림자 */
.stApp [data-testid="stMainBlockContainer"] h1,
.stApp [data-testid="stMainBlockContainer"] h2,
.stApp [data-testid="stMainBlockContainer"] h3,
.stApp [data-testid="stMainBlockContainer"] h4,
.stApp [data-testid="stMainBlockContainer"] h5,
.stApp [data-testid="stMainBlockContainer"] p,
.stApp [data-testid="stMainBlockContainer"] label,
.stApp [data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] p {{
    color: #fff !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.8);
}}
/* 입력 위젯은 반투명 흰 배경으로 가독성 유지 */
.stApp [data-baseweb="input"], .stApp [data-baseweb="select"],
.stApp [data-baseweb="textarea"] {{
    background-color: rgba(255,255,255,0.93) !important;
    border-radius: 8px;
}}
.stApp [data-baseweb="input"] input,
.stApp [data-baseweb="select"] *,
.stApp [data-baseweb="textarea"] textarea {{
    color: #2a2218 !important;
    text-shadow: none !important;
}}
.stApp .stDateInput input {{ color: #2a2218 !important; text-shadow: none !important; }}

/* 페이지 인사 카피 (반투명 박스로 가독성) */
.intro-title, .step-title {{
    color: #fff;
    font-weight: 700;
    text-align: center;
    line-height: 1.3;
    margin: 6vh auto .8rem auto;
    max-width: 720px;
    padding: .5rem 1.2rem;
    background: rgba(0,0,0,0.35);
    backdrop-filter: blur(3px);
    border-radius: 12px;
    text-shadow: 0 2px 12px rgba(0,0,0,0.85);
}}
.intro-title {{ font-size: clamp(1.5rem, 3vw, 2.2rem); }}
.step-title  {{ font-size: clamp(1.1rem, 2vw, 1.5rem); margin-top: 4vh; }}

.intro-sub, .step-sub {{
    color: #fff;
    text-align: center;
    line-height: 1.55;
    max-width: 640px;
    margin: 0 auto 1.8rem auto;
    padding: .55rem 1.1rem;
    background: rgba(0,0,0,0.3);
    backdrop-filter: blur(3px);
    border-radius: 10px;
    text-shadow: 0 1px 8px rgba(0,0,0,0.85);
}}
.intro-sub {{ font-size: clamp(.9rem, 1.3vw, 1.05rem); }}
.step-sub  {{ font-size: clamp(.82rem, 1vw, .95rem); }}

/* 반딧불 (fixed 위치, 페이지 전체에 떠다님) */
.firefly {{
    position: fixed; width: 5px; height: 5px;
    background: #fff7c2; border-radius: 50%;
    box-shadow: 0 0 6px 2px #fff7c2,
                0 0 12px 4px rgba(255,232,128,0.55),
                0 0 22px 6px rgba(255,210,90,0.25);
    pointer-events: none; opacity: 0; z-index: 0;
}}
@keyframes flyA {{
    0%   {{ transform: translate(0,0) scale(.7); opacity: 0; }}
    15%  {{ opacity: 1; }} 85% {{ opacity: 1; }}
    100% {{ transform: translate(240px,10px) scale(.6); opacity: 0; }}
}}
@keyframes flyB {{
    0%   {{ transform: translate(0,0) scale(.8); opacity: 0; }}
    20%  {{ opacity: 1; }} 80% {{ opacity: 1; }}
    100% {{ transform: translate(-180px,20px) scale(.5); opacity: 0; }}
}}
@keyframes flyC {{
    0%   {{ transform: translate(0,0) scale(.6); opacity: 0; }}
    25%  {{ opacity: 1; }} 75% {{ opacity: 1; }}
    100% {{ transform: translate(140px,-30px) scale(.5); opacity: 0; }}
}}
@keyframes glow {{
    0%, 100% {{ filter: brightness(.7); }}
    50%      {{ filter: brightness(1.6); }}
}}
.firefly.f1  {{ top: 55%; left: 8%;   animation: flyA 11s linear infinite, glow 2.1s ease-in-out infinite; }}
.firefly.f2  {{ top: 70%; left: 18%;  animation: flyB 13s linear 1s infinite, glow 1.7s ease-in-out infinite; }}
.firefly.f3  {{ top: 40%; left: 30%;  animation: flyC 10s linear 2s infinite, glow 2.4s ease-in-out infinite; }}
.firefly.f4  {{ top: 60%; left: 45%;  animation: flyA 12s linear 3s infinite, glow 1.9s ease-in-out infinite; }}
.firefly.f5  {{ top: 35%; left: 55%;  animation: flyB 14s linear .5s infinite, glow 2.2s ease-in-out infinite; }}
.firefly.f6  {{ top: 65%; left: 65%;  animation: flyC 11s linear 4s infinite, glow 1.6s ease-in-out infinite; }}
.firefly.f7  {{ top: 50%; left: 75%;  animation: flyA 13s linear 1.5s infinite, glow 2.5s ease-in-out infinite; }}
.firefly.f8  {{ top: 30%; left: 85%;  animation: flyB 12s linear 2.5s infinite, glow 1.8s ease-in-out infinite; }}
.firefly.f9  {{ top: 75%; left: 35%;  animation: flyC 14s linear 3.5s infinite, glow 2s ease-in-out infinite; }}
.firefly.f10 {{ top: 45%; left: 90%;  animation: flyA 10s linear 4.5s infinite, glow 2.3s ease-in-out infinite; }}
.firefly.f11 {{ top: 25%; left: 12%;  animation: flyB 13s linear 5s infinite, glow 1.7s ease-in-out infinite; }}
.firefly.f12 {{ top: 80%; left: 50%;  animation: flyC 11s linear 6s infinite, glow 2.1s ease-in-out infinite; }}
</style>
{fireflies}
""",
        unsafe_allow_html=True,
    )


def render_step_text(title: str, subtitle: str = "", intro: bool = False) -> None:
    """페이지 hero 위에 인사/질문 텍스트만 렌더."""
    cls_t = "intro-title" if intro else "step-title"
    cls_s = "intro-sub" if intro else "step-sub"
    html = f'<div class="{cls_t}">{title}</div>'
    if subtitle:
        html += f'<div class="{cls_s}">{subtitle}</div>'
    st.markdown(html, unsafe_allow_html=True)


# ─── 헬퍼 ──────────────────────────────────────────
def _format_drive_time(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}시간 {m}분" if h else f"{m}분"


def _parse_origins(text: str) -> list[str]:
    return [s.strip() for s in text.replace(";", ",").split(",") if s.strip()]


def _best_origin(origins_with_coords, dest):
    if not origins_with_coords or not dest:
        return None
    best = None
    for name, coord in origins_with_coords:
        if not coord:
            continue
        d = haversine_km(coord[0], coord[1], dest[0], dest[1])
        if best is None or d < best["dist"]:
            best = {"name": name, "dist": d, "drive_min": quick_drive_estimate(d)}
    return best


def collect_region_data(sido_, sigungu_, origins_with_coords, sd, ed):
    coord = geocode_sigungu(sido_, sigungu_)
    best = _best_origin(origins_with_coords, coord)
    days = forecast_safe(coord[0], coord[1], sd, ed) if (coord and sd and ed) else []
    area_code = TOURAPI_AREA_CODE.get(sido_)
    spots = []
    if area_code:
        try:
            spots = fetch_by_area(area_code, CONTENT_TYPES["관광지"], rows=30)
            spots = [s for s in spots
                      if sigungu_ in (s.get("addr1", "") + s.get("addr2", ""))]
        except TourAPIError:
            pass
    return {
        "sido": sido_, "sigungu": sigungu_,
        "coord": coord,
        "best_origin_name": best["name"] if best else None,
        "distance_km": best["dist"] if best else None,
        "drive_min": best["drive_min"] if best else None,
        "days": days, "spots": spots,
        "drinks": find_regional_products(sido_, sigungu_),
        "breweries_v": find_breweries(sido_, sigungu_, visitable_only=True),
        "breweries_all": find_breweries(sido_, sigungu_, visitable_only=False),
        "area_code": area_code,
    }


def reset_button(label: str = "← 처음부터") -> None:
    if st.button(label, key=f"reset_{step}"):
        for k in ["step", "region_packs", "selected_region",
                   "form_start_d", "form_end_d", "form_themes",
                   "form_origins", "form_target_sido", "form_target_sigungu",
                   "search_header", "search_meta"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─── 단계 분기 ─────────────────────────────────────────
# Step 0 — 감성 인사 (자동 2초 후 step 1)
if step == 0:
    apply_hero_page_bg()
    render_step_text(
        title=f"이번은 <span style='color:#ffe8a8'>{ctx.season}</span> 입니다",
        subtitle=(f"{ctx.vibe}.<br>"
                   f"<b>{', '.join(ctx.drinks)}</b> 한 잔, "
                   "어디로 마시러 떠나보면 어떨까요? ✨"),
        intro=True,
    )
    time.sleep(2)
    st.session_state["step"] = 1
    st.rerun()


# Step 1 — 일자
elif step == 1:
    apply_hero_page_bg()
    render_step_text(
        title="언제 떠나세요?",
        subtitle="출발일과 귀가일을 골라주세요.",
    )
    col_l, col_m, col_r = st.columns([1, 4, 1])
    with col_m:
        d_a, d_b = st.columns(2)
        with d_a:
            start_d = st.date_input(
                "출발일",
                value=st.session_state.get("form_start_d", today),
                min_value=today, max_value=max_date,
                key="form_start_d",
            )
        with d_b:
            end_d = st.date_input(
                "귀가일",
                value=st.session_state.get("form_end_d", today + timedelta(days=1)),
                min_value=today, max_value=max_date,
                key="form_end_d",
            )
        st.markdown(" ")
        if st.button("다음 →", type="primary", width="stretch"):
            if end_d < start_d:
                st.error("귀가일이 출발일보다 빠릅니다.")
            else:
                st.session_state["step"] = 2
                st.rerun()


# Step 2 — 테마
elif step == 2:
    apply_hero_page_bg()
    render_step_text(
        title="🎯 어떤 느낌을 원하세요?",
        subtitle="여러 개 골라도 좋아요. 비워두면 오늘 계절에 자동으로 맞춰드립니다.",
    )
    col_l, col_m, col_r = st.columns([1, 4, 1])
    with col_m:
        selected_themes = st.multiselect(
            "테마 (복수 선택)",
            options=THEMES,
            default=st.session_state.get("form_themes", []),
            format_func=lambda t: f"{t.emoji} {t.label} — {t.description}",
            key="form_themes",
            label_visibility="collapsed",
        )
        st.markdown(" ")
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("← 이전", width="stretch"):
                st.session_state["step"] = 1
                st.rerun()
        with c2:
            if st.button("다음 →", type="primary", width="stretch"):
                st.session_state["step"] = 3
                st.rerun()


# Step 3 — 출발지
elif step == 3:
    apply_hero_page_bg()
    render_step_text(
        title="🚗 어디서 출발하세요?",
        subtitle=("여러 도시를 <b>쉼표로 구분</b>해서 적으면 그 중 가장 가까운 곳에서 출발하는 것으로 계산합니다.<br>"
                   "예: <i>경주, 부산, 대구</i>"),
    )
    col_l, col_m, col_r = st.columns([1, 4, 1])
    with col_m:
        origins_text = st.text_input(
            "출발 위치 (쉼표 구분, 선택)",
            value=st.session_state.get("form_origins", ""),
            placeholder="예: 경주, 부산, 대구",
            key="form_origins",
        )

        st.markdown("**🗺️ 가고 싶은 지역이 정해져 있나요?** *(선택 — 비워두면 자동 추천)*")
        tg_a, tg_b = st.columns(2)
        with tg_a:
            sido_opts = ["(자동 추천)"] + list_sido()
            tgt_sido = st.selectbox(
                "시/도",
                options=sido_opts,
                index=(sido_opts.index(st.session_state["form_target_sido"])
                        if st.session_state.get("form_target_sido") in sido_opts
                        else 0),
                key="form_target_sido",
            )
        with tg_b:
            if tgt_sido != "(자동 추천)":
                sg_opts = ["(자동)"] + list_sigungu(tgt_sido)
                tgt_sigungu = st.selectbox(
                    "시/군/구",
                    options=sg_opts,
                    index=(sg_opts.index(st.session_state["form_target_sigungu"])
                            if st.session_state.get("form_target_sigungu") in sg_opts
                            else 0),
                    key="form_target_sigungu",
                )
            else:
                st.session_state["form_target_sigungu"] = "(자동)"
                st.selectbox("시/군/구", options=["(시/도 먼저 선택)"], disabled=True)

        # 시/도가 락인되면 그 시/도 안의 시군구 개수로 최대값 제한
        if tgt_sido != "(자동 추천)":
            n_avail = len(list_sigungu(tgt_sido))
            max_n = max(3, min(n_avail, 30))
        else:
            max_n = 9
        cur_val = st.session_state.get("form_top_n", 5)
        clamped_val = min(max(cur_val, 3), max_n)
        if clamped_val != cur_val:
            st.session_state["form_top_n"] = clamped_val
        top_n = st.slider(
            f"추천 받을 지역 수 *(직접 선택 시 무시 · 최대 {max_n})*",
            3, max_n,
            value=clamped_val,
            key="form_top_n",
        )
        st.markdown(" ")
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("← 이전", width="stretch"):
                st.session_state["step"] = 2
                st.rerun()
        with c2:
            if st.button("✨ 추천 받기", type="primary", width="stretch"):
                st.session_state["step"] = 4
                st.rerun()


# Step 4 — 검색 실행 (결과와 같은 흰 배경 + 페이드 인)
elif step == 4:
    st.markdown(
        """
<style>
.stApp { animation: fadePageIn 0.45s ease-out; }
@keyframes fadePageIn { from { opacity: 0.55; } to { opacity: 1; } }
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown("### ✨ 추천 만들고 있어요…")
    st.caption("잠시만 기다려주세요.")

    start_d = st.session_state.get("form_start_d", today)
    end_d = st.session_state.get("form_end_d", today + timedelta(days=1))
    selected_themes: list[Theme] = st.session_state.get("form_themes", [])
    origins_text: str = st.session_state.get("form_origins", "")
    top_n: int = st.session_state.get("form_top_n", 5)

    origin_names = _parse_origins(origins_text)
    origins_with_coords = []
    if origin_names:
        with st.spinner(f"출발지 좌표 변환 중 ({len(origin_names)}곳)…"):
            for name in origin_names:
                c = geocode(name)
                if c:
                    origins_with_coords.append((name, c))
                else:
                    st.warning(f"'{name}' 좌표를 찾지 못해 거리 계산에서 제외합니다.")

    # 사용자가 직접 지역을 골랐는지 확인
    tgt_sido = st.session_state.get("form_target_sido", "(자동 추천)")
    tgt_sigungu = st.session_state.get("form_target_sigungu", "(자동)")

    if tgt_sido != "(자동 추천)" and tgt_sigungu not in ("(자동)", "", None):
        # 단일 지역 직접 지정 — Gemini 호출 없이 바로
        picks = [{"sido": tgt_sido, "sigungu": tgt_sigungu,
                   "reason": "직접 선택한 지역입니다.", "highlights": ""}]
    elif tgt_sido != "(자동 추천)":
        # 시/도만 지정 → 그 시/도 안에서 Gemini가 시/군/구 추천 (시/도는 잠금)
        rows = get_conn().execute("""
            SELECT sido, sigungu, COUNT(*) AS n_breweries, SUM(visitable) AS n_visitable
            FROM breweries WHERE sigungu != '' AND sido = ?
            GROUP BY sido, sigungu ORDER BY n_breweries DESC
        """, (tgt_sido,)).fetchall()
        candidates = [dict(r) for r in rows]
        with st.spinner(f"Gemini가 {tgt_sido} 안에서 추천 중…"):
            picks = curate_destinations(
                ctx, selected_themes, candidates, top_n=top_n,
                origins=[n for n, _ in origins_with_coords],
                restrict_sido=tgt_sido,
            )
    else:
        # 자동 추천 — 전국에서
        rows = get_conn().execute("""
            SELECT sido, sigungu, COUNT(*) AS n_breweries, SUM(visitable) AS n_visitable
            FROM breweries WHERE sigungu != ''
            GROUP BY sido, sigungu ORDER BY n_breweries DESC
        """).fetchall()
        candidates = [dict(r) for r in rows]
        with st.spinner("Gemini가 지역 추천 중…"):
            picks = curate_destinations(
                ctx, selected_themes, candidates, top_n=top_n,
                origins=[n for n, _ in origins_with_coords],
            )

    if not picks:
        err = st.session_state.pop("_last_curate_error", "")
        st.error("추천 생성에 실패했습니다.")
        if err:
            with st.expander("🔍 자세한 에러 (디버그)"):
                st.code(err)
            if "quota" in err.lower() or "429" in err:
                st.warning("Gemini 무료 한도가 일시 소진된 듯합니다. 30~60초 후 다시 시도해 주세요.")
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("🔄 다시 시도", type="primary", width="stretch"):
                st.rerun()
        with rc2:
            reset_button("← 처음부터 다시")
        st.stop()

    with st.spinner("지역별 명소·술·양조장·날씨 모으는 중…"):
        region_packs = {}
        for p in picks:
            s_, sg_ = p.get("sido", ""), p.get("sigungu", "")
            if not s_ or not sg_:
                continue
            key = f"{s_} {sg_}"
            region_packs[key] = {
                **collect_region_data(s_, sg_, origins_with_coords, start_d, end_d),
                "reason": p.get("reason", ""),
                "highlights": p.get("highlights", ""),
            }

    if selected_themes:
        theme_label = " + ".join(t.label for t in selected_themes)
        theme_desc = ", ".join(t.description for t in selected_themes)
    else:
        theme_label = f"{ctx.season} 자동"
        theme_desc = f"{ctx.season} 분위기, {ctx.vibe}"

    st.session_state["region_packs"] = region_packs
    st.session_state["search_header"] = f"### 🌿 '{theme_label}' 테마 추천 여행지"
    st.session_state["search_meta"] = {
        "origins": [n for n, _ in origins_with_coords],
        "start_d": start_d.isoformat(),
        "end_d": end_d.isoformat(),
        "theme_label": theme_label,
        "theme_desc": theme_desc,
    }
    st.session_state["selected_region"] = None
    st.session_state["step"] = 5
    st.rerun()


# Step 5 — 결과
elif step == 5:
    st.markdown(
        """
<style>
.stApp { animation: fadePageIn 0.45s ease-out; }
@keyframes fadePageIn { from { opacity: 0.55; } to { opacity: 1; } }
</style>
""",
        unsafe_allow_html=True,
    )
    region_packs = st.session_state.get("region_packs", {})
    if not region_packs:
        st.warning("결과가 없습니다. 처음부터 다시 시도해 주세요.")
        reset_button()
        st.stop()

    st.markdown(
        f"""
<style>
.result-banner {{
    position: relative; width: 100%; height: 140px;
    background: {_bg_css}; border-radius: 14px; overflow: hidden;
    margin-bottom: 1rem;
    display: flex; align-items: center; justify-content: center;
}}
.result-banner::after {{
    content: ""; position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,.05) 0%, rgba(0,0,0,.55) 100%);
}}
.result-banner-text {{
    position: relative; z-index: 1; color: #fff; text-align: center;
    text-shadow: 0 2px 10px rgba(0,0,0,.8);
}}
.result-banner-text h3 {{ margin: 0; font-size: 1.6rem; }}
.result-banner-text p  {{ margin: .2rem 0 0 0; font-size: .9rem; opacity: .9; }}
</style>
<div class="result-banner">
  <div class="result-banner-text">
    <h3>🍶 추천 완료</h3>
    <p>카드를 눌러 그 지역의 명소·술·양조장을 확인해 보세요.</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    meta = st.session_state.get("search_meta", {})
    region_keys = list(region_packs.keys())

    top_row = st.columns([3, 1, 1, 1])
    with top_row[0]:
        st.markdown(st.session_state.get("search_header", ""))
    with top_row[1]:
        if st.button("추억", width="stretch", key="nav_mem_s5"):
            st.switch_page("pages/1_Memories.py")
    with top_row[2]:
        if st.button("가고싶은 곳", width="stretch", key="nav_wish_s5"):
            st.switch_page("pages/2_Wishlist.py")
    with top_row[3]:
        reset_button("← 새로 시작")

    # ─── 🔧 인라인 조건 수정 바 ──────────────────────
    with st.container(border=True):
        st.caption("🔧 조건을 바꾸고 [🔄 다시 추천]을 누르면 즉시 재검색됩니다.")

        # Row 1: 일자 + 지역수
        r1a, r1b, r1c = st.columns([1.5, 1.5, 1])
        with r1a:
            new_start = st.date_input(
                "📅 출발일",
                value=st.session_state.get("form_start_d", today),
                min_value=today, max_value=max_date, key="edit_start_d",
            )
        with r1b:
            new_end = st.date_input(
                "📅 귀가일",
                value=st.session_state.get("form_end_d", today + timedelta(days=1)),
                min_value=today, max_value=max_date, key="edit_end_d",
            )
        with r1c:
            # 시/도 락인 시 시군구 수로 제한
            tgt_sido_now = st.session_state.get("form_target_sido", "(자동 추천)")
            if tgt_sido_now != "(자동 추천)":
                _max_n = max(3, min(len(list_sigungu(tgt_sido_now)), 30))
            else:
                _max_n = 9
            _top_opts = list(range(3, _max_n + 1))
            cur_top = st.session_state.get("form_top_n", 5)
            new_top_n = st.selectbox(
                f"🔢 지역 수 (최대 {_max_n})",
                options=_top_opts,
                index=_top_opts.index(cur_top if cur_top in _top_opts else _top_opts[0]),
                key="edit_top_n",
            )

        # Row 2: 가고 싶은 시/도 + 시/군/구
        r2a, r2b = st.columns(2)
        with r2a:
            sido_opts_edit = ["(자동 추천)"] + list_sido()
            cur_target_sido = st.session_state.get("form_target_sido", "(자동 추천)")
            new_target_sido = st.selectbox(
                "🗺️ 가고 싶은 시/도",
                options=sido_opts_edit,
                index=(sido_opts_edit.index(cur_target_sido)
                        if cur_target_sido in sido_opts_edit else 0),
                key="edit_target_sido",
            )
        with r2b:
            if new_target_sido != "(자동 추천)":
                sg_opts_edit = ["(자동)"] + list_sigungu(new_target_sido)
                cur_target_sigungu = st.session_state.get("form_target_sigungu", "(자동)")
                new_target_sigungu = st.selectbox(
                    "📌 시/군/구",
                    options=sg_opts_edit,
                    index=(sg_opts_edit.index(cur_target_sigungu)
                            if cur_target_sigungu in sg_opts_edit else 0),
                    key="edit_target_sigungu",
                )
            else:
                new_target_sigungu = "(자동)"
                st.selectbox("📌 시/군/구",
                              options=["(시/도 먼저 선택)"], disabled=True,
                              key="edit_target_sigungu_disabled")

        # Row 3: 테마 + 출발지
        r3a, r3b = st.columns(2)
        with r3a:
            new_themes = st.multiselect(
                "🎯 테마",
                options=THEMES,
                default=st.session_state.get("form_themes", []),
                format_func=lambda t: f"{t.emoji} {t.label}",
                key="edit_themes",
            )
        with r3b:
            new_origins = st.text_input(
                "🚗 출발지 (쉼표 구분)",
                value=st.session_state.get("form_origins", ""),
                key="edit_origins",
                placeholder="예: 경주, 부산, 대구",
            )

        if st.button("🔄 다시 추천", type="primary", width="stretch"):
            if new_end < new_start:
                st.error("귀가일이 출발일보다 빠릅니다.")
            else:
                st.session_state["form_start_d"] = new_start
                st.session_state["form_end_d"] = new_end
                st.session_state["form_themes"] = new_themes
                st.session_state["form_origins"] = new_origins
                st.session_state["form_top_n"] = new_top_n
                st.session_state["form_target_sido"] = new_target_sido
                st.session_state["form_target_sigungu"] = new_target_sigungu
                st.session_state.pop("region_packs", None)
                st.session_state.pop("selected_region", None)
                for k in list(st.session_state.keys()):
                    if (k.startswith("specialty_") or k.startswith("drinks_sorted_")
                            or k.startswith("local_drink_")):
                        del st.session_state[k]
                st.session_state["step"] = 4
                st.rerun()

    # 카드 그리드
    if len(region_keys) > 1:
        cards_per_row = 3
        for chunk_start in range(0, len(region_keys), cards_per_row):
            chunk = region_keys[chunk_start:chunk_start + cards_per_row]
            cols = st.columns(cards_per_row)
            for idx, key in enumerate(chunk):
                data = region_packs[key]
                with cols[idx]:
                    with st.container(border=True):
                        has_drink = bool(data.get("drinks") or data.get("breweries_v"))
                        drink_badge = ("<span style='float:right; font-size:1.2rem;' "
                                        "title='이 지역에서 술을 즐길 수 있어요'>🍶</span>"
                                        if has_drink else "")
                        st.markdown(f"### 📍 {key}{drink_badge}",
                                     unsafe_allow_html=True)
                        if data["distance_km"] is not None:
                            line = f"🚗 **{data['distance_km']:.0f}km** · 차로 {_format_drive_time(data['drive_min'])}"
                            if data.get("best_origin_name"):
                                line += f"  \n_📍 출발: {data['best_origin_name']}_"
                            st.markdown(line)
                        if data["days"]:
                            rainy_emoji = "☔" if any(d.is_rainy for d in data["days"]) else "☀️"
                            st.markdown(f"{rainy_emoji} {summarize_period(data['days'])}")
                        st.caption(
                            f"🗺️ 명소 {len(data['spots'])}곳  ·  "
                            f"🍶 술 {len(data['drinks'])}종  ·  "
                            f"🏭 체험 양조장 {len(data['breweries_v'])}곳"
                        )
                        if st.button("자세히 보기 →", key=f"sel_{key}", width="stretch"):
                            st.session_state["selected_region"] = key
                            st.session_state["scroll_to_detail"] = True
                            st.rerun()

    st.markdown("---")
    if len(region_keys) == 1:
        selected_key = region_keys[0]
    else:
        selected_key = st.session_state.get("selected_region")

    if not selected_key or selected_key not in region_keys:
        st.info("위 카드에서 **'자세히 보기 →'** 버튼을 누르면 그 지역의 명소·술·양조장이 펼쳐집니다.")
        st.stop()

    # 자세히 보기 영역으로 자동 스크롤할 anchor
    st.markdown('<div id="detail-anchor"></div>', unsafe_allow_html=True)
    if st.session_state.pop("scroll_to_detail", False):
        import streamlit.components.v1 as components
        components.html(
            """
<script>
  const doc = window.parent.document;
  const anchor = doc.getElementById("detail-anchor");
  if (anchor) { anchor.scrollIntoView({behavior: "smooth", block: "start"}); }
</script>
""",
            height=0,
        )

    data = region_packs[selected_key]
    has_drink = bool(data.get("drinks") or data.get("breweries_v"))
    drink_badge_html = ("<span style='float:right; font-size:1.5rem;' "
                         "title='이 지역에서 술을 즐길 수 있어요'>🍶</span>"
                         if has_drink else "")
    with st.container(border=True):
        st.markdown(f"## 📍 {selected_key}{drink_badge_html}",
                     unsafe_allow_html=True)
        if data.get("reason"):
            st.markdown(f"**💡 왜 여기?** {data['reason']}")
        if data.get("highlights"):
            st.caption(f"키워드: {data['highlights']}")

        metric_cols = st.columns(4)
        with metric_cols[0]:
            label = "🚗 거리"
            if data.get("best_origin_name"):
                label = f"🚗 {data['best_origin_name']}서"
            st.metric(label, f"{data['distance_km']:.0f} km"
                       if data["distance_km"] is not None else "—")
        with metric_cols[1]:
            st.metric("⏱ 차시간",
                       _format_drive_time(data["drive_min"])
                       if data["drive_min"] is not None else "—")
        with metric_cols[2]:
            if data["days"]:
                rainy_emoji = "☔" if any(d.is_rainy for d in data["days"]) else "☀️"
                st.metric(f"{rainy_emoji} 기간 날씨", summarize_period(data["days"]))
            else:
                st.metric("📅 기간 날씨", "—")
        with metric_cols[3]:
            st.metric("🏭 체험 양조장",
                       f"{len(data['breweries_v'])}곳",
                       f"전체 {len(data['breweries_all'])}곳")

        if data["days"]:
            with st.expander("📅 일자별 날씨"):
                weather_rows = [{
                    "날짜": d.date, "날씨": f"{d.emoji} {d.label}",
                    "최저(°C)": f"{d.tmin:.0f}", "최고(°C)": f"{d.tmax:.0f}",
                    "강수확률": f"{d.precip_prob}%",
                    "강수량(mm)": f"{d.precip_mm:.1f}",
                } for d in data["days"]]
                st.dataframe(pd.DataFrame(weather_rows),
                              width="stretch", hide_index=True)

        # 4분할: 명소 / 술 / 양조장 / 특산품
        col_s, col_d, col_b, col_p = st.columns(4)
        with col_s:
            st.markdown("##### 명소")
            if data["spots"]:
                spot_rows = [{
                    "이름": s.get("title", ""),
                    "주소": (s.get("addr1") or "").strip(),
                } for s in data["spots"][:8]]
                st.dataframe(pd.DataFrame(spot_rows), width="stretch",
                              hide_index=True, height=320)
            else:
                st.caption("_등록된 명소 없음_")
        with col_d:
            st.markdown("##### 이 지역의 술 *(추천 시음 순서)*")
            if data["drinks"]:
                drinks_cache_key = f"drinks_sorted_{selected_key}"
                if drinks_cache_key not in st.session_state:
                    with st.spinner("추천 순서 정렬 중…"):
                        st.session_state[drinks_cache_key] = sort_drinks_recommended(
                            data["drinks"])
                sorted_drinks = st.session_state[drinks_cache_key]
                drink_rows = [{
                    "순서": i + 1,
                    "제품": d.get("product_name", ""),
                    "도수": f"{d.get('abv','?')}도",
                    "양조장": d.get("brewery_name", ""),
                } for i, d in enumerate(sorted_drinks[:8])]
                st.dataframe(pd.DataFrame(drink_rows), width="stretch",
                              hide_index=True, height=320)
            else:
                # 양조장 정보 없으면 Gemini에게 "이 지역에서 마실 만한 술" 추천
                local_drink_key = f"local_drink_{selected_key}"
                if local_drink_key not in st.session_state:
                    with st.spinner("이 지역 술 정보 확인 중…"):
                        st.session_state[local_drink_key] = local_drink_recommendation(
                            data["sido"], data["sigungu"])
                local_drink = st.session_state[local_drink_key]
                if local_drink:
                    st.markdown(local_drink)
                else:
                    st.caption("_이 지역의 술 정보 없음_")
        with col_b:
            st.markdown("##### 체험 양조장")
            b_list = data["breweries_v"] or data["breweries_all"]
            if b_list:
                b_rows = [{
                    "이름": b.get("name", ""),
                    "체험": "🟢" if b.get("visitable") else "⚪",
                    "주소": b.get("address", ""),
                } for b in b_list[:8]]
                st.dataframe(pd.DataFrame(b_rows), width="stretch",
                              hide_index=True, height=320)
            else:
                st.caption("_등록된 양조장 없음_")
        with col_p:
            st.markdown("##### 특산품 · 향토 음식")
            specialty_cache_key = f"specialty_{selected_key}"
            if specialty_cache_key not in st.session_state:
                with st.spinner("확인 중…"):
                    st.session_state[specialty_cache_key] = regional_specialty(
                        data["sido"], data["sigungu"])
            specialty_text = st.session_state[specialty_cache_key]
            if specialty_text:
                st.markdown(specialty_text)
            else:
                st.caption("_특별히 알려진 특산품이 없습니다_")

        st.markdown("---")
        btn_a, btn_b = st.columns(2)
        with btn_a:
            if st.button("🤖 1박2일 AI 코스 짜기",
                          key=f"course_{selected_key}", width="stretch"):
                with st.spinner("Gemini가 코스 짜는 중…"):
                    spots_data, foods_data, fest_data = [], [], []
                    if data["area_code"]:
                        try:
                            spots_data = fetch_by_area(data["area_code"], CONTENT_TYPES["관광지"])
                            foods_data = fetch_by_area(data["area_code"], CONTENT_TYPES["맛집"])
                            fest_data = fetch_festivals(data["area_code"])
                        except TourAPIError:
                            pass
                    taste = meta.get("theme_desc", "")
                    prompt = build_prompt(selected_key, taste, "1박 2일",
                                           data["breweries_all"], spots_data,
                                           foods_data, fest_data)
                    course = generate_course(prompt)
                st.markdown(course)
        with btn_b:
            if data["days"] and data["breweries_v"]:
                if st.button("🌦️ 날씨 반영 즐기기 가이드",
                              key=f"weather_{selected_key}", width="stretch"):
                    with st.spinner("Gemini 가이드 작성 중…"):
                        b0 = data["breweries_v"][0]
                        products = get_brewery_products(b0["id"])
                        dates_label = f"{meta.get('start_d','')} ~ {meta.get('end_d','')}"
                        guide = weather_aware_plan(b0, data["days"],
                                                     dates_label, products)
                    st.markdown(guide)
            else:
                st.caption("_날씨 가이드는 일자 입력 + 체험 양조장이 있어야 합니다_")
