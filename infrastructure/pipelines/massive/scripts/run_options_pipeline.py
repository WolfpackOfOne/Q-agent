"""Pull EOD options data from Massive.com and write LEAN-compatible alternative data.

Two kinds of output per underlying:

1. Options chain snapshot (greeks, IV, open interest) — a point-in-time
   capture of `list_snapshot_options_chain`, written as
   `alternative/massive/options/chains/<underlying>_<YYYYMMDD>.csv`.
   Run this daily (e.g. via cron/scheduled task) to build up a historical
   panel of EOD greeks/IV/OI snapshots.

2. Per-contract daily OHLCV aggregates via `list_aggs("O:...")`, written as
   `alternative/massive/options/aggregates/<contract_ticker>.csv`. This is
   true historical EOD price data (unlike the snapshot, which is always "now").

Usage:
    python scripts/run_options_pipeline.py
    python scripts/run_options_pipeline.py --underlyings SPY QQQ
    python scripts/run_options_pipeline.py --underlyings SPY --skip-chain-snapshot
    python scripts/run_options_pipeline.py --underlyings SPY \\
        --strike-range 0.95 1.05 --max-expirations 4 \\
        --start 2024-01-01 --end 2024-12-31

Requires MASSIVE_API_KEY (Massive "Advanced" tier for options — see
.env.example / claude.md). Untested against the live API.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv

from massive_lean import (
    DEFAULT_OPTIONS_UNDERLYINGS,
    MassiveAuthError,
    MassiveClient,
    iter_to_list,
    transform_option_daily_bars,
    transform_options_chain_snapshot,
    write_option_daily_aggregates,
    write_options_chain_snapshot,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEAN_DATA_ROOT = os.path.join(ROOT, "lean-data")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--underlyings", nargs="+", default=DEFAULT_OPTIONS_UNDERLYINGS,
        help=f"Underlying tickers to pull (default: {DEFAULT_OPTIONS_UNDERLYINGS})",
    )
    p.add_argument("--skip-chain-snapshot", action="store_true",
                    help="Skip the current options-chain snapshot (greeks/IV/OI).")
    p.add_argument("--skip-aggregates", action="store_true",
                    help="Skip per-contract daily OHLCV aggregate bars.")
    p.add_argument("--strike-range", nargs=2, type=float, default=[0.9, 1.1], metavar=("LOW", "HIGH"),
                    help="Strike filter as a fraction of underlying price, e.g. 0.9 1.1 (default: 0.9 1.1).")
    p.add_argument("--max-expirations", type=int, default=4,
                    help="Max number of upcoming expirations to include in the chain snapshot (default: 4).")
    p.add_argument("--start", default="2024-01-01", help="Aggregate bars start date YYYY-MM-DD")
    p.add_argument("--end", default=None, help="Aggregate bars end date YYYY-MM-DD (default: today)")
    p.add_argument(
        "--output", default=None,
        help="Override output root directory (default: infrastructure/pipelines/massive/lean-data)",
    )
    return p.parse_args()


def main() -> int:
    load_dotenv(os.path.join(ROOT, ".env"))
    args = parse_args()
    output_root = args.output or LEAN_DATA_ROOT
    today = dt.date.today().isoformat()

    try:
        client = MassiveClient()
    except MassiveAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    written, failed = 0, 0
    for underlying in args.underlyings:
        print(f"\n=== {underlying} ===")

        contract_tickers: list[str] = []

        if not args.skip_chain_snapshot:
            try:
                # ASSUMPTION: list_snapshot_options_chain accepts a bare
                # underlying ticker (no "O:"/"X:" prefix). expiration_date
                # filters narrow the chain to near-dated contracts.
                params = {
                    "expiration_date.gte": today,
                }
                chain_raw = iter_to_list(client.list_snapshot_options_chain(underlying, params=params))
                chain_df = transform_options_chain_snapshot(underlying, today, chain_raw)
                if chain_df.empty:
                    print("  chain snapshot: no contracts returned")
                else:
                    path = write_options_chain_snapshot(underlying, today, chain_df, output_root=output_root)
                    print(f"  chain snapshot: {len(chain_df)} contracts -> {path}")
                    written += 1
                    # Limit aggregate-bar pulls to the nearest N expirations
                    # to keep the default run small.
                    expirations = sorted(chain_df["expiration_date"].dropna().unique())[: args.max_expirations]
                    contract_tickers = (
                        chain_df[chain_df["expiration_date"].isin(expirations)]["contract_ticker"]
                        .dropna()
                        .tolist()
                    )
            except Exception as exc:
                print(f"  ERROR fetching chain snapshot: {exc}")
                failed += 1

        if not args.skip_aggregates:
            if not contract_tickers:
                print("  no contract tickers to pull aggregates for "
                      "(enable chain snapshot or pass explicit tickers)")
                continue
            for ticker in contract_tickers:
                try:
                    aggs = iter_to_list(
                        client.list_aggs(ticker, multiplier=1, timespan="day",
                                          from_=args.start, to=args.end)
                    )
                    df = transform_option_daily_bars(ticker, aggs)
                    if df.empty:
                        continue
                    path = write_option_daily_aggregates(ticker, df, output_root=output_root)
                    print(f"  {ticker}: {len(df)} bars -> {path}")
                    written += 1
                except Exception as exc:
                    print(f"  {ticker}: ERROR {exc}")
                    failed += 1

    print(f"\nDone. {written} files written, {failed} failed.")
    return 0 if failed == 0 or written > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
