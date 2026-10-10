---
table: "comp.co_hgic"
schema: "comp"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/comp"
---
# comp.co_hgic

Schema **comp** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|sectors.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## sectors.py → extract_historical_gics

**`extract_historical_gics()`** — line [75](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py#L75) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|infrastructure/pipelines/wrds/src/wrds_lean/sectors.py]] · assigned to `sql`

Tables: [[SQL/Tables/comp.co_hgic|comp.co_hgic]]

```sql
SELECT gvkey, indfrom, indthru, gsector, ggroup, gind, gsubind
FROM comp.co_hgic
WHERE gvkey IN %(gvkeys)s
ORDER BY gvkey, indfrom
```
