# Crypto Pipeline

OHLCV price data for BTC, ETH, and SOL from Coinbase and Kraken, written to LEAN-compatible zip files.

## What it provides

| Asset | Exchange | Pairs |
|---|---|---|
| BTC | Coinbase, Kraken | BTC/USD, BTC/USDT, BTC/USDC |
| ETH | Coinbase, Kraken | ETH/USD, ETH/USDT, ETH/USDC |
| SOL | Kraken only | SOL/USD, SOL/USDT, SOL/USDC |

!!! note
    Coinbase does not list any SOL pair. Run the Kraken pull for SOL data.

## Prerequisites

No credentials required. Both exchanges provide public market data APIs via [ccxt](https://github.com/ccxt/ccxt).

```bash
cd ~/Documents/Q-agent/infrastructure
bash setup.sh
source .venv/bin/activate
```

## Running the pipeline

```bash
source infrastructure/.venv/bin/activate

# BTC and ETH from Coinbase
python infrastructure/pipelines/crypto/scripts/run_pipeline.py --exchange coinbase

# SOL from Kraken (also pulls BTC/ETH as a fallback)
python infrastructure/pipelines/crypto/scripts/run_pipeline.py --exchange kraken --pairs SOL/USD SOL/USDT SOL/USDC
```

By default, output lands in:

```text
infrastructure/pipelines/crypto/lean-data/
```

Use `--lean-root` to write to a different LEAN data folder.

## Output schema

Daily rows inside the generated LEAN zip files follow the pipeline's crypto data schema:

```
Date,Open,High,Low,Close,Volume
20240101,4301245000,4341230000,4289340000,4329870000,12847350000
```

Prices are multiplied by 10,000 per the pipeline's LEAN normalization. Dates are `YYYYMMDD`.

## Using in a notebook

```python
import pandas as pd

zip_path = "infrastructure/pipelines/crypto/lean-data/coinbase/daily/btcusd.zip"
df = pd.read_csv(
    zip_path,
    names=["date", "open", "high", "low", "close", "volume"],
    parse_dates=["date"],
)
df[["open", "high", "low", "close"]] /= 10_000
```

!!! note
    Check the exact generated path after running the pipeline. Exchange and resolution are part of the output path.

## Known issues

- Kraken does not list SOL/USDC as a spot pair. Only SOL/USD and SOL/USDT are available.
- Coinbase rate limits at ~10 requests/second. The pipeline handles pacing automatically.
- Historical depth varies by exchange; Coinbase typically provides 2–3 years of daily OHLCV.
