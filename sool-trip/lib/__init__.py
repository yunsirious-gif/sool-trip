"""Streamlit Cloud secrets / 로컬 .env → os.environ 브리지.

배포 환경(secrets.toml)과 로컬(.env) 양쪽 모두에서
어떤 lib 모듈이 import되든 환경변수가 채워지도록 한다.
"""

import os

# 로컬: .env → os.environ
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 배포: st.secrets → os.environ
try:
    import streamlit as st
    _secrets = getattr(st, "secrets", {})
    for _key in ("GEMINI_API_KEY", "PUBLIC_DATA_API_KEY", "APP_PASSWORD"):
        if _key in _secrets and not os.environ.get(_key):
            os.environ[_key] = str(_secrets[_key])
except Exception:
    pass
