# Polymarket Pipeline

Prediction market metadata and YES-token price history from Polymarket's Gamma and CLOB APIs.

## What it provides

- **Market metadata**: question text, category, resolution date, market IDs
- **YES-token price series**: daily close prices (0–1 probability) for each market

## Prerequisites

No credentials required. Polymarket provides public APIs.

```bash
cd ~/Documents/Q-agent/infrastructure
bash setup.sh
source .venv/bin/activate
```

## Running the pipeline

The pipeline has two steps that must run in order.

**Step 1: Pull market metadata**

```bash
python infrastructure/pipelines/polymarket/scripts/run_markets_pipeline.py
```

This snapshots all active markets and writes `markets.csv`. Takes ~5 minutes for a full scan.

**Step 2: Pull YES-token price history**

```bash
python infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py --skip-existing
```

`--skip-existing` makes the pull incremental — only new markets are downloaded. For a fast smoke test:

```bash
python infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py --limit 10
```

## Filtering markets

The full Polymarket catalogue contains thousands of markets across many categories. Use keyword filtering before the price pull to target specific topics:

```python
import pandas as pd

markets = pd.read_csv("infrastructure/pipelines/polymarket/data/markets.csv")

# Filter to Fed policy markets, exclude noise
INCLUDE = ["federal reserve", "fed funds", "fomc", "interest rate"]
EXCLUDE = ["bank of england", "nba", "norman powell", "turkey", "turkish"]

keep = markets[
    markets["question"].str.lower().str.contains("|".join(INCLUDE)) &
    ~markets["question"].str.lower().str.contains("|".join(EXCLUDE))
]
```

!!! warning
    Apply exclusion terms **before** running the prices pipeline. Terms like "powell" and "rate" match non-Fed markets (NBA player Norman Powell, Bank of England rate decisions). Filtering after the download wastes time and bandwidth.

## Output schema

`markets.csv`:
```
market_id,question,category,end_date,yes_token_id
0x1a2b...,Will the Fed cut rates in March 2025?,Politics,2025-03-31,0xabc...
```

`prices/<market_id>.csv`:
```
Date,Price
20240101,0.342
20240102,0.361
```

## Known issues

- Full market scan is ~200 pages and takes several minutes with 0.15s pacing.
- The CLOB prices endpoint silently fails on schema mismatches when `yesTokenId` is missing. The pipeline validates this field before fetching.
- Pagination uses a cursor that resets to `LTE=` at the end; the pipeline detects this to stop iteration.
