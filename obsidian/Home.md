---
tags:
  - home
---
# Q-agent — Code Vault

An Obsidian map of the [Q-agent](https://github.com/WolfpackOfOne/Q-agent) workspace: every Python module, script, notebook, workflow and agent prompt is a note, and each one links to what it imports and what imports it. Every SQL query is reproduced word for word.

> [!tip] Start here
> - [[Architecture]]: how the workspace is layered
> - [[Data Lineage]]: which pipeline feeds which notebook and strategy
> - [[WRDS Pipeline Walkthrough]]: each WRDS script, its modules, its SQL and its outputs
> - [[SQL/SQL Catalog|SQL Catalog]]: all 30 SQL queries, grouped by file and by table
> - [[About this vault]]: conventions, and how to regenerate it

## Strategy projects (`MyProjects/`)

| Project | What it does |
|---|---|
| [[Hubs/Projects/Alpha101Portfolio\|Alpha101Portfolio]] | Daily dollar-neutral long/short on the point-in-time top 300 US stocks, using the *101 Formulaic Alphas* |
| [[Hubs/Projects/FundamentalsPortfolio\|FundamentalsPortfolio]] | Quarterly long/short on the top 1,000 US stocks, scored by gradient-boosted trees on Compustat quarterly features |
| [[Hubs/Projects/NewsSentimentAlpha\|NewsSentimentAlpha]] | Daily long/short on a 10-stock universe, ranked by a GDELT financial-media tone z-score |
| [[Hubs/Projects/ElectionIndustryBeta\|ElectionIndustryBeta]] | Long/short sector ETFs by rolling β to Polymarket's Trump-2024 win probability |
| [[Hubs/Projects/PassiveMarketInstabilityStrategy\|PassiveMarketInstabilityStrategy]] | Equal-weight broad ETFs with a passive-pressure risk overlay (research only) |
| [[Hubs/Projects/PassiveMarketInstability\|PassiveMarketInstability]] | Notebook-first research package for the Green/Krishnan/Sturm passive-share SDE |
| [[Hubs/Projects/shared signals\|shared signals]] | Pure-Python signal atoms that projects use through symlinks |
| [[Hubs/Projects/_template\|_template]] | Scaffold rendered by `scripts/create_strategy.py` |

## Data pipelines (`infrastructure/pipelines/`)

| Pipeline | Source |
|---|---|
| [[Hubs/Pipelines/wrds\|wrds]] | WRDS Postgres: CRSP, Compustat, CCM, I/B/E/S, TR 13F, FRB, Fama-French, Markit CDS, TRACE |
| [[Hubs/Pipelines/yfinance\|yfinance]] | Yahoo Finance daily OHLCV, written in LEAN format |
| [[Hubs/Pipelines/crypto\|crypto]] | CCXT (Binance / Coinbase / Kraken) OHLCV |
| [[Hubs/Pipelines/polymarket\|polymarket]] | Polymarket Gamma metadata and CLOB price history |
| [[Hubs/Pipelines/edgar\|edgar]] | SEC EDGAR fundamentals via edgartools |
| [[Hubs/Pipelines/news_events_sentiment\|news_events_sentiment]] | GDELT daily news tone and volume per ticker |
| [[Hubs/Pipelines/treasury_gov_rates\|treasury_gov_rates]] | Treasury.gov daily par yield curve |

`equity_liquidity/`, `etf_flows/`, `passive_share/`, `fixed_income/`, `macro_rates/` and `openbb/` contain only READMEs, which reserve the folder or describe interactive use, so they have no hub.

## Workspace areas

- [[Hubs/Areas/Marimo notebooks|Marimo notebooks]]: the research notebook behind each strategy
- [[Hubs/Areas/Agent Graph System|Agent Graph System]]: knowledge-graph ontology, ingestion, RAG and walk-forward agents ([[Indexes/Cypher Queries|Cypher queries]])
- [[Hubs/Areas/Claude agents and skills|Claude agents and skills]]: subagent prompts, skills, memory hooks
- [[Hubs/Areas/Scripts|Scripts]]: scaffolding, repository policy, LEAN wrappers
- [[Hubs/Areas/Tests|Tests]]: hygiene, template, LEAN-format and graph tests
- [[Hubs/Areas/CI workflows|CI workflows]]: GitHub Actions
- [[Hubs/Areas/Workspace root|Workspace root]]: Dockerfile and other top-level code

## Indexes

- [[Indexes/All files|All files]]
- [[Indexes/External packages|External packages]]: which files import pandas, wrds, ccxt and so on
- [[Indexes/Cypher Queries|Cypher Queries]]
