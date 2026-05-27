"""AI 코스 추천 — Gemini가 양조장+관광지+맛집+축제를 묶어 시간순 코스 생성."""

import streamlit as st

from lib.brewery import find_breweries
from lib.gemini import build_prompt, generate_course
from lib.geo import TOURAPI_AREA_CODE
from lib.tourapi import CONTENT_TYPES, TourAPIError, fetch_by_area, fetch_festivals

st.set_page_config(page_title="AI 코스 추천 · 술여행", page_icon="🤖", layout="wide")

sido = st.session_state.get("sido")
sigungu = st.session_state.get("sigungu")

if not sido:
    st.warning("먼저 홈에서 지역을 선택해 주세요.")
    st.page_link("app.py", label="← 홈으로 돌아가기")
    st.stop()

region_label = f"{sido} {sigungu}".strip() if sigungu else sido
st.title(f"🤖 AI 코스 추천")
st.caption(f"{region_label}에서의 술여행 코스를 Gemini가 짜드립니다.")

with st.form("course_form"):
    col_a, col_b = st.columns(2)
    with col_a:
        duration = st.selectbox(
            "일정 길이",
            options=["당일치기", "1박 2일", "2박 3일"],
            index=1,
        )
    with col_b:
        only_visitable = st.checkbox("체험 가능한 양조장만 후보로", value=True)

    taste = st.text_area(
        "취향 · 선호 (자유롭게)",
        value="단맛 막걸리 좋아함, 자연 풍경 위주, 매운 음식 안 좋아함",
        height=80,
    )
    submitted = st.form_submit_button("✨ 코스 만들기", width="stretch", type="primary")

if not submitted:
    st.info("취향을 입력하고 '코스 만들기'를 눌러주세요.")
    st.stop()

with st.status("후보 데이터 수집 중…", expanded=True) as status:
    st.write("양조장 조회…")
    breweries = find_breweries(sido, sigungu, visitable_only=only_visitable)
    if not breweries and only_visitable:
        st.write("체험 가능 양조장이 없어 일반 양조장으로 확장합니다.")
        breweries = find_breweries(sido, sigungu, visitable_only=False)

    area_code = TOURAPI_AREA_CODE.get(sido)
    spots, foods, festivals = [], [], []
    if area_code:
        try:
            st.write("관광지 조회…")
            spots = fetch_by_area(area_code, CONTENT_TYPES["관광지"])
            st.write("맛집 조회…")
            foods = fetch_by_area(area_code, CONTENT_TYPES["맛집"])
            st.write("축제 조회…")
            festivals = fetch_festivals(area_code)
        except TourAPIError as e:
            st.warning(f"TourAPI 일부 실패: {e}")
    else:
        st.warning(f"'{sido}'에 대한 TourAPI 코드 매핑이 없습니다. 양조장만으로 추천을 생성합니다.")

    if sigungu:
        spots = [x for x in spots if sigungu in (x.get("addr1", "") + x.get("addr2", ""))]
        foods = [x for x in foods if sigungu in (x.get("addr1", "") + x.get("addr2", ""))]
        festivals = [x for x in festivals if sigungu in (x.get("addr1", "") + x.get("addr2", ""))]

    status.update(label="Gemini에 요청 중…", state="running")
    prompt = build_prompt(region_label, taste, duration, breweries, spots, foods, festivals)
    try:
        result = generate_course(prompt)
        status.update(label="완성!", state="complete")
    except Exception as e:
        status.update(label="실패", state="error")
        st.error(f"Gemini 호출 실패: {e}")
        st.stop()

st.markdown("---")
st.markdown(result)

with st.expander("🔍 Gemini에 전달된 후보 데이터 (디버그)"):
    st.code(prompt, language="markdown")
