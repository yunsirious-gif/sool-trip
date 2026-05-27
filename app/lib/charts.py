"""Plotly 차트 팩토리 — 워터마크 + 한국 부동산 톤."""

import pandas as pd
import plotly.graph_objects as go

WATERMARK = "출처: 국토교통부 실거래가 공개시스템 (2021-01 ~ 2026-05)"
COLOR_PRIMARY = "#1f3a8a"
COLOR_ACCENT = "#dc2626"
COLOR_MUTED = "#6b7280"


def _watermark(fig: go.Figure) -> go.Figure:
    fig.add_annotation(
        text=WATERMARK,
        xref="paper", yref="paper",
        x=0.99, y=-0.18,
        showarrow=False,
        font=dict(size=10, color=COLOR_MUTED),
        xanchor="right",
    )
    fig.update_layout(margin=dict(l=40, r=20, t=40, b=60))
    return fig


def line_chart_trade(df: pd.DataFrame, title: str = "매매 시세 추이") -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="거래 데이터 없음", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=14))
    else:
        monthly = df.set_index("deal_date").resample("ME")["price_eok"].mean().dropna()
        fig.add_trace(go.Scatter(
            x=monthly.index, y=monthly.values,
            mode="lines+markers",
            line=dict(color=COLOR_PRIMARY, width=2),
            marker=dict(size=5),
            name="월평균 거래가",
        ))
    fig.update_layout(
        title=title, height=320,
        xaxis_title=None, yaxis_title="억원",
        hovermode="x unified",
    )
    return _watermark(fig)


def line_chart_rent(df: pd.DataFrame, title: str = "전월세 추이") -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="전월세 데이터 없음", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=14))
    else:
        jeonse = df[df["is_jeonse"]].copy()
        wolse = df[~df["is_jeonse"]].copy()
        if not jeonse.empty:
            m = jeonse.set_index("deal_date").resample("ME")["deposit_eok"].mean().dropna()
            fig.add_trace(go.Scatter(x=m.index, y=m.values, mode="lines+markers",
                                     name="전세 (보증금 억원)",
                                     line=dict(color=COLOR_PRIMARY, width=2)))
        if not wolse.empty:
            m = wolse.set_index("deal_date").resample("ME")["deposit_eok"].mean().dropna()
            fig.add_trace(go.Scatter(x=m.index, y=m.values, mode="lines+markers",
                                     name="월세 (보증금 억원)",
                                     line=dict(color=COLOR_ACCENT, width=2, dash="dot")))
    fig.update_layout(
        title=title, height=320,
        xaxis_title=None, yaxis_title="억원",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1),
    )
    return _watermark(fig)


def bar_ranking(df: pd.DataFrame, highlight_apt: str | None = None,
                title: str = "자치구 내 거래량 순위 TOP 10") -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return _watermark(fig)
    colors = [COLOR_ACCENT if name == highlight_apt else COLOR_PRIMARY
              for name in df["apt_name"]]
    fig.add_trace(go.Bar(
        x=df["trade_count"], y=df["apt_name"],
        orientation="h", marker_color=colors,
        text=df["trade_count"], textposition="outside",
    ))
    fig.update_layout(
        title=title, height=380,
        xaxis_title="거래 횟수 (5년)", yaxis_title=None,
        yaxis=dict(autorange="reversed"),
        showlegend=False,
    )
    return _watermark(fig)


def line_population(df: pd.DataFrame, title: str = "자치구 인구 추이") -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="인구 데이터 없음", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=14))
    else:
        fig.add_trace(go.Scatter(
            x=df["ref_date"], y=df["total_pop"],
            mode="lines",
            line=dict(color=COLOR_PRIMARY, width=2),
            fill="tozeroy", fillcolor="rgba(31,58,138,0.08)",
            name="총인구",
        ))
    fig.update_layout(
        title=title, height=260,
        xaxis_title=None, yaxis_title="명",
        hovermode="x unified",
    )
    return _watermark(fig)
