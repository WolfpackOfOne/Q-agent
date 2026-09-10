# Alpha101Portfolio - Formulaic-alpha long/short

## Repository

Tracked **directly in the outer Q-agent workspace repository** on the current
branch — intentionally not a standalone nested repo (a
`!MyProjects/Alpha101Portfolio/` negation in the root `.gitignore` makes it
visible). No `git init`, no `origin`, no separate history.

## Project Overview

Daily-rebalanced, dollar-neutral long/short equity strategy on the point-in-time
largest 300 US companies by market cap. The research notebook implements all
101 formulaic alpha expressions from Zura Kakushadze, *101 Formulaic Alphas*
(arXiv:1601.00991), and the committed execution scores now come from that full
model (90 of 101 alphas pass a training-significance filter; 2 are flagged and
excluded as degenerate by an automated coverage diagnostic). Every alpha is
demeaned within its GICS sector before ranking — the paper's `indneutralize`
operator — using point-in-time sector history, plus formula-level
`indneutralize` at industry or sub-industry level where the paper specifies it.
Every session, long the top quintile of scored names and short the bottom
quintile, equal-weighted within each side, 100% total gross exposure.

**Division of labour**: the research notebook
`infrastructure/marimo/notebooks/alpha101_portfolio.py` owns the alpha
implementations, formula verification, the signal-decay analysis, alpha
selection, model fitting and the export of `data/alpha_scores.csv` (test-window
scores only, model fit on 2005–2020). This project owns execution: subscribe to
the tickers in that file, read the newest point-in-time score batch each
session, build the quintile book via the shared signal, trade it.

**Result**: held-out daily information coefficient 0.0128 (t = 3.86) on
2021–2024, positive in every test year, and a gross Sharpe of 1.50. See
`docs/strategy.md` for the full methodology and results.

## Project Structure

```
Alpha101Portfolio/
├── main.py                  # Composition root (QCAlgorithm) — Alpha101PortfolioAlgorithm
├── models/                  # Organisms (plain classes, teaching pattern)
│   ├── alpha.py             # FormulaicAlphaSignal — score batch + the universe
│   ├── portfolio.py         # HysteresisQuintilePortfolio — dollar-neutral L/S with a turnover hold band
│   ├── execution.py         # MarketOrderExecutor — SetHoldings; skips tickers with no bar
│   └── logger.py            # PortfolioLogger — ObjectStore logging
├── domain/                  # Molecules + Atoms
│   ├── config.py            # Dates, LONG_SHORT_FRACTION, GROSS_EXPOSURE, COST_BPS_PER_SIDE
│   ├── models.py            # DTOs, enums
│   └── signals/
│       └── cross_sectional_rank.py   # SYMLINK → ../../../shared/signals/cross_sectional_rank.py
├── data/
│   └── alpha_scores.csv     # date,ticker,score — notebook export, 283k rows (committed)
├── docs/                    # architecture.md, strategy.md (results), objectstore.md
└── claude.md                # This file
```

**Pattern choice**: teaching pattern — `models/{alpha,portfolio,execution}.py`
are plain Python classes called directly from `main.py::_rebalance`, not QC
`AlphaModel` / `PortfolioConstructionModel` framework subclasses.

## Strategy Parameters

| Parameter | Value | Where |
|-----------|-------|-------|
| Universe | Every ticker in `data/alpha_scores.csv` (409 in the test window) | `models/alpha.py::tickers`, `main.py::Initialize` |
| Rebalance | Every trading session, 5 minutes after the open | `main.py::Initialize` |
| Signal | Newest score batch with `date <= today`; flat if older than 4 days | `models/alpha.py`, `MAX_SCORE_AGE_DAYS` |
| Portfolio | Long top quintile / short bottom quintile, equal-weighted, 100% gross; held names stay until rank exits a wider 30%-ile band (turnover hysteresis) | `LONG_SHORT_FRACTION = 0.2`, `HOLD_FRACTION = 0.3`, `GROSS_EXPOSURE` |
| Thin cross-section | < 50 scored names → flat | `MIN_SCORED_NAMES` |
| Transaction cost | 2 bps per side as slippage, commissions zeroed | `COST_BPS_PER_SIDE`, `main.py::_initialize_security` |
| Brokerage | Interactive Brokers, Margin | `main.py::Initialize` |

## Data Sources

| Data | Path | Status |
|------|------|--------|
| Daily OHLCV | `infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip` | Local, gitignored — regenerate with `scripts/run_broad_quarterly_pipeline.py` |
| Point-in-time universe | `lean-data/alternative/fundamentals/broad_universe.csv` | Local, gitignored |
| Point-in-time GICS sectors | `lean-data/alternative/sectors/broad_sector_map.csv` | Local, gitignored — `scripts/run_broad_sector_pipeline.py` |
| Alpha scores | `data/alpha_scores.csv` | Committed — regenerate via the notebook's export switch |

## LEAN CLI Commands

```bash
cd <Q-agent workspace root>
source venv/bin/activate
cd MyProjects

# Local backtest — MUST use the wrapper (mounts MyProjects/shared/ for the signals symlink)
bash ../scripts/lean-backtest.sh "Alpha101Portfolio"
```

Daily rebalancing over ~1,000 sessions produces ~125,000 orders with turnover
hysteresis (~135,000 under the plain quintile rule), so the backtest takes
roughly ten minutes.

## ObjectStore Data

| File | Description |
|------|--------------|
| `alpha101_portfolio/daily_snapshots.csv` | Per-rebalance NAV, gross exposure, n_long/n_short |
| `alpha101_portfolio/positions.csv` | Per-position quantity/price/target weight |
| `alpha101_portfolio/trades.csv` | Fill log from `OnOrderEvent` |

Full schemas: `docs/objectstore.md`.

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | 2021-01-01 |
| End Date | 2024-12-31 |
| Starting Cash | $1,000,000 |
| Benchmark | SPY |
| Brokerage Model | Interactive Brokers, Margin |

This window is the held-out test period, scored once.

## Git Version Control

Tracked in the outer `Q-agent` repo — standard workflow applies (branch → commit
→ push branch → PR). `config.json`, `backtests/` and `__pycache__/` are ignored
by the project `.gitignore`; `data/*.csv` is committable.

## Common Issues

### `No module named 'domain.signals.cross_sectional_rank'`

Use the wrapper, not plain `lean backtest`.

### The backtest is slow

Expected — daily rebalancing across ~110 positions for ~1,000 sessions is ~135,000
orders. This is inherent to the strategy's one-day holding period.
