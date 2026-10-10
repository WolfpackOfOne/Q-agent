---
table: "crsp.dsedist"
schema: "crsp"
queries: 2
tags:
  - "sql/table"
  - "sql/schema/crsp"
---
# crsp.dsedist

Schema **crsp** · read by 2 queries in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|compare_tables.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|extract.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## compare_tables.py → compare_tables

**`compare_tables()`** — line [102](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L102) in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|infrastructure/pipelines/wrds/scripts/compare_tables.py]] · assigned to `dist_sql`

Tables: [[SQL/Tables/crsp.dsedist|crsp.dsedist]]

```sql
SELECT permno, exdt, distcd, divamt, facpr, facshr
FROM crsp.dsedist
WHERE permno IN %(permnos)s
ORDER BY permno, exdt
```

## extract.py → extract_distributions

**`extract_distributions()`** — line [38](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L38) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|infrastructure/pipelines/wrds/src/wrds_lean/extract.py]] · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsedist|crsp.dsedist]]

```sql
SELECT permno, exdt, distcd, divamt, facpr, facshr
FROM crsp.dsedist
WHERE permno IN %(permnos)s
ORDER BY permno, exdt
```
