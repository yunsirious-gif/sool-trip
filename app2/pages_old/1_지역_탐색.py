"""지역 탐색 — 양조장 · 관광지 · 맛집 · 축제 4탭."""

import streamlit as st

from lib.brewery import (count_regional_products, find_breweries,
                          find_regional_products, get_brewery_products)
from lib.geo import TOURAPI_AREA_CODE
from lib.tourapi import CONTENT_TYPES, TourAPIError, fetch_by_area, fetch_festivals

st.set_page_config(page_title="지역 탐색 · 술여행", page_icon="🍶", layout="wide")

sido = st.session_state.get("sido")
sigungu = st.session_state.get("sigungu")

if not sido:
    st.warning("먼저 홈에서 지역을 선택해 주세요.")
    st.page_link("app.py", label="← 홈으로 돌아가기")
    st.stop()

st.title(f"🍶 {sido} {sigungu or ''}".strip())
st.caption("양조장 · 관광지 · 맛집 · 축제를 한 화면에서 모아보기")

n_drinks = count_regional_products(sido, sigungu)
tab_b, tab_d, tab_t, tab_f, tab_e = st.tabs(
    ["🍶 양조장", f"🥃 이 지역의 술 ({n_drinks})", "🗺️ 관광지", "🍽️ 맛집", "🎉 축제"]
)


with tab_b:
    visitable_only = st.checkbox("체험 가능한 양조장만 보기", value=False)
    breweries = find_breweries(sido, sigungu, visitable_only=visitable_only)
    if not breweries:
        st.info("이 지역에 등록된 양조장이 없습니다.")
    else:
        st.caption(f"총 {len(breweries)}곳")
        for b in breweries:
            with st.container(border=True):
                head_l, head_r = st.columns([3, 1])
                with head_l:
                    badge = "🟢 체험 가능" if b["visitable"] else "⚪ 체험 정보 없음"
                    st.markdown(f"### {b['name']}  ·  {badge}")
                    st.caption(b["address"] or "주소 정보 없음")
                with head_r:
                    if b["homepage"]:
                        st.link_button("홈페이지 →", b["homepage"], width="stretch")

                products = get_brewery_products(b["id"])
                if products:
                    with st.expander(f"이 양조장의 술 {len(products)}종 보기"):
                        for p in products:
                            st.markdown(
                                f"**{p['product_name']}** · "
                                f"{p['abv']}도 · {p['volume'] or '-'}"
                            )
                            if p["features"]:
                                st.caption(p["features"])


with tab_d:
    st.caption("이 지역의 양조장에서 빚는 술 — 사실상 '지역 한정주'")
    filter_c1, filter_c2 = st.columns([2, 1])
    with filter_c1:
        keyword = st.text_input(
            "키워드 검색 (제품명·특징·원료)",
            placeholder="예: 막걸리 / 유자 / 햅쌀",
            key="drink_keyword",
        )
    with filter_c2:
        abv_range = st.slider("도수 범위", 0, 50, (0, 50), key="drink_abv")

    def _safe_abv(v) -> float | None:
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    drinks = find_regional_products(sido, sigungu, keyword=keyword.strip())
    filtered = []
    for d in drinks:
        abv = _safe_abv(d.get("abv"))
        if abv is None:
            continue
        if abv_range[0] <= abv <= abv_range[1]:
            d["_abv_float"] = abv
            filtered.append(d)
    drinks = filtered

    if not drinks:
        st.info("조건에 맞는 술이 없습니다.")
    else:
        st.caption(f"총 {len(drinks)}종")
        for d in drinks:
            with st.container(border=True):
                head = f"### 🥃 {d['product_name']}  ·  {d.get('abv','?')}도"
                if d.get("visitable"):
                    head += "  ·  🟢 양조장 체험 가능"
                st.markdown(head)
                meta_bits = [d.get("brewery_name") or "양조장 미상"]
                if d.get("sigungu"):
                    meta_bits.append(d["sigungu"])
                if d.get("volume"):
                    meta_bits.append(d["volume"])
                st.caption(" · ".join(meta_bits))

                if d.get("features"):
                    st.markdown(f"**한 줄 특징**  \n{d['features']}")
                if d.get("description"):
                    with st.expander("상세 소개"):
                        st.write(d["description"])
                        if d.get("ingredients"):
                            st.caption(f"성분: {d['ingredients']}")
                        if d.get("awards"):
                            st.caption(f"🏆 수상: {d['awards']}")


def _render_tour_items(items: list[dict], empty_msg: str) -> None:
    if not items:
        st.info(empty_msg)
        return
    st.caption(f"총 {len(items)}건")
    for it in items:
        with st.container(border=True):
            l, r = st.columns([3, 1])
            with l:
                st.markdown(f"### {it.get('title', '(이름 없음)')}")
                addr = it.get("addr1", "") + " " + (it.get("addr2") or "")
                if addr.strip():
                    st.caption(addr.strip())
                if it.get("tel"):
                    st.caption(f"☎ {it['tel']}")
                if it.get("eventstartdate"):
                    s, e = it.get("eventstartdate", ""), it.get("eventenddate", "")
                    st.caption(f"📅 {s} ~ {e}")
            with r:
                if it.get("firstimage"):
                    st.image(it["firstimage"], width="stretch")


area_code = TOURAPI_AREA_CODE.get(sido)


def _fetch_or_warn(content_type: int) -> list[dict] | None:
    if not area_code:
        st.warning(f"'{sido}'는 TourAPI 지역코드 매핑이 없습니다.")
        return None
    try:
        return fetch_by_area(area_code, content_type)
    except TourAPIError as e:
        st.error(str(e))
        st.caption("`.env`의 `PUBLIC_DATA_API_KEY`가 TourAPI에 신청되어 있어야 합니다.")
        return None


with tab_t:
    items = _fetch_or_warn(CONTENT_TYPES["관광지"])
    if items is not None:
        if sigungu:
            items = [x for x in items if sigungu in (x.get("addr1", "") + x.get("addr2", ""))]
        _render_tour_items(items, "이 지역의 관광지를 찾지 못했습니다.")

with tab_f:
    items = _fetch_or_warn(CONTENT_TYPES["맛집"])
    if items is not None:
        if sigungu:
            items = [x for x in items if sigungu in (x.get("addr1", "") + x.get("addr2", ""))]
        _render_tour_items(items, "이 지역의 맛집을 찾지 못했습니다.")

with tab_e:
    if not area_code:
        st.warning(f"'{sido}'는 TourAPI 지역코드 매핑이 없습니다.")
    else:
        try:
            items = fetch_festivals(area_code)
        except TourAPIError as e:
            st.error(str(e))
            items = []
        if sigungu:
            items = [x for x in items if sigungu in (x.get("addr1", "") + x.get("addr2", ""))]
        _render_tour_items(items, "진행 중인 축제가 없습니다.")
