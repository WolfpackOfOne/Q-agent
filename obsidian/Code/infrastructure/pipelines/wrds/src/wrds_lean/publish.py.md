---
path: "infrastructure/pipelines/wrds/src/wrds_lean/publish.py"
hub: "wrds"
lines: 93
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py"
---
# publish.py

`infrastructure/pipelines/wrds/src/wrds_lean/publish.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py)

## Purpose

Publish LEAN-format files: daily bar zips, factor files, map files.

## Dependencies


**Imports (external):** [[Indexes/External packages#io|io]], [[Indexes/External packages#os|os]], [[Indexes/External packages#zipfile|zipfile]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py|run_broad_quarterly_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_pipeline.py|run_pipeline.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA_ROOT` | `os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')` | [8](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L8) |
| `DAILY_DIR` | `os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'daily')` | [9](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L9) |
| `FACTOR_DIR` | `os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'factor_files')` | [10](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L10) |
| `MAP_DIR` | `os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'map_files')` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L11) |

## Functions

### `_ensure_dirs()`

```python
def _ensure_dirs()
```
[line 14](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L14)

### `publish_daily_bar()`

```python
def publish_daily_bar(ticker, df)
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L19)

Write daily bar DataFrame as {ticker}.zip containing {ticker}.csv.

DataFrame must have columns: date_str, open, high, low, close, volume
Written as CSV with no header.

### `publish_factor_file()`

```python
def publish_factor_file(ticker, df)
```
[line 45](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L45)

Write factor file DataFrame as {ticker}.csv.

DataFrame must have columns: date_str, price_factor, split_factor, ref_price
Written as CSV with no header.

### `publish_map_file()`

```python
def publish_map_file(ticker, df)
```
[line 74](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/publish.py#L74)

Write map file DataFrame as {ticker}.csv.

DataFrame must have columns: date_str, ticker, exchange
Written as CSV with no header.

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/publish.py (93 lines)
> ```python
> """Publish LEAN-format files: daily bar zips, factor files, map files."""
>
> import os
> import zipfile
> import io
>
>
> LEAN_DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
> DAILY_DIR = os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'daily')
> FACTOR_DIR = os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'factor_files')
> MAP_DIR = os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'map_files')
>
>
> def _ensure_dirs():
>     for d in [DAILY_DIR, FACTOR_DIR, MAP_DIR]:
>         os.makedirs(d, exist_ok=True)
>
>
> def publish_daily_bar(ticker, df):
>     """Write daily bar DataFrame as {ticker}.zip containing {ticker}.csv.
>
>     DataFrame must have columns: date_str, open, high, low, close, volume
>     Written as CSV with no header.
>     """
>     _ensure_dirs()
>     ticker = ticker.lower()
>
>     # Build CSV content
>     lines = []
>     for _, row in df.iterrows():
>         lines.append(
>             f"{row['date_str']},{row['open']},{row['high']},"
>             f"{row['low']},{row['close']},{row['volume']}"
>         )
>     csv_content = '\n'.join(lines) + '\n'
>
>     # Write zip
>     zip_path = os.path.join(DAILY_DIR, f'{ticker}.zip')
>     with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
>         zf.writestr(f'{ticker}.csv', csv_content)
>
>     return zip_path
>
>
> def publish_factor_file(ticker, df):
>     """Write factor file DataFrame as {ticker}.csv.
>
>     DataFrame must have columns: date_str, price_factor, split_factor, ref_price
>     Written as CSV with no header.
>     """
>     _ensure_dirs()
>     ticker = ticker.lower()
>
>     lines = []
>     for _, row in df.iterrows():
>         # Format: ref_price can be 0 (sentinel) or a price
>         ref = row['ref_price']
>         if ref == 0:
>             ref_str = '0'
>         else:
>             ref_str = f"{ref}"
>         lines.append(
>             f"{row['date_str']},{row['price_factor']},{row['split_factor']},{ref_str}"
>         )
>     csv_content = '\n'.join(lines) + '\n'
>
>     path = os.path.join(FACTOR_DIR, f'{ticker}.csv')
>     with open(path, 'w') as f:
>         f.write(csv_content)
>
>     return path
>
>
> def publish_map_file(ticker, df):
>     """Write map file DataFrame as {ticker}.csv.
>
>     DataFrame must have columns: date_str, ticker, exchange
>     Written as CSV with no header.
>     """
>     _ensure_dirs()
>     ticker = ticker.lower()
>
>     lines = []
>     for _, row in df.iterrows():
>         lines.append(f"{row['date_str']},{row['ticker']},{row['exchange']}")
>     csv_content = '\n'.join(lines) + '\n'
>
>     path = os.path.join(MAP_DIR, f'{ticker}.csv')
>     with open(path, 'w') as f:
>         f.write(csv_content)
>
>     return path
> ```
