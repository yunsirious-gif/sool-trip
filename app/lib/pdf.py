"""Jinja2 + WeasyPrint으로 브리핑 HTML → A4 PDF 생성."""

from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from lib.format import format_won

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _trade_summary(trade: pd.DataFrame) -> list[dict]:
    if trade.empty:
        return []
    df = trade.dropna(subset=["deal_date"]).copy()
    df["year"] = df["deal_date"].dt.year
    rows = []
    for year, g in df.groupby("year"):
        rows.append({
            "year": int(year),
            "n": len(g),
            "avg_display": format_won(g["dealAmount"].mean()),
            "min_display": format_won(g["dealAmount"].min()),
            "max_display": format_won(g["dealAmount"].max()),
        })
    return rows


def _rent_summary(rent: pd.DataFrame) -> list[dict]:
    if rent.empty:
        return []
    out = []
    jeonse = rent[rent["is_jeonse"]]
    wolse = rent[~rent["is_jeonse"]]
    if not jeonse.empty:
        out.append({
            "label": "전세",
            "n": len(jeonse),
            "deposit_display": format_won(jeonse["deposit"].mean()),
            "rent_display": "—",
        })
    if not wolse.empty:
        out.append({
            "label": "월세",
            "n": len(wolse),
            "deposit_display": format_won(wolse["deposit"].mean()),
            "rent_display": format_won(wolse["monthlyRent"].mean()),
        })
    return out


def _pop_summary(pop: pd.DataFrame) -> tuple[list[dict], str]:
    if pop.empty:
        return [], ""
    df = pop.dropna(subset=["ref_date"]).copy()
    df["ym"] = df["ref_date"].dt.strftime("%Y-%m")
    df["year"] = df["ref_date"].dt.year
    rows = []
    for year, g in df.groupby("year"):
        last = g.iloc[-1]
        rows.append({
            "date": str(year),
            "total": int(last["total_pop"]),
            "hh": int(last["households"]),
        })
    first = df.iloc[0]
    last = df.iloc[-1]
    delta = int(last["total_pop"] - first["total_pop"])
    pct = delta / first["total_pop"] * 100 if first["total_pop"] else 0
    cap = (f"{first['ref_date'].date()} → {last['ref_date'].date()}: "
           f"{int(last['total_pop']):,}명 ({delta:+,}명 · {pct:+.1f}%)")
    return rows, cap


def render_briefing_pdf(info: dict, trade: pd.DataFrame, rent: pd.DataFrame,
                        ranking: pd.DataFrame, infra: dict,
                        pop: pd.DataFrame) -> bytes:
    template = _env.get_template("briefing.html")
    stylesheet = (TEMPLATE_DIR / "styles.css").read_text(encoding="utf-8")

    pop_rows, pop_cap = _pop_summary(pop)

    html = template.render(
        info=info,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        stylesheet=stylesheet,
        trade_summary=_trade_summary(trade),
        rent_summary=_rent_summary(rent),
        ranking=ranking.to_dict(orient="records"),
        infra=infra,
        pop_summary=pop_rows,
        pop_delta_caption=pop_cap,
    )
    return HTML(string=html).write_pdf()
