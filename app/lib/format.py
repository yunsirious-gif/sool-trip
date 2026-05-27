"""금액·날짜 표시 헬퍼."""


def format_won(amount_manwon: int | float | None) -> str:
    """498000 (만원) → '49억 8,000만원'."""
    if amount_manwon is None or amount_manwon == 0:
        return "—"
    n = int(round(float(amount_manwon)))
    eok, manwon = divmod(n, 10000)
    if eok and manwon:
        return f"{eok}억 {manwon:,}만원"
    if eok:
        return f"{eok}억원"
    return f"{manwon:,}만원"


def format_area(area_m2: float | None) -> str:
    if area_m2 is None:
        return "—"
    return f"{area_m2:.1f}㎡ ({area_m2 / 3.3058:.0f}평)"
