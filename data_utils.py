"""Shared data loading, fetching, timeframes, and indicators."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")

TIMEFRAME_OFFSETS = {
    "1M": {"months": 1},
    "3M": {"months": 3},
    "6M": {"months": 6},
    "1Y": {"years": 1},
    "2Y": {"years": 2},
    "5Y": {"years": 5},
}

# CLI menu ↔ shared presets (DateOffset-based, same as the chart app)
CLI_TIMEFRAME_CHOICES = {
    "1": ("1 month", "1M"),
    "2": ("3 months", "3M"),
    "3": ("6 months", "6M"),
    "4": ("1 year", "1Y"),
    "5": ("2 years", "2Y"),
    "6": ("5 years", "5Y"),
    "7": ("custom", "Custom"),
}

INTERVAL_OPTIONS = ("1d", "1wk", "1mo")

SMA_COLORS = {
    20: "#f0a500",
    50: "#00bcd4",
    200: "#e040fb",
}

EMA_COLORS = {
    12: "#81c784",
    26: "#ff8a65",
}

BB_COLOR = "#7e57c2"
RSI_COLOR = "#42a5f5"
MACD_LINE_COLOR = "#26c6da"
MACD_SIGNAL_COLOR = "#ff7043"
MACD_HIST_UP = "#26a69a"
MACD_HIST_DOWN = "#ef5350"

DEFAULT_MAX_MARKERS = 40
VOLUME_SPIKE_MULTIPLE = 2.0
VOLUME_SMA_WINDOW = 20

DATA_DIR = Path(__file__).resolve().parent / "data"

# Backward-compatible alias used by older imports
MA_COLORS = SMA_COLORS


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _drop_extra_columns(df: pd.DataFrame) -> pd.DataFrame:
    drop = [c for c in ("Dividends", "Stock Splits", "Capital Gains") if c in df.columns]
    return df.drop(columns=drop) if drop else df


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV missing required column(s): {', '.join(missing)}. "
            f"Expected: {', '.join(REQUIRED_COLUMNS)}."
        )
    out = df.loc[:, list(REQUIRED_COLUMNS)].copy()
    out.sort_index(inplace=True)
    return out


def normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a yfinance history frame into a plain OHLCV DatetimeIndex series."""
    if df.empty:
        return df
    out = df.copy()
    if getattr(out.index, "tz", None) is not None:
        out.index = out.index.tz_localize(None)
    out.index.name = "Date"
    out = _drop_extra_columns(out)
    return validate_ohlcv(out)


def load_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file, parse_dates=["Date"], index_col="Date")
    df = _drop_extra_columns(df)
    return validate_ohlcv(df)


def guess_ticker_from_filename(name: str) -> str:
    stem = Path(name).stem
    if not stem:
        return ""
    return stem.split("_")[0].upper()


def resolve_date_range(
    preset: str,
    start_date=None,
    end_date=None,
    *,
    today: date | None = None,
) -> tuple[str, str]:
    """Return (start, end) as YYYY-MM-DD using shared DateOffset presets."""
    end = end_date or (today or date.today())
    if isinstance(end, datetime):
        end = end.date()
    elif isinstance(end, str):
        end = datetime.strptime(end, "%Y-%m-%d").date()

    if preset == "Custom":
        if start_date is None or end_date is None:
            raise ValueError("Custom range requires start_date and end_date.")
        start = start_date
        if isinstance(start, datetime):
            start = start.date()
        elif isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if isinstance(end_date, datetime):
            end = end_date.date()
        elif isinstance(end_date, str):
            end = datetime.strptime(str(end_date), "%Y-%m-%d").date()
        elif isinstance(end_date, date):
            end = end_date
        if start >= end:
            raise ValueError("Start date must be before end date.")
        return start.isoformat(), end.isoformat()

    if preset not in TIMEFRAME_OFFSETS:
        raise ValueError(f"Unknown timeframe preset: {preset}")

    start = (pd.Timestamp(end) - pd.DateOffset(**TIMEFRAME_OFFSETS[preset])).date()
    return start.isoformat(), end.isoformat()


def filter_timeframe(
    df: pd.DataFrame,
    preset: str,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    if preset == "All":
        return df.copy()
    if preset == "Custom":
        if start_date is None or end_date is None:
            return df.copy()
        return df.loc[str(start_date) : str(end_date)].copy()
    offset = pd.DateOffset(**TIMEFRAME_OFFSETS[preset])
    start = df.index.max() - offset
    return df.loc[start:].copy()


def fetch_history(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d",
) -> pd.DataFrame:
    if interval not in INTERVAL_OPTIONS:
        raise ValueError(f"Unsupported interval '{interval}'. Use one of {INTERVAL_OPTIONS}.")
    stock = yf.Ticker(ticker)
    # yfinance end is exclusive for daily; bump by one day so the chosen end is included
    end_exclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    raw = stock.history(start=start, end=end_exclusive, interval=interval, auto_adjust=True)
    return normalize_history(raw)


def save_csv(df: pd.DataFrame, ticker: str, start: str, end: str, interval: str = "1d") -> Path:
    ensure_data_dir()
    suffix = "" if interval == "1d" else f"_{interval}"
    filename = f"{ticker.upper()}_{start}_{end}{suffix}.csv"
    path = DATA_DIR / filename
    df.to_csv(path)
    return path


def resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = df.resample("W").agg(
        Open=("Open", "first"),
        High=("High", "max"),
        Low=("Low", "min"),
        Close=("Close", "last"),
        Volume=("Volume", "sum"),
    )
    return weekly.dropna()


def compute_sma(df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    out = df.copy()
    for w in windows:
        out[f"SMA_{w}"] = out["Close"].rolling(w).mean()
    return out


# Backward-compatible name
compute_ma = compute_sma


def compute_ema(df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    out = df.copy()
    for w in windows:
        out[f"EMA_{w}"] = out["Close"].ewm(span=w, adjust=False).mean()
    return out


def compute_bollinger(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    out = df.copy()
    mid = out["Close"].rolling(window).mean()
    std = out["Close"].rolling(window).std()
    out["BB_MID"] = mid
    out["BB_UPPER"] = mid + num_std * std
    out["BB_LOWER"] = mid - num_std * std
    return out


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = df.copy()
    delta = out["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out["RSI"] = 100 - (100 / (1 + rs))
    return out


def compute_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    out = df.copy()
    ema_fast = out["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = out["Close"].ewm(span=slow, adjust=False).mean()
    out["MACD"] = ema_fast - ema_slow
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=signal, adjust=False).mean()
    out["MACD_HIST"] = out["MACD"] - out["MACD_SIGNAL"]
    return out


def compute_volume_sma(df: pd.DataFrame, window: int = VOLUME_SMA_WINDOW) -> pd.DataFrame:
    out = df.copy()
    out[f"VOL_SMA_{window}"] = out["Volume"].rolling(window).mean()
    return out


def apply_indicators(
    df: pd.DataFrame,
    *,
    sma_windows: list[int] | None = None,
    ema_windows: list[int] | None = None,
    bollinger: bool = False,
    bollinger_window: int = 20,
    rsi: bool = False,
    rsi_period: int = 14,
    macd: bool = False,
    volume_sma: bool = False,
    volume_sma_window: int = VOLUME_SMA_WINDOW,
) -> pd.DataFrame:
    out = df.copy()
    if sma_windows:
        out = compute_sma(out, sma_windows)
    if ema_windows:
        out = compute_ema(out, ema_windows)
    if bollinger:
        out = compute_bollinger(out, window=bollinger_window)
    if rsi:
        out = compute_rsi(out, period=rsi_period)
    if macd:
        out = compute_macd(out)
    if volume_sma:
        out = compute_volume_sma(out, window=volume_sma_window)
    return out


def _empty_markers() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "family",
            "direction",
            "price",
            "y",
            "pane",
            "symbol",
            "color",
            "label",
            "stack_rank",
        ]
    )


def _marker_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return _empty_markers()
    return pd.DataFrame(rows)


def detect_ma_cross(
    df: pd.DataFrame,
    fast: int = 20,
    slow: int = 50,
    kind: str = "SMA",
) -> pd.DataFrame:
    """Detect fast MA crossing above/below slow MA. Returns event rows."""
    kind = kind.upper()
    fast_col = f"{kind}_{fast}"
    slow_col = f"{kind}_{slow}"
    if fast_col not in df.columns or slow_col not in df.columns:
        return _empty_markers()
    if fast >= slow:
        raise ValueError("fast window must be < slow window")

    delta = df[fast_col] - df[slow_col]
    prev = delta.shift(1)
    cross_above = (prev <= 0) & (delta > 0)
    cross_below = (prev >= 0) & (delta < 0)

    rows: list[dict] = []
    for ts in df.index[cross_above.fillna(False)]:
        row = df.loc[ts]
        rows.append(
            {
                "date": ts,
                "family": "ma_cross",
                "direction": "above",
                "price": float(row["Close"]),
                "y": float(row["Low"]) * 0.99,
                "pane": "price",
                "symbol": "triangle-up",
                "color": "#26a69a",
                "label": f"{kind} {fast} crossed above {kind} {slow}",
                "stack_rank": 0,
            }
        )
    for ts in df.index[cross_below.fillna(False)]:
        row = df.loc[ts]
        rows.append(
            {
                "date": ts,
                "family": "ma_cross",
                "direction": "below",
                "price": float(row["Close"]),
                "y": float(row["High"]) * 1.01,
                "pane": "price",
                "symbol": "triangle-down",
                "color": "#ef5350",
                "label": f"{kind} {fast} crossed below {kind} {slow}",
                "stack_rank": 0,
            }
        )
    return _marker_frame(rows)


def detect_rsi_exit(
    df: pd.DataFrame,
    overbought: float = 70.0,
    oversold: float = 30.0,
) -> pd.DataFrame:
    """RSI reclaim: crosses back from >overbought or <oversold."""
    if "RSI" not in df.columns:
        return _empty_markers()

    rsi = df["RSI"]
    prev = rsi.shift(1)
    exit_ob = (prev > overbought) & (rsi <= overbought)
    exit_os = (prev < oversold) & (rsi >= oversold)

    rows: list[dict] = []
    for ts in df.index[exit_ob.fillna(False)]:
        row = df.loc[ts]
        label = f"RSI crossed back from above {overbought:g}"
        rows.append(
            {
                "date": ts,
                "family": "rsi_exit",
                "direction": "from_overbought",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "diamond",
                "color": "#ef5350",
                "label": label,
                "stack_rank": 0,
            }
        )
        rows.append(
            {
                "date": ts,
                "family": "rsi_exit",
                "direction": "from_overbought",
                "price": float(row["RSI"]),
                "y": float(row["RSI"]),
                "pane": "rsi",
                "symbol": "diamond",
                "color": "#ef5350",
                "label": label,
                "stack_rank": 0,
            }
        )
    for ts in df.index[exit_os.fillna(False)]:
        row = df.loc[ts]
        label = f"RSI crossed back from below {oversold:g}"
        rows.append(
            {
                "date": ts,
                "family": "rsi_exit",
                "direction": "from_oversold",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "diamond",
                "color": "#26a69a",
                "label": label,
                "stack_rank": 0,
            }
        )
        rows.append(
            {
                "date": ts,
                "family": "rsi_exit",
                "direction": "from_oversold",
                "price": float(row["RSI"]),
                "y": float(row["RSI"]),
                "pane": "rsi",
                "symbol": "diamond",
                "color": "#26a69a",
                "label": label,
                "stack_rank": 0,
            }
        )
    return _marker_frame(rows)


def detect_bb_events(
    df: pd.DataFrame,
    squeeze_lookback: int = 120,
    squeeze_quantile: float = 0.2,
) -> pd.DataFrame:
    """Close outside Bollinger + squeeze-exit (bandwidth leaves low percentile)."""
    needed = {"BB_UPPER", "BB_MID", "BB_LOWER", "Close"}
    if not needed.issubset(df.columns):
        return _empty_markers()

    rows: list[dict] = []
    close = df["Close"]
    upper = df["BB_UPPER"]
    lower = df["BB_LOWER"]
    prev_close = close.shift(1)

    # First close outside the band (was not already outside on the prior bar)
    break_up = (close > upper) & (prev_close <= upper.shift(1)).fillna(False)
    break_down = (close < lower) & (prev_close >= lower.shift(1)).fillna(False)

    for ts in df.index[break_up]:
        row = df.loc[ts]
        rows.append(
            {
                "date": ts,
                "family": "bb_breakout",
                "direction": "above_upper",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "circle",
                "color": BB_COLOR,
                "label": "Close crossed above Bollinger upper",
                "stack_rank": 0,
            }
        )
    for ts in df.index[break_down]:
        row = df.loc[ts]
        rows.append(
            {
                "date": ts,
                "family": "bb_breakout",
                "direction": "below_lower",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "circle",
                "color": BB_COLOR,
                "label": "Close crossed below Bollinger lower",
                "stack_rank": 0,
            }
        )

    mid = df["BB_MID"].replace(0, pd.NA)
    bandwidth = (upper - lower) / mid
    lookback = min(squeeze_lookback, max(len(df) // 2, 20))
    threshold = bandwidth.rolling(lookback, min_periods=max(10, lookback // 5)).quantile(
        squeeze_quantile
    )
    in_squeeze = bandwidth < threshold
    squeeze_exit = in_squeeze.shift(1).fillna(False) & ~in_squeeze.fillna(False)

    for ts in df.index[squeeze_exit]:
        row = df.loc[ts]
        rows.append(
            {
                "date": ts,
                "family": "bb_squeeze_exit",
                "direction": "expand",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "circle-open",
                "color": BB_COLOR,
                "label": (
                    f"Bollinger bandwidth left squeeze "
                    f"(below {squeeze_quantile:.0%} of {lookback}-bar range)"
                ),
                "stack_rank": 0,
                "vrect": True,
            }
        )

    return _marker_frame(rows)


def detect_macd_cross(df: pd.DataFrame) -> pd.DataFrame:
    if not {"MACD", "MACD_SIGNAL"}.issubset(df.columns):
        return _empty_markers()

    delta = df["MACD"] - df["MACD_SIGNAL"]
    prev = delta.shift(1)
    cross_above = (prev <= 0) & (delta > 0)
    cross_below = (prev >= 0) & (delta < 0)

    rows: list[dict] = []
    for ts in df.index[cross_above.fillna(False)]:
        row = df.loc[ts]
        label = "MACD crossed above signal"
        rows.append(
            {
                "date": ts,
                "family": "macd_cross",
                "direction": "above",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "circle",
                "color": MACD_LINE_COLOR,
                "label": label,
                "stack_rank": 0,
            }
        )
        rows.append(
            {
                "date": ts,
                "family": "macd_cross",
                "direction": "above",
                "price": float(row["MACD"]),
                "y": float(row["MACD"]),
                "pane": "macd",
                "symbol": "circle",
                "color": MACD_LINE_COLOR,
                "label": label,
                "stack_rank": 0,
            }
        )
    for ts in df.index[cross_below.fillna(False)]:
        row = df.loc[ts]
        label = "MACD crossed below signal"
        rows.append(
            {
                "date": ts,
                "family": "macd_cross",
                "direction": "below",
                "price": float(row["Close"]),
                "y": float(row["Close"]),
                "pane": "price",
                "symbol": "circle",
                "color": MACD_SIGNAL_COLOR,
                "label": label,
                "stack_rank": 0,
            }
        )
        rows.append(
            {
                "date": ts,
                "family": "macd_cross",
                "direction": "below",
                "price": float(row["MACD"]),
                "y": float(row["MACD"]),
                "pane": "macd",
                "symbol": "circle",
                "color": MACD_SIGNAL_COLOR,
                "label": label,
                "stack_rank": 0,
            }
        )
    return _marker_frame(rows)


def detect_volume_spike(
    df: pd.DataFrame,
    window: int = VOLUME_SMA_WINDOW,
    multiple: float = VOLUME_SPIKE_MULTIPLE,
) -> pd.DataFrame:
    vol_col = f"VOL_SMA_{window}"
    if vol_col not in df.columns:
        return _empty_markers()

    spike = df["Volume"] > (multiple * df[vol_col])
    rows: list[dict] = []
    for ts in df.index[spike.fillna(False)]:
        row = df.loc[ts]
        label = f"Volume > {multiple:g}× SMA({window})"
        rows.append(
            {
                "date": ts,
                "family": "volume_spike",
                "direction": "spike",
                "price": float(row["Volume"]),
                "y": float(row["Volume"]),
                "pane": "volume",
                "symbol": "diamond",
                "color": "#ffca28",
                "label": label,
                "stack_rank": 0,
                "vrect": True,
            }
        )
    return _marker_frame(rows)


def collect_markers(
    df: pd.DataFrame,
    *,
    ma_crosses: list[tuple[str, int, int]] | None = None,
    rsi_exits: bool = False,
    bb_events: bool = False,
    macd_crosses: bool = False,
    volume_spikes: bool = False,
    max_markers: int = DEFAULT_MAX_MARKERS,
    volume_multiple: float = VOLUME_SPIKE_MULTIPLE,
    volume_window: int = VOLUME_SMA_WINDOW,
) -> pd.DataFrame:
    """
    Run enabled detectors, dedupe same-bar/family, offset stacked price glyphs,
    combine hover labels per date, and keep the most recent ``max_markers`` events
    (counted on unique dates that have price/volume/rsi/macd markers).
    """
    frames: list[pd.DataFrame] = []
    for kind, fast, slow in ma_crosses or []:
        frames.append(detect_ma_cross(df, fast=fast, slow=slow, kind=kind))
    if rsi_exits:
        frames.append(detect_rsi_exit(df))
    if bb_events:
        frames.append(detect_bb_events(df))
    if macd_crosses:
        frames.append(detect_macd_cross(df))
    if volume_spikes:
        frames.append(
            detect_volume_spike(df, window=volume_window, multiple=volume_multiple)
        )

    nonempty = [f for f in frames if not f.empty]
    if not nonempty:
        return _empty_markers()

    events = pd.concat(nonempty, ignore_index=True)
    # Drop exact duplicate family+direction+pane+date rows
    events = events.drop_duplicates(subset=["date", "family", "direction", "pane"], keep="first")

    # Cap by unique event dates (most recent), using any pane as membership
    event_dates = (
        events.sort_values("date")["date"].drop_duplicates(keep="last").tail(max_markers)
    )
    events = events[events["date"].isin(set(event_dates))].copy()

    # Vertical offset for multiple price-pane glyphs on the same bar
    price_mask = events["pane"] == "price"
    events.loc[price_mask, "stack_rank"] = (
        events.loc[price_mask].groupby("date").cumcount()
    )

    def _offset_y(row: pd.Series) -> float:
        rank = int(row["stack_rank"])
        base = float(row["y"])
        # triangle-up sits under the low → stack further down; triangle-down above high → up
        if row["symbol"] == "triangle-up":
            return base * (1 - 0.008 * rank)
        if row["symbol"] == "triangle-down":
            return base * (1 + 0.008 * rank)
        # diamonds / circles at close: alternate slightly below/above
        sign = -1 if rank % 2 == 0 else 1
        return base * (1 + sign * 0.006 * ((rank // 2) + 1))

    events.loc[price_mask, "y"] = events.loc[price_mask].apply(_offset_y, axis=1)

    # Combined hover text for all price-pane rules firing on the same date
    combined = (
        events.loc[price_mask]
        .groupby("date")["label"]
        .apply(lambda s: " · ".join(dict.fromkeys(s.tolist())))
    )
    events["hover"] = events.apply(
        lambda r: combined.get(r["date"], r["label"]) if r["pane"] == "price" else r["label"],
        axis=1,
    )

    return events.sort_values(["date", "pane", "stack_rank"]).reset_index(drop=True)
