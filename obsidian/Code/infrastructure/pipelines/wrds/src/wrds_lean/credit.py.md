---
path: "infrastructure/pipelines/wrds/src/wrds_lean/credit.py"
hub: "wrds"
lines: 169
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py"
---
# credit.py

`infrastructure/pipelines/wrds/src/wrds_lean/credit.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py)

## Purpose

Credit-market exports from TRACE and Markit CDS.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py|run_credit_pipeline.py]]

## SQL queries (2)

### extract_cds · L68

**`extract_cds()`** — line [68](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L68) · assigned to `sql`

Tables: [[SQL/Tables/markit_cds.cds|markit_cds.cds]]

f-string placeholders: `{int(year)}`, `{where}`

```sql
SELECT
    date, ticker, shortname, redcode, sector, region, country,
    avrating, impliedrating, tier, currency, docclause,
    runningcoupon, tenor, parspread, convspreard, upfront,
    cdsrealrecovery, cdsassumedrecovery, compositedepth5y,
    compositepricerating, compositecurverating, hasquotes
FROM markit_cds.cds{int(year)}
{where}
ORDER BY date, ticker, tenor
```

### extract_trace_trades · L133

**`extract_trace_trades()`** — line [133](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L133) · assigned to `sql`

Tables: [[SQL/Tables/trace_enhanced.camasterfile|trace_enhanced.camasterfile]], [[SQL/Tables/trace_enhanced.trace_enhanced|trace_enhanced.trace_enhanced]], [[SQL/Tables/trace_standard.camasterfile|trace_standard.camasterfile]], [[SQL/Tables/trace_standard.trace|trace_standard.trace]]

Dynamic table `{master_table}` → [[SQL/Tables/trace_enhanced.camasterfile|trace_enhanced.camasterfile]], [[SQL/Tables/trace_standard.camasterfile|trace_standard.camasterfile]] *(resolved from assignments / call sites)*

Dynamic table `{table}` → [[SQL/Tables/trace_enhanced.trace_enhanced|trace_enhanced.trace_enhanced]], [[SQL/Tables/trace_standard.trace|trace_standard.trace]] *(resolved from assignments / call sites)*

f-string placeholders: `{date_col}`, `{limit_clause}`, `{master_table}`, `{side_col}`, `{table}`, `{volume_col}`, `{where}`

```sql
SELECT
    t.cusip_id, t.bond_sym_id, t.company_symbol,
    m.issuer_nm, m.grade, m.scrty_ds, m.debt_type_cd,
    m.scrty_type_cd, m.scrty_sbtp_cd, m.cpn_rt, m.cpn_type_cd,
    m.mtrty_dt, m.ind_144a, m.dissem, m.cnvrb_fl,
    t.{date_col}, t.trd_exctn_tm,
    t.rptd_pr, t.yld_pt, t.{volume_col} AS reported_volume,
    t.trc_st, t.asof_cd, t.sale_cndtn_cd, t.{side_col} AS side
FROM {table} t
LEFT JOIN {master_table} m
    ON t.cusip_id = m.cusip_id
    AND (m.stdt IS NULL OR m.stdt <= t.{date_col})
    AND (m.enddt IS NULL OR m.enddt >= t.{date_col})
{where}
ORDER BY t.{date_col}, t.trd_exctn_tm, t.cusip_id
{limit_clause}
```

## Constants

| Name | Value | Line |
|---|---|---|
| `GRADE_ALIASES` | `{'I': 'I', 'IG': 'I', 'INVESTMENT': 'I', 'INVESTMENT_GRADE': 'I', 'INVESTMENT-GRADE': 'I', 'H': 'H', 'HY': 'H', 'HIGH_YIELD': 'H', 'HIGH-YIELD': 'H', 'JUNK':...` | [9](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L9) |

## Functions

### `normalize_trace_grades()`

```python
def normalize_trace_grades(grades)
```
[line 27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L27)

Normalize TRACE grade aliases to WRDS codes: I, H, N.

### `extract_cds()`

```python
def extract_cds(tickers=None, start=None, end=None, tenors=None, years=None)
```
[line 43](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L43)

Pull Markit CDS rows from yearly tables.

### `extract_trace_trades()`

```python
def extract_trace_trades(tickers=None, cusips=None, start=None, end=None, enhanced=False, grades=None, limit=None)
```
[line 92](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L92)

Pull TRACE corporate bond trades.

grades filters the corporate/agency master-file grade code:
  I = investment grade, H = high yield, N = not rated.

### `publish_cds()`

```python
def publish_cds(df, lean_data_dir)
```
[line 154](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L154)

### `publish_trace()`

```python
def publish_trace(df, lean_data_dir, enhanced=False)
```
[line 162](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L162)

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/credit.py (169 lines)
> ```python
> """Credit-market exports from TRACE and Markit CDS."""
>
> import os
>
> import pandas as pd
>
> from .connection import get_connection
>
> GRADE_ALIASES = {
>     'I': 'I',
>     'IG': 'I',
>     'INVESTMENT': 'I',
>     'INVESTMENT_GRADE': 'I',
>     'INVESTMENT-GRADE': 'I',
>     'H': 'H',
>     'HY': 'H',
>     'HIGH_YIELD': 'H',
>     'HIGH-YIELD': 'H',
>     'JUNK': 'H',
>     'N': 'N',
>     'NR': 'N',
>     'NOT_RATED': 'N',
>     'NOT-RATED': 'N',
> }
>
>
> def normalize_trace_grades(grades):
>     """Normalize TRACE grade aliases to WRDS codes: I, H, N."""
>     if not grades:
>         return None
>     normalized = []
>     for grade in grades:
>         key = str(grade).strip().upper()
>         if not key:
>             continue
>         if key not in GRADE_ALIASES:
>             valid = ', '.join(sorted(GRADE_ALIASES))
>             raise ValueError(f"Unknown TRACE grade '{grade}'. Valid aliases: {valid}")
>         normalized.append(GRADE_ALIASES[key])
>     return sorted(set(normalized))
>
>
> def extract_cds(tickers=None, start=None, end=None, tenors=None, years=None):
>     """Pull Markit CDS rows from yearly tables."""
>     conn = get_connection()
>     if years is None:
>         start_year = pd.Timestamp(start).year if start else 2001
>         end_year = pd.Timestamp(end).year if end else pd.Timestamp.today().year
>         years = range(start_year, end_year + 1)
>
>     frames = []
>     for year in years:
>         clauses = []
>         params = {}
>         if tickers:
>             clauses.append('ticker IN %(tickers)s')
>             params['tickers'] = tuple(t.upper() for t in tickers)
>         if start:
>             clauses.append('date >= %(start)s')
>             params['start'] = start
>         if end:
>             clauses.append('date <= %(end)s')
>             params['end'] = end
>         if tenors:
>             clauses.append('tenor IN %(tenors)s')
>             params['tenors'] = tuple(tenors)
>         where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
>         sql = f"""
>             SELECT
>                 date, ticker, shortname, redcode, sector, region, country,
>                 avrating, impliedrating, tier, currency, docclause,
>                 runningcoupon, tenor, parspread, convspreard, upfront,
>                 cdsrealrecovery, cdsassumedrecovery, compositedepth5y,
>                 compositepricerating, compositecurverating, hasquotes
>             FROM markit_cds.cds{int(year)}
>             {where}
>             ORDER BY date, ticker, tenor
>         """
>         try:
>             frames.append(conn.raw_sql(sql, params=params))
>         except Exception as exc:
>             msg = str(exc).lower()
>             if 'does not exist' in msg or 'undefined table' in msg:
>                 continue
>             raise
>
>     if not frames:
>         return pd.DataFrame()
>     return pd.concat(frames, ignore_index=True)
>
>
> def extract_trace_trades(
>     tickers=None,
>     cusips=None,
>     start=None,
>     end=None,
>     enhanced=False,
>     grades=None,
>     limit=None,
> ):
>     """Pull TRACE corporate bond trades.
>
>     grades filters the corporate/agency master-file grade code:
>       I = investment grade, H = high yield, N = not rated.
>     """
>     conn = get_connection()
>     schema = 'trace_enhanced' if enhanced else 'trace_standard'
>     table = f'{schema}.trace_enhanced' if enhanced else f'{schema}.trace'
>     master_table = f'{schema}.camasterfile'
>     date_col = 'trd_exctn_dt'
>     volume_col = 'entrd_vol_qt' if enhanced else 'ascii_rptd_vol_tx'
>     side_col = 'rpt_side_cd' if enhanced else 'side'
>     normalized_grades = normalize_trace_grades(grades)
>     clauses = []
>     params = {}
>     if tickers:
>         clauses.append('t.company_symbol IN %(tickers)s')
>         params['tickers'] = tuple(t.upper() for t in tickers)
>     if cusips:
>         clauses.append('t.cusip_id IN %(cusips)s')
>         params['cusips'] = tuple(cusips)
>     if start:
>         clauses.append(f't.{date_col} >= %(start)s')
>         params['start'] = start
>     if end:
>         clauses.append(f't.{date_col} <= %(end)s')
>         params['end'] = end
>     if normalized_grades:
>         clauses.append('m.grade IN %(grades)s')
>         params['grades'] = tuple(normalized_grades)
>     where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
>     limit_clause = f'LIMIT {int(limit)}' if limit else ''
>     sql = f"""
>         SELECT
>             t.cusip_id, t.bond_sym_id, t.company_symbol,
>             m.issuer_nm, m.grade, m.scrty_ds, m.debt_type_cd,
>             m.scrty_type_cd, m.scrty_sbtp_cd, m.cpn_rt, m.cpn_type_cd,
>             m.mtrty_dt, m.ind_144a, m.dissem, m.cnvrb_fl,
>             t.{date_col}, t.trd_exctn_tm,
>             t.rptd_pr, t.yld_pt, t.{volume_col} AS reported_volume,
>             t.trc_st, t.asof_cd, t.sale_cndtn_cd, t.{side_col} AS side
>         FROM {table} t
>         LEFT JOIN {master_table} m
>             ON t.cusip_id = m.cusip_id
>             AND (m.stdt IS NULL OR m.stdt <= t.{date_col})
>             AND (m.enddt IS NULL OR m.enddt >= t.{date_col})
>         {where}
>         ORDER BY t.{date_col}, t.trd_exctn_tm, t.cusip_id
>         {limit_clause}
>     """
>     return conn.raw_sql(sql, params=params)
>
>
> def publish_cds(df, lean_data_dir):
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'credit')
>     os.makedirs(out_dir, exist_ok=True)
>     filepath = os.path.join(out_dir, 'markit_cds.csv')
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
>
>
> def publish_trace(df, lean_data_dir, enhanced=False):
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'credit')
>     os.makedirs(out_dir, exist_ok=True)
>     filename = 'trace_enhanced_trades.csv' if enhanced else 'trace_trades.csv'
>     filepath = os.path.join(out_dir, filename)
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
> ```
