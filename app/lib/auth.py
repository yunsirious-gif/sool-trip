import streamlit as st


def require_password() -> bool:
    if st.session_state.get("authed"):
        return True

    st.markdown("## 부산브리핑")
    st.caption("사무실 비밀번호를 입력하세요.")

    with st.form("login", clear_on_submit=False):
        pwd = st.text_input("비밀번호", type="password", label_visibility="collapsed")
        submitted = st.form_submit_button("입장", use_container_width=True)

    if submitted:
        expected = st.secrets.get("APP_PASSWORD")
        if not expected:
            st.error("secrets.toml에 APP_PASSWORD가 없습니다.")
            return False
        if pwd == expected:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    return False
