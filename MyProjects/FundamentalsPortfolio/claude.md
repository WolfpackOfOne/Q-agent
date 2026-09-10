# FundamentalsPortfolio - Fundamental-score long/short, broad universe

## Repository

Tracked **directly in the outer Q-agent workspace repository** on the
current branch — intentionally not a standalone nested repo (a
`!MyProjects/FundamentalsPortfolio/` negation in the root `.gitignore`
makes it visible). No `git init`, no `origin`, no separate history.

## Project Overview

Quarterly-rebalanced, dollar-neutral long/short equity strategy on the
point-in-time largest 1,000 US companies by market cap. Each stock is
scored by a gradient-boosted trees model on 8 cross-sectionally ranked
quarterly financial-statement features (Compustat via WRDS, linked to
CRSP), selected for a statistically significant training-period
correlation with returns. Every calendar quarter, long the top decile of
scored names and short the bottom decile, equal-weighted within each
side, 100% total gross exposure (50% long / 50% short).

**Division of labour**: the research notebook
`infrastructure/marimo/notebooks/fundamentals_portfolio.py` owns the
data pipeline, cleaning, feature engineering, model fitting, and the
export of `data/fundamental_scores.csv` (test-window scores only, model
fit on 2005–2021). This project owns execution: subscribe to the tickers
in that file, read the newest point-in-time score batch each quarter,
build the decile book via the shared signal, trade it.

**Result**: test IC 0.078 (t = 4.0, positive in 7 of 7 quarters); notebook
Sharpe 1.53 at 3.0% vol, +8.2% over 2022–2023, max drawdown −0.7%. LEAN:
+8.7% net (4.3%/yr, vol 3.6%, max drawdown −3.5%), Sharpe 0.55 after its
risk-free adjustment (≈ 1.2 raw). See `docs/strategy.md` § "Results".

## Project Structure

```
FundamentalsPortfolio/
├── main.py                  # Composition root (QCAlgorithm) — FundamentalsPortfolioAlgorithm
├── models/                  # Organisms (plain classes, teaching pattern)
│   ├── alpha.py             # FundamentalRankAlpha — newest point-in-time score batch; tickers = the universe
│   ├── portfolio.py         # FundamentalRankPortfolio — decile dollar-neutral L/S via shared signal
│   ├── execution.py         # MarketOrderExecutor — SetHoldings; skips tickers with no price bar
│   └── logger.py            # PortfolioLogger — ObjectStore logging
├── domain/                  # Molecules + Atoms
│   ├── config.py            # Dates, REBALANCE_MONTHS, LONG_SHORT_FRACTION, GROSS_EXPOSURE, MAX_SCORE_AGE_DAYS
│   ├── models.py            # DTOs, enums
│   └── signals/
│       └── cross_sectional_rank.py   # SYMLINK → ../../../shared/signals/cross_sectional_rank.py
├── data/
│   └── fundamental_scores.csv        # date,ticker,score — notebook export (committed)
├── docs/                    # architecture.md, strategy.md (results), objectstore.md
├── research/                # Marimo research notebooks (.py, not .ipynb)
└── claude.md                # This file
```

**Pattern choice**: teaching pattern — `models/{alpha,portfolio,execution}.py`
are plain Python classes called directly from `main.py::_rebalance`, not
QC `AlphaModel` / `PortfolioConstructionModel` framework subclasses.

## Strategy Parameters

| Parameter | Value | Where |
|-----------|-------|-------|
| Universe | Every ticker in `data/fundamental_scores.csv` (1,081 in the test window) | `models/alpha.py::tickers`, `main.py::Initialize` |
| Rebalance | First trading day of Jan / Apr / Jul / Oct | `REBALANCE_MONTHS`, `main.py::Initialize` |
| Signal | Newest score batch with `date <= today`; flat if older than 100 days | `models/alpha.py`, `MAX_SCORE_AGE_DAYS` |
| Portfolio | Long top decile / short bottom decile, equal-weighted, 100% gross | `LONG_SHORT_FRACTION = 0.1`, `GROSS_EXPOSURE`, shared signal |
| Thin cross-section | < 100 scored names → flat | `MIN_SCORED_NAMES` |
| Brokerage | Interactive Brokers, Margin, default commissions | `main.py::Initialize` |

## Data Sources

| Data | Path | Status |
|------|------|--------|
| Daily equity prices (2,754 tickers + SPY) | `infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip` | Local, gitignored — regenerate with `scripts/run_broad_quarterly_pipeline.py` (~15 min); `MyProjects/lean.json` data-folder already points at `lean-data` |
| Fundamental scores | `data/fundamental_scores.csv` | Committed — regenerate via the notebook's export switch |
| Broad fundamentals / universe / TRI (research) | `lean-data/alternative/fundamentals/broad_*.csv` | Pipeline output (gitignored) |

Tickers are the pipeline's tradable ticker names: the latest CRSP ticker,
with the PERMNO appended when two companies share one. Research keys on
PERMNO and translates through `broad_permno_map.csv`.

## LEAN CLI Commands

```bash
cd <Q-agent workspace root>
source venv/bin/activate
cd MyProjects

# Local backtest — MUST use the wrapper (mounts MyProjects/shared/ for the signals symlink)
bash ../scripts/lean-backtest.sh "FundamentalsPortfolio"

# Local research
lean research "FundamentalsPortfolio"
```

`config.json` is created on first `lean cloud push`; not needed locally.

## ObjectStore Data

| File | Description |
|------|--------------|
| `fundamentals_portfolio/daily_snapshots.csv` | Per-rebalance NAV, gross exposure, n_long/n_short |
| `fundamentals_portfolio/positions.csv` | Per-position quantity/price/target weight at each rebalance |
| `fundamentals_portfolio/trades.csv` | Fill log from `OnOrderEvent` |

Full schemas: `docs/objectstore.md`.

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | 2022-01-01 |
| End Date | 2023-12-31 |
| Starting Cash | $1,000,000 |
| Benchmark | SPY |
| Brokerage Model | Interactive Brokers, Margin (`AccountType.Margin` — strategy shorts) |

The first rebalance with scores is 2022-04-01; the strategy is in cash
before that.

## Git Version Control

Tracked in the outer `Q-agent` repo — standard workflow applies (branch →
commit → push branch → PR; see root `CLAUDE.md`). `config.json`,
`backtests/`, and `__pycache__/` are ignored by the project `.gitignore`;
`data/*.csv` is committable (bundled-data convention).

## Common Issues

### `No module named 'domain.signals.cross_sectional_rank'` in local backtest

Use the wrapper, not plain `lean backtest`.

### `could not subscribe <ticker>` lines in the log

A ticker in the score file with no local zip — rerun the broad pipeline;
the algorithm drops it from the universe and continues.

### Flat until April 2022

Expected — the first score batch is dated 2022-03-31.
