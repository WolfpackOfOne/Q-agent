---
path: "infrastructure/pipelines/wrds/src/wrds_lean/symbols.py"
hub: "wrds"
lines: 50
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py"
---
# symbols.py

`infrastructure/pipelines/wrds/src/wrds_lean/symbols.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py)

## Purpose

Universe definition and PERMNO resolution from CRSP.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py|run_13f_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py|run_finratio_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py|run_fundamentals_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py|run_ibes_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_pipeline.py|run_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_quarterly_fundamentals_pipeline.py|run_quarterly_fundamentals_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py|run_sector_pipeline.py]]

## SQL queries (1)

### resolve_permnos · L24

**`resolve_permnos()`** — line [24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py#L24) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch, exchcd
FROM crsp.dsenames
WHERE ticker IN %(tickers)s
ORDER BY ticker, nameendt DESC
```

## Constants

| Name | Value | Line |
|---|---|---|
| `UNIVERSE` | `['AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT', '...` | [6](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py#L6) |

## Functions

### `resolve_permnos()`

```python
def resolve_permnos(tickers=None)
```
[line 16](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py#L16)

Query crsp.dsenames for all name periods for given tickers.

Returns DataFrame with columns: permno, ticker, namedt, nameendt, primexch, exchcd

### `get_current_permnos()`

```python
def get_current_permnos(tickers=None)
```
[line 33](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py#L33)

Return {ticker: permno} dict using the most recent name period.

Also prints warnings for tickers not found in CRSP.

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/symbols.py (50 lines)
> ```python
> """Universe definition and PERMNO resolution from CRSP."""
>
> from .connection import get_connection
>
> # 30-stock equity universe + SPY + SGOV
> UNIVERSE = [
>     "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM",
>     "CSCO", "CVX", "DIS", "DOW", "GS", "HD",
>     "HON", "IBM", "INTC", "JNJ", "JPM", "KO",
>     "MCD", "MMM", "MRK", "MSFT", "NKE", "PG",
>     "TRV", "UNH", "V", "VZ", "WBA", "WMT",
>     "SPY", "SGOV",
> ]
>
>
> def resolve_permnos(tickers=None):
>     """Query crsp.dsenames for all name periods for given tickers.
>
>     Returns DataFrame with columns: permno, ticker, namedt, nameendt, primexch, exchcd
>     """
>     if tickers is None:
>         tickers = UNIVERSE
>     conn = get_connection()
>     sql = """
>         SELECT permno, ticker, namedt, nameendt, primexch, exchcd
>         FROM crsp.dsenames
>         WHERE ticker IN %(tickers)s
>         ORDER BY ticker, nameendt DESC
>     """
>     return conn.raw_sql(sql, params={'tickers': tuple(tickers)})
>
>
> def get_current_permnos(tickers=None):
>     """Return {ticker: permno} dict using the most recent name period.
>
>     Also prints warnings for tickers not found in CRSP.
>     """
>     if tickers is None:
>         tickers = UNIVERSE
>     df = resolve_permnos(tickers)
>     # Take the most recent name period per ticker
>     current = (df.sort_values('nameendt', ascending=False)
>                .drop_duplicates('ticker')
>                .set_index('ticker')['permno']
>                .to_dict())
>     missing = [t for t in tickers if t not in current]
>     if missing:
>         print(f"WARNING: Tickers not found in CRSP dsenames: {missing}")
>     return current
> ```
