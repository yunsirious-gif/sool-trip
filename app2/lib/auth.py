"""간단 비밀번호 게이트.

`APP_PASSWORD`가 secrets/env에 설정돼 있으면 입력 화면이 먼저 뜨고,
일치할 때만 본문이 렌더된다. 미설정이면 게이트 비활성(개발용).
"""

from __future__ import annotations

import os

import streamlit as st


def _expected_password() -> str:
    try:
        secrets = getattr(st, "secrets", {})
        if "APP_PASSWORD" in secrets:
            return str(secrets["APP_PASSWORD"])
    except Exception:
        pass
    return os.getenv("APP_PASSWORD", "")


def gate() -> None:
    """본문 위에서 호출. 인증 실패 시 st.stop()."""
    if st.session_state.get("_authed"):
        return

    expected = _expected_password()
    if not expected:
        return

    st.markdown("### 🔒 비밀번호를 입력해주세요")
    pw = st.text_input(
        "비밀번호",
        type="password",
        key="_pw_input",
        label_visibility="collapsed",
        placeholder="비밀번호",
    )
    if pw == expected:
        st.session_state["_authed"] = True
        st.rerun()
    elif pw:
        st.error("비밀번호가 틀렸습니다.")
    st.stop()
