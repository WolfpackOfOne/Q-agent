---
table: "comp.funda"
schema: "comp"
queries: 3
tags:
  - "sql/table"
  - "sql/schema/comp"
---
# comp.funda

Schema **comp** · read by 3 queries in [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|fundamentals.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## run_broad_fscore_pipeline.py → resolve_permnos_via_ccm

**`resolve_permnos_via_ccm()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py#L47) in [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py]] · assigned to `sql`

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

## fundamentals.py → extract_fundamentals

**`extract_fundamentals()`** — line [51](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L51) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py]] · assigned to `sql`

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

## fundamentals.py → extract_all_fundamentals

**`extract_all_fundamentals()`** — line [76](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py#L76) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py]] · assigned to `sql`

Tables: [[SQL/Tables/comp.funda|comp.funda]]

f-string placeholders: `{STANDARD_FILTERS}`, `{cols}`, `{fetch_from}`

```sql
SELECT {cols}
FROM comp.funda
WHERE fyear >= {fetch_from}
  {STANDARD_FILTERS}
ORDER BY tic, datadate
```
