# Data Pipelines

Durable notes on data sources that feed this workspace. All pipelines live under `infrastructure/pipelines/<source>/` and write outputs into `infrastructure/pipelines/<source>/lean-data/` (LEAN format) or `MyProjects/data/<source>/` (plain CSV). EDGAR is the exception — it writes plain CSVs to `MyProjects/data/edgar/`.

Do not store usernames, passwords, DSNs, tokens, or private credentials here.

## Layout convention

```
infrastructure/
├── pipelines/
│   ├── wrds/                    # WRDS/CRSP pipeline (own venv)
│   ├── edgar/                   # SEC EDGAR fundamentals via edgartools
│   ├── crypto/                  # Crypto OHLCV → pipelines/crypto/lean-data/
│   ├── polymarket/              # Polymarket markets + prices → pipelines/polymarket/lean-data/
│   ├── yfinance/                # Yahoo Finance OHLCV → pipelines/yfinance/lean-data/
│   ├── openbb/                  # OpenBB Platform (interactive, no batch pipeline yet)
│   ├── treasury_gov_rates/      # Treasury.gov daily par yield curve
│   ├── macro_rates/             # FRED / SOFR / Fed Funds (planned)
│   ├── fixed_income/            # Treasury auctions, CFTC positioning (planned)
│   └── news_events_sentiment/   # GDELT, Reddit, SEC NLP (planned)
├── marimo/                      # Marimo notebook server (shared tool)
├── notebooks/                   # Cross-pipeline research notebooks
├── setup.sh                     # Shared venv bootstrap
└── requirements.txt
```

`MyProjects/` is for algorithm code and research only — no infrastructure lives there.

## WRDS / CRSP

- Location: `infrastructure/pipelines/wrds/`
- Activate: `cd ~/Documents/Q-agent/infrastructure/pipelines/wrds && source venv/bin/activate`
- LEAN data folder (set in `MyProjects/lean.json`): `infrastructure/pipelines/wrds/lean-data/`
- Universe: 30-stock equity universe + SPY + SGOV, daily, 1998-present (CRSP)
- Additional entitlements (institution-dependent): OptionMetrics, IBES, TAQ. Check your WRDS subscription for available schemas.
- `contrib.global_factor`: US equity factor table (monthly). Filter `cty = 'USA'`. Key columns: `datadate, permno, gvkey, mom1m, mom6m, mom12m, si, dolvol, beta, roe, gpa, acc`. Available via WRDS credentials.
- Extractors: `src/wrds_lean/{fundamentals,sectors,ibes,etf_constituents}.py`

## EDGAR (edgartools)

- Location: `infrastructure/pipelines/edgar/pipeline.py`
- Run: `python infrastructure/pipelines/edgar/pipeline.py [--quarterly] [--tickers ...]`
- Output: `MyProjects/data/edgar/fundamentals_annual.csv` (+ `_quarterly.csv`)
- Wide schema: ticker, period, Revenue, GrossProfit, OperatingIncomeLoss, NetIncome, Assets, Liabilities, AllEquityBalance, LongTermDebt, CashAndMarketableSecurities, NetCashFromOperatingActivities, CapitalExpenses, SharesFullyDilutedAverage
- Must call `edgar.set_identity("Name email@example.com")` before any requests (hard-coded in pipeline.py).
- 10-K balance sheets only report 2 years (vs 3 for income/CF) — NaN in oldest year is expected.
- Balance sheet columns are plain dates (`2025-09-27`), income/CF are tagged (`2025-09-27 (FY)`). Extractor handles both.
- **WBA**: went private in 2024, edgartools cannot find it by ticker — skip it.
- **Look-ahead bias**: `period` is fiscal year-end, not filing date. Account for ~60–90 day reporting lag in backtests. Use WRDS Compustat `pdate` if point-in-time accuracy is needed.

## Crypto

- Location: `infrastructure/pipelines/crypto/`
- Run: `python infrastructure/pipelines/crypto/scripts/run_pipeline.py --exchange coinbase|kraken`
- **Binance geo-blocked in the US (HTTP 451)** — do not include in US pipelines
- Coinbase (coinbasepro): BTC/ETH back to 2013 (3422+ bars); no SOL
- Kraken: BTC/ETH/SOL all quote currencies, ~721 daily bars
- Output: `infrastructure/pipelines/crypto/lean-data/crypto/<market>/daily/<symbol>.zip` (LEAN format)

## Polymarket

- Location: `infrastructure/pipelines/polymarket/`
- Markets:
  - **Tag filter broken (May 2026)** — `events[].tags` empty, `DEFAULT_TAG_FILTER` matches nothing; `search=` param also broken (returns trending, ignores keywords)
  - **Fed/macro markets**: `python infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py --snapshot`
    - Gamma offset pagination, client-side keyword filter on `question` text; 62 active markets as of May 2026
    - Uses `volumeNum` / `liquidityNum` (numeric) — not `volume` / `liquidity` which are strings and may be `"0"`
    - **Gamma API caps offset at ~10,100** — returns HTTP 422 beyond that; script handles it with a clean break
    - Covers only recent/active markets (~10k); pre-2024 resolved markets may not appear
  - **Crypto markets**: `python infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py`
  - Output: `infrastructure/pipelines/polymarket/lean-data/alternative/polymarket/markets.csv`
- Prices: `python infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py --fidelity 1440 --skip-existing`
  - `--skip-existing` makes it resumable; `--fidelity 1440` required for resolved markets
  - Pre-2023 resolved markets return flat post-resolution prices — no historical series available
  - Output: `infrastructure/pipelines/polymarket/lean-data/alternative/polymarket/prices/<slug>.csv`

### Example research notebooks
- Election & industry returns: `infrastructure/marimo/notebooks/election_industry_returns.py` (marimo)

### Correct pipeline sequencing for new research
1. Probe API with one raw request — inspect actual field names before building anything
2. Verify exchange accessibility (test Binance; use Coinbase + Kraken for US)
3. Pull exchange OHLCV first (parallel background tasks)
4. Paginate + keyword-filter Polymarket → write stable `markets.csv`; verify row count + YesTokenId
5. Run prices pipeline with `--skip-existing` (resumable)
6. Build notebook only after all data files are stable

## yfinance (yfinance_lean)

- Location: `infrastructure/pipelines/yfinance/`
- Activate: `cd ~/Documents/Q-agent/infrastructure && source .venv/bin/activate`
- Run: `python infrastructure/pipelines/yfinance/scripts/run_pipeline.py --tickers AAPL MSFT SPY`
- Modules: `download.py` (unadjusted OHLCV + actions), `transform.py` (LEAN format + factor files), `publish.py` (writes zips/CSVs)
- Output: `infrastructure/pipelines/yfinance/lean-data/equity/usa/{daily,factor_files,map_files}/` (LEAN format, prices ×10,000)
- Point `lean.json` at `infrastructure/pipelines/yfinance/lean-data` for local backtests
- Coverage: any Yahoo Finance ticker, daily, from 1990-01-01; unadjusted prices with proper split + dividend factor files
- Exchange mapping: NMS/NGM/NCM → Q, NYQ → N, NYSEArca/PCX → P, ASE → A (falls back to Q)
- Part of shared infra venv (`infrastructure/.venv`); added to `requirements.txt` + `setup.sh`

## OpenBB

- Package: `openbb` (workspace venv).
- No batch pipeline — used interactively from notebooks: `from openbb import obb`.
- Useful for: yfinance prices, FRED macro, SEC filings, multi-provider equity data.
- Provider API keys go in `~/.openbb_platform/user_settings.json` (gitignored), never committed.
