import pandas as pd


TIMEFRAME_OFFSETS = {
    "1M":  {"months": 1},
    "3M":  {"months": 3},
    "6M":  {"months": 6},
    "1Y":  {"years": 1},
    "2Y":  {"years": 2},
    "5Y":  {"years": 5},
}

MA_COLORS = {
    20:  "#f0a500",
    50:  "#00bcd4",
    200: "#e040fb",
}


def _drop_extra_columns(df: pd.DataFrame) -> pd.DataFrame:
    drop = [c for c in ("Dividends", "Stock Splits") if c in df.columns]
    return df.drop(columns=drop)


def load_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file, parse_dates=["Date"], index_col="Date")
    df = _drop_extra_columns(df)
    df.sort_index(inplace=True)
    return df


def filter_timeframe(
    df: pd.DataFrame,
    preset: str,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    if preset == "All":
        return df.copy()
    if preset == "Custom":
        return df.loc[str(start_date): str(end_date)].copy()
    offset = pd.DateOffset(**TIMEFRAME_OFFSETS[preset])
    start = df.index.max() - offset
    return df.loc[start:].copy()


def resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = df.resample("W").agg(
        Open=("Open", "first"),
        High=("High", "max"),
        Low=("Low", "min"),
        Close=("Close", "last"),
        Volume=("Volume", "sum"),
    )
    return weekly.dropna()


def compute_ma(df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    df = df.copy()
    for w in windows:
        df[f"SMA_{w}"] = df["Close"].rolling(w).mean()
    return df
