---
path: "infrastructure/pipelines/wrds/src/wrds_lean/ibes.py"
hub: "wrds"
lines: 226
tags:
  - "code/python"
  - "pipelines/wrds"
  - "has/sql"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py"
---
# ibes.py

`infrastructure/pipelines/wrds/src/wrds_lean/ibes.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py)

## Purpose

IBES earnings pipeline: consensus estimates and earnings surprise (SUE).

Extracts ibes.statsumu_epsus (monthly consensus snapshots) and ibes.actu_epsus
(reported actuals) for the given tickers, then computes standardized unexpected
earnings (SUE) matching each actual to the most recent consensus published
before the announcement date.

Outputs:
  lean-data/alternative/earnings/ibes_consensus.csv  — monthly consensus snapshots
  lean-data/alternative/earnings/ibes_surprise.csv   — earnings surprise at announcement

Point-in-time rules:
  Consensus: StatDate (= statpers) is when IBES published the snapshot.
             Use StatDate for any signal derived from analyst estimates.
  Surprise:  AnnouncementDate (= anndats) is when earnings were reported.
             SUE uses only the consensus snapshot immediately before that date.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]]

**Imports (external):** [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#sqlalchemy|sqlalchemy]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py|run_broad_ibes_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py|run_ibes_pipeline.py]]

## SQL queries (3)

### resolve_ibes_tickers · L40

**`resolve_ibes_tickers()`** — line [40](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L40) · assigned to `sql`

Tables: [[SQL/Tables/ibes.id|ibes.id]]

```sql
SELECT oftic AS crsp_ticker, ticker AS ibes_ticker, sdates
FROM ibes.id
WHERE oftic IN %(tickers)s
  AND usfirm = 1
ORDER BY oftic, sdates DESC
```

### extract_consensus · L71

**`extract_consensus()`** — line [71](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L71) · assigned to `sql`

Tables: [[SQL/Tables/ibes.statsumu_epsus|ibes.statsumu_epsus]]

f-string placeholders: `{start_year}`

```sql
SELECT ticker, cname, statpers, fpedats, fpi, fiscalp,
       numest, numup, numdown, meanest, medest, stdev, highest, lowest
FROM ibes.statsumu_epsus
WHERE ticker IN %(tickers)s
  AND measure = 'EPS'
  AND curcode = 'USD'
  AND usfirm = 1
  AND fpi IN ('1', '6')
  AND EXTRACT(year FROM statpers) >= {start_year}
ORDER BY ticker, fpi, statpers
```

### extract_actuals · L95

**`extract_actuals()`** — line [95](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L95) · assigned to `sql`

Tables: [[SQL/Tables/ibes.actu_epsus|ibes.actu_epsus]]

f-string placeholders: `{start_year}`

```sql
SELECT ticker, cname, pends, pdicity, anndats, value AS actual_eps
FROM ibes.actu_epsus
WHERE ticker IN %(tickers)s
  AND measure = 'EPS'
  AND curr_act = 'USD'
  AND usfirm = 1
  AND pdicity IN ('ANN', 'QTR')
  AND EXTRACT(year FROM pends) >= {start_year}
ORDER BY ticker, pdicity, pends
```

## Functions

### `resolve_ibes_tickers()`

```python
def resolve_ibes_tickers(crsp_tickers)
```
[line 27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L27)

Map CRSP/exchange tickers to IBES internal tickers via ibes.id.oftic.

IBES uses proprietary internal tickers (e.g. NIKE, UNIH, BEL, WAG, STPL)
that differ from the exchange tickers most callers know (NKE, UNH, VZ, WBA,
TRV). This function looks up the most recently active IBES ticker for each
provided exchange ticker.

Returns a dict {crsp_ticker: ibes_ticker}. Tickers with no mapping in IBES
are assumed identical and pass through unchanged.

### `extract_consensus()`

```python
def extract_consensus(tickers, start_year=1980)
```
[line 59](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L59)

Pull monthly consensus EPS snapshots from ibes.statsumu_epsus.

fpi='1' = current annual FY estimate; fpi='6' = current-quarter estimate.
Resolves CRSP tickers to IBES internal tickers automatically and adds a
CRSPTicker column to the result.

### `extract_actuals()`

```python
def extract_actuals(tickers, start_year=1980)
```
[line 88](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L88)

Pull reported actual EPS from ibes.actu_epsus.

### `build_consensus_output()`

```python
def build_consensus_output(raw_consensus)
```
[line 111](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L111)

Format raw consensus extract for CSV output.

Uses crsp_ticker (the exchange ticker) as the Ticker column so output
matches CRSP universe tickers regardless of IBES internal naming.

### `build_surprise_output()`

```python
def build_surprise_output(raw_consensus, raw_actuals)
```
[line 140](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L140)

Compute SUE for each reported actual.

For each (crsp_ticker, fiscal period, periodicity), finds the most recent
consensus snapshot published before the announcement date, then computes:
  SUE = (ActualEPS - ConsensusEPS) / ConsensusStd

Rows with no matching pre-announcement consensus are still included with
SUE=NaN so the announcement date is preserved for event studies.

### `publish_consensus()`

```python
def publish_consensus(df, lean_data_dir=None)
```
[line 206](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L206)

Write consensus CSV to lean-data/alternative/earnings/.

### `publish_surprise()`

```python
def publish_surprise(df, lean_data_dir=None)
```
[line 217](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L217)

Write earnings surprise CSV to lean-data/alternative/earnings/.

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/ibes.py (226 lines)
> ```python
> """IBES earnings pipeline: consensus estimates and earnings surprise (SUE).
>
> Extracts ibes.statsumu_epsus (monthly consensus snapshots) and ibes.actu_epsus
> (reported actuals) for the given tickers, then computes standardized unexpected
> earnings (SUE) matching each actual to the most recent consensus published
> before the announcement date.
>
> Outputs:
>   lean-data/alternative/earnings/ibes_consensus.csv  — monthly consensus snapshots
>   lean-data/alternative/earnings/ibes_surprise.csv   — earnings surprise at announcement
>
> Point-in-time rules:
>   Consensus: StatDate (= statpers) is when IBES published the snapshot.
>              Use StatDate for any signal derived from analyst estimates.
>   Surprise:  AnnouncementDate (= anndats) is when earnings were reported.
>              SUE uses only the consensus snapshot immediately before that date.
> """
>
> import os
>
> import pandas as pd
> from sqlalchemy import text
>
> from .connection import get_connection
>
>
> def resolve_ibes_tickers(crsp_tickers):
>     """Map CRSP/exchange tickers to IBES internal tickers via ibes.id.oftic.
>
>     IBES uses proprietary internal tickers (e.g. NIKE, UNIH, BEL, WAG, STPL)
>     that differ from the exchange tickers most callers know (NKE, UNH, VZ, WBA,
>     TRV). This function looks up the most recently active IBES ticker for each
>     provided exchange ticker.
>
>     Returns a dict {crsp_ticker: ibes_ticker}. Tickers with no mapping in IBES
>     are assumed identical and pass through unchanged.
>     """
>     conn = get_connection()
>     tickers_list = list(crsp_tickers)
>     sql = f"""
>         SELECT oftic AS crsp_ticker, ticker AS ibes_ticker, sdates
>         FROM ibes.id
>         WHERE oftic IN %(tickers)s
>           AND usfirm = 1
>         ORDER BY oftic, sdates DESC
>     """
>     df = conn.raw_sql(sql, params={'tickers': tuple(tickers_list)})
>     if df.empty:
>         return {t: t for t in tickers_list}
>
>     # Take the most recently updated IBES ticker per exchange ticker
>     latest = df.groupby('crsp_ticker', as_index=False).first()
>     mapping = dict(zip(latest['crsp_ticker'], latest['ibes_ticker']))
>
>     # Fill through for any tickers not found in ibes.id
>     return {t: mapping.get(t, t) for t in tickers_list}
>
>
> def extract_consensus(tickers, start_year=1980):
>     """Pull monthly consensus EPS snapshots from ibes.statsumu_epsus.
>
>     fpi='1' = current annual FY estimate; fpi='6' = current-quarter estimate.
>     Resolves CRSP tickers to IBES internal tickers automatically and adds a
>     CRSPTicker column to the result.
>     """
>     ticker_map = resolve_ibes_tickers(tickers)
>     ibes_tickers = list(set(ticker_map.values()))
>     reverse_map = {v: k for k, v in ticker_map.items()}
>
>     conn = get_connection()
>     sql = f"""
>         SELECT ticker, cname, statpers, fpedats, fpi, fiscalp,
>                numest, numup, numdown, meanest, medest, stdev, highest, lowest
>         FROM ibes.statsumu_epsus
>         WHERE ticker IN %(tickers)s
>           AND measure = 'EPS'
>           AND curcode = 'USD'
>           AND usfirm = 1
>           AND fpi IN ('1', '6')
>           AND EXTRACT(year FROM statpers) >= {start_year}
>         ORDER BY ticker, fpi, statpers
>     """
>     df = conn.raw_sql(sql, params={'tickers': tuple(ibes_tickers)})
>     df['crsp_ticker'] = df['ticker'].map(reverse_map).fillna(df['ticker'])
>     return df
>
>
> def extract_actuals(tickers, start_year=1980):
>     """Pull reported actual EPS from ibes.actu_epsus."""
>     ticker_map = resolve_ibes_tickers(tickers)
>     ibes_tickers = list(set(ticker_map.values()))
>     reverse_map = {v: k for k, v in ticker_map.items()}
>
>     conn = get_connection()
>     sql = f"""
>         SELECT ticker, cname, pends, pdicity, anndats, value AS actual_eps
>         FROM ibes.actu_epsus
>         WHERE ticker IN %(tickers)s
>           AND measure = 'EPS'
>           AND curr_act = 'USD'
>           AND usfirm = 1
>           AND pdicity IN ('ANN', 'QTR')
>           AND EXTRACT(year FROM pends) >= {start_year}
>         ORDER BY ticker, pdicity, pends
>     """
>     df = conn.raw_sql(sql, params={'tickers': tuple(ibes_tickers)})
>     df['crsp_ticker'] = df['ticker'].map(reverse_map).fillna(df['ticker'])
>     return df
>
>
> def build_consensus_output(raw_consensus):
>     """Format raw consensus extract for CSV output.
>
>     Uses crsp_ticker (the exchange ticker) as the Ticker column so output
>     matches CRSP universe tickers regardless of IBES internal naming.
>     """
>     df = raw_consensus.copy()
>     df['statpers'] = pd.to_datetime(df['statpers'])
>     df['fpedats'] = pd.to_datetime(df['fpedats'])
>     df['Periodicity'] = df['fpi'].map({'1': 'ANN', '6': 'QTR'})
>
>     return (
>         df.rename(columns={
>             'crsp_ticker': 'Ticker', 'cname': 'CompanyName',
>             'statpers': 'StatDate', 'fpedats': 'FiscalPeriodEnd',
>             'numest': 'NumAnalysts', 'numup': 'NumUp', 'numdown': 'NumDown',
>             'meanest': 'MeanEPS', 'medest': 'MedianEPS', 'stdev': 'StdEPS',
>             'highest': 'HighestEPS', 'lowest': 'LowestEPS',
>         })
>         [[
>             'Ticker', 'CompanyName', 'FiscalPeriodEnd', 'StatDate', 'Periodicity',
>             'NumAnalysts', 'NumUp', 'NumDown',
>             'MeanEPS', 'MedianEPS', 'StdEPS', 'HighestEPS', 'LowestEPS',
>         ]]
>         .sort_values(['Ticker', 'Periodicity', 'StatDate'])
>         .reset_index(drop=True)
>     )
>
>
> def build_surprise_output(raw_consensus, raw_actuals):
>     """Compute SUE for each reported actual.
>
>     For each (crsp_ticker, fiscal period, periodicity), finds the most recent
>     consensus snapshot published before the announcement date, then computes:
>       SUE = (ActualEPS - ConsensusEPS) / ConsensusStd
>
>     Rows with no matching pre-announcement consensus are still included with
>     SUE=NaN so the announcement date is preserved for event studies.
>     """
>     cons = raw_consensus.copy()
>     act = raw_actuals.copy()
>
>     cons['statpers'] = pd.to_datetime(cons['statpers'])
>     cons['fpedats'] = pd.to_datetime(cons['fpedats'])
>     act['anndats'] = pd.to_datetime(act['anndats'])
>     act['pends'] = pd.to_datetime(act['pends'])
>
>     act['fpi'] = act['pdicity'].map({'ANN': '1', 'QTR': '6'})
>     act = act.dropna(subset=['anndats', 'fpi'])
>
>     # Join on crsp_ticker so the mapping is consistent across both tables
>     merged = act.merge(
>         cons[['crsp_ticker', 'fpi', 'fpedats', 'statpers', 'meanest', 'medest', 'stdev', 'numest']],
>         left_on=['crsp_ticker', 'fpi', 'pends'],
>         right_on=['crsp_ticker', 'fpi', 'fpedats'],
>         how='left',
>     )
>
>     # Point-in-time filter: only consensus published before announcement
>     pre = merged[merged['statpers'] < merged['anndats']]
>
>     # Most recent consensus snapshot per actual report
>     pre = pre.sort_values('statpers')
>     latest_cons = pre.groupby(['crsp_ticker', 'fpi', 'pends'], as_index=False).last()
>
>     # Re-attach actuals that had no pre-announcement consensus (SUE will be NaN)
>     act_keys = act[['crsp_ticker', 'fpi', 'pends', 'pdicity', 'anndats', 'actual_eps', 'cname']]
>     result = act_keys.merge(
>         latest_cons[['crsp_ticker', 'fpi', 'pends', 'statpers', 'meanest', 'medest', 'stdev', 'numest']],
>         on=['crsp_ticker', 'fpi', 'pends'],
>         how='left',
>     )
>
>     result['SUE'] = (result['actual_eps'] - result['meanest']) / result['stdev']
>
>     return (
>         result.rename(columns={
>             'crsp_ticker': 'Ticker', 'cname': 'CompanyName',
>             'pends': 'FiscalPeriodEnd', 'pdicity': 'Periodicity',
>             'anndats': 'AnnouncementDate', 'actual_eps': 'ActualEPS',
>             'meanest': 'ConsensusEPS', 'medest': 'ConsensusMedianEPS',
>             'stdev': 'ConsensusStd', 'numest': 'NumAnalysts',
>             'statpers': 'ConsensusDate',
>         })
>         [[
>             'Ticker', 'CompanyName', 'FiscalPeriodEnd', 'Periodicity',
>             'AnnouncementDate', 'ActualEPS',
>             'ConsensusEPS', 'ConsensusMedianEPS', 'ConsensusStd', 'NumAnalysts',
>             'SUE', 'ConsensusDate',
>         ]]
>         .sort_values(['Ticker', 'Periodicity', 'FiscalPeriodEnd'])
>         .reset_index(drop=True)
>     )
>
>
> def publish_consensus(df, lean_data_dir=None):
>     """Write consensus CSV to lean-data/alternative/earnings/."""
>     if lean_data_dir is None:
>         lean_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'earnings')
>     os.makedirs(out_dir, exist_ok=True)
>     filepath = os.path.join(out_dir, 'ibes_consensus.csv')
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
>
>
> def publish_surprise(df, lean_data_dir=None):
>     """Write earnings surprise CSV to lean-data/alternative/earnings/."""
>     if lean_data_dir is None:
>         lean_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
>     out_dir = os.path.join(lean_data_dir, 'alternative', 'earnings')
>     os.makedirs(out_dir, exist_ok=True)
>     filepath = os.path.join(out_dir, 'ibes_surprise.csv')
>     df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
>     return filepath
> ```
