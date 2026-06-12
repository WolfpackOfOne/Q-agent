# Getting Started

This guide walks you through running the example research notebook included in the repo.

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

## 2. Run the notebook

The notebook is launched with `marimo run`. Open the URL in your browser.

### Election & Industry Returns

Explores the relationship between Trump 2024 election probability (Polymarket) and US sector/industry ETF returns (yfinance: 11 SPDR sector ETFs plus 8 Trump-themed industry slices).

**No setup beyond the venv is required.** The Trump-probability series is read from the committed `MyProjects/ElectionIndustryBeta/data/trump_prob.csv`, and the ETF prices are fetched live from yfinance.

```bash
source infrastructure/marimo/venv/bin/activate
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

Open: http://localhost:2719
