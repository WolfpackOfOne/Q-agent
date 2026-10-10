---
table: "information_schema.tables"
schema: "information_schema"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/information_schema"
---
# information_schema.tables

Schema **information_schema** · read by 1 query in [[Code/infrastructure/pipelines/wrds/scripts/probe_fx_access.py|probe_fx_access.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## probe_fx_access.py → list_schema_tables

**`list_schema_tables()`** — line [65](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/probe_fx_access.py#L65) in [[Code/infrastructure/pipelines/wrds/scripts/probe_fx_access.py|infrastructure/pipelines/wrds/scripts/probe_fx_access.py]] · assigned to `sql`

Tables: [[SQL/Tables/information_schema.tables|information_schema.tables]]

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = %(schema)s
ORDER BY table_name
LIMIT 500
```
