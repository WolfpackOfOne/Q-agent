# Getting Started

This guide walks you through running the two example research notebooks included in the repo.

## Prerequisites

- Python 3.11+
- Git

## 1. Clone and set up the environment

```bash
git clone https://github.com/WolfpackOfOne/Q-agent.git
cd Q-agent
```

Create a virtual environment and install the notebook dependencies:

```bash
python -m venv infrastructure/marimo/venv
source infrastructure/marimo/venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r infrastructure/marimo/requirements.txt
```

## 2. Run the notebooks

Both notebooks are launched with `marimo run`. Open each URL in your browser.

### Election & Industry Returns

Explores the relationship between Trump 2024 election probability (Polymarket) and US industry returns (Kenneth French data library).

**All data is fetched live from public APIs — no local data required.**

```bash
source infrastructure/marimo/venv/bin/activate
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

Open: http://localhost:2719

---

### Crypto & Polymarket Correlation

Explores correlations between BTC/ETH/SOL prices (Coinbase, Kraken) plus COIN (yfinance) and Polymarket prediction market prices.

**This notebook reads from local pipeline data.** First create a pipeline venv and run the pipelines:

```bash
# One-time pipeline venv setup
python -m venv infrastructure/.venv
source infrastructure/.venv/bin/activate
pip install -r infrastructure/requirements.txt

# Crypto OHLCV (Coinbase + Kraken)
python infrastructure/pipelines/crypto/scripts/run_pipeline.py

# Polymarket YES-token prices
python infrastructure/pipelines/polymarket/scripts/run_pipeline.py
```

Then launch the notebook:

```bash
source infrastructure/marimo/venv/bin/activate
marimo run infrastructure/marimo/notebooks/crypto_polymarket_correlation.py --port 2720
```

Open: http://localhost:2720

> Charts for any exchange or market where local data is missing will render empty with a note — the notebook will not crash.

## Running both at the same time

```bash
source infrastructure/marimo/venv/bin/activate
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719 &
marimo run infrastructure/marimo/notebooks/crypto_polymarket_correlation.py --port 2720 &
```

- Election notebook: http://localhost:2719
- Crypto notebook: http://localhost:2720
