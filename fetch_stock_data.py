import yfinance as yf
import os
from datetime import datetime, timedelta


TIMEFRAME_OPTIONS = {
    "1": ("1 month", 30),
    "2": ("3 months", 90),
    "3": ("6 months", 180),
    "4": ("1 year", 365),
    "5": ("2 years", 730),
    "6": ("5 years", 1825),
    "7": ("custom", None),
}


def get_ticker() -> str:
    while True:
        ticker = input("Enter stock ticker symbol (e.g. AAPL): ").strip().upper()
        if ticker:
            return ticker
        print("Ticker cannot be empty. Please try again.")


def get_timeframe() -> tuple[str, str]:
    print("\nSelect timeframe:")
    for key, (label, _) in TIMEFRAME_OPTIONS.items():
        print(f"  {key}. {label}")

    while True:
        choice = input("Enter choice (1-7): ").strip()
        if choice not in TIMEFRAME_OPTIONS:
            print("Invalid choice. Please enter a number between 1 and 7.")
            continue

        label, days = TIMEFRAME_OPTIONS[choice]

        if choice == "7":
            start, end = get_custom_dates()
        else:
            end = datetime.today()
            start = end - timedelta(days=days)
            start = start.strftime("%Y-%m-%d")
            end = end.strftime("%Y-%m-%d")

        return start, end


def get_custom_dates() -> tuple[str, str]:
    date_fmt = "%Y-%m-%d"
    while True:
        try:
            start = input("  Start date (YYYY-MM-DD): ").strip()
            datetime.strptime(start, date_fmt)
            end = input("  End date   (YYYY-MM-DD): ").strip()
            datetime.strptime(end, date_fmt)
            if start >= end:
                print("  Start date must be before end date.")
                continue
            return start, end
        except ValueError:
            print("  Invalid date format. Use YYYY-MM-DD.")


def fetch_data(ticker: str, start: str, end: str):
    print(f"\nFetching {ticker} daily data from {start} to {end}...")
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end, interval="1d", auto_adjust=True)

    if df.empty:
        print(f"No data returned for '{ticker}'. Check the ticker symbol and date range.")
        return None

    df.index = df.index.tz_localize(None)
    df.index.name = "Date"
    df.index = df.index.strftime("%Y-%m-%d")
    return df


def save_csv(df, ticker: str, start: str, end: str) -> str:
    filename = f"{ticker}_{start}_{end}.csv"
    output_path = os.path.join(os.path.dirname(__file__), filename)
    df.to_csv(output_path)
    return output_path


def main():
    print("=== Stock Data Fetcher ===\n")
    ticker = get_ticker()
    start, end = get_timeframe()

    df = fetch_data(ticker, start, end)
    if df is None:
        return

    path = save_csv(df, ticker, start, end)
    print(f"\nSaved {len(df)} rows to: {path}")
    print(df[["Open", "High", "Low", "Close", "Volume"]].tail(5).to_string())


if __name__ == "__main__":
    main()
