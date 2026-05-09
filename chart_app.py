import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from data_utils import load_csv, filter_timeframe, compute_ma, resample_weekly, MA_COLORS

st.set_page_config(page_title="Stock Chart", layout="wide")
st.title("Stock Candlestick Chart")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    timeframe = st.radio(
        "Timeframe",
        ["1M", "3M", "6M", "1Y", "2Y", "5Y", "All", "Custom"],
        index=3,
    )

    start_date, end_date = None, None
    if timeframe == "Custom":
        col1, col2 = st.columns(2)
        start_date = col1.date_input("From")
        end_date = col2.date_input("To")

    st.divider()
    st.subheader("Moving Averages")
    ma_20 = st.checkbox("SMA 20", value=True)
    ma_50 = st.checkbox("SMA 50", value=True)
    ma_200 = st.checkbox("SMA 200", value=False)

# ── Main panel ───────────────────────────────────────────────────────────────
if uploaded_file is None:
    st.info("Upload a CSV file in the sidebar to get started.")
    st.stop()

if timeframe == "Custom" and start_date and end_date and start_date >= end_date:
    st.error("'From' date must be before 'To' date.")
    st.stop()


@st.cache_data
def cached_load(file) -> pd.DataFrame:
    return load_csv(file)


df_full = cached_load(uploaded_file)

ticker_name = uploaded_file.name.split("_")[0]

df_filtered = filter_timeframe(df_full, timeframe, start_date, end_date)

if df_filtered.empty:
    st.warning("No data in the selected timeframe.")
    st.stop()

active_windows = [w for w, on in [(20, ma_20), (50, ma_50), (200, ma_200)] if on]

insufficient = [w for w in active_windows if w > len(df_filtered)]
if insufficient:
    st.warning(
        f"Not enough data for SMA {', '.join(str(w) for w in insufficient)} "
        f"(need at least {max(insufficient)} rows, have {len(df_filtered)})."
    )
    active_windows = [w for w in active_windows if w not in insufficient]

df_chart = compute_ma(df_filtered, active_windows)


def build_figure(df: pd.DataFrame, windows: list[int]) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker_name,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # Moving averages
    for w in windows:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f"SMA_{w}"],
                mode="lines",
                name=f"SMA {w}",
                line=dict(width=1.5, color=MA_COLORS.get(w, "#ffffff")),
            ),
            row=1, col=1,
        )

    # Volume bars
    is_up = df["Close"] >= df["Open"]
    volume_colors = ["#26a69a" if u else "#ef5350" for u in is_up]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=volume_colors,
            showlegend=False,
        ),
        row=2, col=1,
    )

    fig.update_layout(
        title=ticker_name,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor="#1e1e2e",
        paper_bgcolor="#1e1e2e",
        font_color="#cdd6f4",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=60, b=0),
        height=700,
    )
    fig.update_xaxes(gridcolor="#313244", showgrid=True)
    fig.update_yaxes(gridcolor="#313244", showgrid=True)

    return fig


fig = build_figure(df_chart, active_windows)
st.plotly_chart(fig, use_container_width=True)

df_weekly = resample_weekly(df_filtered)


def build_weekly_figure(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker_name,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )
    is_up = df["Close"] >= df["Open"]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=["#26a69a" if u else "#ef5350" for u in is_up],
            showlegend=False,
        ),
        row=2, col=1,
    )
    fig.update_layout(
        title=f"{ticker_name} — Weekly",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor="#1e1e2e",
        paper_bgcolor="#1e1e2e",
        font_color="#cdd6f4",
        margin=dict(l=0, r=0, t=60, b=0),
        height=500,
    )
    fig.update_xaxes(gridcolor="#313244", showgrid=True)
    fig.update_yaxes(gridcolor="#313244", showgrid=True)
    return fig


st.subheader("Weekly Candles")
if len(df_weekly) < 2:
    st.warning("Not enough data to display weekly candles for this timeframe.")
else:
    st.plotly_chart(build_weekly_figure(df_weekly), use_container_width=True)

# Stats strip
col1, col2, col3, col4 = st.columns(4)
latest = df_filtered.iloc[-1]
first = df_filtered.iloc[0]
pct_change = (latest["Close"] - first["Close"]) / first["Close"] * 100
col1.metric("Last Close", f"{latest['Close']:.4f}")
col2.metric("Period High", f"{df_filtered['High'].max():.4f}")
col3.metric("Period Low", f"{df_filtered['Low'].min():.4f}")
col4.metric("Period Return", f"{pct_change:+.2f}%")
