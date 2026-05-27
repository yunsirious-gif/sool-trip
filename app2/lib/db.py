import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "breweries.db"


def _ensure_db() -> None:
    """배포 환경에서 DB가 없으면 CSV로부터 빌드."""
    if DB_PATH.exists():
        return
    from scripts.load_data import main as load_main
    with st.spinner("최초 1회 양조장 DB를 빌드하는 중… (약 5초)"):
        load_main()


@st.cache_resource
def get_conn() -> sqlite3.Connection:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
