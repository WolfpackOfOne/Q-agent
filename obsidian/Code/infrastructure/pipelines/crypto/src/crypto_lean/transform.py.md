---
path: "infrastructure/pipelines/crypto/src/crypto_lean/transform.py"
hub: "crypto"
lines: 66
tags:
  - "code/python"
  - "pipelines/crypto"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/transform.py"
---
# transform.py

`infrastructure/pipelines/crypto/src/crypto_lean/transform.py` · hub [[Hubs/Pipelines/crypto|crypto]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/transform.py)

## Purpose

OHLCV → LEAN-format CSV strings.

LEAN crypto convention (unlike equities, prices are NOT scaled):

    daily:   one CSV per symbol  — `YYYYMMDD 00:00,open,high,low,close,volume`
    minute:  one CSV per symbol per day — `<ms-since-midnight>,o,h,l,c,v`

We emit headerless CSV strings ready to be zipped by `writer.write_lean_zip`.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/crypto/src/crypto_lean/__init__.py|__init__.py]]

## Functions

### `_round()`

```python
def _round(series: pd.Series, dp: int) -> pd.Series
```
[line 15](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/transform.py#L15)

### `to_lean_daily()`

```python
def to_lean_daily(df: pd.DataFrame, price_dp: int=4, vol_dp: int=4) -> str
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/transform.py#L19)

Format a daily OHLCV frame as a LEAN daily CSV string (headerless).

`df` must be UTC-indexed with columns open/high/low/close/volume.

### `to_lean_minute()`

```python
def to_lean_minute(df: pd.DataFrame, price_dp: int=4, vol_dp: int=4) -> dict[str, str]
```
[line 36](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/transform.py#L36)

Format a minute frame as one CSV per UTC date (headerless).

Returns `{ "YYYYMMDD": csv_text }`.

## Source

> [!example]- infrastructure/pipelines/crypto/src/crypto_lean/transform.py (66 lines)
> ```python
> """OHLCV → LEAN-format CSV strings.
>
> LEAN crypto convention (unlike equities, prices are NOT scaled):
>
>     daily:   one CSV per symbol  — `YYYYMMDD 00:00,open,high,low,close,volume`
>     minute:  one CSV per symbol per day — `<ms-since-midnight>,o,h,l,c,v`
>
> We emit headerless CSV strings ready to be zipped by `writer.write_lean_zip`.
> """
> from __future__ import annotations
>
> import pandas as pd
>
>
> def _round(series: pd.Series, dp: int) -> pd.Series:
>     return series.astype(float).round(dp)
>
>
> def to_lean_daily(df: pd.DataFrame, price_dp: int = 4, vol_dp: int = 4) -> str:
>     """Format a daily OHLCV frame as a LEAN daily CSV string (headerless).
>
>     `df` must be UTC-indexed with columns open/high/low/close/volume.
>     """
>     if df.empty:
>         return ""
>     out = pd.DataFrame(index=df.index)
>     out["datetime"] = df.index.strftime("%Y%m%d 00:00")
>     out["open"] = _round(df["open"], price_dp)
>     out["high"] = _round(df["high"], price_dp)
>     out["low"] = _round(df["low"], price_dp)
>     out["close"] = _round(df["close"], price_dp)
>     out["volume"] = _round(df["volume"], vol_dp)
>     return out.to_csv(header=False, index=False, lineterminator="\n")
>
>
> def to_lean_minute(df: pd.DataFrame, price_dp: int = 4, vol_dp: int = 4) -> dict[str, str]:
>     """Format a minute frame as one CSV per UTC date (headerless).
>
>     Returns `{ "YYYYMMDD": csv_text }`.
>     """
>     if df.empty:
>         return {}
>     grouped: dict[str, str] = {}
>     midnight_ms = (
>         df.index.normalize().astype("int64") // 1_000_000
>     )
>     bar_ms = df.index.astype("int64") // 1_000_000 - midnight_ms
>
>     work = pd.DataFrame(
>         {
>             "date": df.index.strftime("%Y%m%d"),
>             "ms": bar_ms.astype("int64"),
>             "open": _round(df["open"], price_dp),
>             "high": _round(df["high"], price_dp),
>             "low": _round(df["low"], price_dp),
>             "close": _round(df["close"], price_dp),
>             "volume": _round(df["volume"], vol_dp),
>         },
>         index=df.index,
>     )
>     for day, chunk in work.groupby("date"):
>         grouped[day] = chunk.drop(columns="date").to_csv(
>             header=False, index=False, lineterminator="\n"
>         )
>     return grouped
> ```
