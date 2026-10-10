---
table: "crsp.crsp_daily_data"
schema: "crsp"
queries: 2
tags:
  - "sql/table"
  - "sql/schema/crsp"
---
# crsp.crsp_daily_data

Schema **crsp** · read by 2 queries in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|compare_tables.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## compare_tables.py → compare_tables

**`compare_tables()`** — line [79](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L79) in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|infrastructure/pipelines/wrds/scripts/compare_tables.py]] · assigned to `cdd_sql`

Tables: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]]

```sql
SELECT *
FROM crsp.crsp_daily_data
WHERE permno IN %(permnos)s
LIMIT 100
```

## compare_tables.py → compare_tables

**`compare_tables()`** — line [94](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L94) in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|infrastructure/pipelines/wrds/scripts/compare_tables.py]] · assigned to `count_sql`

Tables: [[SQL/Tables/crsp.crsp_daily_data|crsp.crsp_daily_data]]

```sql
SELECT COUNT(*) as cnt FROM crsp.crsp_daily_data
```
