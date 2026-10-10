---
path: "infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py"
hub: "wrds"
lines: 172
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py"
---
# run_broad_ibes_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py)

## Purpose

Broad IBES earnings pipeline: all tickers that ever scored F >= 7.

Reads the Piotroski F-Score CSV to identify the target universe, then pulls
IBES consensus and surprise data for those tickers via an additional WRDS profile.

Usage:
    caffeinate -dims python scripts/run_broad_ibes_pipeline.py
    caffeinate -dims python scripts/run_broad_ibes_pipeline.py --min-fscore 8
    caffeinate -dims python scripts/run_broad_ibes_pipeline.py --start-year 2000

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|ibes.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [31](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L31) |
| `SCORES_PATH` | `os.path.join(LEAN_DATA, 'alternative', 'fundamentals', 'piotroski_scores.csv')` | [32](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L32) |
| `BATCH_SIZE` | `500` | [35](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L35) |

## Functions

### `load_target_tickers()`

```python
def load_target_tickers(min_fscore)
```
[line 38](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L38)

Load tickers with F >= min_fscore from the Piotroski scores CSV.

### `extract_consensus_batched()`

```python
def extract_consensus_batched(tickers, start_year)
```
[line 45](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L45)

Pull consensus data in batches to handle large ticker lists.

### `extract_actuals_batched()`

```python
def extract_actuals_batched(tickers, start_year)
```
[line 67](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L67)

Pull actuals data in batches.

### `main()`

```python
def main()
```
[line 89](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py#L89)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py (172 lines)
> ```python
> """Broad IBES earnings pipeline: all tickers that ever scored F >= 7.
>
> Reads the Piotroski F-Score CSV to identify the target universe, then pulls
> IBES consensus and surprise data for those tickers via an additional WRDS profile.
>
> Usage:
>     caffeinate -dims python scripts/run_broad_ibes_pipeline.py
>     caffeinate -dims python scripts/run_broad_ibes_pipeline.py --min-fscore 8
>     caffeinate -dims python scripts/run_broad_ibes_pipeline.py --start-year 2000
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
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
> SCORES_PATH = os.path.join(LEAN_DATA, 'alternative', 'fundamentals', 'piotroski_scores.csv')
>
> # Process tickers in batches to avoid huge IN clauses
> BATCH_SIZE = 500
>
>
> def load_target_tickers(min_fscore):
>     """Load tickers with F >= min_fscore from the Piotroski scores CSV."""
>     scores = pd.read_csv(SCORES_PATH)
>     high = scores[scores['F_Score'] >= min_fscore]['Ticker'].unique()
>     return sorted(high)
>
>
> def extract_consensus_batched(tickers, start_year):
>     """Pull consensus data in batches to handle large ticker lists."""
>     all_dfs = []
>     total = len(tickers)
>     for i in range(0, total, BATCH_SIZE):
>         batch = tickers[i:i + BATCH_SIZE]
>         batch_num = i // BATCH_SIZE + 1
>         total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
>         print(f"  Consensus batch {batch_num}/{total_batches} "
>               f"({len(batch)} tickers)...")
>         try:
>             df = extract_consensus(batch, start_year=start_year)
>             all_dfs.append(df)
>             print(f"    {len(df):,} rows")
>         except Exception as e:
>             print(f"    ERROR: {e}")
>             continue
>     if all_dfs:
>         return pd.concat(all_dfs, ignore_index=True)
>     return pd.DataFrame()
>
>
> def extract_actuals_batched(tickers, start_year):
>     """Pull actuals data in batches."""
>     all_dfs = []
>     total = len(tickers)
>     for i in range(0, total, BATCH_SIZE):
>         batch = tickers[i:i + BATCH_SIZE]
>         batch_num = i // BATCH_SIZE + 1
>         total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
>         print(f"  Actuals batch {batch_num}/{total_batches} "
>               f"({len(batch)} tickers)...")
>         try:
>             df = extract_actuals(batch, start_year=start_year)
>             all_dfs.append(df)
>             print(f"    {len(df):,} rows")
>         except Exception as e:
>             print(f"    ERROR: {e}")
>             continue
>     if all_dfs:
>         return pd.concat(all_dfs, ignore_index=True)
>     return pd.DataFrame()
>
>
> def main():
>     parser = argparse.ArgumentParser(
>         description='Broad IBES earnings pipeline for Piotroski high-scorers')
>     parser.add_argument('--profile', default='skema',
>                         help='Named WRDS profile (default: skema)')
>     parser.add_argument('--min-fscore', type=int, default=7,
>                         help='Minimum F-Score to include (default: 7)')
>     parser.add_argument('--start-year', type=int, default=1980,
>                         help='First year to include (default: 1980)')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>
>     # Load target tickers from F-Score CSV
>     if not os.path.exists(SCORES_PATH):
>         print(f"ERROR: F-Score CSV not found at {SCORES_PATH}")
>         print("Run run_broad_fscore_pipeline.py --scores-only first.")
>         sys.exit(1)
>
>     tickers = load_target_tickers(args.min_fscore)
>     print(f"\nTarget universe: {len(tickers):,} tickers with F >= {args.min_fscore}")
>
>     # --- Consensus ---
>     print(f"\n{'=' * 70}")
>     print(f"Extracting consensus estimates (from {args.start_year})")
>     print(f"{'=' * 70}")
>     raw_cons = extract_consensus_batched(tickers, args.start_year)
>     print(f"\nTotal consensus rows: {len(raw_cons):,}")
>
>     if raw_cons.empty:
>         print("No consensus data found. Check IBES access with --profile <additional>.")
>         close_connection()
>         return
>
>     found_tickers = raw_cons['crsp_ticker'].nunique()
>     print(f"Tickers with IBES coverage: {found_tickers:,} / {len(tickers):,}")
>
>     # --- Actuals ---
>     print(f"\n{'=' * 70}")
>     print(f"Extracting actual EPS (from {args.start_year})")
>     print(f"{'=' * 70}")
>     raw_act = extract_actuals_batched(tickers, args.start_year)
>     print(f"\nTotal actuals rows: {len(raw_act):,}")
>
>     # --- Build outputs ---
>     print(f"\n{'=' * 70}")
>     print("Building outputs")
>     print(f"{'=' * 70}")
>
>     print("Building consensus output...")
>     consensus_df = build_consensus_output(raw_cons)
>     print(f"  {len(consensus_df):,} rows, "
>           f"{consensus_df['Ticker'].nunique():,} tickers")
>
>     print("Computing earnings surprise (SUE)...")
>     surprise_df = build_surprise_output(raw_cons, raw_act)
>     valid_sue = surprise_df['SUE'].notna().sum()
>     print(f"  {len(surprise_df):,} rows, {valid_sue:,} with valid SUE")
>
>     # --- Publish ---
>     print(f"\n{'=' * 70}")
>     print("Publishing")
>     print(f"{'=' * 70}")
>     path1 = publish_consensus(consensus_df, LEAN_DATA)
>     print(f"  Consensus: {path1}")
>     path2 = publish_surprise(surprise_df, LEAN_DATA)
>     print(f"  Surprise:  {path2}")
>
>     elapsed = time.time() - t0
>     print(f"\n{'=' * 70}")
>     print(f"IBES pipeline complete in {elapsed / 60:.1f} minutes")
>     print(f"  Consensus: {len(consensus_df):,} rows")
>     print(f"  Surprise:  {len(surprise_df):,} rows ({valid_sue:,} with SUE)")
>     print(f"{'=' * 70}")
>
>     close_connection()
>
>
> if __name__ == '__main__':
>     main()
> ```
