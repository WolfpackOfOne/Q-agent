---
path: "infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py"
hub: "wrds"
lines: 163
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py"
---
# etf_constituents.py

`infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py)

## Purpose

ETF constituent extraction from CRSP mutual fund holdings.

Extracts historical ETF constituent data from crsp.holdings, transforms
to LEAN ETF universe format, and publishes daily CSV files.

LEAN format: equity/usa/universes/etf/{etf_ticker}/{YYYYMMDD}.csv
Each line: Ticker,SID,Date,Weight,SharesHeld,

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py|run_etf_pipeline.py]]

## SQL queries (2)

### extract_holdings · L43

**`extract_holdings()`** — line [43](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L43) · assigned to `sql`

Tables: [[SQL/Tables/crsp.holdings|crsp.holdings]]

f-string placeholders: `{date_filter}`

```sql
SELECT h.report_dt, h.ticker, h.permno,
       h.percent_tna, h.nbr_shares, h.market_val
FROM crsp.holdings h
WHERE h.crsp_portno IN %(portnos)s
  AND h.ticker IS NOT NULL
  {date_filter}
ORDER BY h.report_dt, h.percent_tna DESC
```

### extract_trading_days · L68

**`extract_trading_days()`** — line [68](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L68) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT DISTINCT date
FROM crsp.dsf
WHERE permno = 84398
  AND date >= %(start)s
  AND date <= %(end)s
ORDER BY date
```

## Constants

| Name | Value | Line |
|---|---|---|
| `DIA_PORTNOS` | `[1004198, 1021964]` | [21](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L21) |

## Functions

### `extract_holdings()`

```python
def extract_holdings(portnos, start=None, end=None)
```
[line 24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L24)

Extract ETF holdings from crsp.holdings.

Args:
    portnos: List of CRSP portfolio numbers for the ETF
    start: Optional start date string (YYYY-MM-DD)
    end: Optional end date string (YYYY-MM-DD)

Returns:
    DataFrame with columns: report_dt, ticker, permno, percent_tna, nbr_shares

### `extract_trading_days()`

```python
def extract_trading_days(start, end)
```
[line 56](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L56)

Get US equity trading days from CRSP daily data (using SPY).

Args:
    start: Start date string (YYYY-MM-DD)
    end: End date string (YYYY-MM-DD)

Returns:
    Sorted list of datetime.date objects

### `transform_to_lean()`

```python
def transform_to_lean(holdings_df, sid_lookup, trading_days)
```
[line 81](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L81)

Transform CRSP holdings into LEAN ETF universe format.

Forward-fills monthly CRSP data to each trading day.

Args:
    holdings_df: DataFrame from extract_holdings()
    sid_lookup: Dict mapping ticker -> SID string (from sid.build_sid_lookup)
    trading_days: Sorted list of trading day dates

Returns:
    Dict mapping date -> list of CSV line strings

### `publish_etf_universe()`

```python
def publish_etf_universe(etf_ticker, daily_output, lean_data_dir=None)
```
[line 135](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L135)

Write LEAN ETF universe CSV files.

Args:
    etf_ticker: ETF ticker (e.g. "dia")
    daily_output: Dict mapping date -> list of CSV lines
    lean_data_dir: Base lean-data directory (default: lean-data/ relative to package)

Returns:
    Path to the universe directory

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py (163 lines)
> ```python
> """ETF constituent extraction from CRSP mutual fund holdings.
>
> Extracts historical ETF constituent data from crsp.holdings, transforms
> to LEAN ETF universe format, and publishes daily CSV files.
>
> LEAN format: equity/usa/universes/etf/{etf_ticker}/{YYYYMMDD}.csv
> Each line: Ticker,SID,Date,Weight,SharesHeld,
> """
>
> import os
>
> import pandas as pd
>
> from .connection import get_connection
>
>
> # CRSP fund portfolio numbers for DIA (SPDR Dow Jones Industrial Average ETF)
> # Two portfolio numbers cover different date ranges:
> #   1004198: 2002-10-31 to 2010-05-31
> #   1021964: 2010-06-30 to present
> DIA_PORTNOS = [1004198, 1021964]
>
>
> def extract_holdings(portnos, start=None, end=None):
>     """Extract ETF holdings from crsp.holdings.
>
>     Args:
>         portnos: List of CRSP portfolio numbers for the ETF
>         start: Optional start date string (YYYY-MM-DD)
>         end: Optional end date string (YYYY-MM-DD)
>
>     Returns:
>         DataFrame with columns: report_dt, ticker, permno, percent_tna, nbr_shares
>     """
>     conn = get_connection()
>
>     date_filter = ""
>     if start:
>         date_filter += f" AND h.report_dt >= '{start}'"
>     if end:
>         date_filter += f" AND h.report_dt <= '{end}'"
>
>     sql = f"""
>         SELECT h.report_dt, h.ticker, h.permno,
>                h.percent_tna, h.nbr_shares, h.market_val
>         FROM crsp.holdings h
>         WHERE h.crsp_portno IN %(portnos)s
>           AND h.ticker IS NOT NULL
>           {date_filter}
>         ORDER BY h.report_dt, h.percent_tna DESC
>     """
>     df = conn.raw_sql(sql, params={'portnos': tuple(portnos)})
>     return df
>
>
> def extract_trading_days(start, end):
>     """Get US equity trading days from CRSP daily data (using SPY).
>
>     Args:
>         start: Start date string (YYYY-MM-DD)
>         end: End date string (YYYY-MM-DD)
>
>     Returns:
>         Sorted list of datetime.date objects
>     """
>     conn = get_connection()
>     # Use SPY (PERMNO 84398) as trading calendar reference
>     sql = """
>         SELECT DISTINCT date
>         FROM crsp.dsf
>         WHERE permno = 84398
>           AND date >= %(start)s
>           AND date <= %(end)s
>         ORDER BY date
>     """
>     df = conn.raw_sql(sql, params={'start': start, 'end': end})
>     dates = pd.to_datetime(df['date'])
>     return sorted(dates.dt.date.tolist())
>
>
> def transform_to_lean(holdings_df, sid_lookup, trading_days):
>     """Transform CRSP holdings into LEAN ETF universe format.
>
>     Forward-fills monthly CRSP data to each trading day.
>
>     Args:
>         holdings_df: DataFrame from extract_holdings()
>         sid_lookup: Dict mapping ticker -> SID string (from sid.build_sid_lookup)
>         trading_days: Sorted list of trading day dates
>
>     Returns:
>         Dict mapping date -> list of CSV line strings
>     """
>     # Group holdings by report date
>     holdings_df = holdings_df.copy()
>     holdings_df['report_dt'] = pd.to_datetime(holdings_df['report_dt']).dt.date
>
>     report_dates = sorted(holdings_df['report_dt'].unique())
>     if not report_dates:
>         return {}
>
>     # Build report-date -> holdings lookup
>     holdings_by_report = {}
>     for report_dt, group in holdings_df.groupby('report_dt'):
>         rows = []
>         for _, row in group.iterrows():
>             ticker = row['ticker']
>             if pd.isna(ticker) or ticker not in sid_lookup:
>                 continue
>             sid = sid_lookup[ticker]
>             weight = row['percent_tna'] / 100.0 if pd.notna(row['percent_tna']) else ''
>             shares = int(row['nbr_shares']) if pd.notna(row['nbr_shares']) else ''
>             market_val = int(row['market_val']) if pd.notna(row['market_val']) else ''
>             date_str = report_dt.strftime('%Y%m%d')
>             rows.append(f"{ticker},{sid},{date_str},{weight},{shares},{market_val}")
>         holdings_by_report[report_dt] = rows
>
>     # Forward-fill to each trading day
>     daily_output = {}
>     current_holdings = None
>     report_idx = 0
>
>     for day in trading_days:
>         # Advance to the latest report date <= this trading day
>         while report_idx < len(report_dates) and report_dates[report_idx] <= day:
>             current_holdings = holdings_by_report[report_dates[report_idx]]
>             report_idx += 1
>
>         if current_holdings is not None:
>             daily_output[day] = current_holdings
>
>     return daily_output
>
>
> def publish_etf_universe(etf_ticker, daily_output, lean_data_dir=None):
>     """Write LEAN ETF universe CSV files.
>
>     Args:
>         etf_ticker: ETF ticker (e.g. "dia")
>         daily_output: Dict mapping date -> list of CSV lines
>         lean_data_dir: Base lean-data directory (default: lean-data/ relative to package)
>
>     Returns:
>         Path to the universe directory
>     """
>     if lean_data_dir is None:
>         lean_data_dir = os.path.join(
>             os.path.dirname(__file__), '..', '..', 'lean-data'
>         )
>
>     universe_dir = os.path.join(
>         lean_data_dir, 'equity', 'usa', 'universes', 'etf', etf_ticker.lower()
>     )
>     os.makedirs(universe_dir, exist_ok=True)
>
>     for day, lines in daily_output.items():
>         filename = day.strftime('%Y%m%d') + '.csv'
>         filepath = os.path.join(universe_dir, filename)
>         with open(filepath, 'w') as f:
>             f.write('\n'.join(lines) + '\n')
>
>     return universe_dir
> ```
