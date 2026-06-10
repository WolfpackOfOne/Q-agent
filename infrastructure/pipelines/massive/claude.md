# Massive.com Pipeline

Pulls **end-of-day (EOD) US futures and options data from Massive.com**
(formerly Polygon.io — same client lineage, REST shape, and Python package
name `massive`) and writes LEAN-compatible output under `lean-data/`.

## Status: scaffolded, NOT YET TESTED against the live API

This pipeline was built **without a Massive.com API key** — the user has
not signed up yet (US options data requires the "Advanced" tier, ~$199/mo).
Method names, signatures, and response model field names were cross-checked
against the `massive==2.8.0` package source on PyPI (the official client),
so the *shapes* used by `transform.py`/`client.py` should be accurate. What
has **not** been verified:

- That the endpoints actually return data for the requested tickers/date
  ranges on a real account/subscription tier.
- Pagination behavior across many pages (`MassiveClient`/`iter_to_list`
  materializes the full iterator — fine for small default universes, may
  need streaming for large pulls).
- The exact accepted values for `list_futures_aggregates(resolution=...)`
  — `"day"` is the best-effort guess (see `client.py` "ASSUMPTION" comment).
- Rate limits / retry behavior (no `tenacity` retry wrapper added yet —
  add one once real latency/error behavior is observed).

Run `python scripts/run_futures_pipeline.py` and
`python scripts/run_options_pipeline.py` once `MASSIVE_API_KEY` is set, and
update this file with what you find (especially anything marked
"ASSUMPTION" in `src/massive_lean/client.py` and `transform.py`).

## Why this pipeline exists

The WRDS pipeline (`infrastructure/pipelines/wrds/`) has US options data
permission-denied (`optionm_all`, `cboe_eod` both require subscriptions this
account doesn't have) and no US futures coverage at all — only OptionMetrics
Europe (2002-2023, European exchanges, via `--profile <additional>`).
Massive.com's dedicated Futures and Options Data APIs cover the full US
market, so this pipeline fills that gap.

## Sign-up & API key setup

1. Sign up at **https://massive.com**.
   - **Options data requires the "Advanced" tier** (~$199/mo as of this
     writing — verify current pricing at https://massive.com/pricing).
   - Futures data may be available on a lower tier; check the pricing page
     when you sign up.
2. Generate an API key from **https://massive.com/dashboard**.
3. Copy `.env.example` to `.env` and fill in `MASSIVE_API_KEY`:
   ```bash
   cd ~/Documents/Q-agent/infrastructure/pipelines/massive
   cp .env.example .env
   # edit .env, set MASSIVE_API_KEY=<your key>
   ```
   `.env` is gitignored — never commit it.

If `MASSIVE_API_KEY` is unset, every pipeline script fails fast with an
actionable error message pointing back to this section.

## Quick start

```bash
# One-time: build the shared venv at infrastructure/.venv
cd ~/Documents/Q-agent/infrastructure && bash setup.sh
source .venv/bin/activate

cd pipelines/massive

# Futures EOD daily bars (default roots: ES, NQ, CL, GC, ZN)
python scripts/run_futures_pipeline.py
python scripts/run_futures_pipeline.py --roots ES NQ
python scripts/run_futures_pipeline.py --roots ES --start 2024-01-01 --end 2024-12-31
python scripts/run_futures_pipeline.py --roots ES --contracts ESZ24 ESH25  # explicit contracts

# Options EOD chain snapshot + per-contract daily aggregates (default underlyings: SPY, QQQ)
python scripts/run_options_pipeline.py
python scripts/run_options_pipeline.py --underlyings SPY QQQ
python scripts/run_options_pipeline.py --underlyings SPY --skip-aggregates       # snapshot only
python scripts/run_options_pipeline.py --underlyings SPY --skip-chain-snapshot \
    --strike-range 0.95 1.05
```

## Output layout

```
lean-data/
├── future/<market>/daily/<symbol>_trade.zip       # e.g. future/cme/daily/esz24_trade.zip
│   └── <symbol>_trade_<expiration YYYYMMDD>.csv   # Time,Open,High,Low,Close,Volume (no header)
└── alternative/massive/
    ├── futures/contracts/<root>.csv               # contract reference metadata (header row)
    └── options/
        ├── chains/<underlying>_<YYYYMMDD>.csv     # EOD chain snapshot: greeks/IV/OI (header row)
        └── aggregates/<contract_ticker>.csv       # per-contract daily OHLCV bars (header row)
```

### Futures daily zips (`future/<market>/daily/`)

Follows the documented LEAN futures daily format
(https://github.com/QuantConnect/Lean/blob/master/Data/future/readme.md):
zip named `<symbol>_trade.zip` containing
`<symbol>_trade_<expiration>.csv` with headerless rows
`Time,Open,High,Low,Close,Volume` (`YYYYMMDD 00:00,...`). **Prices are NOT
scaled by 10,000** — that convention is equities-only. `<symbol>` is the
contract ticker (e.g. `esz24`), lowercased. `<market>` is the LEAN exchange
folder name (`cme`, `nymex`, `comex`, `cbot`) from
`massive_lean.config.FUTURES_ROOT_MARKET`.

This format is best-effort and **has not been loaded into a running LEAN
engine** — verify the zip/CSV naming and whether LEAN expects the
continuous/front-month symbol vs. the dated contract ticker once you have
real output to test with.

### Options EOD data (`alternative/massive/options/`)

Written as **alternative data** (header row, point-in-time date column)
rather than native LEAN `option/usa/daily` zips. The native LEAN options
format requires per-contract files named with deci-cent strike prices
embedded in the filename
(https://github.com/QuantConnect/Lean/blob/master/Data/option/readme.md) —
that mapping has not been validated against real Massive.com responses, so
this scaffold keeps options output in the simpler, always-valid alternative
data layer. Two files per underlying:

- **`chains/<underlying>_<YYYYMMDD>.csv`** — a snapshot of
  `list_snapshot_options_chain(underlying)` taken on the day the pipeline
  ran (`snapshot_date` = run date, so it's point-in-time safe — never
  backfilled). Columns: `snapshot_date, underlying_ticker, contract_ticker,
  expiration_date, strike_price, contract_type, bid, ask, last_price,
  volume, open_interest, implied_volatility, delta, gamma, theta, vega`.
  Run this daily (cron / scheduled task) to build a historical panel.

- **`aggregates/<contract_ticker>.csv`** — true historical EOD OHLCV bars
  per contract via `list_aggs("O:...", 1, "day", from, to)`. Columns:
  `date, contract_ticker, open, high, low, close, volume, vwap,
  transactions`. Re-running merges by `date` (new data wins), so it's safe
  to re-run for overlapping date ranges.

### Futures contract reference (`alternative/massive/futures/contracts/`)

One CSV per root symbol with columns `ticker, product_code, exchange,
first_trade_date, last_trade_date, expiration_date, name` — written so you
can see which contract tickers were discovered for a root before the daily
bars were pulled.

## Configuration

Defaults live in `src/massive_lean/config.py`:

- `DEFAULT_FUTURES_ROOTS = ["ES", "NQ", "CL", "GC", "ZN"]` — E-mini S&P 500,
  E-mini Nasdaq 100, Crude Oil WTI, Gold, 10-Year T-Note.
- `FUTURES_ROOT_MARKET` — maps each root to its LEAN exchange folder
  (`cme`, `nymex`, `comex`, `cbot`). Add an entry here if you add a root
  from a different exchange.
- `DEFAULT_OPTIONS_UNDERLYINGS = ["SPY", "QQQ"]`.

Override any of these via CLI flags (`--roots`, `--underlyings`,
`--contracts`) — never hardcode a different universe deep in the pipeline
logic.

## Endpoints reference

Massive's REST surface mirrors Polygon.io's shape; the official Python
client (`pip install -U massive`, `from massive import RESTClient`) is used
throughout. Method names confirmed against `massive==2.8.0` source:

| Data | Method | Endpoint |
|---|---|---|
| Futures contracts | `client.list_futures_contracts(product_code=..., active=...)` | `GET /futures/v1/contracts` |
| Futures daily bars | `client.list_futures_aggregates(ticker=..., resolution="day", window_start_gte=..., window_start_lte=...)` | `GET /futures/v1/aggs/{ticker}` |
| Futures products | `client.list_futures_products(...)` | `GET /futures/v1/products` |
| Futures snapshot | `client.get_futures_snapshot(...)` | `GET /futures/v1/snapshot` |
| Options contracts | `client.list_options_contracts(underlying_ticker=..., expired=...)` | `GET /v3/reference/options/contracts` |
| Options chain snapshot | `client.list_snapshot_options_chain(underlying, params={...})` | `GET /v3/snapshot/options/{underlying}` |
| Options/equity daily aggs | `client.list_aggs("O:...", 1, "day", from_, to)` | `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}` |

`O:`-prefixed option tickers follow the OSI format:
`O:<UNDERLYING><YYMMDD><C/P><strike*1000, zero-padded to 8 digits>`, e.g.
`O:SPY251219C00650000`.

## Using in research / marimo

```python
import pandas as pd, pathlib, zipfile

root = pathlib.Path("../massive/lean-data")

# Futures daily bars
with zipfile.ZipFile(root / "future/cme/daily/esz24_trade.zip") as z:
    df = pd.read_csv(z.open(z.namelist()[0]), header=None,
                     names=["datetime", "open", "high", "low", "close", "volume"],
                     parse_dates=["datetime"])

# Options chain snapshot history (one file per day pulled)
chains = pd.concat(
    pd.read_csv(p) for p in (root / "alternative/massive/options/chains").glob("spy_*.csv")
)

# Per-contract option daily aggregates
aggs = pd.read_csv(root / "alternative/massive/options/aggregates/SPY251219C00650000.csv",
                    parse_dates=["date"])
```

## Known limitations / things to verify once a key is available

- **`list_futures_aggregates(resolution=...)`** — `"day"` is a best-effort
  guess by analogy with the stocks/options `timespan` argument. If it
  400s, check https://massive.com/docs/rest/futures/aggregates for the
  correct value (possibly `"session"`, `"1d"`, or a separate
  `multiplier`+`timespan` pair).
- **Futures daily LEAN format is unverified end-to-end** — written per the
  documented `Lean/Data/future/readme.md` convention but not loaded into a
  running LEAN engine. Confirm `<market>` folder names and whether LEAN
  expects per-contract or continuous-symbol files for the futures
  `AddFuture`/`AddFutureContract` APIs you intend to use.
- **Options native LEAN format not implemented** — only the alternative-data
  layer (`alternative/massive/options/...`) is written. If you need native
  `option/usa/daily` zips for `AddOption`/`AddOptionContract`, implement the
  per-contract deci-cent-strike file naming from
  `Lean/Data/option/readme.md` as a follow-up.
- **No retry/backoff wrapper yet** — crypto/polymarket pipelines use
  `tenacity` for exponential backoff; add similar wrapping to
  `MassiveClient` once real rate-limit behavior is observed.
- **Options chain snapshot is "now", not historical** — `snapshot_date` is
  always the date the pipeline ran. To build a historical panel, run the
  pipeline daily (e.g. via cron) rather than expecting a single backfill.
- **Pagination is fully materialized** (`iter_to_list`) — fine for the
  small default universe (5 futures roots, 2 options underlyings × a few
  expirations), but large pulls (many strikes/expirations or long futures
  history) may need a streaming/chunked rewrite.
