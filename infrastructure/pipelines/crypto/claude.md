# Crypto Pipeline

`ccxt`-based puller for **Coinbase** and **Kraken** OHLCV. Writes LEAN-format zips under `lean-data/crypto/<market>/<resolution>/<symbol>.zip`.

## Quick start

```bash
# One-time: build the shared venv at infrastructure/.venv
cd /path/to/Q-agent/infrastructure && bash setup.sh
source .venv/bin/activate

# Pull defaults (BTC/ETH/SOL × USD/USDT/USDC) at daily resolution
cd crypto
python scripts/run_pipeline.py --exchange coinbase
python scripts/run_pipeline.py --exchange kraken
```

The script auto-skips pairs that an exchange doesn't list (e.g. Kraken does not have `BTC/USDC`).

## Output layout

```
lean-data/crypto/
├── coinbasepro/daily/btcusd.zip       # ccxt 'coinbase' → LEAN 'coinbasepro'
└── kraken/daily/btcusd.zip
```

Each zip contains one CSV: headerless rows of `YYYYMMDD 00:00,open,high,low,close,volume`.
**Prices are raw decimals, NOT scaled by 10,000** (that scaling is equities-only).

## Resolutions

- `--resolution daily` (default): one zip per pair containing the full history.
- `--resolution minute`: one zip per pair *per day* under `lean-data/crypto/<market>/minute/<sym>/<YYYYMMDD>_trade.zip`. Heavy — expect long runs.

## Rate limits

The `ExchangeClient` paces requests conservatively per exchange:

| Exchange | Pacing | Notes |
|---|---|---|
| Coinbase | 0.20 s | 10 req/sec public limit |
| Kraken | 1.10 s | 1 req/sec strict; do not lower |

Failures retry with exponential backoff (`tenacity`, 5 attempts).

## API keys (optional)

Public endpoints work without auth. Add keys in `infrastructure/crypto/.env` to raise rate limits. `.env` is gitignored.

## Listing symbols

```bash
python scripts/list_symbols.py --exchange kraken --quote USD | head
```

## Using in LEAN

Point `lean.json` at the parent data dir (you'll need a merged data folder if you also use WRDS equities — keep them as separate `--data-folder` runs for now).

```python
self.AddCrypto("BTCUSD", Resolution.Daily, Market.Kraken)
```

## Using in research / marimo

```python
import zipfile, pandas as pd, pathlib
root = pathlib.Path("../crypto/lean-data/crypto/kraken/daily")
with zipfile.ZipFile(root / "btcusd.zip") as z:
    df = pd.read_csv(z.open(z.namelist()[0]),
                     header=None,
                     names=["datetime", "open", "high", "low", "close", "volume"],
                     parse_dates=["datetime"])
```

## Known gotchas

- **Coinbase ccxt ID** is `coinbase` (was `coinbasepro` before 2023). We map output to `lean-data/crypto/coinbasepro/...` for LEAN compatibility.
- **Kraken pacing is non-negotiable** — public endpoints rate-limit hard at >1 req/sec.
- **SOL/USD on Kraken** uses the `SOL/USD` symbol; `SOL/USDC` may also be listed.
