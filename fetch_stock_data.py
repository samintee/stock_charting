"""CLI to download OHLCV data from yfinance into data/."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from data_utils import (
    CLI_TIMEFRAME_CHOICES,
    INTERVAL_OPTIONS,
    fetch_history,
    resolve_date_range,
    save_csv,
)


def get_ticker() -> str:
    while True:
        ticker = input("Enter stock ticker symbol (e.g. AAPL): ").strip().upper()
        if ticker:
            return ticker
        print("Ticker cannot be empty. Please try again.")


def get_interval() -> str:
    print("\nSelect interval:")
    for i, interval in enumerate(INTERVAL_OPTIONS, start=1):
        print(f"  {i}. {interval}")
    while True:
        choice = input(f"Enter choice (1-{len(INTERVAL_OPTIONS)}) [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(INTERVAL_OPTIONS):
            return INTERVAL_OPTIONS[int(choice) - 1]
        print("Invalid choice.")


def get_timeframe() -> tuple[str, str]:
    print("\nSelect timeframe:")
    for key, (label, _) in CLI_TIMEFRAME_CHOICES.items():
        print(f"  {key}. {label}")

    while True:
        choice = input("Enter choice (1-7): ").strip()
        if choice not in CLI_TIMEFRAME_CHOICES:
            print("Invalid choice. Please enter a number between 1 and 7.")
            continue

        _, preset = CLI_TIMEFRAME_CHOICES[choice]
        if preset == "Custom":
            start, end = get_custom_dates()
            return start, end
        return resolve_date_range(preset)


def get_custom_dates() -> tuple[str, str]:
    date_fmt = "%Y-%m-%d"
    while True:
        try:
            start = input("  Start date (YYYY-MM-DD): ").strip()
            datetime.strptime(start, date_fmt)
            end = input("  End date   (YYYY-MM-DD): ").strip()
            datetime.strptime(end, date_fmt)
            return resolve_date_range("Custom", start, end)
        except ValueError as exc:
            print(f"  {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download stock OHLCV data from yfinance into data/.",
    )
    parser.add_argument("ticker", nargs="?", help="Ticker symbol (e.g. AAPL). Omit for prompts.")
    parser.add_argument(
        "--preset",
        choices=[p for _, p in CLI_TIMEFRAME_CHOICES.values() if p != "Custom"],
        help="Lookback preset using calendar DateOffsets (same as the chart app).",
    )
    parser.add_argument("--start", help="Start date YYYY-MM-DD (use with --end).")
    parser.add_argument("--end", help="End date YYYY-MM-DD (use with --start).")
    parser.add_argument(
        "--interval",
        choices=INTERVAL_OPTIONS,
        default=None,
        help="Bar interval (default: 1d, or prompted interactively).",
    )
    return parser


def resolve_from_args(args: argparse.Namespace) -> tuple[str, str, str, str]:
    ticker = (args.ticker or "").strip().upper()
    if not ticker:
        ticker = get_ticker()

    if args.start or args.end:
        if not (args.start and args.end):
            raise SystemExit("Provide both --start and --end for a custom range.")
        start, end = resolve_date_range("Custom", args.start, args.end)
    elif args.preset:
        start, end = resolve_date_range(args.preset)
    elif args.ticker:
        # Non-interactive partial args: default to 1Y
        start, end = resolve_date_range("1Y")
    else:
        start, end = get_timeframe()

    if args.interval:
        interval = args.interval
    elif args.ticker:
        interval = "1d"
    else:
        interval = get_interval()

    return ticker, start, end, interval


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    print("=== Stock Data Fetcher ===\n")
    try:
        ticker, start, end, interval = resolve_from_args(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Fetching {ticker} ({interval}) from {start} to {end}...")
    df = fetch_history(ticker, start, end, interval=interval)
    if df.empty:
        print(f"No data returned for '{ticker}'. Check the ticker symbol and date range.")
        return 1

    path = save_csv(df, ticker, start, end, interval=interval)
    print(f"\nSaved {len(df)} rows to: {path}")
    print(df[["Open", "High", "Low", "Close", "Volume"]].tail(5).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
