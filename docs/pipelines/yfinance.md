# yfinance Pipeline

Daily OHLCV price data for any ticker covered by Yahoo Finance, written to LEAN-compatible CSV format. Free, no credentials required.

## What it provides

- Any equity, ETF, index, or currency pair on Yahoo Finance
- Daily OHLCV with adjusted close prices
- Fast pulls — typical ticker completes in under 1 second

## Prerequisites

No credentials required.

```bash
cd ~/Documents/Q-agent/infrastructure
bash setup.sh
source .venv/bin/activate
```

## Running the pipeline

```bash
cd infrastructure/pipelines/yfinance
python scripts/run_pipeline.py --tickers AAPL SPY QQQ GLD TLT
```

To pull a specific date range:

```bash
python scripts/run_pipeline.py --tickers AAPL --start 2020-01-01 --end 2024-12-31
```

## Output schema

```
Date,Open,High,Low,Close,Volume
20240101,1852340000,1876520000,1845670000,1869430000,75234100
```

Prices are multiplied by 10,000 per LEAN's internal format.

## Using in a notebook

```python
import pandas as pd

df = pd.read_csv(
    "infrastructure/pipelines/yfinance/data/aapl.csv",
    names=["date", "open", "high", "low", "close", "volume"],
    parse_dates=["date"]
)
df[["open", "high", "low", "close"]] /= 10_000
```

## Good use cases

- Quick price history for a ticker not in the WRDS universe
- ETF constituents and sector proxies (XLK, XLF, XLE, etc.)
- Factor ETFs (MTUM, VLUE, QUAL, SIZE)
- International indices (EFA, EEM, VWO)
- Commodities and rates proxies (GLD, TLT, HYG, LQD)
- Crypto prices as a fallback when the crypto pipeline is not set up

## Notes

- Yahoo Finance data quality is adequate for research but not production. Use WRDS/CRSP for publication-quality results.
- The adjusted close corrects for splits and dividends. LEAN uses unadjusted prices internally — the pipeline writes unadjusted OHLCV by default.
- Rate limits are informal and not published. The pipeline adds small delays between requests to avoid 429 errors.
