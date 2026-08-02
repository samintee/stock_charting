"""CLI to download OHLCV data from yfinance into data/."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from data_utils import (
    CLI_TIMEFRAME_CHOICES,
    INTERVAL_OPTIONS,
    fetch_history,
    looks_like_ticker,
    resolve_date_range,
    resolve_ticker_query,
    save_csv,
)


def pick_from_candidates(query: str, candidates: list) -> str | None:
    print(f"\nMultiple matches for “{query}”:")
    for i, match in enumerate(candidates, start=1):
        print(f"  {i}. {match.label}")
    print("  0. Cancel")
    while True:
        choice = input(f"Select 1-{len(candidates)}: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            return candidates[int(choice) - 1].symbol
        print("Invalid choice.")


def resolve_query_to_ticker(query: str) -> str | None:
    """Resolve a ticker or company name; prompt when several matches exist."""
    q = query.strip()
    if not q:
        return None
    try:
        resolved, candidates = resolve_ticker_query(q)
    except RuntimeError as exc:
        print(f"  {exc}")
        if looks_like_ticker(q):
            return q.upper()
        return None

    if resolved:
        if resolved.label != resolved.symbol:
            print(f"Resolved: {resolved.label}")
        return resolved.symbol
    if candidates:
        return pick_from_candidates(q, candidates)
    if looks_like_ticker(q):
        return q.upper()
    print(f"No ticker found for “{q}”.")
    return None


def get_ticker() -> str:
    while True:
        query = input("Enter ticker or company name (e.g. AAPL or Apple): ").strip()
        if not query:
            print("Input cannot be empty. Please try again.")
            continue
        ticker = resolve_query_to_ticker(query)
        if ticker:
            return ticker
        print("Please try again.")


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
    parser.add_argument(
        "ticker",
        nargs="?",
        help="Ticker symbol or company name (e.g. AAPL or Apple). Omit for prompts.",
    )
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
    raw_query = (args.ticker or "").strip()
    if raw_query:
        ticker = resolve_query_to_ticker(raw_query)
        if not ticker:
            raise SystemExit(f"Could not resolve ticker for “{raw_query}”.")
    else:
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
