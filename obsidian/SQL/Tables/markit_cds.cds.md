---
table: "markit_cds.cds"
schema: "markit_cds"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/markit_cds"
---
# markit_cds.cds

Schema **markit_cds** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|credit.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## credit.py → extract_cds

**`extract_cds()`** — line [68](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L68) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|infrastructure/pipelines/wrds/src/wrds_lean/credit.py]] · assigned to `sql`

Tables: [[SQL/Tables/markit_cds.cds|markit_cds.cds]]

f-string placeholders: `{int(year)}`, `{where}`

```sql
SELECT
    date, ticker, shortname, redcode, sector, region, country,
    avrating, impliedrating, tier, currency, docclause,
    runningcoupon, tenor, parspread, convspreard, upfront,
    cdsrealrecovery, cdsassumedrecovery, compositedepth5y,
    compositepricerating, compositecurverating, hasquotes
FROM markit_cds.cds{int(year)}
{where}
ORDER BY date, ticker, tenor
```
