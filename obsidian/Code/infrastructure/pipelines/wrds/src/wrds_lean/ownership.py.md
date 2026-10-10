---
path: "infrastructure/pipelines/wrds/src/wrds_lean/ownership.py"
hub: "wrds"
lines: 93
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py"
---
# ownership.py

`infrastructure/pipelines/wrds/src/wrds_lean/ownership.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py)

## Purpose

Institutional ownership exports from Thomson Reuters 13F.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py|run_13f_pipeline.py]]

## SQL queries (1)

### extract_13f_holdings · L29

**`extract_13f_holdings()`** — line [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py#L29) · assigned to `sql`

Tables: [[SQL/Tables/tr_13f.s34|tr_13f.s34]]

f-string placeholders: `{where}`

```sql
SELECT
    rdate, fdate, mgrno, mgrname, typecode, country,
    ticker, cusip, stkname, shares, change, prc,
    shrout1, shrout2, sole, shared, no
FROM tr_13f.s34
{where}
ORDER BY rdate, ticker, mgrno
```

## Functions

### `extract_13f_holdings()`

```python
def extract_13f_holdings(tickers=None, start=None, end=None, min_shares=None)
```
[line 10](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py#L10)

Pull manager-level 13F holdings from tr_13f.s34.

### `build_13f_summary()`

```python
def build_13f_summary(holdings)
```
[line 41](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py#L41)

Aggregate 13F holdings by report date and ticker.

### `publish_13f_holdings()`

```python
def publish_13f_holdings(df, lean_data_dir)
```
[line 79](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py#L79)

### `publish_13f_summary()`

```python
def publish_13f_summary(df, lean_data_dir)
```
[line 87](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py#L87)

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/ownership.py (93 lines)
> ```python
> """Institutional ownership exports from Thomson Reuters 13F."""
>
> import os
>
> import pandas as pd
>
> from .connection import get_connection
>
>
> def extract_13f_holdings(tickers=None, start=None, end=None, min_shares=None):
>     """Pull manager-level 13F holdings from tr_13f.s34."""
>     conn = get_connection()
>     clauses = []
>     params = {}
>     if tickers:
>         clauses.append('ticker IN %(tickers)s')
>         params['tickers'] = tuple(t.upper() for t in tickers)
>     if start:
>         clauses.append('rdate >= %(start)s')
>         params['start'] = start
>     if end:
>         clauses.append('rdate <= %(end)s')
>         params['end'] = end
>     if min_shares is not None:
>         clauses.append('shares >= %(min_shares)s')
>         params['min_shares'] = min_shares
>
>     where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
>     sql = f"""
>         SELECT
>             rdate, fdate, mgrno, mgrname, typecode, country,
>             ticker, cusip, stkname, shares, change, prc,
>             shrout1, shrout2, sole, shared, no
>         FROM tr_13f.s34
>         {where}
>         ORDER BY rdate, ticker, mgrno
>     """
>     return conn.raw_sql(sql, params=params)
>
>
> def build_13f_summary(holdings):
>     """Aggregate 13F holdings by report date and ticker."""
>     if holdings.empty:
>         return pd.DataFrame(columns=[
>             'ReportDate', 'Ticker', 'CUSIP', 'IssuerName', 'ManagerCount',
>             'TotalShares', 'TotalMarketValue', 'SharesOutstanding',
>             'InstitutionalOwnershipPct',
>         ])
>
>     df = holdings.copy()
>     df['market_value'] = df['shares'] * df['prc']
>     grouped = (
>         df.groupby(['rdate', 'ticker'], dropna=False)
>         .agg(
>             CUSIP=('cusip', 'first'),
>             IssuerName=('stkname', 'first'),
>             ManagerCount=('mgrno', 'nunique'),
>             TotalShares=('shares', 'sum'),
>             TotalMarketValue=('market_value', 'sum'),
>             SharesOutstanding=('shrout1', 'max'),
>         )
>         .reset_index()
>     )
>     grouped['InstitutionalOwnershipPct'] = (
>         grouped['TotalShares'] / grouped['SharesOutstanding']
>     )
>     return (
>         grouped.rename(columns={'rdate': 'ReportDate', 'ticker': 'Ticker'})
>         [[
>             'ReportDate', 'Ticker', 'CUSIP', 'IssuerName', 'ManagerCount',
>             'TotalShares', 'TotalMarketValue', 'SharesOutstanding',
>             'InstitutionalOwnershipPct',
>         ]]
>         .sort_values(['Ticker', 'ReportDate'])
>         .reset_index(drop=True)
>     )
>
>
> def publish_13f_holdings(df, lean_data_dir):
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'ownership')
>     os.makedirs(out_dir, exist_ok=True)
>     filepath = os.path.join(out_dir, '13f_holdings.csv')
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
>
>
> def publish_13f_summary(df, lean_data_dir):
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'ownership')
>     os.makedirs(out_dir, exist_ok=True)
>     filepath = os.path.join(out_dir, '13f_summary.csv')
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
> ```
