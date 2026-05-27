"""모든 양조장 시군구의 좌표를 미리 캐시. Nominatim 1 req/sec.

체험 가능 양조장(visitable=1)만 우선 캐시, 나머지는 옵션.
"""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "breweries.db"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "sool-trip-app/0.1 (https://example.local)"}


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geocache (
            query TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            ts INTEGER
        )
    """)


def geocode(query: str) -> tuple[float, float] | None:
    try:
        r = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1,
                    "countrycodes": "kr", "accept-language": "ko"},
            headers=HEADERS, timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ❌ {query}: {e}")
        return None
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def main(all_breweries: bool = False) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_table(conn)

    if all_breweries:
        rows = conn.execute(
            "SELECT DISTINCT sido, sigungu FROM breweries WHERE sigungu != ''"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT sido, sigungu FROM breweries "
            "WHERE visitable=1 AND sigungu != ''"
        ).fetchall()

    cached = {r["query"] for r in conn.execute("SELECT query FROM geocache")}

    todo = []
    for r in rows:
        query = f"{r['sigungu']} {r['sido']}"
        if query not in cached:
            todo.append(query)

    print(f"전체 시군구: {len(rows)}, 캐시 됨: {len(rows) - len(todo)}, 신규: {len(todo)}")

    for i, query in enumerate(todo, 1):
        latlon = geocode(query)
        if latlon:
            conn.execute(
                "INSERT OR REPLACE INTO geocache(query, lat, lon, ts) "
                "VALUES (?, ?, ?, strftime('%s','now'))",
                (query, latlon[0], latlon[1]),
            )
            print(f"  [{i}/{len(todo)}] {query}: {latlon[0]:.4f}, {latlon[1]:.4f}")
        else:
            conn.execute(
                "INSERT OR REPLACE INTO geocache(query, lat, lon, ts) "
                "VALUES (?, NULL, NULL, strftime('%s','now'))",
                (query,),
            )
            print(f"  [{i}/{len(todo)}] {query}: ❌")
        conn.commit()
        time.sleep(1.1)

    print("\n✅ 캐시 적재 완료")


if __name__ == "__main__":
    main(all_breweries="--all" in sys.argv)
