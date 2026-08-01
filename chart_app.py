"""Streamlit candlestick chart app with live fetch, indicators, and event markers."""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from chart_builder import build_ohlcv_figure
from data_utils import (
    DEFAULT_MAX_MARKERS,
    INTERVAL_OPTIONS,
    TIMEFRAME_OFFSETS,
    VOLUME_SMA_WINDOW,
    VOLUME_SPIKE_MULTIPLE,
    apply_indicators,
    collect_markers,
    fetch_history,
    filter_timeframe,
    guess_ticker_from_filename,
    load_csv,
    resample_weekly,
    resolve_date_range,
    save_csv,
)

st.set_page_config(page_title="Stock Chart", layout="wide")
st.title("Stock Candlestick Chart")

TIMEFRAME_CHOICES = list(TIMEFRAME_OFFSETS) + ["All", "Custom"]


@st.cache_data(show_spinner=False)
def cached_load_csv(name: str, raw: bytes) -> pd.DataFrame:
    return load_csv(io.BytesIO(raw))


@st.cache_data(show_spinner="Fetching market data…")
def cached_fetch(ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
    return fetch_history(ticker, start, end, interval=interval)


def indicator_controls() -> dict:
    st.subheader("Overlays")
    c1, c2, c3 = st.columns(3)
    sma_20 = c1.checkbox("SMA 20", value=True)
    sma_50 = c2.checkbox("SMA 50", value=True)
    sma_200 = c3.checkbox("SMA 200", value=False)

    e1, e2 = st.columns(2)
    ema_12 = e1.checkbox("EMA 12", value=False)
    ema_26 = e2.checkbox("EMA 26", value=False)

    st.subheader("Bands & oscillators")
    bollinger = st.checkbox("Bollinger Bands (20, 2σ)", value=False)
    rsi = st.checkbox("RSI (14)", value=False)
    macd = st.checkbox("MACD (12, 26, 9)", value=False)

    st.subheader("Event markers")
    st.caption("Mechanical rule labels only — default off. Hover for details.")
    ma_cross = st.checkbox("MA crosses", value=False)
    ma_pairs: list[tuple[str, int, int]] = []
    if ma_cross:
        p1, p2, p3 = st.columns(3)
        if p1.checkbox("SMA 20/50", value=True, key="ma_sma_20_50"):
            ma_pairs.append(("SMA", 20, 50))
        if p2.checkbox("SMA 50/200", value=False, key="ma_sma_50_200"):
            ma_pairs.append(("SMA", 50, 200))
        if p3.checkbox("EMA 12/26", value=False, key="ma_ema_12_26"):
            ma_pairs.append(("EMA", 12, 26))

    rsi_exits = st.checkbox("RSI exits (reclaim 70 / 30)", value=False)
    bb_events = st.checkbox("Bollinger breakout / squeeze exit", value=False)
    macd_crosses = st.checkbox("MACD crosses", value=False)
    volume_spikes = st.checkbox(
        f"Volume spikes (>{VOLUME_SPIKE_MULTIPLE:g}× SMA {VOLUME_SMA_WINDOW})",
        value=False,
    )
    max_markers = st.slider(
        "Max marker dates in view",
        min_value=5,
        max_value=100,
        value=DEFAULT_MAX_MARKERS,
        help="Keeps the most recent event dates after deduplication.",
    )

    return {
        "sma": [w for w, on in [(20, sma_20), (50, sma_50), (200, sma_200)] if on],
        "ema": [w for w, on in [(12, ema_12), (26, ema_26)] if on],
        "bollinger": bollinger,
        "rsi": rsi,
        "macd": macd,
        "ma_pairs": ma_pairs,
        "rsi_exits": rsi_exits,
        "bb_events": bb_events,
        "macd_crosses": macd_crosses,
        "volume_spikes": volume_spikes,
        "max_markers": max_markers,
    }


def resolve_indicator_needs(cfg: dict) -> dict:
    """Ensure series required by enabled detectors/overlays are computed."""
    sma = set(cfg["sma"])
    ema = set(cfg["ema"])
    for kind, fast, slow in cfg["ma_pairs"]:
        if kind == "SMA":
            sma.update((fast, slow))
        else:
            ema.update((fast, slow))

    bollinger = cfg["bollinger"] or cfg["bb_events"]
    rsi = cfg["rsi"] or cfg["rsi_exits"]
    macd = cfg["macd"] or cfg["macd_crosses"]
    volume_sma = cfg["volume_spikes"]

    return {
        "sma": sorted(sma),
        "ema": sorted(ema),
        "bollinger": bollinger,
        "rsi": rsi,
        "macd": macd,
        "volume_sma": volume_sma,
        "show_bollinger": cfg["bollinger"],
        "show_rsi": cfg["rsi"],
        "show_macd": cfg["macd"],
        "overlay_sma": cfg["sma"],
        "overlay_ema": cfg["ema"],
    }


def build_view(
    df_ohlcv: pd.DataFrame,
    cfg: dict,
    *,
    title: str,
    theme: str,
    height: int,
) -> tuple:
    needs = resolve_indicator_needs(cfg)
    indicated = apply_indicators(
        df_ohlcv,
        sma_windows=needs["sma"] or None,
        ema_windows=needs["ema"] or None,
        bollinger=needs["bollinger"],
        rsi=needs["rsi"],
        macd=needs["macd"],
        volume_sma=needs["volume_sma"],
    )
    markers = collect_markers(
        indicated,
        ma_crosses=cfg["ma_pairs"] or None,
        rsi_exits=cfg["rsi_exits"],
        bb_events=cfg["bb_events"],
        macd_crosses=cfg["macd_crosses"],
        volume_spikes=cfg["volume_spikes"],
        max_markers=cfg["max_markers"],
    )
    fig = build_ohlcv_figure(
        indicated,
        title=title,
        sma_windows=needs["overlay_sma"],
        ema_windows=needs["overlay_ema"],
        show_bollinger=needs["show_bollinger"],
        show_rsi=needs["show_rsi"],
        show_macd=needs["show_macd"],
        markers=markers,
        theme=theme,
        height=height,
    )
    return indicated, markers, fig


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Data")
    source = st.radio("Source", ["Fetch online", "Upload CSV"], index=0)

    ticker_name = ""
    df_full: pd.DataFrame | None = None
    fetch_meta: dict | None = None

    if source == "Fetch online":
        ticker_input = st.text_input("Ticker", value="AAPL").strip().upper()
        fetch_preset = st.selectbox(
            "History to download",
            list(TIMEFRAME_OFFSETS) + ["Custom"],
            index=3,
        )
        fetch_start = fetch_end = None
        if fetch_preset == "Custom":
            fc1, fc2 = st.columns(2)
            fetch_start = fc1.date_input("Fetch from", key="fetch_from")
            fetch_end = fc2.date_input("Fetch to", key="fetch_to")

        interval = st.selectbox("Interval", INTERVAL_OPTIONS, index=0)
        do_fetch = st.button("Fetch", type="primary", use_container_width=True)
        save_local = st.checkbox("Also save CSV to data/", value=False)

        if do_fetch or st.session_state.get("last_fetch"):
            if do_fetch:
                if not ticker_input:
                    st.error("Enter a ticker symbol.")
                    st.stop()
                try:
                    start, end = resolve_date_range(fetch_preset, fetch_start, fetch_end)
                except ValueError as exc:
                    st.error(str(exc))
                    st.stop()
                st.session_state["last_fetch"] = {
                    "ticker": ticker_input,
                    "start": start,
                    "end": end,
                    "interval": interval,
                    "save": save_local,
                }

            meta = st.session_state["last_fetch"]
            try:
                df_full = cached_fetch(
                    meta["ticker"], meta["start"], meta["end"], meta["interval"]
                )
            except Exception as exc:
                st.error(f"Fetch failed: {exc}")
                st.stop()

            if df_full.empty:
                st.error(f"No data returned for '{meta['ticker']}'.")
                st.stop()

            ticker_name = meta["ticker"]
            fetch_meta = meta
            if do_fetch and meta.get("save"):
                path = save_csv(
                    df_full, meta["ticker"], meta["start"], meta["end"], meta["interval"]
                )
                st.caption(f"Saved {path.name}")
    else:
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        default_ticker = (
            guess_ticker_from_filename(uploaded_file.name) if uploaded_file else ""
        )
        ticker_name = st.text_input(
            "Ticker label",
            value=default_ticker,
            help="Used in chart titles. Defaults from the filename when possible.",
        ).strip().upper()

        if uploaded_file is not None:
            try:
                df_full = cached_load_csv(uploaded_file.name, uploaded_file.getvalue())
            except ValueError as exc:
                st.error(str(exc))
                st.stop()
            if not ticker_name:
                ticker_name = guess_ticker_from_filename(uploaded_file.name) or "SYMBOL"

    st.divider()
    st.header("Chart window")
    timeframe = st.radio("Timeframe", TIMEFRAME_CHOICES, index=3)
    start_date = end_date = None
    if timeframe == "Custom":
        col1, col2 = st.columns(2)
        start_date = col1.date_input("From", key="chart_from")
        end_date = col2.date_input("To", key="chart_to")

    st.divider()
    indicators = indicator_controls()

    st.divider()
    theme = st.radio("Chart theme", ["dark", "light"], horizontal=True)
    show_weekly = st.checkbox("Show weekly chart", value=True)

# ── Main panel ───────────────────────────────────────────────────────────────
if df_full is None:
    st.info("Fetch a ticker or upload a CSV in the sidebar to get started.")
    st.stop()

if timeframe == "Custom" and start_date and end_date and start_date >= end_date:
    st.error("'From' date must be before 'To' date.")
    st.stop()

needs = resolve_indicator_needs(indicators)
needed_bars = max(
    [
        *(needs["sma"] or [0]),
        *(needs["ema"] or [0]),
        20 if needs["bollinger"] else 0,
        14 if needs["rsi"] else 0,
        26 if needs["macd"] else 0,
        VOLUME_SMA_WINDOW if needs["volume_sma"] else 0,
    ],
    default=0,
)
if needed_bars and len(df_full) < needed_bars:
    st.warning(
        f"Loaded series has {len(df_full)} bars; some indicators need at least {needed_bars}."
    )

# Compute on full history, then filter (correct left-edge indicator values)
df_indicated = apply_indicators(
    df_full,
    sma_windows=needs["sma"] or None,
    ema_windows=needs["ema"] or None,
    bollinger=needs["bollinger"],
    rsi=needs["rsi"],
    macd=needs["macd"],
    volume_sma=needs["volume_sma"],
)
df_chart = filter_timeframe(df_indicated, timeframe, start_date, end_date)

if df_chart.empty:
    st.warning("No data in the selected timeframe.")
    st.stop()

markers = collect_markers(
    df_chart,
    ma_crosses=indicators["ma_pairs"] or None,
    rsi_exits=indicators["rsi_exits"],
    bb_events=indicators["bb_events"],
    macd_crosses=indicators["macd_crosses"],
    volume_spikes=indicators["volume_spikes"],
    max_markers=indicators["max_markers"],
)

subtitle = ""
if fetch_meta:
    subtitle = f" · {fetch_meta['interval']} · {fetch_meta['start']} → {fetch_meta['end']}"
marker_note = f" · {markers['date'].nunique()} marker dates" if not markers.empty else ""
st.caption(
    f"{ticker_name}{subtitle} · {len(df_chart)} bars in view · {len(df_full)} loaded{marker_note}"
)

fig = build_ohlcv_figure(
    df_chart,
    title=ticker_name or "Chart",
    sma_windows=needs["overlay_sma"],
    ema_windows=needs["overlay_ema"],
    show_bollinger=needs["show_bollinger"],
    show_rsi=needs["show_rsi"],
    show_macd=needs["show_macd"],
    markers=markers,
    theme=theme,
    height=700,
)
st.plotly_chart(fig, use_container_width=True)

if show_weekly:
    ohlcv_cols = ["Open", "High", "Low", "Close", "Volume"]
    df_weekly_raw = resample_weekly(df_chart[ohlcv_cols])
    st.subheader("Weekly Candles")
    if len(df_weekly_raw) < 2:
        st.warning("Not enough data to display weekly candles for this timeframe.")
    else:
        weekly_cfg = {
            **indicators,
            "sma": [w for w in indicators["sma"] if w <= len(df_weekly_raw)],
            "ema": [w for w in indicators["ema"] if w <= len(df_weekly_raw)],
            "ma_pairs": [
                (k, f, s)
                for k, f, s in indicators["ma_pairs"]
                if s <= len(df_weekly_raw)
            ],
            "bollinger": indicators["bollinger"] and len(df_weekly_raw) >= 20,
            "rsi": indicators["rsi"] and len(df_weekly_raw) >= 15,
            "macd": indicators["macd"] and len(df_weekly_raw) >= 35,
            "rsi_exits": indicators["rsi_exits"] and len(df_weekly_raw) >= 15,
            "bb_events": indicators["bb_events"] and len(df_weekly_raw) >= 20,
            "macd_crosses": indicators["macd_crosses"] and len(df_weekly_raw) >= 35,
            "volume_spikes": indicators["volume_spikes"]
            and len(df_weekly_raw) >= VOLUME_SMA_WINDOW,
        }
        _, _, weekly_fig = build_view(
            df_weekly_raw,
            weekly_cfg,
            title=f"{ticker_name} — Weekly",
            theme=theme,
            height=520,
        )
        st.plotly_chart(weekly_fig, use_container_width=True)

col1, col2, col3, col4 = st.columns(4)
latest = df_chart.iloc[-1]
first = df_chart.iloc[0]
pct_change = (latest["Close"] - first["Close"]) / first["Close"] * 100
col1.metric("Last Close", f"{latest['Close']:.4f}")
col2.metric("Period High", f"{df_chart['High'].max():.4f}")
col3.metric("Period Low", f"{df_chart['Low'].min():.4f}")
col4.metric("Period Return", f"{pct_change:+.2f}%")
