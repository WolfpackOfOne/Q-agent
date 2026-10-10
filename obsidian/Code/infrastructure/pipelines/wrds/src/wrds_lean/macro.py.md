---
path: "infrastructure/pipelines/wrds/src/wrds_lean/macro.py"
hub: "wrds"
lines: 97
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py"
---
# macro.py

`infrastructure/pipelines/wrds/src/wrds_lean/macro.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py)

## Purpose

Macro, FX, and factor data exports from WRDS.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#os|os]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_macro_pipeline.py|run_macro_pipeline.py]]

## SQL queries (2)

### _select_table · L25

**`_select_table()`** — line [25](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L25) · assigned to `sql`

Tables: [[SQL/Tables/ff.factors_daily|ff.factors_daily]], [[SQL/Tables/ff.fivefactors_daily|ff.fivefactors_daily]], [[SQL/Tables/frb.fx_daily|frb.fx_daily]], [[SQL/Tables/frb.rates_daily|frb.rates_daily]]

Dynamic table `{schema}.{table}` → [[SQL/Tables/ff.factors_daily|ff.factors_daily]], [[SQL/Tables/ff.fivefactors_daily|ff.fivefactors_daily]], [[SQL/Tables/frb.fx_daily|frb.fx_daily]], [[SQL/Tables/frb.rates_daily|frb.rates_daily]] *(resolved from assignments / call sites)*

Call sites:
- [L36](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L36) `_select_table('frb', 'fx_daily', start=start, end=end)`
- [L41](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L41) `_select_table('frb', 'rates_daily', start=start, end=end)`
- [L47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L47) `_select_table('ff', table, start=start, end=end)`

f-string placeholders: `{date_col}`, `{schema}`, `{selected}`, `{table}`, `{where}`

```sql
SELECT {selected}
FROM {schema}.{table}
{where}
ORDER BY {date_col}
```

### extract_global_factors · L80

**`extract_global_factors()`** — line [80](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L80) · assigned to `sql`

Tables: [[SQL/Tables/contrib_global_factor.global_factor|contrib_global_factor.global_factor]]

f-string placeholders: `{', '.join(selected_cols)}`, `{limit_clause}`, `{where}`

```sql
SELECT {', '.join(selected_cols)}
FROM contrib_global_factor.global_factor
{where}
ORDER BY date, permno
{limit_clause}
```

## Functions

### `_date_filter()`

```python
def _date_filter(column, start=None, end=None)
```
[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L8)

### `_select_table()`

```python
def _select_table(schema, table, date_col='date', start=None, end=None, columns=None)
```
[line 20](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L20)

### `extract_fx_daily()`

```python
def extract_fx_daily(start=None, end=None)
```
[line 34](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L34)

Pull Federal Reserve H.10 daily FX rates.

### `extract_rates_daily()`

```python
def extract_rates_daily(start=None, end=None)
```
[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L39)

Pull Federal Reserve daily interest rates and credit spreads.

### `extract_ff_factors()`

```python
def extract_ff_factors(start=None, end=None, five_factor=False)
```
[line 44](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L44)

Pull daily Fama-French factors.

### `extract_global_factors()`

```python
def extract_global_factors(start=None, end=None, countries=None, permnos=None, columns=None, limit=None)
```
[line 50](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L50)

Pull Jensen-Kelly-Pedersen global factor rows.

The source is very wide and large. Callers should pass countries, permnos,
columns, or a limit when exploring.

### `publish_csv()`

```python
def publish_csv(df, lean_data_dir, subdir, filename)
```
[line 90](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L90)

Publish a DataFrame to a CSV under lean-data/alternative.

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/macro.py (97 lines)
> ```python
> """Macro, FX, and factor data exports from WRDS."""
>
> import os
>
> from .connection import get_connection
>
>
> def _date_filter(column, start=None, end=None):
>     clauses = []
>     params = {}
>     if start:
>         clauses.append(f"{column} >= %(start)s")
>         params['start'] = start
>     if end:
>         clauses.append(f"{column} <= %(end)s")
>         params['end'] = end
>     return clauses, params
>
>
> def _select_table(schema, table, date_col='date', start=None, end=None, columns=None):
>     conn = get_connection()
>     selected = ', '.join(columns) if columns else '*'
>     clauses, params = _date_filter(date_col, start, end)
>     where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
>     sql = f"""
>         SELECT {selected}
>         FROM {schema}.{table}
>         {where}
>         ORDER BY {date_col}
>     """
>     return conn.raw_sql(sql, params=params)
>
>
> def extract_fx_daily(start=None, end=None):
>     """Pull Federal Reserve H.10 daily FX rates."""
>     return _select_table('frb', 'fx_daily', start=start, end=end)
>
>
> def extract_rates_daily(start=None, end=None):
>     """Pull Federal Reserve daily interest rates and credit spreads."""
>     return _select_table('frb', 'rates_daily', start=start, end=end)
>
>
> def extract_ff_factors(start=None, end=None, five_factor=False):
>     """Pull daily Fama-French factors."""
>     table = 'fivefactors_daily' if five_factor else 'factors_daily'
>     return _select_table('ff', table, start=start, end=end)
>
>
> def extract_global_factors(
>     start=None,
>     end=None,
>     countries=None,
>     permnos=None,
>     columns=None,
>     limit=None,
> ):
>     """Pull Jensen-Kelly-Pedersen global factor rows.
>
>     The source is very wide and large. Callers should pass countries, permnos,
>     columns, or a limit when exploring.
>     """
>     conn = get_connection()
>     default_cols = [
>         'id', 'permno', 'gvkey', 'iid', 'excntry', 'date', 'eom',
>         'curcd', 'fx', 'me', 'prc', 'ret', 'ret_exc',
>         'gics', 'sic', 'ff49', 'ret_1_0', 'ret_12_1',
>         'market_equity', 'book_equity', 'net_income', 'sales',
>     ]
>     selected_cols = columns or default_cols
>     clauses, params = _date_filter('date', start, end)
>     if countries:
>         clauses.append('excntry IN %(countries)s')
>         params['countries'] = tuple(countries)
>     if permnos:
>         clauses.append('permno IN %(permnos)s')
>         params['permnos'] = tuple(int(p) for p in permnos)
>     where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
>     limit_clause = f'LIMIT {int(limit)}' if limit else ''
>     sql = f"""
>         SELECT {', '.join(selected_cols)}
>         FROM contrib_global_factor.global_factor
>         {where}
>         ORDER BY date, permno
>         {limit_clause}
>     """
>     return conn.raw_sql(sql, params=params)
>
>
> def publish_csv(df, lean_data_dir, subdir, filename):
>     """Publish a DataFrame to a CSV under lean-data/alternative."""
>     out_dir = os.path.join(lean_data_dir, 'alternative', subdir)
>     os.makedirs(out_dir, exist_ok=True)
>     filepath = os.path.join(out_dir, filename)
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
> ```
