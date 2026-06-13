# yfinance Pipeline

Daily OHLCV price data for tickers covered by Yahoo Finance, written to LEAN-compatible local data format. Free, no credentials required.

## What it provides

- Daily OHLCV for equities and ETFs covered by Yahoo Finance
- LEAN-ready daily equity zip files under `lean-data/equity/usa/daily/`
- Factor and map files under `lean-data/equity/usa/`
- Fast pulls — a typical ticker completes in under 1 second

!!! note
    Open PR work may add Forex support. Until that lands, treat this page as the documentation for the current equity/ETF pipeline.

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

## Output location

The pipeline writes LEAN-ready files under:

```text
infrastructure/pipelines/yfinance/lean-data/
├── equity/usa/daily/<ticker>.zip
├── equity/usa/factor_files/<ticker>.csv
└── equity/usa/map_files/<ticker>.csv
```

Point `lean.json` at `infrastructure/pipelines/yfinance/lean-data` when you want a local LEAN backtest to read this data.

## Output schema

Daily equity rows inside each zip are headerless and use LEAN's scaled-price convention:

```
Date,Open,High,Low,Close,Volume
20240101,1852340000,1876520000,1845670000,1869430000,75234100
```

Prices are multiplied by 10,000 per LEAN's internal format.

## Using in a notebook

For notebook research, read the CSV inside the zip and undo the LEAN scaling:

```python
import pandas as pd

zip_path = "infrastructure/pipelines/yfinance/lean-data/equity/usa/daily/aapl.zip"
df = pd.read_csv(
    zip_path,
    names=["date", "open", "high", "low", "close", "volume"],
    parse_dates=["date"],
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
