---
path: "infrastructure/pipelines/wrds/src/wrds_lean/extract.py"
hub: "wrds"
lines: 66
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py"
---
# extract.py

`infrastructure/pipelines/wrds/src/wrds_lean/extract.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py)

## Purpose

SQL extraction functions for CRSP daily data, distributions, and name history.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py|run_broad_quarterly_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_pipeline.py|run_pipeline.py]]

## SQL queries (3)

### extract_daily_prices · L14

**`extract_daily_prices()`** — line [14](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L14) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
       cfacpr, cfacshr
FROM crsp.dsf
WHERE permno IN %(permnos)s
  AND date BETWEEN %(start)s AND %(end)s
ORDER BY permno, date
```

### extract_distributions · L38

**`extract_distributions()`** — line [38](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L38) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsedist|crsp.dsedist]]

```sql
SELECT permno, exdt, distcd, divamt, facpr, facshr
FROM crsp.dsedist
WHERE permno IN %(permnos)s
ORDER BY permno, exdt
```

### extract_name_history · L56

**`extract_name_history()`** — line [56](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L56) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch, exchcd
FROM crsp.dsenames
WHERE permno IN %(permnos)s
ORDER BY permno, namedt
```

## Functions

### `extract_daily_prices()`

```python
def extract_daily_prices(permnos, start='1998-01-01', end='2026-12-31')
```
[line 7](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L7)

Extract daily price data from crsp.dsf.

Returns DataFrame with columns:
    permno, date, openprc, askhi, bidlo, prc, vol, ret, retx, cfacpr, cfacshr

### `extract_distributions()`

```python
def extract_distributions(permnos)
```
[line 31](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L31)

Extract distribution events from crsp.dsedist.

Returns DataFrame with columns:
    permno, exdt, distcd, divamt, facpr, facshr

### `extract_name_history()`

```python
def extract_name_history(permnos)
```
[line 49](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L49)

Extract name/ticker history from crsp.dsenames.

Returns DataFrame with columns:
    permno, ticker, namedt, nameendt, primexch, exchcd

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/extract.py (66 lines)
> ```python
> """SQL extraction functions for CRSP daily data, distributions, and name history."""
>
> import pandas as pd
> from .connection import get_connection
>
>
> def extract_daily_prices(permnos, start='1998-01-01', end='2026-12-31'):
>     """Extract daily price data from crsp.dsf.
>
>     Returns DataFrame with columns:
>         permno, date, openprc, askhi, bidlo, prc, vol, ret, retx, cfacpr, cfacshr
>     """
>     conn = get_connection()
>     sql = """
>         SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
>                cfacpr, cfacshr
>         FROM crsp.dsf
>         WHERE permno IN %(permnos)s
>           AND date BETWEEN %(start)s AND %(end)s
>         ORDER BY permno, date
>     """
>     df = conn.raw_sql(sql, params={
>         'permnos': tuple(permnos),
>         'start': start,
>         'end': end,
>     })
>     df['date'] = pd.to_datetime(df['date'])
>     return df
>
>
> def extract_distributions(permnos):
>     """Extract distribution events from crsp.dsedist.
>
>     Returns DataFrame with columns:
>         permno, exdt, distcd, divamt, facpr, facshr
>     """
>     conn = get_connection()
>     sql = """
>         SELECT permno, exdt, distcd, divamt, facpr, facshr
>         FROM crsp.dsedist
>         WHERE permno IN %(permnos)s
>         ORDER BY permno, exdt
>     """
>     df = conn.raw_sql(sql, params={'permnos': tuple(permnos)})
>     df['exdt'] = pd.to_datetime(df['exdt'])
>     return df
>
>
> def extract_name_history(permnos):
>     """Extract name/ticker history from crsp.dsenames.
>
>     Returns DataFrame with columns:
>         permno, ticker, namedt, nameendt, primexch, exchcd
>     """
>     conn = get_connection()
>     sql = """
>         SELECT permno, ticker, namedt, nameendt, primexch, exchcd
>         FROM crsp.dsenames
>         WHERE permno IN %(permnos)s
>         ORDER BY permno, namedt
>     """
>     df = conn.raw_sql(sql, params={'permnos': tuple(permnos)})
>     df['namedt'] = pd.to_datetime(df['namedt'])
>     df['nameendt'] = pd.to_datetime(df['nameendt'])
>     return df
> ```
