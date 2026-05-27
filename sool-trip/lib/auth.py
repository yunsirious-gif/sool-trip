"""간단 비밀번호 게이트 — 메인 페이지(hero 배경) 톤과 맞춤."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import streamlit as st


_HERO_IMG = Path(__file__).resolve().parent.parent / "static" / "hero_bg.png"


def _bg_css() -> str:
    if _HERO_IMG.exists():
        b64 = base64.b64encode(_HERO_IMG.read_bytes()).decode()
        return f"url(data:image/png;base64,{b64}) center/cover"
    return "linear-gradient(180deg, #2a1a4f 0%, #6b3a4f 55%, #d97a4a 100%)"


def _expected_password() -> str:
    try:
        secrets = getattr(st, "secrets", {})
        if "APP_PASSWORD" in secrets:
            return str(secrets["APP_PASSWORD"])
    except Exception:
        pass
    return os.getenv("APP_PASSWORD", "")


def _render_gate_ui() -> None:
    fireflies = "".join(f'<div class="firefly f{i}"></div>' for i in range(1, 9))
    st.markdown(
        f"""
<style>
.stApp {{
    background: {_bg_css()};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ display: none !important; }}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{ display: none !important; }}
.stApp::before {{
    content: "";
    position: fixed; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.65) 100%);
    pointer-events: none;
    z-index: 0;
}}
[data-testid="stMainBlockContainer"] {{ position: relative; z-index: 1; }}

/* 타이틀 — intro-title 스타일 그대로 */
.gate-title {{
    color: #fff;
    font-weight: 700;
    text-align: center;
    line-height: 1.3;
    margin: 14vh auto 1rem auto;
    max-width: 480px;
    padding: .7rem 1.4rem;
    background: rgba(0,0,0,0.38);
    backdrop-filter: blur(3px);
    border-radius: 14px;
    text-shadow: 0 2px 12px rgba(0,0,0,0.85);
    font-size: clamp(1.4rem, 2.6vw, 2rem);
}}
.gate-sub {{
    color: #fff;
    text-align: center;
    margin: 0 auto 2rem auto;
    max-width: 420px;
    padding: .55rem 1.1rem;
    background: rgba(0,0,0,0.3);
    backdrop-filter: blur(3px);
    border-radius: 10px;
    text-shadow: 0 1px 8px rgba(0,0,0,0.85);
    font-size: clamp(.85rem, 1.2vw, 1rem);
}}

/* 입력 위젯 — 메인과 동일 톤 (반투명 흰 배경) */
.stApp [data-baseweb="input"] {{
    background-color: rgba(255,255,255,0.93) !important;
    border-radius: 10px;
}}
.stApp [data-baseweb="input"] input {{
    color: #2a2218 !important;
    text-shadow: none !important;
    text-align: center;
    font-size: 1.1rem;
    letter-spacing: 0.3em;
}}
/* 위젯 라벨 숨김 */
.stApp [data-testid="stWidgetLabel"] {{ display: none; }}

/* 에러 메시지 가독성 */
.stApp [data-testid="stAlert"] {{
    background: rgba(180, 30, 30, 0.85) !important;
    color: #fff !important;
    border-radius: 8px;
    max-width: 420px;
    margin: 0 auto;
}}
.stApp [data-testid="stAlert"] * {{ color: #fff !important; }}

/* 반딧불 — 8마리 */
.firefly {{
    position: fixed; width: 5px; height: 5px;
    background: #fff7c2; border-radius: 50%;
    box-shadow: 0 0 6px 2px #fff7c2,
                0 0 12px 4px rgba(255,232,128,0.55),
                0 0 22px 6px rgba(255,210,90,0.25);
    pointer-events: none; opacity: 0; z-index: 0;
}}
@keyframes flyA {{
    0%   {{ transform: translate(0,0) scale(.7); opacity: 0; }}
    15%  {{ opacity: 1; }} 85% {{ opacity: 1; }}
    100% {{ transform: translate(240px,10px) scale(.6); opacity: 0; }}
}}
@keyframes flyB {{
    0%   {{ transform: translate(0,0) scale(.8); opacity: 0; }}
    20%  {{ opacity: 1; }} 80% {{ opacity: 1; }}
    100% {{ transform: translate(-180px,20px) scale(.5); opacity: 0; }}
}}
@keyframes flyC {{
    0%   {{ transform: translate(0,0) scale(.6); opacity: 0; }}
    25%  {{ opacity: 1; }} 75% {{ opacity: 1; }}
    100% {{ transform: translate(140px,-30px) scale(.5); opacity: 0; }}
}}
@keyframes glow {{
    0%, 100% {{ filter: brightness(.7); }}
    50%      {{ filter: brightness(1.6); }}
}}
.firefly.f1 {{ top: 30%; left: 12%; animation: flyA 11s linear infinite, glow 2.1s ease-in-out infinite; }}
.firefly.f2 {{ top: 65%; left: 22%; animation: flyB 13s linear 1s infinite, glow 1.7s ease-in-out infinite; }}
.firefly.f3 {{ top: 45%; left: 35%; animation: flyC 10s linear 2s infinite, glow 2.4s ease-in-out infinite; }}
.firefly.f4 {{ top: 70%; left: 50%; animation: flyA 12s linear 3s infinite, glow 1.9s ease-in-out infinite; }}
.firefly.f5 {{ top: 35%; left: 62%; animation: flyB 14s linear .5s infinite, glow 2.2s ease-in-out infinite; }}
.firefly.f6 {{ top: 60%; left: 78%; animation: flyC 11s linear 4s infinite, glow 1.6s ease-in-out infinite; }}
.firefly.f7 {{ top: 25%; left: 85%; animation: flyA 13s linear 1.5s infinite, glow 2.5s ease-in-out infinite; }}
.firefly.f8 {{ top: 80%; left: 38%; animation: flyB 12s linear 2.5s infinite, glow 1.8s ease-in-out infinite; }}
</style>
{fireflies}
<div class="gate-title">🍶 술여행</div>
<div class="gate-sub">비밀번호를 입력해주세요</div>
""",
        unsafe_allow_html=True,
    )


def gate() -> None:
    """본문 위에서 호출. 인증 실패 시 st.stop()."""
    if st.session_state.get("_authed"):
        return

    expected = _expected_password()
    if not expected:
        return

    _render_gate_ui()

    # 가운데 정렬된 좁은 입력칸
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pw = st.text_input(
            "비밀번호",
            type="password",
            key="_pw_input",
            placeholder="● ● ● ●",
            label_visibility="collapsed",
        )
        if pw == expected:
            st.session_state["_authed"] = True
            st.rerun()
        elif pw:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()
