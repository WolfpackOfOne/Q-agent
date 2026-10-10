---
table: "comp.security"
schema: "comp"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/comp"
---
# comp.security

Schema **comp** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|sectors.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## sectors.py → extract_sectors

**`extract_sectors()`** — line [45](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py#L45) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|infrastructure/pipelines/wrds/src/wrds_lean/sectors.py]] · assigned to `sql`

Tables: [[SQL/Tables/comp.company|comp.company]], [[SQL/Tables/comp.security|comp.security]]

```sql
SELECT s.tic AS ticker, c.gvkey, c.gsector, c.gind, c.gsubind, c.sic, c.conm
FROM comp.security s
JOIN comp.company c ON s.gvkey = c.gvkey
WHERE s.tic IN %(tickers)s
  AND s.iid = '01'
ORDER BY s.tic
```
