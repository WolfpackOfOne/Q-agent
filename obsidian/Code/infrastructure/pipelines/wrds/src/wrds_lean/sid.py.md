---
path: "infrastructure/pipelines/wrds/src/wrds_lean/sid.py"
hub: "wrds"
lines: 118
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py"
---
# sid.py

`infrastructure/pipelines/wrds/src/wrds_lean/sid.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py)

## Purpose

LEAN SecurityIdentifier generation for equity symbols.

Ports the essential parts of LEAN's C# SecurityIdentifier.Generate() to Python
so we can produce valid SID strings for ETF universe files.

The SID string format is: "{SYMBOL} {base36_encoded_properties}"
where properties encodes the first trade date, market, and security type.

## Dependencies


**Imports (external):** [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#os|os]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py|run_etf_pipeline.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `_SECURITY_TYPE_OFFSET` | `1` | [15](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L15) |
| `_SECURITY_TYPE_WIDTH` | `100` | [16](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L16) |
| `_MARKET_OFFSET` | `_SECURITY_TYPE_OFFSET * _SECURITY_TYPE_WIDTH` | [17](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L17) |
| `_MARKET_WIDTH` | `1000` | [18](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L18) |
| `_STRIKE_SCALE_OFFSET` | `_MARKET_OFFSET * _MARKET_WIDTH` | [19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L19) |
| `_STRIKE_SCALE_WIDTH` | `100` | [20](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L20) |
| `_STRIKE_OFFSET` | `_STRIKE_SCALE_OFFSET * _STRIKE_SCALE_WIDTH` | [21](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L21) |
| `_STRIKE_WIDTH` | `1000000` | [22](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L22) |
| `_OPTION_STYLE_OFFSET` | `_STRIKE_OFFSET * _STRIKE_WIDTH` | [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L23) |
| `_OPTION_STYLE_WIDTH` | `10` | [24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L24) |
| `_DAYS_OFFSET` | `_OPTION_STYLE_OFFSET * _OPTION_STYLE_WIDTH` | [25](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L25) |
| `_DAYS_WIDTH` | `100000` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L26) |
| `_MARKET_USA` | `1` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L29) |
| `_SECURITY_TYPE_EQUITY` | `1` | [32](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L32) |
| `_OA_BASE` | `datetime.date(1899, 12, 30)` | [35](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L35) |
| `_BASE36_CHARS` | `'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'` | [37](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L37) |

## Functions

### `_to_oa_date()`

```python
def _to_oa_date(dt)
```
[line 40](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L40)

Convert a date to OLE Automation date (days since 1899-12-30).

### `_encode_base36()`

```python
def _encode_base36(n)
```
[line 47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L47)

Encode an unsigned integer as a base-36 string (uppercase).

### `generate_equity_sid()`

```python
def generate_equity_sid(symbol, first_date)
```
[line 58](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L58)

Generate a LEAN SecurityIdentifier string for a US equity.

Args:
    symbol: Ticker symbol (e.g. "AAPL")
    first_date: First trade date as datetime.date (from map file first row)

Returns:
    SID string like "AAPL R735QTJ8XC9X"

### `get_first_date_from_map_file()`

```python
def get_first_date_from_map_file(map_file_path)
```
[line 77](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L77)

Read the first date from a LEAN map file.

Map files have format: date,ticker,exchange (no header).
The first row's date is the first trade date used for SID generation.

### `build_sid_lookup()`

```python
def build_sid_lookup(map_files_dir)
```
[line 93](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sid.py#L93)

Build a {ticker_upper: sid_string} dict from all map files in a directory.

Args:
    map_files_dir: Path to equity/usa/map_files/ directory

Returns:
    Dict mapping e.g. "AAPL" -> "AAPL R735QTJ8XC9X"

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/sid.py (118 lines)
> ```python
> """LEAN SecurityIdentifier generation for equity symbols.
>
> Ports the essential parts of LEAN's C# SecurityIdentifier.Generate() to Python
> so we can produce valid SID strings for ETF universe files.
>
> The SID string format is: "{SYMBOL} {base36_encoded_properties}"
> where properties encodes the first trade date, market, and security type.
> """
>
> import datetime
> import os
>
> # LEAN SecurityIdentifier bit-packing constants
> # Layout: {put/call:1}{oa-date:5}{style:1}{strike:6}{strike-scale:2}{market:3}{security-type:2}
> _SECURITY_TYPE_OFFSET = 1
> _SECURITY_TYPE_WIDTH = 100
> _MARKET_OFFSET = _SECURITY_TYPE_OFFSET * _SECURITY_TYPE_WIDTH       # 100
> _MARKET_WIDTH = 1000
> _STRIKE_SCALE_OFFSET = _MARKET_OFFSET * _MARKET_WIDTH               # 100_000
> _STRIKE_SCALE_WIDTH = 100
> _STRIKE_OFFSET = _STRIKE_SCALE_OFFSET * _STRIKE_SCALE_WIDTH         # 10_000_000
> _STRIKE_WIDTH = 1_000_000
> _OPTION_STYLE_OFFSET = _STRIKE_OFFSET * _STRIKE_WIDTH               # 10_000_000_000_000
> _OPTION_STYLE_WIDTH = 10
> _DAYS_OFFSET = _OPTION_STYLE_OFFSET * _OPTION_STYLE_WIDTH           # 100_000_000_000_000
> _DAYS_WIDTH = 100_000
>
> # Market codes (from LEAN Market.cs)
> _MARKET_USA = 1
>
> # Security types (from LEAN SecurityType enum)
> _SECURITY_TYPE_EQUITY = 1
>
> # OA date base: December 30, 1899
> _OA_BASE = datetime.date(1899, 12, 30)
>
> _BASE36_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
>
>
> def _to_oa_date(dt):
>     """Convert a date to OLE Automation date (days since 1899-12-30)."""
>     if isinstance(dt, datetime.datetime):
>         dt = dt.date()
>     return (dt - _OA_BASE).days
>
>
> def _encode_base36(n):
>     """Encode an unsigned integer as a base-36 string (uppercase)."""
>     if n == 0:
>         return "0"
>     chars = []
>     while n > 0:
>         chars.append(_BASE36_CHARS[n % 36])
>         n //= 36
>     return "".join(reversed(chars))
>
>
> def generate_equity_sid(symbol, first_date):
>     """Generate a LEAN SecurityIdentifier string for a US equity.
>
>     Args:
>         symbol: Ticker symbol (e.g. "AAPL")
>         first_date: First trade date as datetime.date (from map file first row)
>
>     Returns:
>         SID string like "AAPL R735QTJ8XC9X"
>     """
>     oa_date = _to_oa_date(first_date)
>     properties = (
>         oa_date * _DAYS_OFFSET
>         + _MARKET_USA * _MARKET_OFFSET
>         + _SECURITY_TYPE_EQUITY
>     )
>     return f"{symbol.upper()} {_encode_base36(properties)}"
>
>
> def get_first_date_from_map_file(map_file_path):
>     """Read the first date from a LEAN map file.
>
>     Map files have format: date,ticker,exchange (no header).
>     The first row's date is the first trade date used for SID generation.
>     """
>     with open(map_file_path) as f:
>         for line in f:
>             line = line.strip()
>             if not line:
>                 continue
>             date_str = line.split(",")[0]
>             return datetime.datetime.strptime(date_str, "%Y%m%d").date()
>     raise ValueError(f"Empty map file: {map_file_path}")
>
>
> def build_sid_lookup(map_files_dir):
>     """Build a {ticker_upper: sid_string} dict from all map files in a directory.
>
>     Args:
>         map_files_dir: Path to equity/usa/map_files/ directory
>
>     Returns:
>         Dict mapping e.g. "AAPL" -> "AAPL R735QTJ8XC9X"
>     """
>     lookup = {}
>     if not os.path.isdir(map_files_dir):
>         return lookup
>
>     for filename in os.listdir(map_files_dir):
>         if not filename.endswith(".csv"):
>             continue
>         ticker = filename.replace(".csv", "").upper()
>         path = os.path.join(map_files_dir, filename)
>         try:
>             first_date = get_first_date_from_map_file(path)
>             lookup[ticker] = generate_equity_sid(ticker, first_date)
>         except (ValueError, IndexError):
>             continue
>
>     return lookup
> ```
