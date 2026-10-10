---
table: "ibes.statsumu_epsus"
schema: "ibes"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/ibes"
---
# ibes.statsumu_epsus

Schema **ibes** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|ibes.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## ibes.py → extract_consensus

**`extract_consensus()`** — line [71](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L71) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|infrastructure/pipelines/wrds/src/wrds_lean/ibes.py]] · assigned to `sql`

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
