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

Explores the relationship between Trump 2024 election probability (Polymarket) and US sector/industry ETF returns (yfinance: 11 SPDR sector ETFs plus 8 Trump-themed industry slices).

**All data is fetched live from public APIs — no local data required.**

```bash
source infrastructure/marimo/venv/bin/activate
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

Open: http://localhost:2719

---

### Crypto & Polymarket Correlation

Explores correlations between BTC/ETH/SOL prices (Coinbase, Kraken) plus COIN (yfinance) and Polymarket prediction market prices.

**This notebook reads from local pipeline data, which is not committed to the repo.** Run the setup script and both pipelines before launching the notebook:

```bash
# One-time pipeline venv setup. Creates infrastructure/.venv and
# editable-installs crypto_lean / polymarket_lean / yfinance_lean.
bash infrastructure/setup.sh
source infrastructure/.venv/bin/activate

# Crypto OHLCV. Defaults to BTC/ETH/SOL × USD/USDT/USDC; --exchange is required.
# Coinbase covers BTC and ETH but does not list any SOL pair, so run the
# Kraken pull too if you want SOL data.
python infrastructure/pipelines/crypto/scripts/run_pipeline.py --exchange coinbase
python infrastructure/pipelines/crypto/scripts/run_pipeline.py --exchange kraken --pairs SOL/USD SOL/USDT SOL/USDC

# Polymarket: snapshot market metadata first, then pull YES-token price series.
python infrastructure/pipelines/polymarket/scripts/run_markets_pipeline.py
python infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py --skip-existing
```

The polymarket prices pull is incremental and resumable. For a fast smoke test,
substitute `--limit 10` on the prices command.

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
