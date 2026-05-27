from datetime import datetime

import streamlit as st

from lib.auth import require_password
from lib.charts import bar_ranking, line_chart_rent, line_chart_trade, line_population
from lib.format import format_won
from lib.queries import (
    complex_info,
    gu_infra,
    gu_population,
    gu_ranking,
    rent_history,
    search_complex,
    trade_history,
)

st.set_page_config(page_title="단지 브리핑 · 부산브리핑", page_icon="🏠", layout="wide")

if not require_password():
    st.stop()

if "recent_apts" not in st.session_state:
    st.session_state["recent_apts"] = []


def _push_recent(name: str) -> None:
    lst = st.session_state["recent_apts"]
    if name in lst:
        lst.remove(name)
    lst.insert(0, name)
    st.session_state["recent_apts"] = lst[:5]


with st.sidebar:
    st.markdown("### 🕒 최근 본 단지")
    if not st.session_state["recent_apts"]:
        st.caption("아직 없음")
    else:
        for nm in st.session_state["recent_apts"]:
            if st.button(nm, key=f"recent_{nm}", use_container_width=True):
                st.query_params["apt"] = nm
                st.rerun()

st.title("🏠 단지 브리핑")

query = st.text_input("단지명 검색", placeholder="예: 엘시티, 해운대 I PARK")

selected: str | None = st.query_params.get("apt")

if query:
    matches = search_complex(query)
    if matches.empty:
        st.warning(f"'{query}'에 해당하는 단지를 찾을 수 없습니다. 검색어를 확인해주세요.")
        st.stop()
    if len(matches) == 1:
        selected = matches.iloc[0]["apt_name"]
    else:
        options = [
            f"{r.apt_name}  ({r.gu_name} · 거래 {r.trade_count}회)"
            for r in matches.itertuples()
        ]
        choice = st.selectbox("단지 선택", options, index=0)
        selected = matches.iloc[options.index(choice)]["apt_name"]

if not selected:
    st.info("단지명을 입력하면 시세 · 전월세 · 학군 · 인구 추이가 한 페이지로 표시됩니다.")
    st.stop()

info = complex_info(selected)
if not info:
    st.error(f"단지 정보를 찾을 수 없습니다: {selected}")
    st.stop()

_push_recent(selected)

st.markdown(f"## {info['apt_name']}")
st.caption(
    f"{info['gu_name']} · {info['road_name'] or '도로명 정보 없음'} · "
    f"건축년도 {info['build_year'] or '—'} · 총 거래 {info['trade_count']:,}회"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("자치구", info["gu_name"])
c2.metric("건축년도", info["build_year"] or "—")
c3.metric("평형 범위", f"{info['min_area']:.0f} ~ {info['max_area']:.0f}㎡"
          if info["min_area"] else "—")
c4.metric("총 거래", f"{info['trade_count']:,}회")

st.markdown("---")
trade = trade_history(selected)
rent = rent_history(selected)

cA, cB = st.columns(2)
with cA:
    st.plotly_chart(line_chart_trade(trade), use_container_width=True)
    if not trade.empty:
        latest = trade.iloc[-1]
        st.caption(f"가장 최근 거래: {latest['deal_date'].date()} · "
                   f"{format_won(latest['dealAmount'])} · "
                   f"{latest['excluUseAr']:.1f}㎡ · {latest['floor']}층")
with cB:
    st.plotly_chart(line_chart_rent(rent), use_container_width=True)

st.markdown("---")
st.subheader(f"📊 {info['gu_name']} 내 거래량 순위")
ranking = gu_ranking(info["gu_name"], limit=10)
st.plotly_chart(bar_ranking(ranking, highlight_apt=selected), use_container_width=True)

st.markdown("---")
st.subheader(f"🏫 {info['gu_name']} 인프라 요약")
infra = gu_infra(info["gu_name"])
cols = st.columns(len(infra))
for col, (label, n) in zip(cols, infra.items()):
    col.metric(label, f"{n:,}")

st.markdown("---")
st.subheader(f"👥 {info['gu_name']} 인구 추이")
pop = gu_population(info["gu_name"])
st.plotly_chart(line_population(pop), use_container_width=True)
if not pop.empty:
    first, last = pop.iloc[0], pop.iloc[-1]
    delta = last["total_pop"] - first["total_pop"]
    pct = delta / first["total_pop"] * 100 if first["total_pop"] else 0
    st.caption(f"{first['ref_date'].date()} → {last['ref_date'].date()}: "
               f"{int(last['total_pop']):,}명 ({delta:+,}명 · {pct:+.1f}%)")

st.markdown("---")
st.subheader("📄 PDF 다운로드")
st.caption(f"생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
try:
    from lib.pdf import render_briefing_pdf
    pdf_bytes = render_briefing_pdf(info, trade, rent, ranking, infra, pop)
    st.download_button(
        label="📥 브리핑 PDF 다운로드",
        data=pdf_bytes,
        file_name=f"브리핑_{selected}_{datetime.now():%Y%m%d}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
except ImportError:
    st.info("PDF 모듈은 M3에서 활성화됩니다.")
except Exception as e:
    st.error(f"PDF 생성 실패: {e}")
