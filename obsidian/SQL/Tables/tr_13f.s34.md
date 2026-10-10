---
table: "tr_13f.s34"
schema: "tr_13f"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/tr_13f"
---
# tr_13f.s34

Schema **tr_13f** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py|ownership.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## ownership.py → extract_13f_holdings

**`extract_13f_holdings()`** — line [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py#L29) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py|infrastructure/pipelines/wrds/src/wrds_lean/ownership.py]] · assigned to `sql`

Tables: [[SQL/Tables/tr_13f.s34|tr_13f.s34]]

f-string placeholders: `{where}`

```sql
SELECT
    rdate, fdate, mgrno, mgrname, typecode, country,
    ticker, cusip, stkname, shares, change, prc,
    shrout1, shrout2, sole, shared, no
FROM tr_13f.s34
{where}
ORDER BY rdate, ticker, mgrno
```
