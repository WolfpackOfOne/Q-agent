---
tags:
  - wrds
  - sql
---
# WRDS Pipeline Walkthrough

Back to [[Home]] · hub [[Hubs/Pipelines/wrds|wrds]] · all queries in the [[SQL/SQL Catalog|SQL Catalog]]

Every extractor in `src/wrds_lean/` opens a connection through [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]] (which reads `~/.pgpass` or a profile from `wrds_profiles.json`), then runs `conn.raw_sql(sql, params=...)`. Bind parameters use the psycopg `%(name)s` style. Where a table name is built with an f-string, the vault resolves it from local assignments and call sites.

## Script → module → tables

| CLI script | Modules used | WRDS tables |
|---|---|---|
| [[Code/infrastructure/pipelines/wrds/scripts/run_pipeline.py\|run_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py\|symbols]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py\|extract]], transform, publish | [[SQL/Tables/crsp.dsenames\|crsp.dsenames]], [[SQL/Tables/crsp.dsf\|crsp.dsf]], [[SQL/Tables/crsp.dsedist\|crsp.dsedist]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py\|run_etf_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py\|etf_constituents]], sid | [[SQL/Tables/crsp.holdings\|crsp.holdings]], [[SQL/Tables/crsp.dsf\|crsp.dsf]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py\|run_sector_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py\|sectors]], symbols | [[SQL/Tables/comp.company\|comp.company]], [[SQL/Tables/comp.security\|comp.security]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py\|run_broad_sector_pipeline.py]] | sectors (+ an inline query) | [[SQL/Tables/comp.co_hgic\|comp.co_hgic]], [[SQL/Tables/comp.company\|comp.company]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py\|run_fundamentals_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py\|fundamentals]], symbols | [[SQL/Tables/comp.funda\|comp.funda]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py\|run_broad_fscore_pipeline.py]] | fundamentals, extract (+ an inline CCM query) | [[SQL/Tables/comp.funda\|comp.funda]], [[SQL/Tables/crsp_a_ccm.ccmxpf_lnkhist\|crsp_a_ccm.ccmxpf_lnkhist]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_quarterly_fundamentals_pipeline.py\|run_quarterly_fundamentals_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py\|quarterly_fundamentals]], symbols | [[SQL/Tables/comp.fundq\|comp.fundq]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py\|run_broad_quarterly_pipeline.py]] | quarterly_fundamentals, extract, transform, publish | [[SQL/Tables/comp.fundq\|comp.fundq]], [[SQL/Tables/crsp_a_ccm.ccmxpf_lnkhist\|crsp_a_ccm.ccmxpf_lnkhist]], [[SQL/Tables/crsp.dsf\|crsp.dsf]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py\|run_ibes_pipeline.py]] / [[Code/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py\|run_broad_ibes_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py\|ibes]] | [[SQL/Tables/ibes.id\|ibes.id]], [[SQL/Tables/ibes.statsumu_epsus\|ibes.statsumu_epsus]], [[SQL/Tables/ibes.actu_epsus\|ibes.actu_epsus]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_macro_pipeline.py\|run_macro_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py\|macro]] | [[SQL/Tables/frb.fx_daily\|frb.fx_daily]], [[SQL/Tables/frb.rates_daily\|frb.rates_daily]], [[SQL/Tables/ff.factors_daily\|ff.factors_daily]], [[SQL/Tables/ff.fivefactors_daily\|ff.fivefactors_daily]], [[SQL/Tables/contrib_global_factor.global_factor\|contrib_global_factor.global_factor]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py\|run_13f_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py\|ownership]], symbols | [[SQL/Tables/tr_13f.s34\|tr_13f.s34]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py\|run_finratio_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py\|ratios]], symbols | [[SQL/Tables/wrdsapps_finratio.firm_ratio\|wrdsapps_finratio.firm_ratio]], [[SQL/Tables/wrdsapps_finratio.id\|wrdsapps_finratio.id]] |
| [[Code/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py\|run_credit_pipeline.py]] | [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py\|credit]] | [[SQL/Tables/markit_cds.cds\|markit_cds.cds]], [[SQL/Tables/trace_standard.trace\|trace_standard.trace]] / [[SQL/Tables/trace_enhanced.trace_enhanced\|trace_enhanced.trace_enhanced]] + camasterfile |
| [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py\|compare_tables.py]] | (inline SQL) | [[SQL/Tables/crsp.dsf\|crsp.dsf]] vs [[SQL/Tables/crsp.crsp_daily_data\|crsp.crsp_daily_data]] |
| [[Code/infrastructure/pipelines/wrds/scripts/probe_fx_access.py\|probe_fx_access.py]] | (inline SQL) | [[SQL/Tables/information_schema.tables\|information_schema.tables]] + probed FX candidates |

## Outputs (`infrastructure/pipelines/wrds/lean-data/`, gitignored)

| Path | Written by |
|---|---|
| `equity/usa/daily/{ticker}.zip`, `factor_files/`, `map_files/` | run_pipeline, run_broad_quarterly_pipeline (prices) |
| `equity/usa/universes/etf/dia/{YYYYMMDD}.csv` | run_etf_pipeline |
| `alternative/sectors/sector_map.csv`, `broad_sector_map.csv` | run_sector_pipeline, run_broad_sector_pipeline |
| `alternative/fundamentals/piotroski_scores.csv` | run_fundamentals_pipeline / run_broad_fscore_pipeline |
| `alternative/fundamentals/quarterly_fundamentals.csv` | run_quarterly_fundamentals_pipeline |
| `alternative/fundamentals/broad_quarterly_fundamentals.csv`, `broad_universe.csv`, `broad_permno_map.csv`, `broad_monthly_tri.csv` | run_broad_quarterly_pipeline |
| `alternative/macro/`, `alternative/factors/` | run_macro_pipeline |
| `alternative/ownership/` | run_13f_pipeline |
| `alternative/credit/` | run_credit_pipeline |

## Tables

```dataview
TABLE schema, queries FROM "SQL/Tables" SORT schema ASC
```

Without the Dataview plugin, use the [[SQL/SQL Catalog|SQL Catalog]] instead.
