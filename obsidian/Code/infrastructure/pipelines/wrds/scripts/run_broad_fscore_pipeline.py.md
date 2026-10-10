---
path: "infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py"
hub: "wrds"
lines: 257
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py"
---
# run_broad_fscore_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py)

## Purpose

Broad Piotroski F-Score pipeline: all US equities.

Pulls ALL comp.funda rows (no ticker filter), computes F-Scores, resolves
PERMNOs via the CRSP-Compustat CCM link, pulls CRSP daily prices for every
ticker that ever scored F >= 7, and publishes LEAN-format data.

Usage:
    # Wrap with caffeinate to prevent Mac sleep during long pull
    caffeinate -dims python scripts/run_broad_fscore_pipeline.py

    # Options
    caffeinate -dims python scripts/run_broad_fscore_pipeline.py --start-year 2000
    caffeinate -dims python scripts/run_broad_fscore_pipeline.py --min-fscore 8
    caffeinate -dims python scripts/run_broad_fscore_pipeline.py --profile <additional>

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|extract.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|fundamentals.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/publish.py|publish.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/transform.py|transform.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## SQL queries (1)

### resolve_permnos_via_ccm · L47

**`resolve_permnos_via_ccm()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L47) · assigned to `sql`

Tables: [[SQL/Tables/comp.funda|comp.funda]], [[SQL/Tables/crsp_a_ccm.ccmxpf_lnkhist|crsp_a_ccm.ccmxpf_lnkhist]]

```sql
SELECT DISTINCT f.tic AS ticker, l.lpermno AS permno
FROM comp.funda f
JOIN crsp_a_ccm.ccmxpf_lnkhist l
    ON f.gvkey = l.gvkey
    AND l.linktype IN ('LU', 'LC')
    AND l.linkprim IN ('P', 'C')
    AND l.linkdt <= f.datadate
    AND (l.linkenddt IS NULL OR l.linkenddt >= f.datadate)
WHERE f.tic IN %(tickers)s
  AND f.fyear >= %(start_year)s
  AND f.indfmt = 'INDL'
  AND f.datafmt = 'STD'
  AND f.popsrc = 'D'
  AND f.consol = 'C'
```

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [32](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L32) |
| `RAW_DIR` | `os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')` | [33](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L33) |
| `BATCH_SIZE` | `500` | [36](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L36) |

## Functions

### `resolve_permnos_via_ccm()`

```python
def resolve_permnos_via_ccm(tickers, start_year)
```
[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L39)

Resolve Compustat tickers to CRSP PERMNOs using the CCM link table.

Returns dict {ticker: permno} for tickers that have a valid link.

### `pull_crsp_batch()`

```python
def pull_crsp_batch(permnos, permno_to_ticker, start, end, batch_num, total_batches)
```
[line 76](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L76)

Pull CRSP daily data for a batch of PERMNOs and publish LEAN files.

### `main()`

```python
def main()
```
[line 126](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L126)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py (257 lines)
> ```python
> """Broad Piotroski F-Score pipeline: all US equities.
>
> Pulls ALL comp.funda rows (no ticker filter), computes F-Scores, resolves
> PERMNOs via the CRSP-Compustat CCM link, pulls CRSP daily prices for every
> ticker that ever scored F >= 7, and publishes LEAN-format data.
>
> Usage:
>     # Wrap with caffeinate to prevent Mac sleep during long pull
>     caffeinate -dims python scripts/run_broad_fscore_pipeline.py
>
>     # Options
>     caffeinate -dims python scripts/run_broad_fscore_pipeline.py --start-year 2000
>     caffeinate -dims python scripts/run_broad_fscore_pipeline.py --min-fscore 8
>     caffeinate -dims python scripts/run_broad_fscore_pipeline.py --profile <additional>
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
> from wrds_lean.connection import get_connection, close_connection, set_connection_profile
> from wrds_lean.fundamentals import extract_all_fundamentals, compute_piotroski, publish_piotroski
> from wrds_lean.extract import extract_daily_prices, extract_distributions, extract_name_history
> from wrds_lean.transform import transform_daily_bars, transform_factor_file, transform_map_file
> from wrds_lean.publish import publish_daily_bar, publish_factor_file, publish_map_file
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
> RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
>
> # CRSP extraction batch size (number of PERMNOs per query)
> BATCH_SIZE = 500
>
>
> def resolve_permnos_via_ccm(tickers, start_year):
>     """Resolve Compustat tickers to CRSP PERMNOs using the CCM link table.
>
>     Returns dict {ticker: permno} for tickers that have a valid link.
>     """
>     conn = get_connection()
>
>     # Use the CCM link table to map gvkey -> permno, then match on ticker
>     sql = """
>         SELECT DISTINCT f.tic AS ticker, l.lpermno AS permno
>         FROM comp.funda f
>         JOIN crsp_a_ccm.ccmxpf_lnkhist l
>             ON f.gvkey = l.gvkey
>             AND l.linktype IN ('LU', 'LC')
>             AND l.linkprim IN ('P', 'C')
>             AND l.linkdt <= f.datadate
>             AND (l.linkenddt IS NULL OR l.linkenddt >= f.datadate)
>         WHERE f.tic IN %(tickers)s
>           AND f.fyear >= %(start_year)s
>           AND f.indfmt = 'INDL'
>           AND f.datafmt = 'STD'
>           AND f.popsrc = 'D'
>           AND f.consol = 'C'
>     """
>     df = conn.raw_sql(sql, params={
>         'tickers': tuple(tickers),
>         'start_year': start_year,
>     })
>
>     # Take the most recent permno per ticker (in case of multiple links)
>     result = {}
>     for _, row in df.iterrows():
>         result[row['ticker']] = int(row['permno'])
>
>     return result
>
>
> def pull_crsp_batch(permnos, permno_to_ticker, start, end, batch_num, total_batches):
>     """Pull CRSP daily data for a batch of PERMNOs and publish LEAN files."""
>     print(f"\n  --- Batch {batch_num}/{total_batches}: "
>           f"{len(permnos)} PERMNOs ---")
>
>     prices_df = extract_daily_prices(permnos, start, end)
>     print(f"    {len(prices_df):,} price rows")
>
>     if prices_df.empty:
>         return 0
>
>     dist_df = extract_distributions(permnos)
>     names_df = extract_name_history(permnos)
>
>     # Transform and publish
>     daily_bars = transform_daily_bars(prices_df, permno_to_ticker)
>
>     published = 0
>     for ticker_lower, bars_df in daily_bars.items():
>         ticker_upper = ticker_lower.upper()
>         if ticker_upper not in permno_to_ticker.values():
>             # Reverse lookup
>             permno = None
>             for p, t in permno_to_ticker.items():
>                 if t.lower() == ticker_lower:
>                     permno = p
>                     break
>         else:
>             for p, t in permno_to_ticker.items():
>                 if t.lower() == ticker_lower:
>                     permno = p
>                     break
>
>         if permno is None:
>             continue
>
>         publish_daily_bar(ticker_lower, bars_df)
>
>         factor_df = transform_factor_file(prices_df, dist_df, permno)
>         publish_factor_file(ticker_lower, factor_df)
>
>         map_df = transform_map_file(names_df, permno, ticker_upper)
>         publish_map_file(ticker_lower, map_df)
>
>         published += 1
>
>     print(f"    Published {published} tickers")
>     return published
>
>
> def main():
>     parser = argparse.ArgumentParser(
>         description='Broad Piotroski F-Score pipeline (all US equities)')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--start-year', type=int, default=1997,
>                         help='First fiscal year (default: 1997)')
>     parser.add_argument('--min-fscore', type=int, default=7,
>                         help='Minimum F-Score to include in price pull (default: 7)')
>     parser.add_argument('--start', default='1998-01-01',
>                         help='CRSP price start date (default: 1998-01-01)')
>     parser.add_argument('--end', default='2026-12-31',
>                         help='CRSP price end date (default: 2026-12-31)')
>     parser.add_argument('--scores-only', action='store_true',
>                         help='Only compute and publish F-Scores, skip CRSP price pull')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>
>     # =========================================================================
>     # Phase 1: Pull ALL fundamentals and compute F-Scores
>     # =========================================================================
>     print("=" * 70)
>     print("PHASE 1: Extract all US fundamentals from comp.funda")
>     print("=" * 70)
>
>     raw_df = extract_all_fundamentals(start_year=args.start_year)
>     print(f"  {len(raw_df):,} rows, {raw_df['tic'].nunique():,} unique tickers")
>
>     print("\nComputing Piotroski F-Scores...")
>     scores_df = compute_piotroski(raw_df)
>     print(f"  {len(scores_df):,} scored rows")
>
>     # Publish F-Scores
>     filepath = publish_piotroski(scores_df, LEAN_DATA)
>     print(f"  Written to {filepath}")
>
>     # F-Score distribution
>     print("\n  F-Score distribution:")
>     dist = scores_df['F_Score'].value_counts().sort_index()
>     for score, count in dist.items():
>         pct = count / len(scores_df) * 100
>         bar = '#' * int(pct)
>         print(f"    {score}: {count:>6,} ({pct:5.1f}%) {bar}")
>
>     # =========================================================================
>     # Phase 2: Identify tickers with F >= threshold
>     # =========================================================================
>     high_scorers = scores_df[scores_df['F_Score'] >= args.min_fscore]['Ticker'].unique()
>     print(f"\n  Tickers with F >= {args.min_fscore} (ever): {len(high_scorers):,}")
>
>     if args.scores_only:
>         elapsed = time.time() - t0
>         print(f"\n=== Scores-only mode complete in {elapsed:.1f}s ===")
>         close_connection()
>         return
>
>     # =========================================================================
>     # Phase 3: Resolve PERMNOs via CCM link
>     # =========================================================================
>     print("\n" + "=" * 70)
>     print("PHASE 2: Resolve PERMNOs via CRSP-Compustat CCM link")
>     print("=" * 70)
>
>     ticker_list = list(high_scorers)
>     permno_map = resolve_permnos_via_ccm(ticker_list, args.start_year)
>
>     resolved = [t for t in ticker_list if t in permno_map]
>     unresolved = [t for t in ticker_list if t not in permno_map]
>
>     print(f"  Resolved: {len(resolved):,} / {len(ticker_list):,}")
>     if unresolved:
>         print(f"  Unresolved (no CCM link): {len(unresolved):,}")
>         if len(unresolved) <= 20:
>             print(f"    {unresolved}")
>
>     # =========================================================================
>     # Phase 4: Pull CRSP daily prices in batches
>     # =========================================================================
>     print("\n" + "=" * 70)
>     print(f"PHASE 3: Pull CRSP daily prices ({args.start} to {args.end})")
>     print(f"  {len(resolved):,} tickers in batches of {BATCH_SIZE}")
>     print("=" * 70)
>
>     # Build permno -> ticker mapping (reversed from permno_map)
>     all_permnos = [permno_map[t] for t in resolved]
>     permno_to_ticker = {permno_map[t]: t for t in resolved}
>
>     total_published = 0
>     total_batches = (len(all_permnos) + BATCH_SIZE - 1) // BATCH_SIZE
>
>     for i in range(0, len(all_permnos), BATCH_SIZE):
>         batch_permnos = all_permnos[i:i + BATCH_SIZE]
>         batch_p2t = {p: permno_to_ticker[p] for p in batch_permnos}
>         batch_num = i // BATCH_SIZE + 1
>
>         try:
>             n = pull_crsp_batch(
>                 batch_permnos, batch_p2t, args.start, args.end,
>                 batch_num, total_batches
>             )
>             total_published += n
>         except Exception as e:
>             print(f"    ERROR in batch {batch_num}: {e}")
>             print(f"    Continuing with next batch...")
>             continue
>
>     # =========================================================================
>     # Summary
>     # =========================================================================
>     elapsed = time.time() - t0
>     print("\n" + "=" * 70)
>     print("PIPELINE COMPLETE")
>     print("=" * 70)
>     print(f"  F-Score rows:     {len(scores_df):,}")
>     print(f"  High scorers:     {len(high_scorers):,} (F >= {args.min_fscore})")
>     print(f"  PERMNOs resolved: {len(resolved):,}")
>     print(f"  Tickers published: {total_published:,}")
>     print(f"  Elapsed:          {elapsed / 60:.1f} minutes")
>     print(f"\n  F-Scores: {filepath}")
>     print(f"  LEAN data: {os.path.abspath(LEAN_DATA)}")
>
>     close_connection()
>
>
> if __name__ == '__main__':
>     main()
> ```
