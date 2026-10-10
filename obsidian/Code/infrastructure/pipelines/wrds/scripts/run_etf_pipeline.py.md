---
path: "infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py"
hub: "wrds"
lines: 121
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py"
---
# run_etf_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py)

## Purpose

CLI for the ETF constituent universe pipeline.

Extracts DIA (or other ETF) constituent data from CRSP mutual fund holdings,
transforms to LEAN format, and publishes daily universe CSV files.

Usage:
    python scripts/run_etf_pipeline.py                    # DIA, full date range
    python scripts/run_etf_pipeline.py --profile new_university
    python scripts/run_etf_pipeline.py --start 2018-01-01 --end 2019-01-01
    python scripts/run_etf_pipeline.py --etf dia

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|etf_constituents.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sid.py|sid.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py#L30) |
| `MAP_FILES_DIR` | `os.path.join(LEAN_DATA, 'equity', 'usa', 'map_files')` | [31](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py#L31) |

## Functions

### `main()`

```python
def main()
```
[line 34](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py#L34)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py (121 lines)
> ```python
> """CLI for the ETF constituent universe pipeline.
>
> Extracts DIA (or other ETF) constituent data from CRSP mutual fund holdings,
> transforms to LEAN format, and publishes daily universe CSV files.
>
> Usage:
>     python scripts/run_etf_pipeline.py                    # DIA, full date range
>     python scripts/run_etf_pipeline.py --profile new_university
>     python scripts/run_etf_pipeline.py --start 2018-01-01 --end 2019-01-01
>     python scripts/run_etf_pipeline.py --etf dia
> """
>
> import argparse
> import os
> import sys
> import time
>
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> from wrds_lean.connection import close_connection, set_connection_profile
> from wrds_lean.sid import build_sid_lookup
> from wrds_lean.etf_constituents import (
>     DIA_PORTNOS,
>     extract_holdings,
>     extract_trading_days,
>     transform_to_lean,
>     publish_etf_universe,
> )
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
> MAP_FILES_DIR = os.path.join(LEAN_DATA, 'equity', 'usa', 'map_files')
>
>
> def main():
>     parser = argparse.ArgumentParser(description='ETF constituent universe pipeline')
>     parser.add_argument('--etf', default='dia',
>                         help='ETF ticker (default: dia)')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--start', default='2002-01-01',
>                         help='Start date (default: 2002-01-01)')
>     parser.add_argument('--end', default='2026-04-18',
>                         help='End date (default: 2026-04-18)')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>
>     # --- Step 1: Build SID lookup from local map files ---
>     print("=== Building SID lookup from map files ===")
>     sid_lookup = build_sid_lookup(MAP_FILES_DIR)
>     print(f"  {len(sid_lookup)} tickers with SIDs")
>
>     # --- Step 2: Extract holdings from CRSP ---
>     etf = args.etf.upper()
>     if etf == 'DIA':
>         portnos = DIA_PORTNOS
>     else:
>         print(f"ERROR: ETF '{etf}' not configured. Only DIA is supported.")
>         print("  To add a new ETF, find its crsp_portno in crsp.fund_names")
>         sys.exit(1)
>
>     print(f"\n=== Extracting {etf} holdings from CRSP ({args.start} to {args.end}) ===")
>     holdings_df = extract_holdings(portnos, start=args.start, end=args.end)
>     n_reports = holdings_df['report_dt'].nunique()
>     print(f"  {len(holdings_df)} holding rows across {n_reports} report dates")
>
>     if holdings_df.empty:
>         print("  No holdings found. Check date range and portfolio numbers.")
>         close_connection()
>         sys.exit(1)
>
>     # Show tickers found
>     tickers_found = set(holdings_df['ticker'].dropna())
>     tickers_with_sid = tickers_found & set(sid_lookup.keys())
>     tickers_missing_sid = tickers_found - set(sid_lookup.keys())
>     print(f"  {len(tickers_with_sid)} tickers have map files (SIDs)")
>     if tickers_missing_sid:
>         print(f"  WARNING: {len(tickers_missing_sid)} tickers missing map files: {sorted(tickers_missing_sid)}")
>         print("  These tickers will be SKIPPED in universe files.")
>         print("  Run the equity pipeline for these tickers first.")
>
>     # --- Step 3: Get trading days ---
>     # Use the actual date range from the holdings data
>     first_report = holdings_df['report_dt'].min()
>     print(f"\n=== Fetching trading days ({first_report} to {args.end}) ===")
>     trading_days = extract_trading_days(str(first_report), args.end)
>     print(f"  {len(trading_days)} trading days")
>
>     # --- Step 4: Transform to LEAN format ---
>     print(f"\n=== Transforming to LEAN ETF universe format ===")
>     daily_output = transform_to_lean(holdings_df, sid_lookup, trading_days)
>     print(f"  {len(daily_output)} daily universe files to write")
>
>     # Show sample
>     if daily_output:
>         sample_date = sorted(daily_output.keys())[0]
>         sample_lines = daily_output[sample_date]
>         print(f"\n  Sample ({sample_date}, {len(sample_lines)} constituents):")
>         for line in sample_lines[:3]:
>             print(f"    {line}")
>         if len(sample_lines) > 3:
>             print(f"    ... and {len(sample_lines) - 3} more")
>
>     # --- Step 5: Publish ---
>     print(f"\n=== Publishing to lean-data ===")
>     universe_dir = publish_etf_universe(args.etf, daily_output, LEAN_DATA)
>     print(f"  Written to {universe_dir}")
>
>     elapsed = time.time() - t0
>     print(f"\n=== ETF constituent pipeline complete in {elapsed:.1f}s ===")
>
>     close_connection()
>
>
> if __name__ == '__main__':
>     main()
> ```
