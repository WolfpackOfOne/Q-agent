---
table: "crsp_a_ccm.ccmxpf_lnkhist"
schema: "crsp_a_ccm"
queries: 2
tags:
  - "sql/table"
  - "sql/schema/crsp_a_ccm"
---
# crsp_a_ccm.ccmxpf_lnkhist

Schema **crsp_a_ccm** · read by 2 queries in [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py|quarterly_fundamentals.py]]

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

## quarterly_fundamentals.py → extract_all_quarterly_fundamentals

**`extract_all_quarterly_fundamentals()`** — line [96](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py#L96) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py|infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py]] · assigned to `sql`

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
