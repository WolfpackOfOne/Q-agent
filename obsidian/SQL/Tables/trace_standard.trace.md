---
table: "trace_standard.trace"
schema: "trace_standard"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/trace_standard"
---
# trace_standard.trace

Schema **trace_standard** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|credit.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## credit.py → extract_trace_trades

**`extract_trace_trades()`** — line [133](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/credit.py#L133) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|infrastructure/pipelines/wrds/src/wrds_lean/credit.py]] · assigned to `sql`

Tables: [[SQL/Tables/trace_enhanced.camasterfile|trace_enhanced.camasterfile]], [[SQL/Tables/trace_enhanced.trace_enhanced|trace_enhanced.trace_enhanced]], [[SQL/Tables/trace_standard.camasterfile|trace_standard.camasterfile]], [[SQL/Tables/trace_standard.trace|trace_standard.trace]]

Dynamic table `{master_table}` → [[SQL/Tables/trace_enhanced.camasterfile|trace_enhanced.camasterfile]], [[SQL/Tables/trace_standard.camasterfile|trace_standard.camasterfile]] *(resolved from assignments / call sites)*

Dynamic table `{table}` → [[SQL/Tables/trace_enhanced.trace_enhanced|trace_enhanced.trace_enhanced]], [[SQL/Tables/trace_standard.trace|trace_standard.trace]] *(resolved from assignments / call sites)*

f-string placeholders: `{date_col}`, `{limit_clause}`, `{master_table}`, `{side_col}`, `{table}`, `{volume_col}`, `{where}`

```sql
SELECT
    t.cusip_id, t.bond_sym_id, t.company_symbol,
    m.issuer_nm, m.grade, m.scrty_ds, m.debt_type_cd,
    m.scrty_type_cd, m.scrty_sbtp_cd, m.cpn_rt, m.cpn_type_cd,
    m.mtrty_dt, m.ind_144a, m.dissem, m.cnvrb_fl,
    t.{date_col}, t.trd_exctn_tm,
    t.rptd_pr, t.yld_pt, t.{volume_col} AS reported_volume,
    t.trc_st, t.asof_cd, t.sale_cndtn_cd, t.{side_col} AS side
FROM {table} t
LEFT JOIN {master_table} m
    ON t.cusip_id = m.cusip_id
    AND (m.stdt IS NULL OR m.stdt <= t.{date_col})
    AND (m.enddt IS NULL OR m.enddt >= t.{date_col})
{where}
ORDER BY t.{date_col}, t.trd_exctn_tm, t.cusip_id
{limit_clause}
```
