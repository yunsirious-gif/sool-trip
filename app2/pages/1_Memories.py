"""여행 추억 — 좋았던 곳·먹은 것·코멘트 저장."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from lib.memory import add_memory, delete_memory, list_memories

st.set_page_config(page_title="여행 추억", page_icon="📔", layout="wide")
st.markdown(
    "<style>[data-testid='stSidebarNav']{display:none;}</style>",
    unsafe_allow_html=True,
)
if st.button("← 메인으로"):
    st.switch_page("app.py")

st.title("📔 여행 추억")
st.caption("좋았던 여행지, 먹은 음식과 술, 한 줄 코멘트를 남겨두세요.")

# ─── 새 추억 추가 ────────────────────────────────────
with st.expander("✏️ 새 추억 남기기", expanded=False):
    with st.form("add_memory"):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("제목 *", placeholder="예: 영천 와이너리 야영")
            region = st.text_input("지역", placeholder="예: 경상북도 영천시")
        with c2:
            visited_date = st.date_input("다녀온 날짜", value=date.today())
            rating = st.slider("별점", 1, 5, 5)

        c3, c4 = st.columns(2)
        with c3:
            food = st.text_input("먹은 음식", placeholder="예: 미나리 삼겹살")
        with c4:
            drink = st.text_input("마신 술", placeholder="예: 청도 감와인")

        comment = st.text_area("한 줄 코멘트",
                                placeholder="어땠는지 자유롭게…",
                                height=80)

        if st.form_submit_button("💾 저장", type="primary", width="stretch"):
            if not title.strip():
                st.error("제목은 필수입니다.")
            else:
                add_memory(
                    title=title.strip(), region=region.strip(),
                    visited_date=visited_date, rating=rating,
                    food=food.strip(), drink=drink.strip(),
                    comment=comment.strip(),
                )
                st.success("저장됐어요!")
                st.rerun()

# ─── 저장된 추억 목록 ────────────────────────────────
st.markdown("---")
memories = list_memories()

if not memories:
    st.info("아직 남긴 추억이 없어요. 위 **'✏️ 새 추억 남기기'**를 펼쳐 첫 추억을 남겨보세요.")
    st.stop()

st.subheader(f"📚 저장된 추억 — {len(memories)}건")

# 표 형식 요약
table_rows = [{
    "다녀온 날": m.get("visited_date") or "",
    "제목": m.get("title") or "",
    "지역": m.get("region") or "",
    "별점": "⭐" * (m.get("rating") or 0),
    "음식": m.get("food") or "",
    "술": m.get("drink") or "",
} for m in memories]
st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

st.markdown("---")
st.subheader("🗂️ 카드로 보기")
for m in memories:
    with st.container(border=True):
        head_l, head_r = st.columns([4, 1])
        with head_l:
            stars = "⭐" * (m.get("rating") or 0)
            st.markdown(f"### {m.get('title')}  ·  {stars}")
            meta_bits = []
            if m.get("visited_date"):
                meta_bits.append(f"📅 {m['visited_date']}")
            if m.get("region"):
                meta_bits.append(f"📍 {m['region']}")
            if meta_bits:
                st.caption("  ·  ".join(meta_bits))
        with head_r:
            if st.button("🗑️ 삭제", key=f"del_{m['id']}", width="stretch"):
                delete_memory(m["id"])
                st.rerun()

        bits = []
        if m.get("food"):
            bits.append(f"**🍴 음식**: {m['food']}")
        if m.get("drink"):
            bits.append(f"**🍶 술**: {m['drink']}")
        if bits:
            st.markdown("  ·  ".join(bits))
        if m.get("comment"):
            st.markdown(f"> {m['comment']}")
        st.caption(f"_저장: {m.get('created_at','')}_")
