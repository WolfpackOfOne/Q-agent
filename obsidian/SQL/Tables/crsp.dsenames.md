---
table: "crsp.dsenames"
schema: "crsp"
queries: 3
tags:
  - "sql/table"
  - "sql/schema/crsp"
---
# crsp.dsenames

Schema **crsp** · read by 3 queries in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|compare_tables.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|extract.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## compare_tables.py → compare_tables

**`compare_tables()`** — line [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L23) in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|infrastructure/pipelines/wrds/scripts/compare_tables.py]] · assigned to `names_sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch
FROM crsp.dsenames
WHERE ticker IN %(tickers)s
ORDER BY ticker, nameendt DESC
```

## extract.py → extract_name_history

**`extract_name_history()`** — line [56](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L56) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|infrastructure/pipelines/wrds/src/wrds_lean/extract.py]] · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch, exchcd
FROM crsp.dsenames
WHERE permno IN %(permnos)s
ORDER BY permno, namedt
```

## symbols.py → resolve_permnos

**`resolve_permnos()`** — line [24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py#L24) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|infrastructure/pipelines/wrds/src/wrds_lean/symbols.py]] · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsenames|crsp.dsenames]]

```sql
SELECT permno, ticker, namedt, nameendt, primexch, exchcd
FROM crsp.dsenames
WHERE ticker IN %(tickers)s
ORDER BY ticker, nameendt DESC
```
