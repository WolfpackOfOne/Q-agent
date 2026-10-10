---
table: "ibes.id"
schema: "ibes"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/ibes"
---
# ibes.id

Schema **ibes** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|ibes.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## ibes.py → resolve_ibes_tickers

**`resolve_ibes_tickers()`** — line [40](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py#L40) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|infrastructure/pipelines/wrds/src/wrds_lean/ibes.py]] · assigned to `sql`

Tables: [[SQL/Tables/ibes.id|ibes.id]]

```sql
SELECT oftic AS crsp_ticker, ticker AS ibes_ticker, sdates
FROM ibes.id
WHERE oftic IN %(tickers)s
  AND usfirm = 1
ORDER BY oftic, sdates DESC
```
