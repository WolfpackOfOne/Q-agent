"""CLI for the quarterly financial-statement fundamentals pipeline.

Extracts income statement, balance sheet, and cash-flow items per fiscal
quarter from Compustat (comp.fundq), attaches point-in-time availability
dates (rdq), and publishes a flat CSV for local backtests and research.

Usage:
    python scripts/run_quarterly_fundamentals_pipeline.py                        # 30-stock equity universe
    python scripts/run_quarterly_fundamentals_pipeline.py --tickers AAPL MSFT GS  # Specific tickers
    python scripts/run_quarterly_fundamentals_pipeline.py --start-year 2000       # From fiscal 2000
    python scripts/run_quarterly_fundamentals_pipeline.py --profile new_university

Credentials: the wrds package needs a username — set WRDS_USERNAME (or a
named profile); the password is read from ~/.pgpass.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wrds_lean.connection import close_connection, set_connection_profile
from wrds_lean.quarterly_fundamentals import (
    extract_quarterly_fundamentals,
    publish_quarterly_fundamentals,
    tidy_quarterly_fundamentals,
)
from wrds_lean.symbols import UNIVERSE

LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')

# Equities only — ETFs have no Compustat entries
EQUITY_UNIVERSE = [t for t in UNIVERSE if t not in ('SPY', 'SGOV')]


def main():
    parser = argparse.ArgumentParser(description='Quarterly fundamentals pipeline (comp.fundq)')
    parser.add_argument('--tickers', nargs='+', default=None,
                        help='Specific tickers (default: 30-stock equity universe, excludes ETFs)')
    parser.add_argument('--profile', default=None,
                        help='Named WRDS profile from .wrds_profiles.json')
    parser.add_argument('--start-year', type=int, default=1997,
                        help='First fiscal year to include (default: 1997)')
    args = parser.parse_args()

    set_connection_profile(args.profile)
    if args.profile:
        print(f"Using WRDS profile: {args.profile}")

    t0 = time.time()
    tickers = args.tickers if args.tickers else EQUITY_UNIVERSE

    print(f"=== Extracting quarterly fundamentals for {len(tickers)} tickers (fyearq >= {args.start_year}) ===")
    raw_df = extract_quarterly_fundamentals(tickers, start_year=args.start_year)
    print(f"  {len(raw_df)} rows returned from comp.fundq")

    found = set(raw_df['tic'])
    missing = [t for t in tickers if t not in found]
    if missing:
        print(f"  Not found in Compustat: {missing}")

    print("\n=== Attaching point-in-time availability dates ===")
    tidy_df = tidy_quarterly_fundamentals(raw_df)
    n_rdq = tidy_df['ReportDate'].notna().sum()
    print(f"  {len(tidy_df)} rows after restatement dedupe; "
          f"{n_rdq} have rdq, {len(tidy_df) - n_rdq} use datadate + filing-lag fallback")

    print(f"\n  {'Ticker':<8} {'Qtrs':>5}  {'First avail.':<12}  {'Last avail.':<12}")
    print(f"  {'------':<8} {'----':>5}  {'------------':<12}  {'-----------':<12}")
    for ticker, grp in tidy_df.groupby('Ticker'):
        print(f"  {ticker:<8} {len(grp):>5}  {grp['AvailableDate'].min().date()!s:<12}  "
              f"{grp['AvailableDate'].max().date()!s:<12}")

    print("\n=== Publishing to lean-data ===")
    filepath = publish_quarterly_fundamentals(tidy_df, LEAN_DATA)
    print(f"  Written to {filepath}")
    print(f"  {len(tidy_df.columns)} columns")

    print(f"\n=== Quarterly fundamentals pipeline complete in {time.time() - t0:.1f}s ===")
    close_connection()


if __name__ == '__main__':
    main()
