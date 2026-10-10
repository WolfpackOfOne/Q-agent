---
table: "comp.company"
schema: "comp"
queries: 2
tags:
  - "sql/table"
  - "sql/schema/comp"
---
# comp.company

Schema **comp** · read by 2 queries in [[Code/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py|run_broad_sector_pipeline.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|sectors.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## run_broad_sector_pipeline.py → main

**`main()`** — line [64](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py#L64) in [[Code/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py|infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py]] · assigned to `company`

Tables: [[SQL/Tables/comp.company|comp.company]]

```sql
SELECT gvkey, conm, sic FROM comp.company WHERE gvkey IN %(g)s
```

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
