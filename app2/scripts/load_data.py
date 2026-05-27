"""CSV 두 개를 정제 → SQLite(breweries.db)로 적재.

찾아가는 양조장(체험 가능 양조장)과 전통주 정보(술 상세)를 양조장명으로 묶어
breweries / products 두 테이블로 저장한다.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "breweries.db"

VISIT_CSV = RAW_DIR / "한국농수산식품유통공사_찾아가는양조장정보_20241231 (1).csv"
PRODUCT_CSV = RAW_DIR / "한국농수산식품유통공사_전통주정보_20241231.csv"

SIDO_NORMALIZE = {
    "서울특별시": "서울특별시", "서울시": "서울특별시", "서울": "서울특별시",
    "부산광역시": "부산광역시", "부산시": "부산광역시", "부산": "부산광역시",
    "대구광역시": "대구광역시", "대구시": "대구광역시", "대구": "대구광역시",
    "인천광역시": "인천광역시", "인천시": "인천광역시", "인천": "인천광역시",
    "광주광역시": "광주광역시", "광주시": "광주광역시", "광주": "광주광역시",
    "대전광역시": "대전광역시", "대전시": "대전광역시", "대전": "대전광역시",
    "울산광역시": "울산광역시", "울산시": "울산광역시", "울산": "울산광역시",
    "세종특별자치시": "세종특별자치시", "세종시": "세종특별자치시", "세종": "세종특별자치시",
    "경기도": "경기도", "경기": "경기도",
    "강원특별자치도": "강원특별자치도", "강원도": "강원특별자치도", "강원": "강원특별자치도",
    "충청북도": "충청북도", "충북": "충청북도",
    "충청남도": "충청남도", "충남": "충청남도",
    "전북특별자치도": "전북특별자치도", "전라북도": "전북특별자치도", "전북": "전북특별자치도",
    "전라남도": "전라남도", "전남": "전라남도",
    "경상북도": "경상북도", "경북": "경상북도",
    "경상남도": "경상남도", "경남": "경상남도",
    "제주특별자치도": "제주특별자치도", "제주도": "제주특별자치도", "제주": "제주특별자치도",
}

SIDO_KEYWORDS = sorted(SIDO_NORMALIZE.keys(), key=len, reverse=True)


def parse_address(addr: str) -> tuple[str, str]:
    """주소 문자열에서 (시/도, 시/군/구) 추출. 우편번호·법인명 prefix 제거."""
    if not isinstance(addr, str) or not addr.strip():
        return "", ""
    cleaned = re.sub(r"^\(\d+\)\s*", "", addr.strip())
    cleaned = re.sub(r"^[\(\[][^\)\]]*[\)\]]\s*", "", cleaned)
    for kw in SIDO_KEYWORDS:
        idx = cleaned.find(kw)
        if idx == -1:
            continue
        sido = SIDO_NORMALIZE[kw]
        rest = cleaned[idx + len(kw):].strip()
        tokens = rest.split()
        sigungu = tokens[0] if tokens else ""
        sigungu = re.sub(r"[,.]$", "", sigungu)
        return sido, sigungu
    return "", ""


def normalize_brewery_name(name: str) -> str:
    """양조장명 매칭용 정규화 — 법인 표기·공백·괄호 제거."""
    if not isinstance(name, str):
        return ""
    n = name.strip()
    n = re.sub(r"\([^)]*\)", "", n)
    n = n.replace("㈜", "").replace("(주)", "").replace("(유)", "")
    n = re.sub(r"^(주식회사|농업회사법인|영농조합법인|영농조합)\s*", "", n)
    n = re.sub(r"\s*(주식회사|농업회사법인|영농조합법인|영농조합)$", "", n)
    n = re.sub(r"\s+", "", n)
    return n


def load_visit(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df[df["사용여부"] == "Y"].copy()
    df["상시방문가능"] = df["상시방문가능여부"].fillna("").str.strip() == "Y"
    df["예약방문가능"] = df["예약방문가능여부"].fillna("").str.strip() == "Y"
    df["체험가능"] = df["상시방문가능"] | df["예약방문가능"]
    df["match_key"] = df["상호명"].map(normalize_brewery_name)
    sido_sigungu = df["주소"].map(parse_address)
    df["sido"] = sido_sigungu.map(lambda x: x[0])
    df["sigungu"] = sido_sigungu.map(lambda x: x[1])
    return df.rename(columns={"상호명": "name", "주소": "address", "홈페이지": "homepage"})[
        ["match_key", "name", "address", "sido", "sigungu", "homepage",
         "상시방문가능", "예약방문가능", "체험가능", "조회수"]
    ].rename(columns={"상시방문가능": "always_open", "예약방문가능": "by_reservation",
                       "체험가능": "visitable", "조회수": "views"})


def load_products(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df[df["판매여부"] == "Y"].copy()
    df["match_key"] = df["양조장"].map(normalize_brewery_name)
    return df.rename(columns={
        "제품명": "product_name", "제품소개": "description",
        "알콜도수": "abv", "용량": "volume", "성분": "ingredients",
        "특이사항": "notes", "특징": "features",
        "양조장": "brewery_name", "양조장주소": "brewery_address",
        "홈페이지주소": "homepage", "수상경력": "awards",
    })[["match_key", "product_name", "description", "abv", "volume", "ingredients",
        "notes", "features", "brewery_name", "brewery_address", "homepage", "awards"]]


def build_breweries(visit: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    prod_breweries = products[["match_key", "brewery_name", "brewery_address", "homepage"]].copy()
    prod_breweries = prod_breweries.drop_duplicates(subset=["match_key"])
    prod_breweries = prod_breweries.rename(columns={
        "brewery_name": "name", "brewery_address": "address"
    })
    sido_sigungu = prod_breweries["address"].map(parse_address)
    prod_breweries["sido"] = sido_sigungu.map(lambda x: x[0])
    prod_breweries["sigungu"] = sido_sigungu.map(lambda x: x[1])

    merged = prod_breweries.merge(
        visit[["match_key", "always_open", "by_reservation", "visitable", "views"]],
        on="match_key", how="left",
    )
    merged["visitable"] = merged["visitable"].fillna(False)
    merged["always_open"] = merged["always_open"].fillna(False)
    merged["by_reservation"] = merged["by_reservation"].fillna(False)
    merged["views"] = merged["views"].fillna(0).astype(int)

    visit_only = visit[~visit["match_key"].isin(merged["match_key"])][
        ["match_key", "name", "address", "sido", "sigungu", "homepage",
         "always_open", "by_reservation", "visitable", "views"]
    ]
    breweries = pd.concat([merged, visit_only], ignore_index=True)
    breweries = breweries.dropna(subset=["match_key"]).reset_index(drop=True)
    breweries["id"] = breweries.index + 1
    return breweries[["id", "match_key", "name", "address", "sido", "sigungu",
                       "homepage", "always_open", "by_reservation", "visitable", "views"]]


def attach_brewery_id(products: pd.DataFrame, breweries: pd.DataFrame) -> pd.DataFrame:
    key_to_id = dict(zip(breweries["match_key"], breweries["id"]))
    products = products.copy()
    products["brewery_id"] = products["match_key"].map(key_to_id)
    products["id"] = products.index + 1
    return products[["id", "brewery_id", "product_name", "description", "abv", "volume",
                      "ingredients", "notes", "features", "awards"]]


def write_sqlite(breweries: pd.DataFrame, products: pd.DataFrame) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as conn:
        breweries.to_sql("breweries", conn, index=False)
        products.to_sql("products", conn, index=False)
        conn.executescript("""
            CREATE INDEX idx_breweries_sido ON breweries(sido);
            CREATE INDEX idx_breweries_sigungu ON breweries(sigungu);
            CREATE INDEX idx_products_brewery ON products(brewery_id);
        """)


def main() -> None:
    print(f"Reading {VISIT_CSV.name}…")
    visit = load_visit(VISIT_CSV)
    print(f"  → {len(visit)} 양조장 (체험 가능)")

    print(f"Reading {PRODUCT_CSV.name}…")
    products_raw = load_products(PRODUCT_CSV)
    print(f"  → {len(products_raw)} 술 제품")

    breweries = build_breweries(visit, products_raw)
    products = attach_brewery_id(products_raw, breweries)
    products = products[products["brewery_id"].notna()].copy()
    products["brewery_id"] = products["brewery_id"].astype(int)

    print(f"\n총 양조장: {len(breweries)} (체험 가능 {breweries['visitable'].sum()})")
    print(f"총 술 제품: {len(products)}")
    print(f"\n시/도별 양조장 수:")
    print(breweries["sido"].value_counts().to_string())

    write_sqlite(breweries, products)
    print(f"\n✅ SQLite 적재 완료 → {DB_PATH}")


if __name__ == "__main__":
    main()
