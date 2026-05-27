"""가고 싶은 여행지 — to-do 리스트."""

from __future__ import annotations

from lib.db import get_conn

CATEGORIES = {
    "관광지": {"emoji": "🗺️", "color": [80, 150, 255]},
    "식당": {"emoji": "🍽️", "color": [255, 110, 110]},
    "카페": {"emoji": "☕", "color": [200, 150, 80]},
    "양조장": {"emoji": "🏭", "color": [200, 100, 200]},
    "숙소": {"emoji": "🏨", "color": [100, 200, 150]},
    "기타": {"emoji": "📌", "color": [120, 120, 120]},
}


def init_table() -> None:
    get_conn().execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            category TEXT,
            name TEXT NOT NULL,
            address TEXT,
            lat REAL,
            lon REAL,
            memo TEXT,
            priority INTEGER DEFAULT 3,
            visited INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    get_conn().commit()


def add_item(*, region: str, category: str, name: str,
              address: str = "", lat: float | None = None, lon: float | None = None,
              memo: str = "", priority: int = 3) -> int:
    init_table()
    cur = get_conn().execute(
        """INSERT INTO wishlist(region, category, name, address, lat, lon, memo, priority)
           VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
        (region, category, name, address, lat, lon, memo, priority),
    )
    get_conn().commit()
    return cur.lastrowid


def list_items(region: str = "") -> list[dict]:
    init_table()
    if region:
        rows = get_conn().execute(
            "SELECT * FROM wishlist WHERE region = ? ORDER BY visited, priority DESC, datetime(created_at) DESC",
            (region,),
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT * FROM wishlist ORDER BY visited, region, priority DESC, datetime(created_at) DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def list_regions() -> list[str]:
    init_table()
    rows = get_conn().execute(
        "SELECT DISTINCT region FROM wishlist WHERE region != '' ORDER BY region"
    ).fetchall()
    return [r["region"] for r in rows]


def delete_item(item_id: int) -> None:
    get_conn().execute("DELETE FROM wishlist WHERE id = ?", (item_id,))
    get_conn().commit()


def toggle_visited(item_id: int, visited: bool) -> None:
    get_conn().execute(
        "UPDATE wishlist SET visited = ? WHERE id = ?",
        (1 if visited else 0, item_id),
    )
    get_conn().commit()
