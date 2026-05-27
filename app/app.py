import streamlit as st

from lib.auth import require_password
from lib.db import get_conn

st.set_page_config(
    page_title="부산브리핑",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not require_password():
    st.stop()

st.title("🏠 부산브리핑")
st.caption("부산 부동산 중개인용 단지 브리핑 도구 · 국토교통부 실거래가 (2021-01 ~ 2026-05)")

try:
    row = get_conn().execute("SELECT COUNT(*) AS n FROM apt_complex").fetchone()
    st.success(f"DB 연결 정상 — 등록된 단지 {row['n']:,}개")
except Exception as e:
    st.error(f"DB 연결 실패: {e}")
    st.stop()

st.markdown("---")
st.markdown(
    """
    ### 시작하기
    왼쪽 사이드바에서 **단지 브리핑** 페이지로 이동해 단지명을 검색하세요.

    상담 자리에서 손님과 함께 시세·전월세·학군·인구 추이를 한 페이지로 보고
    필요하면 PDF로 다운받아 카카오톡으로 전송할 수 있습니다.
    """
)
