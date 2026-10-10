---
table: "ff.fivefactors_daily"
schema: "ff"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/ff"
---
# ff.fivefactors_daily

Schema **ff** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|macro.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## macro.py → _select_table

**`_select_table()`** — line [25](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L25) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|infrastructure/pipelines/wrds/src/wrds_lean/macro.py]] · assigned to `sql`

Tables: [[SQL/Tables/ff.factors_daily|ff.factors_daily]], [[SQL/Tables/ff.fivefactors_daily|ff.fivefactors_daily]], [[SQL/Tables/frb.fx_daily|frb.fx_daily]], [[SQL/Tables/frb.rates_daily|frb.rates_daily]]

Dynamic table `{schema}.{table}` → [[SQL/Tables/ff.factors_daily|ff.factors_daily]], [[SQL/Tables/ff.fivefactors_daily|ff.fivefactors_daily]], [[SQL/Tables/frb.fx_daily|frb.fx_daily]], [[SQL/Tables/frb.rates_daily|frb.rates_daily]] *(resolved from assignments / call sites)*

Call sites:
- [L36](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L36) `_select_table('frb', 'fx_daily', start=start, end=end)`
- [L41](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L41) `_select_table('frb', 'rates_daily', start=start, end=end)`
- [L47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/macro.py#L47) `_select_table('ff', table, start=start, end=end)`

f-string placeholders: `{date_col}`, `{schema}`, `{selected}`, `{table}`, `{where}`

```sql
SELECT {selected}
FROM {schema}.{table}
{where}
ORDER BY {date_col}
```
