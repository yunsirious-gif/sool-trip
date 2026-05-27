import sqlite3
from pathlib import Path

import streamlit as st


def _resolve_db_path() -> Path:
    raw = st.secrets.get("DB_PATH", "../02_데이터베이스/bptc_realestate.db")
    p = Path(raw)
    if not p.is_absolute():
        p = (Path(__file__).resolve().parent.parent / p).resolve()
    if not p.exists():
        raise FileNotFoundError(
            f"DB 파일을 찾을 수 없습니다: {p}\n"
            f".streamlit/secrets.toml의 DB_PATH를 확인해주세요."
        )
    return p


@st.cache_resource(show_spinner=False)
def get_conn() -> sqlite3.Connection:
    path = _resolve_db_path()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def query_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return get_conn().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()):
    return get_conn().execute(sql, params).fetchone()
