---
path: "infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py"
hub: "wrds"
lines: 95
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py"
---
# run_sector_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py)

## Purpose

CLI for the sector classification pipeline.

Extracts GICS sector data from Compustat, maps to Morningstar sector codes,
and publishes a static sector map CSV for local backtests.

Usage:
    python scripts/run_sector_pipeline.py                           # 30-stock equity universe
    python scripts/run_sector_pipeline.py --profile new_university
    python scripts/run_sector_pipeline.py --tickers AAPL MSFT GS    # Specific tickers
    python scripts/run_sector_pipeline.py --include-dia-history      # Include all historical DIA members

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|sectors.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py#L24) |
| `HISTORICAL_DIA_EXTRAS` | `['AA', 'AIG', 'AMZN', 'BAC', 'C', 'DD', 'GE', 'GM', 'HPQ', 'IP', 'KFT', 'MO', 'NVDA', 'PFE', 'SHW', 'T', 'UTX', 'XOM']` | [27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py#L27) |

## Functions

### `main()`

```python
def main()
```
[line 33](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py#L33)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py (95 lines)
> ```python
> """CLI for the sector classification pipeline.
>
> Extracts GICS sector data from Compustat, maps to Morningstar sector codes,
> and publishes a static sector map CSV for local backtests.
>
> Usage:
>     python scripts/run_sector_pipeline.py                           # 30-stock equity universe
>     python scripts/run_sector_pipeline.py --profile new_university
>     python scripts/run_sector_pipeline.py --tickers AAPL MSFT GS    # Specific tickers
>     python scripts/run_sector_pipeline.py --include-dia-history      # Include all historical DIA members
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
> from wrds_lean.symbols import UNIVERSE
> from wrds_lean.sectors import extract_sectors, transform_sector_map, publish_sector_map
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
>
> # Historical DIA members not in the 30-stock equity universe (for completeness)
> HISTORICAL_DIA_EXTRAS = [
>     'AA', 'AIG', 'AMZN', 'BAC', 'C', 'DD', 'GE', 'GM', 'HPQ',
>     'IP', 'KFT', 'MO', 'NVDA', 'PFE', 'SHW', 'T', 'UTX', 'XOM',
> ]
>
>
> def main():
>     parser = argparse.ArgumentParser(description='Sector classification pipeline')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Specific tickers (default: 30-stock equity universe + benchmarks)')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--include-dia-history', action='store_true',
>                         help='Include historical DIA members not in the 30-stock equity universe')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>
>     # Build ticker list
>     if args.tickers:
>         tickers = args.tickers
>     else:
>         tickers = list(UNIVERSE)
>         if args.include_dia_history:
>             tickers.extend(HISTORICAL_DIA_EXTRAS)
>         # Deduplicate
>         tickers = sorted(set(tickers))
>
>     # --- Step 1: Extract from Compustat ---
>     print(f"=== Extracting sector data for {len(tickers)} tickers ===")
>     sectors_df = extract_sectors(tickers)
>     print(f"  {len(sectors_df)} rows returned")
>
>     found_tickers = set(sectors_df['ticker'])
>     missing = [t for t in tickers if t not in found_tickers]
>     if missing:
>         print(f"  Not found in Compustat: {missing}")
>         print(f"  (ETFs like SPY/SGOV/DIA/BIL won't have Compustat entries)")
>
>     # --- Step 2: Transform ---
>     print(f"\n=== Mapping GICS to Morningstar sectors ===")
>     sector_map = transform_sector_map(sectors_df)
>
>     # Display the mapping
>     print(f"\n  {'Ticker':<8} {'Company':<30} {'GICS':<6} {'MS Code':<8} {'MS Sector'}")
>     print(f"  {'------':<8} {'-------':<30} {'----':<6} {'-------':<8} {'---------'}")
>     for _, row in sector_map.iterrows():
>         print(f"  {row['Ticker']:<8} {str(row['CompanyName'])[:29]:<30} "
>               f"{str(row['GICSSector']):<6} {str(row['MorningstarSectorCode']):<8} "
>               f"{row['MorningstarSectorName']}")
>
>     # --- Step 3: Publish ---
>     print(f"\n=== Publishing sector map ===")
>     filepath = publish_sector_map(sector_map, LEAN_DATA)
>     print(f"  Written to {filepath}")
>
>     elapsed = time.time() - t0
>     print(f"\n=== Sector pipeline complete in {elapsed:.1f}s ===")
>
>     close_connection()
>
>
> if __name__ == '__main__':
>     main()
> ```
