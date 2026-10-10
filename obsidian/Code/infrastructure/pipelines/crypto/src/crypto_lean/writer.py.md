---
path: "infrastructure/pipelines/crypto/src/crypto_lean/writer.py"
hub: "crypto"
lines: 107
tags:
  - "code/python"
  - "pipelines/crypto"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py"
---
# writer.py

`infrastructure/pipelines/crypto/src/crypto_lean/writer.py` · hub [[Hubs/Pipelines/crypto|crypto]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py)

## Purpose

Write LEAN-style zips for crypto.

Layout mirrors LEAN's expected paths:

    <root>/crypto/<market>/daily/<symbol>.zip
    <root>/crypto/<market>/minute/<symbol>/<YYYYMMDD>_trade.zip

Symbol is lowercase with the slash stripped (`btcusdt`, `btcusd`).

Concurrent-agent safety
-----------------------
Daily zips are merge-on-write: if the target zip already exists its rows are
read and merged with the new payload by date key (new data wins).  The result
is written atomically via a sibling temp file + os.replace(), so a concurrent
writer never sees a half-written file.

Minute zips are already one file per day, so they cannot interleave data from
different date ranges; they get the same atomic-write treatment.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#io|io]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#zipfile|zipfile]]

**Imported by:** [[Code/infrastructure/pipelines/crypto/src/crypto_lean/__init__.py|__init__.py]]

## Functions

### `normalize_symbol()`

```python
def normalize_symbol(pair: str) -> str
```
[line 28](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py#L28)

`BTC/USDT` → `btcusdt`.

### `market_dir()`

```python
def market_dir(lean_root: pathlib.Path, exchange: str) -> pathlib.Path
```
[line 33](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py#L33)

### `write_lean_zip()`

```python
def write_lean_zip(lean_root: pathlib.Path, exchange: str, pair: str, resolution: str, payload: str | dict[str, str]) -> pathlib.Path
```
[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py#L39)

Write a daily zip (`payload: str`) or minute zip-set (`payload: dict[date,str]`).

Returns the path of the resulting daily zip (or the parent dir for minute).

### `_merge_daily_csv()`

```python
def _merge_daily_csv(zip_path: pathlib.Path, inner_name: str, new_csv: str) -> str
```
[line 76](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py#L76)

Return a merged CSV where new_csv rows win over any existing rows for the same date.

### `_atomic_write_zip()`

```python
def _atomic_write_zip(zip_path: pathlib.Path, inner_name: str, csv_text: str) -> None
```
[line 99](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/writer.py#L99)

Write csv_text into a zip at zip_path via an atomic temp-file swap.

## Source

> [!example]- infrastructure/pipelines/crypto/src/crypto_lean/writer.py (107 lines)
> ```python
> """Write LEAN-style zips for crypto.
>
> Layout mirrors LEAN's expected paths:
>
>     <root>/crypto/<market>/daily/<symbol>.zip
>     <root>/crypto/<market>/minute/<symbol>/<YYYYMMDD>_trade.zip
>
> Symbol is lowercase with the slash stripped (`btcusdt`, `btcusd`).
>
> Concurrent-agent safety
> -----------------------
> Daily zips are merge-on-write: if the target zip already exists its rows are
> read and merged with the new payload by date key (new data wins).  The result
> is written atomically via a sibling temp file + os.replace(), so a concurrent
> writer never sees a half-written file.
>
> Minute zips are already one file per day, so they cannot interleave data from
> different date ranges; they get the same atomic-write treatment.
> """
> from __future__ import annotations
>
> import io
> import os
> import pathlib
> import zipfile
>
>
> def normalize_symbol(pair: str) -> str:
>     """`BTC/USDT` → `btcusdt`."""
>     return pair.replace("/", "").replace("-", "").lower()
>
>
> def market_dir(lean_root: pathlib.Path, exchange: str) -> pathlib.Path:
>     # LEAN uses 'coinbasepro' historically; ccxt 'coinbase' maps there.
>     market = {"coinbase": "coinbasepro"}.get(exchange, exchange)
>     return lean_root / "crypto" / market
>
>
> def write_lean_zip(
>     lean_root: pathlib.Path,
>     exchange: str,
>     pair: str,
>     resolution: str,
>     payload: str | dict[str, str],
> ) -> pathlib.Path:
>     """Write a daily zip (`payload: str`) or minute zip-set (`payload: dict[date,str]`).
>
>     Returns the path of the resulting daily zip (or the parent dir for minute).
>     """
>     sym = normalize_symbol(pair)
>     base = market_dir(lean_root, exchange) / resolution
>     base.mkdir(parents=True, exist_ok=True)
>
>     if resolution == "daily":
>         if not isinstance(payload, str):
>             raise TypeError("daily payload must be a CSV string")
>         zip_path = base / f"{sym}.zip"
>         merged = _merge_daily_csv(zip_path, f"{sym}.csv", payload)
>         _atomic_write_zip(zip_path, f"{sym}.csv", merged)
>         return zip_path
>
>     if resolution == "minute":
>         if not isinstance(payload, dict):
>             raise TypeError("minute payload must be dict[YYYYMMDD, csv]")
>         sym_dir = base / sym
>         sym_dir.mkdir(parents=True, exist_ok=True)
>         for day, csv_text in payload.items():
>             zip_path = sym_dir / f"{day}_trade.zip"
>             inner = f"{day}_{sym}_minute_trade.csv"
>             _atomic_write_zip(zip_path, inner, csv_text)
>         return sym_dir
>
>     raise ValueError(f"Unsupported resolution: {resolution}")
>
>
> def _merge_daily_csv(zip_path: pathlib.Path, inner_name: str, new_csv: str) -> str:
>     """Return a merged CSV where new_csv rows win over any existing rows for the same date."""
>     if not zip_path.exists():
>         return new_csv
>
>     try:
>         with zipfile.ZipFile(zip_path, "r") as z:
>             existing_csv = z.read(inner_name).decode()
>     except (KeyError, zipfile.BadZipFile):
>         return new_csv
>
>     # Index rows by their date key (first comma-delimited field).
>     rows: dict[str, str] = {}
>     for line in existing_csv.splitlines():
>         if line:
>             rows[line.split(",", 1)[0]] = line
>     for line in new_csv.splitlines():
>         if line:
>             rows[line.split(",", 1)[0]] = line  # new data wins
>
>     return "\n".join(rows[k] for k in sorted(rows)) + "\n"
>
>
> def _atomic_write_zip(zip_path: pathlib.Path, inner_name: str, csv_text: str) -> None:
>     """Write csv_text into a zip at zip_path via an atomic temp-file swap."""
>     buf = io.BytesIO()
>     with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
>         z.writestr(inner_name, csv_text)
>     tmp = zip_path.with_suffix(".tmp")
>     tmp.write_bytes(buf.getvalue())
>     os.replace(tmp, zip_path)  # atomic on POSIX and Windows
> ```
