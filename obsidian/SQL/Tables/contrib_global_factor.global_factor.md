---
table: "contrib_global_factor.global_factor"
schema: "contrib_global_factor"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/contrib_global_factor"
---
# contrib_global_factor.global_factor

Schema **contrib_global_factor** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|macro.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## macro.py → extract_global_factors

**`extract_global_factors()`** — line [80](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L80) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|infrastructure/pipelines/wrds/src/wrds_lean/macro.py]] · assigned to `sql`

Tables: [[SQL/Tables/contrib_global_factor.global_factor|contrib_global_factor.global_factor]]

f-string placeholders: `{', '.join(selected_cols)}`, `{limit_clause}`, `{where}`

```sql
SELECT {', '.join(selected_cols)}
FROM contrib_global_factor.global_factor
{where}
ORDER BY date, permno
{limit_clause}
```
