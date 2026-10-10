---
path: "infrastructure/pipelines/wrds/scripts/run_pipeline.py"
hub: "wrds"
lines: 211
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py"
---
# run_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py)

## Purpose

Main CLI for the WRDS-to-LEAN daily equity data pipeline.

Usage:
    python scripts/run_pipeline.py                           # Full universe
    python scripts/run_pipeline.py --tickers AAPL SPY        # Specific symbols
    python scripts/run_pipeline.py --profile new_university  # Named WRDS account
    python scripts/run_pipeline.py --start 1998-01-01 --end 2026-03-12
    python scripts/run_pipeline.py --validate                # Run with validation

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|extract.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/publish.py|publish.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/transform.py|transform.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]], [[Indexes/External packages#zipfile|zipfile]]

## Constants

| Name | Value | Line |
|---|---|---|
| `RAW_DIR` | `os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')` | [27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py#L27) |
| `REF_DATA` | `os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'equity', 'usa')` | [28](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py#L28) |

## Functions

### `run_pipeline()`

```python
def run_pipeline(tickers, start, end, validate=False, save_raw=True)
```
[line 31](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py#L31)

### `validate_against_reference()`

```python
def validate_against_reference(daily_bars, tickers)
```
[line 101](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py#L101)

Compare generated LEAN data against existing reference in MyProjects/data/.

### `main()`

```python
def main()
```
[line 184](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_pipeline.py#L184)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_pipeline.py (211 lines)
> ```python
> """Main CLI for the WRDS-to-LEAN daily equity data pipeline.
>
> Usage:
>     python scripts/run_pipeline.py                           # Full universe
>     python scripts/run_pipeline.py --tickers AAPL SPY        # Specific symbols
>     python scripts/run_pipeline.py --profile new_university  # Named WRDS account
>     python scripts/run_pipeline.py --start 1998-01-01 --end 2026-03-12
>     python scripts/run_pipeline.py --validate                # Run with validation
> """
>
> import argparse
> import os
> import sys
> import time
> import zipfile
>
> import pandas as pd
>
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> from wrds_lean.connection import close_connection, set_connection_profile
> from wrds_lean.symbols import UNIVERSE, get_current_permnos
> from wrds_lean.extract import extract_daily_prices, extract_distributions, extract_name_history
> from wrds_lean.transform import transform_daily_bars, transform_factor_file, transform_map_file
> from wrds_lean.publish import publish_daily_bar, publish_factor_file, publish_map_file
>
> RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
> REF_DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'equity', 'usa')
>
>
> def run_pipeline(tickers, start, end, validate=False, save_raw=True):
>     t0 = time.time()
>
>     # --- Step 1: Resolve PERMNOs ---
>     print(f"=== Resolving PERMNOs for {len(tickers)} tickers ===")
>     permno_map = get_current_permnos(tickers)
>     found_tickers = [t for t in tickers if t in permno_map]
>     print(f"Resolved {len(found_tickers)}/{len(tickers)} tickers")
>     for t in found_tickers:
>         print(f"  {t} -> {permno_map[t]}")
>
>     permnos = [permno_map[t] for t in found_tickers]
>     permno_to_ticker = {permno_map[t]: t for t in found_tickers}
>
>     # --- Step 2: Extract from WRDS ---
>     print(f"\n=== Extracting daily prices ({start} to {end}) ===")
>     prices_df = extract_daily_prices(permnos, start, end)
>     print(f"  {len(prices_df)} price rows")
>
>     print("=== Extracting distributions ===")
>     dist_df = extract_distributions(permnos)
>     print(f"  {len(dist_df)} distribution rows")
>
>     print("=== Extracting name history ===")
>     names_df = extract_name_history(permnos)
>     print(f"  {len(names_df)} name rows")
>
>     # Save raw data
>     if save_raw:
>         os.makedirs(RAW_DIR, exist_ok=True)
>         prices_df.to_csv(os.path.join(RAW_DIR, 'prices.csv'), index=False)
>         dist_df.to_csv(os.path.join(RAW_DIR, 'distributions.csv'), index=False)
>         names_df.to_csv(os.path.join(RAW_DIR, 'names.csv'), index=False)
>         print("  Raw data saved to data/raw/")
>
>     # --- Step 3: Transform ---
>     print("\n=== Transforming daily bars ===")
>     daily_bars = transform_daily_bars(prices_df, permno_to_ticker)
>     print(f"  Transformed {len(daily_bars)} tickers")
>
>     # --- Step 4: Publish ---
>     print("\n=== Publishing LEAN data ===")
>     for ticker_lower, bars_df in daily_bars.items():
>         # Daily bars
>         zip_path = publish_daily_bar(ticker_lower, bars_df)
>         print(f"  {ticker_lower}: {len(bars_df)} bars -> {os.path.basename(zip_path)}")
>
>         # Factor file
>         ticker_upper = ticker_lower.upper()
>         permno = permno_map[ticker_upper]
>         factor_df = transform_factor_file(prices_df, dist_df, permno)
>         factor_path = publish_factor_file(ticker_lower, factor_df)
>         print(f"    factor_files/{ticker_lower}.csv ({len(factor_df)} rows)")
>
>         # Map file
>         map_df = transform_map_file(names_df, permno, ticker_upper)
>         map_path = publish_map_file(ticker_lower, map_df)
>         print(f"    map_files/{ticker_lower}.csv ({len(map_df)} rows)")
>
>     elapsed = time.time() - t0
>     print(f"\n=== Pipeline complete in {elapsed:.1f}s ===")
>
>     # --- Step 5: Validate ---
>     if validate:
>         print("\n=== Validation ===")
>         validate_against_reference(daily_bars, found_tickers)
>
>     close_connection()
>
>
> def validate_against_reference(daily_bars, tickers):
>     """Compare generated LEAN data against existing reference in MyProjects/data/."""
>     ref_daily_dir = os.path.join(REF_DATA, 'daily')
>     ref_factor_dir = os.path.join(REF_DATA, 'factor_files')
>
>     for ticker in tickers:
>         ticker_lower = ticker.lower()
>
>         # --- Validate daily bars ---
>         ref_zip = os.path.join(ref_daily_dir, f'{ticker_lower}.zip')
>         if not os.path.exists(ref_zip):
>             print(f"  {ticker}: No reference daily data (skipping)")
>             continue
>
>         # Read reference
>         with zipfile.ZipFile(ref_zip) as zf:
>             with zf.open(f'{ticker_lower}.csv') as f:
>                 ref_lines = f.read().decode().strip().split('\n')
>
>         ref_data = {}
>         for line in ref_lines:
>             parts = line.split(',')
>             date_str = parts[0].strip()
>             close = int(parts[4])
>             ref_data[date_str] = close
>
>         # Compare
>         if ticker_lower not in daily_bars:
>             print(f"  {ticker}: Not in generated data (skipping)")
>             continue
>
>         gen_df = daily_bars[ticker_lower]
>         matches = 0
>         mismatches = 0
>         mismatch_examples = []
>         for _, row in gen_df.iterrows():
>             date_str = row['date_str']
>             if date_str in ref_data:
>                 ref_close = ref_data[date_str]
>                 gen_close = row['close']
>                 if abs(ref_close - gen_close) <= 1:  # 1 deci-cent tolerance
>                     matches += 1
>                 else:
>                     mismatches += 1
>                     if len(mismatch_examples) < 5:
>                         mismatch_examples.append(
>                             f"    {date_str}: ref={ref_close} gen={gen_close} "
>                             f"diff={gen_close - ref_close}"
>                         )
>
>         overlap = matches + mismatches
>         if overlap > 0:
>             pct = matches / overlap * 100
>             print(f"  {ticker} daily close: {matches}/{overlap} match ({pct:.1f}%), "
>                   f"{mismatches} mismatches")
>             for ex in mismatch_examples:
>                 print(ex)
>         else:
>             print(f"  {ticker}: No overlapping dates with reference")
>
>         # --- Validate factor file ---
>         ref_factor = os.path.join(ref_factor_dir, f'{ticker_lower}.csv')
>         if os.path.exists(ref_factor):
>             with open(ref_factor) as f:
>                 ref_factor_lines = f.read().strip().split('\n')
>             print(f"  {ticker} factor file: reference has {len(ref_factor_lines)} rows")
>             # Show split factor comparison for key dates
>             ref_splits = {}
>             for line in ref_factor_lines:
>                 parts = line.split(',')
>                 if len(parts) >= 3:
>                     ref_splits[parts[0]] = (float(parts[1]), float(parts[2]))
>             # Check our generated factor file
>             gen_factor_path = os.path.join(
>                 os.path.dirname(__file__), '..', 'lean-data', 'equity', 'usa',
>                 'factor_files', f'{ticker_lower}.csv'
>             )
>             if os.path.exists(gen_factor_path):
>                 with open(gen_factor_path) as f:
>                     gen_lines = f.read().strip().split('\n')
>                 print(f"    generated has {len(gen_lines)} rows")
>
>
> def main():
>     parser = argparse.ArgumentParser(description='WRDS-to-LEAN daily equity pipeline')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Specific tickers to process (default: full universe)')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--start', default='1998-01-01',
>                         help='Start date (default: 1998-01-01)')
>     parser.add_argument('--end', default='2026-03-12',
>                         help='End date (default: 2026-03-12)')
>     parser.add_argument('--validate', action='store_true',
>                         help='Run validation against reference LEAN data')
>     parser.add_argument('--no-raw', action='store_true',
>                         help='Skip saving raw extracts')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     tickers = args.tickers if args.tickers else UNIVERSE
>     run_pipeline(tickers, args.start, args.end,
>                  validate=args.validate, save_raw=not args.no_raw)
>
>
> if __name__ == '__main__':
>     main()
> ```
