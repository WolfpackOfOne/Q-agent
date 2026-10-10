---
table: "crsp.dsf"
schema: "crsp"
queries: 3
tags:
  - "sql/table"
  - "sql/schema/crsp"
---
# crsp.dsf

Schema **crsp** · read by 3 queries in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|compare_tables.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|etf_constituents.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|extract.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## compare_tables.py → compare_tables

**`compare_tables()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/compare_tables.py#L47) in [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|infrastructure/pipelines/wrds/scripts/compare_tables.py]] · assigned to `dsf_sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
       cfacpr, cfacshr
FROM crsp.dsf
WHERE permno IN %(permnos)s
ORDER BY permno, date
```

## etf_constituents.py → extract_trading_days

**`extract_trading_days()`** — line [68](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L68) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py]] · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT DISTINCT date
FROM crsp.dsf
WHERE permno = 84398
  AND date >= %(start)s
  AND date <= %(end)s
ORDER BY date
```

## extract.py → extract_daily_prices

**`extract_daily_prices()`** — line [14](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/extract.py#L14) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|infrastructure/pipelines/wrds/src/wrds_lean/extract.py]] · assigned to `sql`

Tables: [[SQL/Tables/crsp.dsf|crsp.dsf]]

```sql
SELECT permno, date, openprc, askhi, bidlo, prc, vol, ret, retx,
       cfacpr, cfacshr
FROM crsp.dsf
WHERE permno IN %(permnos)s
  AND date BETWEEN %(start)s AND %(end)s
ORDER BY permno, date
```
