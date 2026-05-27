"""양조장 시군구 좌표를 Nominatim에서 받아 JSON으로 저장.

Streamlit Cloud 재배포 시에도 좌표가 즉시 유효하도록 정적 JSON을 git에 commit해두는 용도.
실행: python3 scripts/build_sigungu_coords.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "sigungu_coords.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "sool-trip-app/0.1 (https://example.local)"}


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


def collect_sigungu_keys() -> list[str]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from load_data import VISIT_CSV, PRODUCT_CSV, load_visit, load_products, build_breweries
    v = load_visit(VISIT_CSV)
    p = load_products(PRODUCT_CSV)
    b = build_breweries(v, p)
    keys: set[str] = set()
    for _, row in b.iterrows():
        sido, sg = row["sido"], row["sigungu"]
        if sido:
            keys.add(sido)
        if sido and sg:
            keys.add(f"{sg} {sido}")
    return sorted(keys)


def main() -> None:
    existing: dict[str, list[float] | None] = {}
    if OUT_PATH.exists():
        existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))

    keys = collect_sigungu_keys()
    todo = [k for k in keys if k not in existing]
    print(f"전체 키: {len(keys)} / 기존: {len(existing)} / 신규: {len(todo)}")

    for i, q in enumerate(todo, 1):
        latlon = geocode(q)
        existing[q] = list(latlon) if latlon else None
        marker = f"{latlon[0]:.4f},{latlon[1]:.4f}" if latlon else "—"
        print(f"  [{i}/{len(todo)}] {q}: {marker}")
        OUT_PATH.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        time.sleep(1.1)

    hit = sum(1 for v in existing.values() if v)
    print(f"\n✅ 저장 완료 → {OUT_PATH} (성공 {hit}/{len(existing)})")


if __name__ == "__main__":
    main()
