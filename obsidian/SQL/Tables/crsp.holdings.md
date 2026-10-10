---
table: "crsp.holdings"
schema: "crsp"
queries: 1
tags:
  - "sql/table"
  - "sql/schema/crsp"
---
# crsp.holdings

Schema **crsp** · read by 1 query in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|etf_constituents.py]]

Back to [[SQL/SQL Catalog|SQL Catalog]]

## etf_constituents.py → extract_holdings

**`extract_holdings()`** — line [43](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py#L43) in [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py]] · assigned to `sql`

Tables: [[SQL/Tables/crsp.holdings|crsp.holdings]]

f-string placeholders: `{date_filter}`

```sql
SELECT h.report_dt, h.ticker, h.permno,
       h.percent_tna, h.nbr_shares, h.market_val
FROM crsp.holdings h
WHERE h.crsp_portno IN %(portnos)s
  AND h.ticker IS NOT NULL
  {date_filter}
ORDER BY h.report_dt, h.percent_tna DESC
```
