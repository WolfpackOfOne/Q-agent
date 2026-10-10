---
path: "infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py"
hub: "wrds"
lines: 221
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py"
---
# fundamentals.py

`infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py)

## Purpose

Piotroski F-score pipeline from Compustat annual fundamentals.

Extracts comp.funda data, computes 9 binary F-score signals (point-in-time safe),
and publishes a flat CSV for use in local backtests and research notebooks.

Output: lean-data/alternative/fundamentals/piotroski_scores.csv

Point-in-time: availability date uses rdq (actual earnings release date) when
present, falling back to datadate + 90 days to avoid look-ahead bias.

Signals:
  Profitability:       F1=NI>0, F2=ROA>0, F3=CFO>0, F4=CFO>NI
  Leverage/Liquidity:  F5=LeverageDown, F6=LiquidityUp, F7=NoNewShares
  Efficiency:          F8=GrossMarginUp, F9=AssetTurnoverUp

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py|run_fundamentals_pipeline.py]]

## SQL queries (2)

### extract_fundamentals · L51

**`extract_fundamentals()`** — line [51](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L51) · assigned to `sql`

Tables: [[SQL/Tables/comp.funda|comp.funda]]

f-string placeholders: `{STANDARD_FILTERS}`, `{cols}`, `{fetch_from}`

```sql
SELECT {cols}
FROM comp.funda
WHERE tic IN %(tickers)s
  AND fyear >= {fetch_from}
  {STANDARD_FILTERS}
ORDER BY tic, datadate
```

### extract_all_fundamentals · L76

**`extract_all_fundamentals()`** — line [76](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L76) · assigned to `sql`

Tables: [[SQL/Tables/comp.funda|comp.funda]]

f-string placeholders: `{STANDARD_FILTERS}`, `{cols}`, `{fetch_from}`

```sql
SELECT {cols}
FROM comp.funda
WHERE fyear >= {fetch_from}
  {STANDARD_FILTERS}
ORDER BY tic, datadate
```

## Constants

| Name | Value | Line |
|---|---|---|
| `FUNDA_COLS` | `['gvkey', 'tic', 'conm', 'datadate', 'pdate', 'fyear', 'ni', 'at', 'oancf', 'dltt', 'act', 'lct', 'csho', 'gp', 'sale']` | [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L23) |
| `STANDARD_FILTERS` | `"\n    AND indfmt = 'INDL'\n    AND datafmt = 'STD'\n    AND popsrc = 'D'\n    AND consol = 'C'\n"` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L26) |

## Functions

### `extract_fundamentals()`

```python
def extract_fundamentals(tickers, start_year=1997)
```
[line 34](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L34)

Pull annual fundamentals from comp.funda for the given tickers.

Fetches one extra year before start_year so YoY signals are available
from start_year onward.

Args:
    tickers: List of ticker strings
    start_year: First fiscal year to include in output (default 1997)

Returns:
    DataFrame sorted by (tic, datadate)

### `extract_all_fundamentals()`

```python
def extract_all_fundamentals(start_year=1997)
```
[line 63](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L63)

Pull annual fundamentals from comp.funda for ALL US equities.

Same as extract_fundamentals() but without a ticker filter.
Fetches one extra year before start_year for YoY signals.

Returns:
    DataFrame sorted by (tic, datadate)

### `_availability_date()`

```python
def _availability_date(row)
```
[line 87](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L87)

Return point-in-time availability date for a fiscal year row.

Uses pdate (Compustat preliminary entry date, ~earnings announcement)
when present, falling back to datadate + 90 days.

### `compute_piotroski()`

```python
def compute_piotroski(df)
```
[line 98](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L98)

Compute Piotroski F-scores from raw comp.funda DataFrame.

Args:
    df: DataFrame from extract_fundamentals()

Returns:
    DataFrame with F_Score (0-9) and 9 binary signal columns, one row per
    (ticker, fiscal year). Rows missing prior-year data (first year per
    ticker) are dropped since YoY signals cannot be computed.

### `publish_piotroski()`

```python
def publish_piotroski(scores_df, lean_data_dir=None)
```
[line 200](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L200)

Write Piotroski scores CSV to lean-data.

Args:
    scores_df: DataFrame from compute_piotroski()
    lean_data_dir: Base lean-data directory

Returns:
    Path to the written file

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py (221 lines)
> ```python
> """Piotroski F-score pipeline from Compustat annual fundamentals.
>
> Extracts comp.funda data, computes 9 binary F-score signals (point-in-time safe),
> and publishes a flat CSV for use in local backtests and research notebooks.
>
> Output: lean-data/alternative/fundamentals/piotroski_scores.csv
>
> Point-in-time: availability date uses rdq (actual earnings release date) when
> present, falling back to datadate + 90 days to avoid look-ahead bias.
>
> Signals:
>   Profitability:       F1=NI>0, F2=ROA>0, F3=CFO>0, F4=CFO>NI
>   Leverage/Liquidity:  F5=LeverageDown, F6=LiquidityUp, F7=NoNewShares
>   Efficiency:          F8=GrossMarginUp, F9=AssetTurnoverUp
> """
>
> import os
>
> import pandas as pd
>
> from .connection import get_connection
>
> FUNDA_COLS = ['gvkey', 'tic', 'conm', 'datadate', 'pdate', 'fyear',
>               'ni', 'at', 'oancf', 'dltt', 'act', 'lct', 'csho', 'gp', 'sale']
>
> STANDARD_FILTERS = """
>     AND indfmt = 'INDL'
>     AND datafmt = 'STD'
>     AND popsrc = 'D'
>     AND consol = 'C'
> """
>
>
> def extract_fundamentals(tickers, start_year=1997):
>     """Pull annual fundamentals from comp.funda for the given tickers.
>
>     Fetches one extra year before start_year so YoY signals are available
>     from start_year onward.
>
>     Args:
>         tickers: List of ticker strings
>         start_year: First fiscal year to include in output (default 1997)
>
>     Returns:
>         DataFrame sorted by (tic, datadate)
>     """
>     conn = get_connection()
>     fetch_from = start_year - 1  # need prior year for YoY signals
>
>     cols = ', '.join(FUNDA_COLS)
>     sql = f"""
>         SELECT {cols}
>         FROM comp.funda
>         WHERE tic IN %(tickers)s
>           AND fyear >= {fetch_from}
>           {STANDARD_FILTERS}
>         ORDER BY tic, datadate
>     """
>     df = conn.raw_sql(sql, params={'tickers': tuple(tickers)})
>     return df
>
>
> def extract_all_fundamentals(start_year=1997):
>     """Pull annual fundamentals from comp.funda for ALL US equities.
>
>     Same as extract_fundamentals() but without a ticker filter.
>     Fetches one extra year before start_year for YoY signals.
>
>     Returns:
>         DataFrame sorted by (tic, datadate)
>     """
>     conn = get_connection()
>     fetch_from = start_year - 1
>
>     cols = ', '.join(FUNDA_COLS)
>     sql = f"""
>         SELECT {cols}
>         FROM comp.funda
>         WHERE fyear >= {fetch_from}
>           {STANDARD_FILTERS}
>         ORDER BY tic, datadate
>     """
>     df = conn.raw_sql(sql)
>     return df
>
>
> def _availability_date(row):
>     """Return point-in-time availability date for a fiscal year row.
>
>     Uses pdate (Compustat preliminary entry date, ~earnings announcement)
>     when present, falling back to datadate + 90 days.
>     """
>     if pd.notna(row['pdate']):
>         return pd.Timestamp(row['pdate'])
>     return pd.Timestamp(row['datadate']) + pd.DateOffset(days=90)
>
>
> def compute_piotroski(df):
>     """Compute Piotroski F-scores from raw comp.funda DataFrame.
>
>     Args:
>         df: DataFrame from extract_fundamentals()
>
>     Returns:
>         DataFrame with F_Score (0-9) and 9 binary signal columns, one row per
>         (ticker, fiscal year). Rows missing prior-year data (first year per
>         ticker) are dropped since YoY signals cannot be computed.
>     """
>     df = df.copy()
>     df['datadate'] = pd.to_datetime(df['datadate'])
>     df = df.sort_values(['tic', 'datadate']).reset_index(drop=True)
>
>     # --- Prior-year values (shifted within each ticker group) ---
>     grp = df.groupby('tic')
>     df['at_lag'] = grp['at'].shift(1)
>     df['dltt_lag'] = grp['dltt'].shift(1)
>     df['act_lag'] = grp['act'].shift(1)
>     df['lct_lag'] = grp['lct'].shift(1)
>     df['csho_lag'] = grp['csho'].shift(1)
>     df['gp_lag'] = grp['gp'].shift(1)
>     df['sale_lag'] = grp['sale'].shift(1)
>
>     # --- Average assets (denominator for ROA / asset turnover) ---
>     df['at_avg'] = (df['at'] + df['at_lag']) / 2
>
>     def _flag(series):
>         """Convert a boolean/nullable-boolean Series to 0/1 int, treating NA as 0."""
>         return series.fillna(False).astype(int)
>
>     # --- 9 Binary Signals ---
>
>     # Profitability
>     df['F1_PositiveNI'] = _flag(df['ni'] > 0)
>     df['F2_PositiveROA'] = _flag(df['ni'] / df['at_avg'] > 0)
>     df['F3_PositiveCFO'] = _flag(df['oancf'] > 0)
>     df['F4_CFOgtNI'] = _flag(df['oancf'] > df['ni'])
>
>     # Leverage / Liquidity / Funding
>     lev_curr = df['dltt'] / df['at']
>     lev_lag = df['dltt_lag'] / df['at_lag']
>     df['F5_LeverageDown'] = _flag(lev_curr < lev_lag)
>
>     cr_curr = df['act'] / df['lct']
>     cr_lag = df['act_lag'] / df['lct_lag']
>     df['F6_LiquidityUp'] = _flag(cr_curr > cr_lag)
>
>     df['F7_NoNewShares'] = _flag(df['csho'] <= df['csho_lag'])
>
>     # Operating Efficiency
>     gm_curr = df['gp'] / df['sale']
>     gm_lag = df['gp_lag'] / df['sale_lag']
>     df['F8_GrossMarginUp'] = _flag(gm_curr > gm_lag)
>
>     at_curr = df['sale'] / df['at_avg']
>     at_lag = df['sale_lag'] / df['at_lag']
>     df['F9_AssetTurnoverUp'] = _flag(at_curr > at_lag)
>
>     signal_cols = [f'F{i}_{n}' for i, n in [
>         (1, 'PositiveNI'), (2, 'PositiveROA'), (3, 'PositiveCFO'), (4, 'CFOgtNI'),
>         (5, 'LeverageDown'), (6, 'LiquidityUp'), (7, 'NoNewShares'),
>         (8, 'GrossMarginUp'), (9, 'AssetTurnoverUp'),
>     ]]
>     df['F_Score'] = df[signal_cols].sum(axis=1).astype(int)
>
>     # --- Point-in-time availability date ---
>     df['pdate'] = pd.to_datetime(df['pdate'], errors='coerce')
>     df['AvailableDate'] = df.apply(_availability_date, axis=1)
>
>     # Drop rows with no prior-year data (first fiscal year per ticker)
>     df = df.dropna(subset=['at_lag'])
>
>     # Raw underlying values (useful for research decomposition)
>     raw_cols = ['ni', 'at', 'oancf', 'dltt', 'act', 'lct', 'csho', 'gp', 'sale']
>
>     output_cols = (
>         ['tic', 'conm', 'AvailableDate', 'datadate', 'fyear', 'F_Score']
>         + signal_cols
>         + raw_cols
>     )
>     result = df[output_cols].copy()
>     result = result.rename(columns={
>         'tic': 'Ticker',
>         'conm': 'CompanyName',
>         'datadate': 'FiscalYearEnd',
>         'fyear': 'FiscalYear',
>         'ni': 'NetIncome',
>         'at': 'TotalAssets',
>         'oancf': 'OperatingCashFlow',
>         'dltt': 'LongTermDebt',
>         'act': 'CurrentAssets',
>         'lct': 'CurrentLiabilities',
>         'csho': 'SharesOutstanding',
>         'gp': 'GrossProfit',
>         'sale': 'Revenue',
>     })
>     result = result.sort_values(['Ticker', 'AvailableDate']).reset_index(drop=True)
>     return result
>
>
> def publish_piotroski(scores_df, lean_data_dir=None):
>     """Write Piotroski scores CSV to lean-data.
>
>     Args:
>         scores_df: DataFrame from compute_piotroski()
>         lean_data_dir: Base lean-data directory
>
>     Returns:
>         Path to the written file
>     """
>     if lean_data_dir is None:
>         lean_data_dir = os.path.join(
>             os.path.dirname(__file__), '..', '..', 'lean-data'
>         )
>
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'fundamentals')
>     os.makedirs(out_dir, exist_ok=True)
>
>     filepath = os.path.join(out_dir, 'piotroski_scores.csv')
>     scores_df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
> ```
