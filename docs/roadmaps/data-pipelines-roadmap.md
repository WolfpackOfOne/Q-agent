# Data Pipelines Roadmap

This document tracks planned data pipeline infrastructure for the Q-agent repository.

The long-term goal is to transform the repository into a reusable multi-source quantitative research platform.

---

# Pipeline Categories

## 1. Macro and Rates Infrastructure

Purpose:

Provide reusable macroeconomic and yield-curve datasets for:

- macro regime research
- factor investing
- risk modeling
- asset allocation
- fixed income analytics
- machine learning features

Planned pipelines:

- Treasury.gov rates
- Treasury par yield curve
- FRED macro series
- SOFR
- Fed Funds
- CPI
- unemployment
- recession indicators
- credit spreads

Status:

- Treasury.gov rates -> scaffolded
- FRED -> planned
- SOFR -> planned
- Fed Funds -> planned

---

## 2. Fixed Income Infrastructure

Purpose:

Provide institutional-style fixed income and rates analytics.

Planned pipelines:

- Treasury auctions
- CFTC rates positioning
- futures curve data
- duration and convexity features
- yield curve PCA factors
- Nelson-Siegel modeling

Status:

- planned

---

## 3. News, Events, and Sentiment Infrastructure

Purpose:

Provide alternative-data and NLP research pipelines.

Planned pipelines:

- GDELT global event data
- Reddit sentiment
- SEC filing NLP
- earnings transcripts
- event-study infrastructure
- news embeddings

Status:

- GDELT news tone/volume -> scaffolded (`infrastructure/pipelines/news_events_sentiment/`)
- Reddit -> planned
- SEC filing NLP -> planned
- earnings transcripts -> planned
- news embeddings -> planned

---

# Long-Term Architecture Goals

Future architecture targets:

- standardized schemas
- reusable dataset loaders
- feature registry
- metadata registry
- parquet-based storage
- notebook templates
- QuantConnect integration
- ObjectStore integration
- SQL persistence
- experiment tracking

---

# Repository Structure

All data pipelines are centralized under `infrastructure/pipelines/<source>/`. Each pipeline owns its own scripts, source package, and (where applicable) LEAN-format output directory.

```text
infrastructure/
  pipelines/
    # Established
    crypto/                  # Crypto OHLCV via ccxt (Binance, Coinbase, Kraken)
    edgar/                   # SEC EDGAR fundamentals via edgartools
    polymarket/              # Polymarket markets + YES-token prices
    wrds/                    # WRDS/CRSP equity, fundamentals, IBES, etc.
    yfinance/                # Yahoo Finance OHLCV
    openbb/                  # OpenBB Platform (interactive)
    treasury_gov_rates/      # Treasury.gov daily par yield curve

    # Planned (scaffolded)
    macro_rates/             # FRED, SOFR, Fed Funds, CPI, unemployment
    fixed_income/            # Treasury auctions, CFTC, futures curves, NS factors
    news_events_sentiment/   # GDELT, Reddit, SEC NLP, earnings transcripts

research/
  notebooks/
    macro_rates/
    fixed_income/
    news_events_sentiment/
```
