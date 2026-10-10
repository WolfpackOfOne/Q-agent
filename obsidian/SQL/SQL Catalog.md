---
tags:
  - "sql"
  - "index"
---
# SQL Catalog

Every SQL statement found in the workspace: **30 queries** over **28 tables** in **13 schemas**. Each query is reproduced verbatim (f-string placeholders kept as `{...}`).

## Tables by schema

- **comp**: [[SQL/Tables/comp.co_hgic|comp.co_hgic]] (1), [[SQL/Tables/comp.company|comp.company]] (2), [[SQL/Tables/comp.funda|comp.funda]] (3), [[SQL/Tables/comp.fundq|comp.fundq]] (2), [[SQL/Tables/comp.security|comp.security]] (1)
- **contrib_global_factor**: [[SQL/Tables/contrib_global_factor.global_factor|contrib_global_factor.global_factor]] (1)
- **crsp**: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]] (2), [[SQL/Tables/crsp.dsedist|crsp.dsedist]] (2), [[SQL/Tables/crsp.dsenames|crsp.dsenames]] (3), [[SQL/Tables/crsp.dsf|crsp.dsf]] (3), [[SQL/Tables/crsp.holdings|crsp.holdings]] (1)
- **crsp_a_ccm**: [[SQL/Tables/crsp_a_ccm.ccmxpf_lnkhist|crsp_a_ccm.ccmxpf_lnkhist]] (2)
- **ff**: [[SQL/Tables/ff.factors_daily|ff.factors_daily]] (1), [[SQL/Tables/ff.fivefactors_daily|ff.fivefactors_daily]] (1)
- **frb**: [[SQL/Tables/frb.fx_daily|frb.fx_daily]] (1), [[SQL/Tables/frb.rates_daily|frb.rates_daily]] (1)
- **ibes**: [[SQL/Tables/ibes.actu_epsus|ibes.actu_epsus]] (1), [[SQL/Tables/ibes.id|ibes.id]] (1), [[SQL/Tables/ibes.statsumu_epsus|ibes.statsumu_epsus]] (1)
- **information_schema**: [[SQL/Tables/information_schema.tables|information_schema.tables]] (1)
- **markit_cds**: [[SQL/Tables/markit_cds.cds|markit_cds.cds]] (1)
- **tr_13f**: [[SQL/Tables/tr_13f.s34|tr_13f.s34]] (1)
- **trace_enhanced**: [[SQL/Tables/trace_enhanced.camasterfile|trace_enhanced.camasterfile]] (1), [[SQL/Tables/trace_enhanced.trace_enhanced|trace_enhanced.trace_enhanced]] (1)
- **trace_standard**: [[SQL/Tables/trace_standard.camasterfile|trace_standard.camasterfile]] (1), [[SQL/Tables/trace_standard.trace|trace_standard.trace]] (1)
- **wrdsapps_finratio**: [[SQL/Tables/wrdsapps_finratio.firm_ratio|wrdsapps_finratio.firm_ratio]] (1), [[SQL/Tables/wrdsapps_finratio.id|wrdsapps_finratio.id]] (1)

## Queries by file

### [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|infrastructure/pipelines/wrds/scripts/compare_tables.py]]

**`compare_tables()`** — line [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L23) · assigned to `names_sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch
FROM crsp.dsenames
WHERE ticker IN %(tickers)s
ORDER BY ticker, nameendt DESC
```

**`compare_tables()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L47) · assigned to `dsf_sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
       cfacpr, cfacshr
FROM crsp.dsf
WHERE permno IN %(permnos)s
ORDER BY permno, date
```

**`compare_tables()`** — line [79](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L79) · assigned to `cdd_sql`

Tables: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]]

```sql
SELECT *
FROM crsp.crsp_daily_data
WHERE permno IN %(permnos)s
LIMIT 100
```

**`compare_tables()`** — line [94](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L94) · assigned to `count_sql`

Tables: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]]

```sql
SELECT COUNT(*) as cnt FROM crsp.crsp_daily_data
```

**`compare_tables()`** — line [102](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L102) · assigned to `dist_sql`

Tables: [[SQL/Tables/crsp.dsedist|crsp.dsedist]]

```sql
SELECT permno, exdt, distcd, divamt, facpr, facshr
FROM crsp.dsedist
WHERE permno IN %(permnos)s
ORDER BY permno, exdt
```

### [[Code/infrastructure/pipelines/wrds/scripts/probe_fx_access.py|infrastructure/pipelines/wrds/scripts/probe_fx_access.py]]

**`probe_table()`** — line [49](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/probe_fx_access.py#L49) · assigned to `df`

Dynamic table `{qualified}` → *not statically resolvable*

Call sites:
- [L98](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/probe_fx_access.py#L98) `probe_table(conn, schema, table)`

f-string placeholders: `{qualified}`

```sql
SELECT * FROM {qualified} LIMIT 1
```

**`list_schema_tables()`** — line [65](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/probe_fx_access.py#L65) · assigned to `sql`

Tables: [[SQL/Tables/information_schema.tables|information_schema.tables]]

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = %(schema)s
ORDER BY table_name
LIMIT 500
```

### [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py]]

**`resolve_permnos_via_ccm()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L47) · assigned to `sql`

Tables: [[SQL/Tables/comp.funda|comp.funda]], [[SQL/Tables/crsp_a_ccm.ccmxpf_lnkhist|crsp_a_ccm.ccmxpf_lnkhist]]

```sql
SELECT DISTINCT f.tic AS ticker, l.lpermno AS permno
FROM comp.funda f
JOIN crsp_a_ccm.ccmxpf_lnkhist l
    ON f.gvkey = l.gvkey
    AND l.linktype IN ('LU', 'LC')
    AND l.linkprim IN ('P', 'C')
    AND l.linkdt <= f.datadate
    AND (l.linkenddt IS NULL OR l.linkenddt >= f.datadate)
WHERE f.tic IN %(tickers)s
  AND f.fyear >= %(start_year)s
  AND f.indfmt = 'INDL'
  AND f.datafmt = 'STD'
  AND f.popsrc = 'D'
  AND f.consol = 'C'
```

### [[Code/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py|infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py]]

**`main()`** — line [64](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py#L64) · assigned to `company`

Tables: [[SQL/Tables/comp.company|comp.company]]

```sql
SELECT gvkey, conm, sic FROM comp.company WHERE gvkey IN %(g)s
```

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|infrastructure/pipelines/wrds/src/wrds_lean/credit.py]]

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

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py]]

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

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|infrastructure/pipelines/wrds/src/wrds_lean/extract.py]]

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

**`extract_distributions()`** — line [38](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L38) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsedist|crsp.dsedist]]

```sql
SELECT permno, exdt, distcd, divamt, facpr, facshr
FROM crsp.dsedist
WHERE permno IN %(permnos)s
ORDER BY permno, exdt
```

**`extract_name_history()`** — line [56](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L56) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch, exchcd
FROM crsp.dsenames
WHERE permno IN %(permnos)s
ORDER BY permno, namedt
```

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py]]

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

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|infrastructure/pipelines/wrds/src/wrds_lean/ibes.py]]

**`resolve_ibes_tickers()`** — line [40](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L40) · assigned to `sql`

Tables: [[SQL/Tables/ibes.id|ibes.id]]

```sql
SELECT oftic AS crsp_ticker, ticker AS ibes_ticker, sdates
FROM ibes.id
WHERE oftic IN %(tickers)s
  AND usfirm = 1
ORDER BY oftic, sdates DESC
```

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

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|infrastructure/pipelines/wrds/src/wrds_lean/macro.py]]

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

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py|infrastructure/pipelines/wrds/src/wrds_lean/ownership.py]]

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

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py|infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py]]

**`extract_quarterly_fundamentals()`** — line [66](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py#L66) · assigned to `sql`

Tables: [[SQL/Tables/comp.fundq|comp.fundq]]

f-string placeholders: `{STANDARD_FILTERS}`, `{cols}`, `{start_year}`

```sql
SELECT {cols}
FROM comp.fundq
WHERE tic IN %(tickers)s
  AND fyearq >= {start_year}
  {STANDARD_FILTERS}
ORDER BY tic, datadate
```

**`extract_all_quarterly_fundamentals()`** — line [96](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py#L96) · assigned to `sql`

Tables: [[SQL/Tables/comp.fundq|comp.fundq]], [[SQL/Tables/crsp_a_ccm.ccmxpf_lnkhist|crsp_a_ccm.ccmxpf_lnkhist]]

f-string placeholders: `{STANDARD_FILTERS}`, `{cols}`, `{float(min_mktcap_musd)}`, `{start_year}`

```sql
SELECT {cols}, l.lpermno AS permno
FROM comp.fundq f
JOIN crsp_a_ccm.ccmxpf_lnkhist l
  ON f.gvkey = l.gvkey
 AND l.linktype IN ('LU', 'LC')
 AND l.linkprim IN ('P', 'C')
 AND l.linkdt <= f.datadate
 AND (l.linkenddt IS NULL OR l.linkenddt >= f.datadate)
WHERE f.fyearq >= {start_year}
  AND f.curcdq = 'USD'
  AND f.prccq IS NOT NULL AND f.cshoq IS NOT NULL
  AND f.prccq * f.cshoq >= {float(min_mktcap_musd)}
  {STANDARD_FILTERS}
ORDER BY f.gvkey, f.datadate
```

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py|infrastructure/pipelines/wrds/src/wrds_lean/ratios.py]]

**`extract_financial_ratios()`** — line [36](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py#L36) · assigned to `sql`

Tables: [[SQL/Tables/wrdsapps_finratio.firm_ratio|wrdsapps_finratio.firm_ratio]], [[SQL/Tables/wrdsapps_finratio.id|wrdsapps_finratio.id]]

f-string placeholders: `{', '.join(select_parts)}`, `{where}`

```sql
SELECT {', '.join(select_parts)}
FROM wrdsapps_finratio.firm_ratio fr
LEFT JOIN wrdsapps_finratio.id id
    ON fr.permno = id.permno
{where}
ORDER BY id.ticker, fr.public_date
```

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|infrastructure/pipelines/wrds/src/wrds_lean/sectors.py]]

**`extract_sectors()`** — line [45](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py#L45) · assigned to `sql`

Tables: [[SQL/Tables/comp.company|comp.company]], [[SQL/Tables/comp.security|comp.security]]

```sql
SELECT s.tic AS ticker, c.gvkey, c.gsector, c.gind, c.gsubind, c.sic, c.conm
FROM comp.security s
JOIN comp.company c ON s.gvkey = c.gvkey
WHERE s.tic IN %(tickers)s
  AND s.iid = '01'
ORDER BY s.tic
```

**`extract_historical_gics()`** — line [75](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py#L75) · assigned to `sql`

Tables: [[SQL/Tables/comp.co_hgic|comp.co_hgic]]

```sql
SELECT gvkey, indfrom, indthru, gsector, ggroup, gind, gsubind
FROM comp.co_hgic
WHERE gvkey IN %(gvkeys)s
ORDER BY gvkey, indfrom
```

### [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|infrastructure/pipelines/wrds/src/wrds_lean/symbols.py]]

**`resolve_permnos()`** — line [24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py#L24) · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch, exchcd
FROM crsp.dsenames
WHERE ticker IN %(tickers)s
ORDER BY ticker, nameendt DESC
```

## Queries with dynamic table names

These build the table name from an f-string placeholder; resolved values come from local assignments and same-file call sites.

- [[Code/infrastructure/pipelines/wrds/scripts/probe_fx_access.py|probe_fx_access.py]] → `probe_table` (L49): `{qualified}` → unresolved
- [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|credit.py]] → `extract_trace_trades` (L133): `{master_table}` → [[SQL/Tables/trace_enhanced.camasterfile|trace_enhanced.camasterfile]], [[SQL/Tables/trace_standard.camasterfile|trace_standard.camasterfile]]; `{table}` → [[SQL/Tables/trace_enhanced.trace_enhanced|trace_enhanced.trace_enhanced]], [[SQL/Tables/trace_standard.trace|trace_standard.trace]]
- [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|macro.py]] → `_select_table` (L25): `{schema}.{table}` → [[SQL/Tables/ff.factors_daily|ff.factors_daily]], [[SQL/Tables/ff.fivefactors_daily|ff.fivefactors_daily]], [[SQL/Tables/frb.fx_daily|frb.fx_daily]], [[SQL/Tables/frb.rates_daily|frb.rates_daily]]
