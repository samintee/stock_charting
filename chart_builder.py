"""Unified Plotly OHLCV figure builder with indicator panes and event markers."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_utils import (
    BB_COLOR,
    EMA_COLORS,
    MACD_HIST_DOWN,
    MACD_HIST_UP,
    MACD_LINE_COLOR,
    MACD_SIGNAL_COLOR,
    RSI_COLOR,
    SMA_COLORS,
)

CHART_THEMES = {
    "dark": {
        "plot_bgcolor": "#1e1e2e",
        "paper_bgcolor": "#1e1e2e",
        "font_color": "#cdd6f4",
        "gridcolor": "#313244",
        "up": "#26a69a",
        "down": "#ef5350",
        "rsi_overbought": "rgba(239, 83, 80, 0.15)",
        "rsi_oversold": "rgba(38, 166, 154, 0.15)",
        "rsi_guide": "#585b70",
        "vrect": "rgba(255, 202, 40, 0.08)",
        "bb_vrect": "rgba(126, 87, 194, 0.10)",
    },
    "light": {
        "plot_bgcolor": "#ffffff",
        "paper_bgcolor": "#ffffff",
        "font_color": "#1e1e2e",
        "gridcolor": "#e0e0e0",
        "up": "#2e7d32",
        "down": "#c62828",
        "rsi_overbought": "rgba(198, 40, 40, 0.12)",
        "rsi_oversold": "rgba(46, 125, 50, 0.12)",
        "rsi_guide": "#9e9e9e",
        "vrect": "rgba(255, 193, 7, 0.12)",
        "bb_vrect": "rgba(126, 87, 194, 0.10)",
    },
}

_FAMILY_LEGEND = {
    "ma_cross": "MA cross",
    "rsi_exit": "RSI exit",
    "bb_breakout": "BB breakout",
    "bb_squeeze_exit": "BB squeeze exit",
    "macd_cross": "MACD cross",
    "volume_spike": "Volume spike",
}


def _subplot_layout(show_rsi: bool, show_macd: bool) -> tuple[int, list[float], list[str | None]]:
    # Always: price (1), volume (2); then optional RSI / MACD
    panes = ["price", "volume"]
    if show_rsi:
        panes.append("rsi")
    if show_macd:
        panes.append("macd")

    n = len(panes)
    if n == 2:
        heights = [0.75, 0.25]
    elif n == 3:
        heights = [0.58, 0.18, 0.24]
    else:
        heights = [0.48, 0.14, 0.19, 0.19]

    titles: list[str | None] = [None, None]
    if show_rsi:
        titles.append("RSI (14)")
    if show_macd:
        titles.append("MACD (12, 26, 9)")
    return n, heights, titles


def _pane_row(pane: str, show_rsi: bool, show_macd: bool) -> int:
    mapping = {"price": 1, "volume": 2}
    next_row = 3
    if show_rsi:
        mapping["rsi"] = next_row
        next_row += 1
    if show_macd:
        mapping["macd"] = next_row
    return mapping[pane]


def _add_marker_traces(
    fig: go.Figure,
    markers: pd.DataFrame,
    *,
    show_rsi: bool,
    show_macd: bool,
    colors: dict,
) -> None:
    if markers is None or markers.empty:
        return

    events = markers.copy()
    if "vrect" not in events.columns:
        events["vrect"] = False
    else:
        events["vrect"] = events["vrect"].fillna(False)

    # Faint vertical bands for squeeze exits / volume spikes (capped)
    vrect_events = events[events["vrect"].astype(bool)].drop_duplicates(subset=["date", "family"])
    for _, row in vrect_events.tail(25).iterrows():
        fill = colors["bb_vrect"] if row["family"] == "bb_squeeze_exit" else colors["vrect"]
        ts = pd.Timestamp(row["date"])
        fig.add_vrect(
            x0=ts - pd.Timedelta(hours=12),
            x1=ts + pd.Timedelta(hours=12),
            fillcolor=fill,
            opacity=1.0,
            line_width=0,
            layer="below",
            row=1,
            col=1,
        )

    # One scatter per family(+direction for MA) on each pane — legend once
    legend_seen: set[str] = set()
    for (family, pane, symbol, color), group in events.groupby(
        ["family", "pane", "symbol", "color"], sort=False
    ):
        if pane == "rsi" and not show_rsi:
            continue
        if pane == "macd" and not show_macd:
            continue
        try:
            row = _pane_row(pane, show_rsi, show_macd)
        except KeyError:
            continue

        legend_name = _FAMILY_LEGEND.get(family, family)
        show_legend = legend_name not in legend_seen and pane == "price"
        if family == "volume_spike":
            show_legend = legend_name not in legend_seen
        if show_legend:
            legend_seen.add(legend_name)

        hover = group["hover"] if "hover" in group.columns else group["label"]
        fig.add_trace(
            go.Scatter(
                x=group["date"],
                y=group["y"],
                mode="markers",
                name=legend_name,
                legendgroup=family,
                showlegend=show_legend,
                marker=dict(
                    symbol=symbol,
                    size=10 if symbol.startswith("triangle") else 8,
                    color=color,
                    line=dict(width=1, color=color),
                ),
                text=hover,
                hovertemplate="%{text}<extra></extra>",
            ),
            row=row,
            col=1,
        )


def build_ohlcv_figure(
    df: pd.DataFrame,
    *,
    title: str,
    sma_windows: list[int] | None = None,
    ema_windows: list[int] | None = None,
    show_bollinger: bool = False,
    show_rsi: bool = False,
    show_macd: bool = False,
    markers: pd.DataFrame | None = None,
    theme: str = "dark",
    height: int = 700,
) -> go.Figure:
    sma_windows = sma_windows or []
    ema_windows = ema_windows or []
    colors = CHART_THEMES.get(theme, CHART_THEMES["dark"])

    rows, row_heights, subplot_titles = _subplot_layout(show_rsi, show_macd)

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.035,
        subplot_titles=subplot_titles,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=title,
            increasing_line_color=colors["up"],
            decreasing_line_color=colors["down"],
        ),
        row=1,
        col=1,
    )

    if show_bollinger and {"BB_UPPER", "BB_MID", "BB_LOWER"}.issubset(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_UPPER"],
                mode="lines",
                name="BB Upper",
                line=dict(width=1, color=BB_COLOR, dash="dot"),
                legendgroup="bb",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_LOWER"],
                mode="lines",
                name="BB Lower",
                line=dict(width=1, color=BB_COLOR, dash="dot"),
                fill="tonexty",
                fillcolor="rgba(126, 87, 194, 0.08)",
                legendgroup="bb",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_MID"],
                mode="lines",
                name="BB Mid",
                line=dict(width=1, color=BB_COLOR),
                legendgroup="bb",
            ),
            row=1,
            col=1,
        )

    for w in sma_windows:
        col = f"SMA_{w}"
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="lines",
                    name=f"SMA {w}",
                    line=dict(width=1.5, color=SMA_COLORS.get(w, "#ffffff")),
                ),
                row=1,
                col=1,
            )

    for w in ema_windows:
        col = f"EMA_{w}"
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="lines",
                    name=f"EMA {w}",
                    line=dict(width=1.5, color=EMA_COLORS.get(w, "#aaaaaa"), dash="dash"),
                ),
                row=1,
                col=1,
            )

    is_up = df["Close"] >= df["Open"]
    volume_colors = [colors["up"] if u else colors["down"] for u in is_up]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=volume_colors,
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    if show_rsi and "RSI" in df.columns:
        rsi_row = _pane_row("rsi", show_rsi, show_macd)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                mode="lines",
                name="RSI",
                line=dict(width=1.5, color=RSI_COLOR),
            ),
            row=rsi_row,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dot", line_color=colors["rsi_guide"], row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color=colors["rsi_guide"], row=rsi_row, col=1)
        fig.add_hrect(
            y0=70, y1=100, fillcolor=colors["rsi_overbought"], line_width=0, row=rsi_row, col=1
        )
        fig.add_hrect(
            y0=0, y1=30, fillcolor=colors["rsi_oversold"], line_width=0, row=rsi_row, col=1
        )
        fig.update_yaxes(range=[0, 100], title_text="RSI", row=rsi_row, col=1)

    if show_macd and {"MACD", "MACD_SIGNAL", "MACD_HIST"}.issubset(df.columns):
        macd_row = _pane_row("macd", show_rsi, show_macd)
        hist_colors = [
            MACD_HIST_UP if v >= 0 else MACD_HIST_DOWN for v in df["MACD_HIST"].fillna(0)
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["MACD_HIST"],
                name="MACD hist",
                marker_color=hist_colors,
                showlegend=False,
            ),
            row=macd_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD"],
                mode="lines",
                name="MACD",
                line=dict(width=1.5, color=MACD_LINE_COLOR),
            ),
            row=macd_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD_SIGNAL"],
                mode="lines",
                name="Signal",
                line=dict(width=1.2, color=MACD_SIGNAL_COLOR),
            ),
            row=macd_row,
            col=1,
        )
        fig.update_yaxes(title_text="MACD", row=macd_row, col=1)

    _add_marker_traces(
        fig,
        markers if markers is not None else pd.DataFrame(),
        show_rsi=show_rsi,
        show_macd=show_macd,
        colors=colors,
    )

    extra = 0
    if show_rsi:
        extra += 110
    if show_macd:
        extra += 110

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor=colors["plot_bgcolor"],
        paper_bgcolor=colors["paper_bgcolor"],
        font_color=colors["font_color"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=60, b=0),
        height=height + extra,
    )
    fig.update_xaxes(gridcolor=colors["gridcolor"], showgrid=True)
    fig.update_yaxes(gridcolor=colors["gridcolor"], showgrid=True)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig
