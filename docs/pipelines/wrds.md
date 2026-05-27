# WRDS / CRSP Pipeline

Daily equity price and fundamental data for a 30-stock universe plus SPY and SGOV, sourced from the Wharton Research Data Services (WRDS) CRSP database.

## What it provides

- **Daily OHLCV prices**: 1998–present, 30 large-cap equities + SPY + SGOV
- **Sector classifications**: GICS sector and industry group
- **Fundamentals**: quarterly balance sheet, income statement, and cash flow data
- **Piotroski F-scores**: pre-computed from EDGAR fundamentals

## Prerequisites

WRDS institutional access is required. This is available through most university library systems.

```bash
# One-time credential setup
python -c "import wrds; db = wrds.Connection()"
# Enter your WRDS username and password when prompted
```

## Running the pipeline

```bash
source ~/Documents/Q-agent/infrastructure/.venv/bin/activate

# Pull daily price data
python infrastructure/pipelines/wrds/scripts/run_pipeline.py

# Pull with additional entitlements profile
python infrastructure/pipelines/wrds/scripts/run_pipeline.py --profile additional
```

The `--profile additional` flag enables access to OptionMetrics European options data (2002–2023) and IBES analyst earnings estimates (1980–2026, 35M rows) if your WRDS account has those entitlements.

## Output schema

Daily prices:
```
Date,Open,High,Low,Close,Volume
19980102,3234500,3267800,3198200,3251400,4523100
```

Sector classifications:
```
ticker,gics_sector,gics_industry_group
AAPL,Information Technology,Technology Hardware & Equipment
```

## The 30-stock universe

The universe is fixed and designed for teaching and research. It covers major GICS sectors with sufficient history for factor studies:

| Ticker | Sector |
|---|---|
| AAPL, MSFT, GOOGL, META | Technology |
| JPM, BAC, GS, MS | Financials |
| JNJ, UNH, PFE, ABBV | Health Care |
| XOM, CVX | Energy |
| PG, KO, PEP, WMT | Consumer Staples |
| AMZN, HD, NKE | Consumer Discretionary |
| CAT, BA, HON | Industrials |
| NEE, DUK | Utilities |
| AMT, PLD | Real Estate |
| LIN, APD | Materials |
| SPY, SGOV | Benchmarks |

## Using in a notebook

```python
import pandas as pd

prices = pd.read_csv(
    "infrastructure/pipelines/wrds/data/prices.csv",
    index_col=0, parse_dates=True
)
prices /= 10_000  # undo LEAN scaling
```

## Notes

- WRDS denied access is not an error — it means that data product is not included in your subscription. The pipeline handles this gracefully.
- US equity options, RavenPack news, 13F ownership, and short interest data require additional WRDS entitlements that are not currently enabled.
