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
DateTime,Open,High,Low,Close,Volume
20240101 00:00,42301.25,43412.30,42089.34,43298.70,12847.35
```

Prices are **real, unscaled** values rounded to 4 decimal places — LEAN's crypto
convention does **not** scale prices (unlike equities). The first column is a
`YYYYMMDD 00:00` timestamp. Files are headerless; the header above is shown only
to name the columns.

## Using in a notebook

```python
import pandas as pd

# coinbase maps to LEAN's historical 'coinbasepro' market, under the crypto
# asset-class folder. Check the path printed by the pipeline run to be sure.
zip_path = "infrastructure/pipelines/crypto/lean-data/crypto/coinbasepro/daily/btcusd.zip"
df = pd.read_csv(
    zip_path,
    names=["datetime", "open", "high", "low", "close", "volume"],
    parse_dates=["datetime"],
)
# Prices are already real values — no /10_000 rescaling needed.
```

!!! note
    Check the exact generated path after running the pipeline. Exchange and resolution are part of the output path.

## Known issues

- Kraken does not list SOL/USDC as a spot pair. Only SOL/USD and SOL/USDT are available.
- Coinbase rate limits at ~10 requests/second. The pipeline handles pacing automatically.
- Historical depth varies by exchange; Coinbase typically provides 2–3 years of daily OHLCV.
