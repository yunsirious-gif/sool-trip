"""계절 + 테마 → 여행지(시군구) 중심 추천.

흐름: Gemini가 시군구 N곳을 골라줌 → 각 지역에 대해
  1️⃣ 지역 소개 (Gemini의 추천 이유)
  2️⃣ 🗺️ 명소 (TourAPI 관광지)
  3️⃣ 🍶 그 지역의 술 (해당 시군구 양조장 products)
  4️⃣ 🏭 체험 가능 양조장
순으로 카드 노출.
"""

from __future__ import annotations

import streamlit as st

from lib.brewery import find_breweries, find_regional_products
from lib.db import get_conn
from lib.gemini import curate_destinations
from lib.geo import TOURAPI_AREA_CODE
from lib.season import current_context
from lib.theme import THEMES, by_key
from lib.tourapi import CONTENT_TYPES, TourAPIError, fetch_by_area

st.set_page_config(page_title="계절·테마 추천 · 술여행", page_icon="🌿", layout="wide")

ctx = current_context()

st.title(f"🌿 지금은 '{ctx.season}'")
st.caption(f"{ctx.today.isoformat()} · 분위기: {ctx.vibe}")

c1, c2 = st.columns([2, 3])
with c1:
    st.markdown(f"**🍶 계절 어울리는 술**  \n{', '.join(ctx.drinks)}")
with c2:
    st.markdown(f"**📍 권역 힌트**  \n{ctx.regions_hint}")

st.markdown("---")
st.subheader("🎯 어떤 테마로 떠나시겠어요?")

theme_keys = [t.key for t in THEMES]
theme_labels = [f"{t.emoji} {t.label}" for t in THEMES]
theme_idx = st.radio(
    "테마 선택",
    options=range(len(THEMES)),
    format_func=lambda i: theme_labels[i],
    horizontal=True,
    label_visibility="collapsed",
)
selected_theme = THEMES[theme_idx]
st.caption(f"_{selected_theme.description}_")

origin = st.text_input(
    "🚗 출발 위치 (선택, 거리 가중치)",
    value=st.session_state.get("origin_detail", ""),
    placeholder="예: 서울시 강남구",
)
st.session_state["origin_detail"] = origin

top_n = st.slider("추천 받을 지역 수", 3, 7, 5)

if not st.button("✨ 이 계절·테마에 어울리는 여행지 찾기", type="primary", width="stretch"):
    st.info("테마를 고르고 '여행지 찾기'를 눌러주세요.")
    st.stop()

# 1. 후보 시군구 + 양조장 카운트
with st.spinner("후보 지역 모으는 중…"):
    candidate_rows = get_conn().execute("""
        SELECT sido, sigungu,
               COUNT(*) AS n_breweries,
               SUM(visitable) AS n_visitable
        FROM breweries
        WHERE sigungu != ''
        GROUP BY sido, sigungu
        ORDER BY n_breweries DESC
    """).fetchall()
    candidates = [dict(r) for r in candidate_rows]

# 2. Gemini가 N개 지역 큐레이션
with st.spinner(f"Gemini가 '{selected_theme.label}' 테마에 어울리는 지역을 고르는 중…"):
    picks = curate_destinations(ctx, selected_theme, candidates, top_n=top_n, origin=origin)

if not picks:
    st.error("추천 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

st.markdown("---")
st.markdown(f"### 🏆 {selected_theme.emoji} '{selected_theme.label}' 테마 추천 여행지")

for rank, pick in enumerate(picks, 1):
    sido = pick.get("sido", "")
    sigungu = pick.get("sigungu", "")
    if not sido or not sigungu:
        continue

    with st.container(border=True):
        st.markdown(f"#### {rank}. {sido} {sigungu}")
        if pick.get("reason"):
            st.markdown(f"**💡 왜 이 곳?**  \n{pick['reason']}")
        if pick.get("highlights"):
            st.caption(f"키워드: {pick['highlights']}")

        # 1️⃣ 명소 (TourAPI)
        st.markdown("##### 🗺️ 이 지역의 명소")
        area_code = TOURAPI_AREA_CODE.get(sido)
        spots_shown = 0
        if area_code:
            try:
                spots = fetch_by_area(area_code, CONTENT_TYPES["관광지"], rows=30)
                spots = [s for s in spots
                          if sigungu in (s.get("addr1", "") + s.get("addr2", ""))]
                for s in spots[:5]:
                    st.markdown(f"- **{s.get('title','?')}** · "
                                 f"{(s.get('addr1') or '').strip()}")
                    spots_shown += 1
            except TourAPIError as e:
                st.caption(f"⚠️ 관광지 조회 실패: {e}")
        if spots_shown == 0:
            st.caption("_등록된 관광지 정보 없음_")

        # 2️⃣ 지역 술
        st.markdown("##### 🍶 이 지역에서 즐길 수 있는 술")
        drinks = find_regional_products(sido, sigungu)
        if not drinks:
            st.caption("_데이터에 등록된 지역 술 없음_")
        else:
            for d in drinks[:4]:
                head = f"- **{d['product_name']}** ({d.get('abv','?')}도)"
                if d.get("brewery_name"):
                    head += f" · {d['brewery_name']}"
                st.markdown(head)
                if d.get("features"):
                    st.caption(d["features"])
            if len(drinks) > 4:
                st.caption(f"…외 {len(drinks) - 4}종")

        # 3️⃣ 체험 가능 양조장
        st.markdown("##### 🏭 체험할 수 있는 양조장")
        breweries = find_breweries(sido, sigungu, visitable_only=True)
        if not breweries:
            st.caption("_등록된 체험 양조장 없음 — 자유 방문 양조장도 확인해 보세요_")
            other = find_breweries(sido, sigungu, visitable_only=False)
            for b in other[:2]:
                st.markdown(f"- {b['name']}  ·  {b['address']}")
        else:
            for b in breweries[:3]:
                st.markdown(f"- **{b['name']}**  ·  {b['address']}")
                if b.get("homepage"):
                    st.caption(b["homepage"])
