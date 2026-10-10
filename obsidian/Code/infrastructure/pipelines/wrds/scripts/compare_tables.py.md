---
path: "infrastructure/pipelines/wrds/scripts/compare_tables.py"
hub: "wrds"
lines: 135
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py"
---
# compare_tables.py

`infrastructure/pipelines/wrds/scripts/compare_tables.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py)

## Purpose

Phase 0: Compare crsp.dsf vs crsp.crsp_daily_data for 5 test symbols.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#sys|sys]]

## SQL queries (5)

### compare_tables · L23

**`compare_tables()`** — line [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L23) · assigned to `names_sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch
FROM crsp.dsenames
WHERE ticker IN %(tickers)s
ORDER BY ticker, nameendt DESC
```

### compare_tables · L47

**`compare_tables()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L47) · assigned to `dsf_sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
       cfacpr, cfacshr
FROM crsp.dsf
WHERE permno IN %(permnos)s
ORDER BY permno, date
```

### compare_tables · L79

**`compare_tables()`** — line [79](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L79) · assigned to `cdd_sql`

Tables: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]]

```sql
SELECT *
FROM crsp.crsp_daily_data
WHERE permno IN %(permnos)s
LIMIT 100
```

### compare_tables · L94

**`compare_tables()`** — line [94](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L94) · assigned to `count_sql`

Tables: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]]

```sql
SELECT COUNT(*) as cnt FROM crsp.crsp_daily_data
```

### compare_tables · L102

**`compare_tables()`** — line [102](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L102) · assigned to `dist_sql`

Tables: [[SQL/Tables/crsp.dsedist|crsp.dsedist]]

```sql
SELECT permno, exdt, distcd, divamt, facpr, facshr
FROM crsp.dsedist
WHERE permno IN %(permnos)s
ORDER BY permno, exdt
```

## Constants

| Name | Value | Line |
|---|---|---|
| `RAW_DIR` | `os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')` | [12](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L12) |
| `TEST_TICKERS` | `['AAPL', 'SPY', 'SGOV', 'IBM', 'BAC']` | [15](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L15) |

## Functions

### `compare_tables()`

```python
def compare_tables()
```
[line 18](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L18)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/compare_tables.py (135 lines)
> ```python
> """Phase 0: Compare crsp.dsf vs crsp.crsp_daily_data for 5 test symbols."""
>
> import argparse
> import sys
> import os
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> import pandas as pd
>
> from wrds_lean.connection import close_connection, get_connection, set_connection_profile
>
> RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
> os.makedirs(RAW_DIR, exist_ok=True)
>
> TEST_TICKERS = ['AAPL', 'SPY', 'SGOV', 'IBM', 'BAC']
>
>
> def compare_tables():
>     conn = get_connection()
>
>     # --- 1. Resolve permnos for test tickers ---
>     print("=== Resolving PERMNOs from crsp.dsenames ===")
>     names_sql = """
>         SELECT permno, ticker, namedt, nameendt, primexch
>         FROM crsp.dsenames
>         WHERE ticker IN %(tickers)s
>         ORDER BY ticker, nameendt DESC
>     """
>     names_df = conn.raw_sql(names_sql, params={'tickers': tuple(TEST_TICKERS)})
>     print(names_df.to_string())
>     names_df.to_csv(os.path.join(RAW_DIR, 'dsenames_test.csv'), index=False)
>
>     # Get most recent permno per ticker
>     permnos = (names_df.sort_values('nameendt', ascending=False)
>                .drop_duplicates('ticker')
>                .set_index('ticker')['permno']
>                .to_dict())
>     print(f"\nTicker -> PERMNO: {permnos}")
>     missing = [t for t in TEST_TICKERS if t not in permnos]
>     if missing:
>         print(f"WARNING: Tickers not found in dsenames: {missing}")
>
>     permno_list = list(permnos.values())
>
>     # --- 2. Sample from crsp.dsf ---
>     print("\n=== crsp.dsf (daily stock file) ===")
>     dsf_sql = """
>         SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
>                cfacpr, cfacshr
>         FROM crsp.dsf
>         WHERE permno IN %(permnos)s
>         ORDER BY permno, date
>     """
>     dsf_df = conn.raw_sql(dsf_sql, params={'permnos': tuple(permno_list)})
>     print(f"Total rows: {len(dsf_df)}")
>     print(f"Date range: {dsf_df['date'].min()} to {dsf_df['date'].max()}")
>     print(f"Columns: {list(dsf_df.columns)}")
>     print(f"\nNull rates:")
>     for col in ['openprc', 'askhi', 'bidlo', 'prc', 'vol', 'cfacpr', 'cfacshr']:
>         null_rate = dsf_df[col].isna().mean()
>         print(f"  {col}: {null_rate:.4f} ({dsf_df[col].isna().sum()} / {len(dsf_df)})")
>     print(f"\nRows per PERMNO:")
>     for ticker, permno in permnos.items():
>         count = len(dsf_df[dsf_df['permno'] == permno])
>         sub = dsf_df[dsf_df['permno'] == permno]
>         if count > 0:
>             print(f"  {ticker} ({permno}): {count} rows, "
>                   f"{sub['date'].min()} to {sub['date'].max()}")
>         else:
>             print(f"  {ticker} ({permno}): 0 rows")
>     dsf_df.to_csv(os.path.join(RAW_DIR, 'dsf_test.csv'), index=False)
>     print(f"\nSample (AAPL last 5 rows):")
>     if 'AAPL' in permnos:
>         print(dsf_df[dsf_df['permno'] == permnos['AAPL']].tail().to_string())
>
>     # --- 3. Sample from crsp.crsp_daily_data (if it exists) ---
>     print("\n=== crsp.crsp_daily_data ===")
>     try:
>         cdd_sql = """
>             SELECT *
>             FROM crsp.crsp_daily_data
>             WHERE permno IN %(permnos)s
>             LIMIT 100
>         """
>         cdd_df = conn.raw_sql(cdd_sql, params={'permnos': tuple(permno_list)})
>         print(f"Rows returned: {len(cdd_df)}")
>         print(f"Columns: {list(cdd_df.columns)}")
>         if len(cdd_df) > 0:
>             print(f"Date range: {cdd_df['date'].min()} to {cdd_df['date'].max()}")
>             cdd_df.to_csv(os.path.join(RAW_DIR, 'crsp_daily_data_test.csv'), index=False)
>             print(cdd_df.head().to_string())
>
>         # Get total row count
>         count_sql = "SELECT COUNT(*) as cnt FROM crsp.crsp_daily_data"
>         count_df = conn.raw_sql(count_sql)
>         print(f"\nTotal table row count: {count_df['cnt'].iloc[0]:,}")
>     except Exception as e:
>         print(f"Error querying crsp.crsp_daily_data: {e}")
>
>     # --- 4. Check distributions table ---
>     print("\n=== crsp.dsedist (distributions) ===")
>     dist_sql = """
>         SELECT permno, exdt, distcd, divamt, facpr, facshr
>         FROM crsp.dsedist
>         WHERE permno IN %(permnos)s
>         ORDER BY permno, exdt
>     """
>     dist_df = conn.raw_sql(dist_sql, params={'permnos': tuple(permno_list)})
>     print(f"Total rows: {len(dist_df)}")
>     for ticker, permno in permnos.items():
>         sub = dist_df[dist_df['permno'] == permno]
>         print(f"  {ticker}: {len(sub)} distribution events")
>         if len(sub) > 0:
>             # Show split events (distcd 5xxx)
>             splits = sub[sub['distcd'].astype(str).str.startswith('5')]
>             dividends = sub[sub['distcd'].astype(str).str.startswith('12')]
>             print(f"    Splits: {len(splits)}, Cash dividends: {len(dividends)}")
>     dist_df.to_csv(os.path.join(RAW_DIR, 'dsedist_test.csv'), index=False)
>
>     close_connection()
>     print("\n=== Done. Raw extracts saved to data/raw/ ===")
>
>
> if __name__ == '__main__':
>     parser = argparse.ArgumentParser(description='Compare CRSP daily tables')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     compare_tables()
> ```
