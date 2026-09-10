# Polymarket Pipeline

Pulls Polymarket market metadata (Gamma API) and historical YES-token prices (CLOB API). No auth required.

Default filter keeps **crypto + macro + elections** markets; pass `--filter all` to keep everything (note: Polymarket has many markets).

## Quick start

```bash
# One-time: build the shared venv at infrastructure/.venv
cd /path/to/Q-agent/infrastructure && bash setup.sh
source .venv/bin/activate

cd polymarket

# 1) Snapshot market metadata (fast — ~1 minute)
python scripts/run_markets_pipeline.py

# 2) Pull historical prices for the filtered markets (slow)
python scripts/run_prices_pipeline.py --limit 10           # smoke test
python scripts/run_prices_pipeline.py --skip-existing       # full pull, resumable
```

## Output layout

```
lean-data/alternative/polymarket/
├── markets.csv                              # Latest filtered market metadata
├── markets_history/<YYYYMMDD>.csv           # Optional dated snapshots
└── prices/<market-slug>.csv                 # One file per market, hourly YES price
```

`markets.csv` columns: `MarketId, Slug, Question, EventSlug, EventTitle, Active, Closed, Archived, StartDate, EndDate, ResolvedOutcome, OutcomePrices, Volume, Liquidity, YesTokenId, NoTokenId, Tags`.

`prices/<slug>.csv` columns: `datetime, price`. Price is the YES-token probability (0–1). NO probability is `1 - price` for binary markets.

## Filters

The default tag filter is defined in `polymarket_lean/gamma.py::DEFAULT_TAG_FILTER`:

```
crypto, bitcoin, ethereum, solana, macro, economics, fed, inflation,
elections, politics, us-elections, trump, biden
```

Override via CLI:

```bash
python scripts/run_markets_pipeline.py --filter crypto bitcoin
python scripts/run_markets_pipeline.py --filter all      # disable filter
```

## Endpoints reference

- **Gamma**: `https://gamma-api.polymarket.com/markets` — paginated market metadata.
- **CLOB**: `https://clob.polymarket.com/prices-history?market=<token_id>&interval=max&fidelity=60` — historical bar prices for a given outcome token.

Both are public; no API key needed. Be polite (default pacing 0.20 s between requests).

## Using in research / marimo

```python
import pandas as pd, pathlib
root = pathlib.Path("../polymarket/lean-data/alternative/polymarket")
markets = pd.read_csv(root / "markets.csv")
crypto = markets[markets["Tags"].str.contains("crypto", na=False)]

# Load one market's price history
prices = pd.read_csv(
    root / "prices" / f"{crypto.iloc[0]['Slug']}.csv",
    parse_dates=["datetime"],
)
```

## Gotchas

- **`clobTokenIds` is sometimes a JSON string**, sometimes a list — `writer._outcome_token_ids` handles both.
- **Markets without YES token id are skipped** in the prices pipeline (typically archived multi-outcome markets).
- **Polymarket has no "official" rate limit doc** — 5 req/sec is comfortable, much higher risks 429s.
- **Prices are in USDC** and represent probability (0–1) for YES tokens.
- **`run_prices_pipeline.py --skip-existing`** makes the pull resumable after interruption.
