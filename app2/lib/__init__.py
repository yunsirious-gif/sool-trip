"""Streamlit Cloud secrets → os.environ 브리지.

배포 환경에선 `.env` 파일이 없고 `st.secrets`만 있다.
lib의 어떤 모듈이든 import되는 순간 환경변수를 채워둔다.
"""

import os

try:
    import streamlit as st
    _secrets = getattr(st, "secrets", {})
    for _key in ("GEMINI_API_KEY", "PUBLIC_DATA_API_KEY"):
        if _key in _secrets and not os.environ.get(_key):
            os.environ[_key] = str(_secrets[_key])
except Exception:
    pass
