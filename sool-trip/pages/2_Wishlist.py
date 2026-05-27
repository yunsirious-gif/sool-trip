"""가고 싶은 여행지 — 지역별 to-do + 지도."""

from __future__ import annotations

import pandas as pd
import pydeck as pdk
import streamlit as st

from lib.auth import gate
from lib.gemini import _generate
from lib.geocoding import geocode
from lib.wishlist import (CATEGORIES, add_item, delete_item, init_table,
                            list_items, list_regions, toggle_visited)

st.set_page_config(page_title="가고 싶은 여행지", page_icon="💝", layout="wide")
gate()
st.markdown(
    "<style>[data-testid='stSidebarNav']{display:none;}</style>",
    unsafe_allow_html=True,
)
if st.button("← 메인으로"):
    st.switch_page("app.py")
init_table()

st.title("💝 가고 싶은 여행지")
st.caption("가보고 싶은 지역의 카페·식당·관광지를 모아두고, 지도로 한눈에 확인하세요.")

# ─── 새 항목 추가 ────────────────────────────────────
with st.expander("➕ 항목 추가하기", expanded=False):
    with st.form("add_wish"):
        c1, c2 = st.columns(2)
        with c1:
            region = st.text_input("지역 *", placeholder="예: 제주도, 경상북도 청도군",
                                     key="form_wish_region")
        with c2:
            category = st.selectbox(
                "카테고리",
                options=list(CATEGORIES.keys()),
                format_func=lambda k: f"{CATEGORIES[k]['emoji']} {k}",
            )

        c3, c4 = st.columns(2)
        with c3:
            name = st.text_input("이름 *", placeholder="예: 동문시장, 카페델문도")
        with c4:
            address = st.text_input("주소 (지도 표시용)", placeholder="비워두면 지역명으로 대체")

        c5, c6 = st.columns(2)
        with c5:
            priority = st.slider("우선순위 ⭐", 1, 5, 3)
        with c6:
            st.markdown("&nbsp;")  # spacer
        memo = st.text_area("메모", height=70, placeholder="왜 가고 싶은지 / 추천 메뉴 등")

        if st.form_submit_button("💾 저장", type="primary", width="stretch"):
            if not region.strip() or not name.strip():
                st.error("지역과 이름은 필수입니다.")
            else:
                search_addr = address.strip() or f"{region.strip()} {name.strip()}"
                with st.spinner("좌표 변환 중…"):
                    latlon = geocode(search_addr)
                lat = latlon[0] if latlon else None
                lon = latlon[1] if latlon else None
                add_item(
                    region=region.strip(), category=category, name=name.strip(),
                    address=address.strip(), lat=lat, lon=lon,
                    memo=memo.strip(), priority=priority,
                )
                st.success("저장됐어요!")
                st.rerun()

# ─── AI 추천 ─────────────────────────────────────────
with st.expander("🤖 AI에게 추천 받기", expanded=False):
    rec_region = st.text_input("어떤 지역?", placeholder="예: 제주도, 강릉시")
    rec_cats = st.multiselect(
        "어떤 카테고리?",
        options=list(CATEGORIES.keys()),
        default=["관광지", "식당", "카페"],
        format_func=lambda k: f"{CATEGORIES[k]['emoji']} {k}",
    )
    if st.button("✨ 추천 받기"):
        if not rec_region.strip():
            st.warning("지역을 입력해주세요.")
        elif not rec_cats:
            st.warning("카테고리를 1개 이상 골라주세요.")
        else:
            cat_list = ", ".join(rec_cats)
            prompt = f"""당신은 한국 여행 큐레이터입니다.
'{rec_region}'에서 여행자가 꼭 가봐야 할 곳을 카테고리별로 추천해 주세요.
카테고리: {cat_list}
각 카테고리당 2~3곳, 정말 유명하고 검증된 곳만.
각 항목은 "- 이름 | 주소 | 한 줄 설명" 형식으로 한 줄씩.
다른 텍스트 금지, 항목만.

예시:
[관광지]
- 성산일출봉 | 제주 서귀포시 성산읍 일출로 284-12 | 유네스코 세계자연유산, 일출 명소
"""
            with st.spinner("Gemini가 추천 중…"):
                response = _generate(prompt)
            if not response:
                st.error("추천 실패 — 잠시 후 다시 시도해주세요.")
            else:
                st.markdown(response)
                st.caption("👆 마음에 드는 곳을 위 **'➕ 항목 추가하기'**에서 직접 입력해 저장하세요.")

# ─── 지역 필터 ────────────────────────────────────────
st.markdown("---")
regions = list_regions()

if not regions:
    st.info("아직 저장된 여행지가 없어요. 위 **'➕ 항목 추가하기'**로 첫 항목을 추가해 보세요.")
    st.stop()

selected_region = st.selectbox(
    "🔍 지역 선택",
    options=["(전체)"] + regions,
)
items = list_items("" if selected_region == "(전체)" else selected_region)

if not items:
    st.info("이 지역에 저장된 항목이 없습니다.")
    st.stop()

# ─── 지도 ──────────────────────────────────────────
items_with_coord = [i for i in items if i.get("lat") and i.get("lon")]

if items_with_coord:
    st.subheader("🗺️ 지도")
    df_map = pd.DataFrame([{
        "name": i["name"],
        "category": i.get("category", "기타"),
        "lat": i["lat"],
        "lon": i["lon"],
        "color": CATEGORIES.get(i.get("category", "기타"),
                                  CATEGORIES["기타"])["color"] + [200],
        "memo": i.get("memo") or "",
        "visited": "✅ 다녀옴" if i.get("visited") else "📌 가고 싶음",
    } for i in items_with_coord])

    center_lat = df_map["lat"].mean()
    center_lon = df_map["lon"].mean()

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position="[lon, lat]",
        get_color="color",
        get_radius=300,
        pickable=True,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )
    view = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=10,
        pitch=0,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style="light",
        tooltip={"html": "<b>{name}</b><br/>{category}<br/>{visited}<br/>{memo}"},
    )
    st.pydeck_chart(deck)

    # 카테고리별 범례
    legend_bits = []
    for cat, info in CATEGORIES.items():
        present = any(i.get("category") == cat for i in items_with_coord)
        if present:
            r, g, b = info["color"]
            legend_bits.append(
                f"<span style='display:inline-block; width:12px; height:12px; "
                f"background:rgb({r},{g},{b}); border-radius:50%; margin-right:4px;'></span>"
                f"{info['emoji']} {cat}"
            )
    if legend_bits:
        st.markdown(" &nbsp; ".join(legend_bits), unsafe_allow_html=True)

    n_no_coord = len(items) - len(items_with_coord)
    if n_no_coord:
        st.caption(f"_좌표를 찾지 못한 항목 {n_no_coord}건은 지도에서 빠짐_")
else:
    st.warning("저장된 항목 중 좌표가 있는 게 없어 지도를 표시하지 못합니다.")


# ─── 카테고리별 목록 ─────────────────────────────────
st.markdown("---")
st.subheader("📋 카테고리별 목록")

cat_tabs = st.tabs([
    f"{CATEGORIES[c]['emoji']} {c} ({sum(1 for i in items if i.get('category') == c)})"
    for c in CATEGORIES if any(i.get("category") == c for i in items)
])
cats_present = [c for c in CATEGORIES if any(i.get("category") == c for i in items)]

for cat, tab in zip(cats_present, cat_tabs):
    with tab:
        for i in [x for x in items if x.get("category") == cat]:
            with st.container(border=True):
                head_l, head_r = st.columns([4, 1])
                with head_l:
                    star = "⭐" * (i.get("priority") or 0)
                    visited_tag = "✅ 다녀옴" if i.get("visited") else ""
                    st.markdown(f"**{i['name']}**  ·  {star}  {visited_tag}")
                    if i.get("region"):
                        st.caption(f"📍 {i['region']}")
                    if i.get("address"):
                        st.caption(f"🏠 {i['address']}")
                    if i.get("memo"):
                        st.markdown(f"> {i['memo']}")
                with head_r:
                    if i.get("visited"):
                        if st.button("↩️ 다시 가고싶음", key=f"unv_{i['id']}",
                                       width="stretch"):
                            toggle_visited(i["id"], False)
                            st.rerun()
                    else:
                        if st.button("✅ 다녀옴", key=f"vis_{i['id']}",
                                       width="stretch"):
                            toggle_visited(i["id"], True)
                            st.rerun()
                    if st.button("🗑️ 삭제", key=f"del_{i['id']}",
                                   width="stretch"):
                        delete_item(i["id"])
                        st.rerun()
