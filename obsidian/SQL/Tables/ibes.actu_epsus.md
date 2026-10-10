---
table: "ibes.actu_epsus"
schema: "ibes"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/ibes"
---
# ibes.actu_epsus

Schema **ibes** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|ibes.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## ibes.py → extract_actuals

**`extract_actuals()`** — line [95](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L95) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|infrastructure/pipelines/wrds/src/wrds_lean/ibes.py]] · assigned to `sql`

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
