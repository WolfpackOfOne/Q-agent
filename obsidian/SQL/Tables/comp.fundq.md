---
table: "comp.fundq"
schema: "comp"
queries: 2
tags:
  - "sql/table"
  - "sql/schema/comp"
---
# comp.fundq

Schema **comp** · read by 2 queries in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py|quarterly_fundamentals.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## quarterly_fundamentals.py → extract_quarterly_fundamentals

**`extract_quarterly_fundamentals()`** — line [66](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py#L66) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py|infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py]] · assigned to `sql`

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
