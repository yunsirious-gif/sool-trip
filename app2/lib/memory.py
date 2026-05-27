"""여행 추억 저장 — SQLite memories 테이블."""

from __future__ import annotations

from datetime import date

from lib.db import get_conn


def init_table() -> None:
    get_conn().execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            region TEXT,
            visited_date TEXT,
            rating INTEGER,
            food TEXT,
            drink TEXT,
            comment TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    get_conn().commit()


def add_memory(*, title: str, region: str = "", visited_date: date | None = None,
                rating: int = 5, food: str = "", drink: str = "",
                comment: str = "") -> int:
    init_table()
    cur = get_conn().execute(
        """INSERT INTO memories(title, region, visited_date, rating, food, drink, comment)
           VALUES(?, ?, ?, ?, ?, ?, ?)""",
        (title, region,
         visited_date.isoformat() if visited_date else None,
         rating, food, drink, comment),
    )
    get_conn().commit()
    return cur.lastrowid


def list_memories() -> list[dict]:
    init_table()
    rows = get_conn().execute(
        "SELECT * FROM memories ORDER BY datetime(created_at) DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_memory(memory_id: int) -> None:
    get_conn().execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    get_conn().commit()
