---
path: "infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py"
hub: "wrds"
lines: 89
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py"
---
# run_fundamentals_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py)

## Purpose

CLI for the Piotroski F-score fundamentals pipeline.

Extracts annual fundamentals from Compustat (comp.funda), computes 9-signal
Piotroski F-scores with point-in-time availability dates, and publishes a flat
CSV for local backtests and research notebooks.

Usage:
    python scripts/run_fundamentals_pipeline.py                         # 30-stock equity universe
    python scripts/run_fundamentals_pipeline.py --profile new_university
    python scripts/run_fundamentals_pipeline.py --tickers AAPL MSFT GS  # Specific tickers
    python scripts/run_fundamentals_pipeline.py --start-year 2000        # From 2000

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|fundamentals.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [25](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py#L25) |
| `EQUITY_UNIVERSE` | `[t for t in UNIVERSE if t not in ('SPY', 'SGOV')]` | [28](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py#L28) |

## Functions

### `main()`

```python
def main()
```
[line 31](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py#L31)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py (89 lines)
> ```python
> """CLI for the Piotroski F-score fundamentals pipeline.
>
> Extracts annual fundamentals from Compustat (comp.funda), computes 9-signal
> Piotroski F-scores with point-in-time availability dates, and publishes a flat
> CSV for local backtests and research notebooks.
>
> Usage:
>     python scripts/run_fundamentals_pipeline.py                         # 30-stock equity universe
>     python scripts/run_fundamentals_pipeline.py --profile new_university
>     python scripts/run_fundamentals_pipeline.py --tickers AAPL MSFT GS  # Specific tickers
>     python scripts/run_fundamentals_pipeline.py --start-year 2000        # From 2000
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
> from wrds_lean.fundamentals import compute_piotroski, extract_fundamentals, publish_piotroski
> from wrds_lean.symbols import UNIVERSE
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
>
> # Equities only — exclude ETFs which have no Compustat entries
> EQUITY_UNIVERSE = [t for t in UNIVERSE if t not in ('SPY', 'SGOV')]
>
>
> def main():
>     parser = argparse.ArgumentParser(description='Piotroski F-score fundamentals pipeline')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Specific tickers (default: 30-stock equity universe, excludes ETFs)')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--start-year', type=int, default=1997,
>                         help='First fiscal year to include in output (default: 1997)')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>
>     tickers = args.tickers if args.tickers else EQUITY_UNIVERSE
>
>     # --- Step 1: Extract from comp.funda ---
>     print(f"=== Extracting fundamentals for {len(tickers)} tickers (from fyear {args.start_year - 1}) ===")
>     raw_df = extract_fundamentals(tickers, start_year=args.start_year)
>     print(f"  {len(raw_df)} rows returned from comp.funda")
>
>     found = set(raw_df['tic'])
>     missing = [t for t in tickers if t not in found]
>     if missing:
>         print(f"  Not found in Compustat: {missing}")
>
>     # --- Step 2: Compute F-scores ---
>     print(f"\n=== Computing Piotroski F-scores ===")
>     scores_df = compute_piotroski(raw_df)
>     print(f"  {len(scores_df)} scored rows (after dropping first fiscal year per ticker)")
>
>     # Summary table
>     print(f"\n  {'Ticker':<8} {'Obs':>4}  {'F-Score range':<15}  Latest")
>     print(f"  {'------':<8} {'---':>4}  {'-------------':<15}  ------")
>     for ticker, grp in scores_df.groupby('Ticker'):
>         latest = grp.sort_values('AvailableDate').iloc[-1]
>         score_range = f"{grp['F_Score'].min()}-{grp['F_Score'].max()}"
>         print(f"  {ticker:<8} {len(grp):>4}  {score_range:<15}  "
>               f"{latest['F_Score']}/9 ({latest['AvailableDate'].date()})")
>
>     # --- Step 3: Publish ---
>     print(f"\n=== Publishing to lean-data ===")
>     filepath = publish_piotroski(scores_df, LEAN_DATA)
>     print(f"  Written to {filepath}")
>     print(f"  Columns: {list(scores_df.columns)}")
>     print(f"  Date range: {scores_df['AvailableDate'].min().date()} — "
>           f"{scores_df['AvailableDate'].max().date()}")
>
>     elapsed = time.time() - t0
>     print(f"\n=== Fundamentals pipeline complete in {elapsed:.1f}s ===")
>
>     close_connection()
>
>
> if __name__ == '__main__':
>     main()
> ```
