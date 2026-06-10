"""Pull EOD daily bars for US futures contracts from Massive.com and write LEAN zips.

Usage:
    python scripts/run_futures_pipeline.py
    python scripts/run_futures_pipeline.py --roots ES NQ CL
    python scripts/run_futures_pipeline.py --roots ES --start 2024-01-01 --end 2024-12-31
    python scripts/run_futures_pipeline.py --roots ES --contracts ESZ24 ESH25

Requires MASSIVE_API_KEY (see .env.example / claude.md). Untested against the
live API — see claude.md "Known limitations" before relying on this.

Output:
    lean-data/future/<market>/daily/<symbol>_trade.zip
    lean-data/alternative/massive/futures/contracts/<root>.csv  (reference data)
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv

from massive_lean import (
    DEFAULT_FUTURES_ROOTS,
    FUTURES_ROOT_MARKET,
    MassiveAuthError,
    MassiveClient,
    iter_to_list,
    transform_futures_contracts,
    transform_futures_daily_bars,
    write_futures_contracts,
    write_futures_daily,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEAN_DATA_ROOT = os.path.join(ROOT, "lean-data")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--roots", nargs="+", default=DEFAULT_FUTURES_ROOTS,
        help=f"Root/product symbols to pull (default: {DEFAULT_FUTURES_ROOTS})",
    )
    p.add_argument(
        "--contracts", nargs="*", default=None,
        help=(
            "Explicit contract tickers to pull instead of discovering them via "
            "list_futures_contracts (e.g. ESZ24 ESH25)."
        ),
    )
    p.add_argument("--start", default="2020-01-01", help="Start date YYYY-MM-DD (default: 2020-01-01)")
    p.add_argument("--end", default=None, help="End date YYYY-MM-DD (default: today)")
    p.add_argument(
        "--output", default=None,
        help="Override output root directory (default: infrastructure/pipelines/massive/lean-data)",
    )
    return p.parse_args()


def main() -> int:
    load_dotenv(os.path.join(ROOT, ".env"))
    args = parse_args()
    output_root = args.output or LEAN_DATA_ROOT

    try:
        client = MassiveClient()
    except MassiveAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    written, failed = 0, 0
    for root in args.roots:
        market = FUTURES_ROOT_MARKET.get(root.upper())
        if market is None:
            print(f"  {root}: no market mapping in config.FUTURES_ROOT_MARKET — skipping")
            failed += 1
            continue

        print(f"\n=== {root} ({market}) ===")
        try:
            contracts_raw = iter_to_list(client.list_futures_contracts(product_code=root))
        except Exception as exc:
            print(f"  ERROR listing contracts: {exc}")
            contracts_raw = []

        if contracts_raw:
            contracts_df = transform_futures_contracts(contracts_raw)
            ref_path = write_futures_contracts(root, contracts_df, output_root=output_root)
            print(f"  contracts reference -> {ref_path} ({len(contracts_df)} rows)")
            tickers = args.contracts or [
                t for t in contracts_df["ticker"].dropna().tolist()
            ]
            expirations = dict(
                zip(contracts_df["ticker"], contracts_df["expiration_date"])
            )
        else:
            tickers = args.contracts or []
            expirations = {}
            if not tickers:
                print(f"  No contracts discovered for {root} and no --contracts given — skipping")
                failed += 1
                continue

        for ticker in tickers:
            try:
                aggs = iter_to_list(
                    client.list_futures_aggregates(
                        ticker=ticker, resolution="day", from_=args.start, to=args.end,
                    )
                )
                df = transform_futures_daily_bars(aggs)
                if df.empty:
                    print(f"  {ticker}: no bars returned")
                    continue
                expiration = (expirations.get(ticker) or "20501231").replace("-", "")
                path = write_futures_daily(ticker, market, expiration, df, output_root=output_root)
                print(f"  {ticker}: {len(df)} bars -> {path}")
                written += 1
            except Exception as exc:
                print(f"  {ticker}: ERROR {exc}")
                failed += 1

    print(f"\nDone. {written} contracts written, {failed} failed.")
    return 0 if failed == 0 or written > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
