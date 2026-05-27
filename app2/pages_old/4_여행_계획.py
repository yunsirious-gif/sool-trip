"""여행 계획 — 일자 + 출발지 → 거리순 양조장 + 일자별 날씨 + 가이드."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from lib.brewery import get_brewery_products
from lib.db import get_conn
from lib.gemini import weather_aware_plan
from lib.geocoding import geocode, geocode_sigungu
from lib.geo import list_sido, list_sigungu
from lib.travel import haversine_km, quick_drive_estimate
from lib.weather import forecast, summarize_period

st.set_page_config(page_title="여행 계획 · 술여행", page_icon="🗓️", layout="wide")
st.title("🗓️ 여행 계획")
st.caption("출발지·일자를 정하면 거리 순으로 양조장을 보여주고, 일자별 날씨와 함께 즐기는 법을 알려드려요.")

today = date.today()
max_date = today + timedelta(days=15)

with st.form("plan_form"):
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        start_d = st.date_input("출발일", value=today, min_value=today, max_value=max_date)
    with col_b:
        end_d = st.date_input("귀가일", value=today + timedelta(days=1),
                               min_value=today, max_value=max_date)
    with col_c:
        only_visitable = st.checkbox("체험 가능 양조장만", value=True)

    col_d, col_e = st.columns([1, 2])
    with col_d:
        origin_sido = st.selectbox("출발 시/도", ["(자유 입력)"] + list_sido())
    with col_e:
        if origin_sido != "(자유 입력)":
            origin_sigungu = st.selectbox("출발 시/군/구", ["(전체)"] + list_sigungu(origin_sido))
            origin = (f"{origin_sigungu} {origin_sido}" if origin_sigungu != "(전체)"
                       else origin_sido)
        else:
            origin = st.text_input("출발 위치 (자유)",
                                    value=st.session_state.get("origin_detail", ""),
                                    placeholder="예: 서울시 강남구")
            st.session_state["origin_detail"] = origin

    top_n = st.slider("거리 순 상위 N개", 3, 10, 5)
    submitted = st.form_submit_button("✨ 일정 + 거리순 + 날씨 보기",
                                        type="primary", width="stretch")

if not submitted:
    st.info("출발지와 일자를 정하고 '보기'를 눌러주세요.")
    st.stop()

if end_d < start_d:
    st.error("귀가일이 출발일보다 빠릅니다.")
    st.stop()
if not origin.strip():
    st.error("출발지를 입력하세요.")
    st.stop()

dates_label = f"{start_d.isoformat()} ~ {end_d.isoformat()} ({(end_d - start_d).days + 1}일)"
st.markdown(f"### 🚗 출발: {origin}  ·  📅 {dates_label}")

# 1. 출발지 좌표
with st.spinner("출발지 좌표 변환 중…"):
    origin_latlon = geocode(origin)
if not origin_latlon:
    st.error(f"'{origin}' 좌표를 찾을 수 없습니다. 시/군/구 단위로 다시 시도해 주세요.")
    st.stop()

# 2. 후보 양조장
sql = "SELECT * FROM breweries WHERE sigungu != ''"
if only_visitable:
    sql += " AND visitable = 1"
candidates = [dict(r) for r in get_conn().execute(sql).fetchall()]

# 3. 시군구 단위로 좌표 일괄 변환 (캐시 활용)
sigungu_keys = {(b["sido"], b["sigungu"]) for b in candidates}
sigungu_coords: dict[tuple[str, str], tuple[float, float]] = {}
progress = st.progress(0.0, text="양조장 좌표 매핑 중 (캐시 활용)…")
for i, (sido, sigungu) in enumerate(sigungu_keys, 1):
    coord = geocode_sigungu(sido, sigungu)
    if coord:
        sigungu_coords[(sido, sigungu)] = coord
    progress.progress(i / len(sigungu_keys),
                       text=f"양조장 좌표 매핑 중… ({i}/{len(sigungu_keys)})")
progress.empty()

# 4. 거리 계산 + 정렬
ranked = []
for b in candidates:
    coord = sigungu_coords.get((b["sido"], b["sigungu"]))
    if not coord:
        continue
    dist = haversine_km(origin_latlon[0], origin_latlon[1], coord[0], coord[1])
    b["_lat"], b["_lon"] = coord
    b["_distance_km"] = dist
    b["_drive_min"] = quick_drive_estimate(dist)
    ranked.append(b)

ranked.sort(key=lambda x: x["_distance_km"])
top = ranked[:top_n]

if not top:
    st.warning("거리 계산이 가능한 양조장이 없습니다. 캐시 적재가 안 끝났을 수 있어요.")
    st.stop()

st.markdown(f"### 🏆 거리순 상위 {len(top)}곳")
for rank, b in enumerate(top, 1):
    days = forecast(b["_lat"], b["_lon"], start_d, end_d)
    summary = summarize_period(days)
    rainy_emoji = "☔" if any(d.is_rainy for d in days) else "☀️"

    with st.container(border=True):
        head_l, head_r = st.columns([3, 1])
        with head_l:
            visit_badge = "🟢 체험 가능" if b["visitable"] else "⚪ 체험 정보 없음"
            st.markdown(f"#### {rank}. {b['name']}  ·  {visit_badge}")
            st.caption(f"{b['address']}")
        with head_r:
            hours = b["_drive_min"] // 60
            mins = b["_drive_min"] % 60
            time_label = f"{hours}시간 {mins}분" if hours else f"{mins}분"
            st.metric("거리", f"{b['_distance_km']:.0f} km",
                       f"차로 약 {time_label} (직선 기준)")

        st.markdown(f"**{rainy_emoji} 기간 날씨 한 줄:** {summary}")

        if days:
            with st.expander("📅 일자별 날씨 자세히"):
                for d in days:
                    st.markdown(f"- **{d.date}**: {d.one_line()}")

        guide_key = f"guide_{b['id']}"
        if st.button(f"🤖 이 양조장에서 어떻게 즐길지 보기", key=guide_key):
            with st.spinner("Gemini 가이드 작성 중…"):
                products = get_brewery_products(b["id"])
                guide = weather_aware_plan(b, days, dates_label, products)
            st.markdown(guide)
