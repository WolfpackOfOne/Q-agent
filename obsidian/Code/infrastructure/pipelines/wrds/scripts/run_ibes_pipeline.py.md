---
path: "infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py"
hub: "wrds"
lines: 112
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py"
---
# run_ibes_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py)

## Purpose

CLI for the IBES earnings pipeline.

Extracts consensus EPS estimates and actual EPS from WRDS IBES (skema profile),
computes standardized unexpected earnings (SUE), and publishes two CSVs for
local backtests and research notebooks.

Usage:
    python scripts/run_ibes_pipeline.py                            # 30-stock equity universe
    python scripts/run_ibes_pipeline.py --profile <additional>
    python scripts/run_ibes_pipeline.py --tickers AAPL MSFT GS    # Specific tickers
    python scripts/run_ibes_pipeline.py --start-year 2000          # From 2000 onward

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|ibes.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [34](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py#L34) |
| `EQUITY_UNIVERSE` | `[t for t in UNIVERSE if t not in ('SPY', 'SGOV')]` | [35](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py#L35) |

## Functions

### `main()`

```python
def main()
```
[line 38](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py#L38)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py (112 lines)
> ```python
> """CLI for the IBES earnings pipeline.
>
> Extracts consensus EPS estimates and actual EPS from WRDS IBES (skema profile),
> computes standardized unexpected earnings (SUE), and publishes two CSVs for
> local backtests and research notebooks.
>
> Usage:
>     python scripts/run_ibes_pipeline.py                            # 30-stock equity universe
>     python scripts/run_ibes_pipeline.py --profile <additional>
>     python scripts/run_ibes_pipeline.py --tickers AAPL MSFT GS    # Specific tickers
>     python scripts/run_ibes_pipeline.py --start-year 2000          # From 2000 onward
> """
>
> import argparse
> import os
> import sys
> import time
>
> import pandas as pd
>
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> from wrds_lean.connection import close_connection, set_connection_profile
> from wrds_lean.ibes import (
>     build_consensus_output,
>     build_surprise_output,
>     extract_actuals,
>     extract_consensus,
>     publish_consensus,
>     publish_surprise,
> )
> from wrds_lean.symbols import UNIVERSE
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
> EQUITY_UNIVERSE = [t for t in UNIVERSE if t not in ('SPY', 'SGOV')]
>
>
> def main():
>     parser = argparse.ArgumentParser(description='IBES earnings consensus + surprise pipeline')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Specific tickers (default: 30-stock equity universe)')
>     parser.add_argument('--profile', default='skema',
>                         help='Named WRDS profile (default: skema)')
>     parser.add_argument('--start-year', type=int, default=1980,
>                         help='First year to include (default: 1980)')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>     tickers = args.tickers if args.tickers else EQUITY_UNIVERSE
>
>     # --- Step 1: Extract ---
>     print(f"\n=== Extracting consensus estimates for {len(tickers)} tickers ===")
>     raw_cons = extract_consensus(tickers, start_year=args.start_year)
>     print(f"  {len(raw_cons)} consensus rows")
>
>     print(f"\n=== Extracting actual EPS for {len(tickers)} tickers ===")
>     raw_act = extract_actuals(tickers, start_year=args.start_year)
>     print(f"  {len(raw_act)} actuals rows")
>
>     found_cons = set(raw_cons['crsp_ticker'])
>     found_act = set(raw_act['crsp_ticker'])
>     missing = [t for t in tickers if t not in found_cons and t not in found_act]
>     if missing:
>         print(f"  Not found in IBES: {missing}")
>
>     # --- Step 2: Build outputs ---
>     print(f"\n=== Building consensus output ===")
>     consensus_df = build_consensus_output(raw_cons)
>     print(f"  {len(consensus_df)} rows")
>     print(f"  Date range: {consensus_df['StatDate'].min().date()} — "
>           f"{consensus_df['StatDate'].max().date()}")
>
>     print(f"\n=== Computing earnings surprise (SUE) ===")
>     surprise_df = build_surprise_output(raw_cons, raw_act)
>     valid_sue = surprise_df['SUE'].notna().sum()
>     print(f"  {len(surprise_df)} total rows, {valid_sue} with valid SUE")
>
>     if not surprise_df.empty:
>         print(f"\n  {'Ticker':<8} {'Ann':>4} {'Qtr':>4}  Latest annual SUE")
>         print(f"  {'------':<8} {'---':>4} {'---':>4}  -----------------")
>         for ticker, grp in surprise_df.groupby('Ticker'):
>             ann = grp[grp['Periodicity'] == 'ANN']
>             qtr = grp[grp['Periodicity'] == 'QTR']
>             if not ann.empty:
>                 latest = ann.sort_values('AnnouncementDate').iloc[-1]
>                 sue_str = (
>                     f"{latest['SUE']:.2f} ({latest['AnnouncementDate'].date()})"
>                     if pd.notna(latest['SUE']) else
>                     f"N/A ({latest['AnnouncementDate'].date()})"
>                 )
>             else:
>                 sue_str = 'no annual data'
>             print(f"  {ticker:<8} {len(ann):>4} {len(qtr):>4}  {sue_str}")
>
>     # --- Step 3: Publish ---
>     print(f"\n=== Publishing to lean-data ===")
>     path1 = publish_consensus(consensus_df, LEAN_DATA)
>     print(f"  Consensus written to {path1}")
>     path2 = publish_surprise(surprise_df, LEAN_DATA)
>     print(f"  Surprise   written to {path2}")
>
>     elapsed = time.time() - t0
>     print(f"\n=== IBES pipeline complete in {elapsed:.1f}s ===")
>     close_connection()
>
>
> if __name__ == '__main__':
>     main()
> ```
