---
table: "wrdsapps_finratio.firm_ratio"
schema: "wrdsapps_finratio"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/wrdsapps_finratio"
---
# wrdsapps_finratio.firm_ratio

Schema **wrdsapps_finratio** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py|ratios.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## ratios.py → extract_financial_ratios

**`extract_financial_ratios()`** — line [36](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py#L36) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py|infrastructure/pipelines/wrds/src/wrds_lean/ratios.py]] · assigned to `sql`

Tables: [[SQL/Tables/wrdsapps_finratio.firm_ratio|wrdsapps_finratio.firm_ratio]], [[SQL/Tables/wrdsapps_finratio.id|wrdsapps_finratio.id]]

f-string placeholders: `{', '.join(select_parts)}`, `{where}`

```sql
SELECT {', '.join(select_parts)}
FROM wrdsapps_finratio.firm_ratio fr
LEFT JOIN wrdsapps_finratio.id id
    ON fr.permno = id.permno
{where}
ORDER BY id.ticker, fr.public_date
```
