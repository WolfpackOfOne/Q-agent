# NewsSentimentAlpha - News-tone long/short equity strategy

## Repository

- **GitHub URL:** (none — local-only standalone repo, no remote added)
- **Default Branch:** main

## Project Overview

Daily long/short portfolio ranked by a financial-media news-tone z-score
signal per stock (GDELT), rebalanced daily. A selective top/bottom slice
of the 10-stock universe (at least `N_FLOOR` names per side), weighted by
signal magnitude, 100% total gross exposure.

**Result**: `MIN_NAMES=7, SELECT_FRAC=0.5, N_FLOOR=2` (current code) was
selected via a train (2017-18) / validate (2019) / test (2020-21) split
— see `docs/strategy.md` § "Validation Methodology". The backtest window
is the held-out test period, trimmed to 2020-01-01 – 2021-04-30 (GDELT
coverage of this universe collapses through 2021; the strategy places
zero trades past 2021-04-30 either way — same trades, same
`OrderListHash`, so the trim only removes a flat tail from the elapsed-
time-based metrics, it's not a performance-driven choice). Produces
**Sharpe 0.907** on a real LEAN backtest with zero commissions. Read that
section before retuning `MIN_NAMES`/`N_FLOOR` — they should be
re-selected with a fresh held-out split, not fit against this window
directly.

## Project Structure

```
NewsSentimentAlpha/
├── main.py                  # Composition root (QCAlgorithm), daily scheduled rebalance,
│                             # one-trading-day signal lag (stateful, see AGENTS.md)
├── models/                  # Organisms (orchestrators)
│   ├── alpha.py             # NewsToneAlpha — exact-date tone-z lookup, no ffill
│   ├── portfolio.py         # NewsToneLongShortPortfolio — delegates ranking to shared signal
│   ├── execution.py         # MarketOrderExecutor — SetHoldings per target weight
│   └── logger.py            # ObjectStore logging
├── domain/                  # Molecules + Atoms
│   ├── config.py            # Universe, dates, cash, MIN_NAMES, ObjectStore namespace, SENTIMENT_PANEL_CSV path
│   ├── models.py            # DTOs, enums
│   └── signals/
│       └── news_tone.py     # SYMLINK → ../../../shared/signals/news_tone.py
├── data/                    # Bundled per-project CSV — sentiment_panel.csv (committed)
├── tools/
│   └── refresh_sentiment.py # Regenerate the bundled CSV from the pipeline's output
├── docs/                    # Documentation
│   ├── architecture.md      # System architecture
│   ├── strategy.md          # Strategy logic, signal timing, validation methodology
│   └── objectstore.md       # Data schemas
├── research/                # Marimo notebooks (empty for now — .py, not .ipynb)
├── Manually_Backtested_Results/  # Drop QC-website backtest downloads here for qc-backtest-analyzer
├── config.json               # QC cloud config (DO NOT COMMIT, not required for local dev)
└── claude.md                 # This file
```

**Pattern**: direct `SetHoldings` from a scheduled `_rebalance` method (teaching
pattern), not the QC `AlphaModel`/`PortfolioConstructionModel` framework
lifecycle. See `AGENTS.md` § "Pattern Choice" and
`MyProjects/ElectionIndustryBeta/` as the worked example this mirrors.

## Data Sources

| Source | Local path | Status |
|--------|-----------|--------|
| WRDS/CRSP daily equity prices | `infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip` | Ready — used by `AddEquity` calls |
| GDELT financial-media news-tone z-score panel | `data/sentiment_panel.csv` (this project) | Bundled — regenerate via `tools/refresh_sentiment.py` |

## Strategy Parameters

| Parameter | Value | Description |
|-----------|-------|--------------|
| Universe | GS, AAPL, JPM, BA, HD, IBM, VZ, V, NKE, CSCO | Static 10-stock list, `domain/config.py::UNIVERSE` |
| Rebalance | Daily, market open + 5 min | `main.py::Initialize` Schedule.On |
| Signal | Exact-date tone-z, 1-trading-day lag | `models/alpha.py::NewsToneAlpha.record()/eligible_signals()`, `SIGNAL_MAX_STALE_DAYS=0` |
| Portfolio | Magnitude-weighted top/bottom slice, diversification floor, 100% gross | `domain/signals/news_tone.py::rank_magnitude_weighted_targets` |
| MIN_NAMES | 7 | Below this, flat for the day — selected via validate split |
| SELECT_FRAC | 0.5 | Fraction of scored names to trade (N_FLOOR usually dominates) |
| N_FLOOR | 2 | Minimum names per side — selected via validate split, see docs/strategy.md |
| REBALANCE_THRESHOLD | 0.04 | Skip re-issuing SetHoldings for sub-threshold weight drift |
| Commission | $0 (`ConstantFeeModel(0)`) | Modern zero-commission US retail brokerage assumption |

## LEAN CLI Commands

### Setup (Run Once Per Terminal Session)

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
```

### Local Backtest — use the shared-signal-aware wrapper

```bash
bash ~/Documents/Q-agent/scripts/lean-backtest.sh "NewsSentimentAlpha"
```

Plain `lean backtest "NewsSentimentAlpha"` fails with `No module named
'domain.signals.news_tone'` — the wrapper mounts `MyProjects/shared/` so
the symlink at `domain/signals/news_tone.py` resolves inside Docker.

`MyProjects/lean.json` `data-folder` is set to
`../infrastructure/pipelines/wrds/lean-data`, which already has zip/factor/map
files for all 10 universe tickers plus SPY.

### Local Research

```bash
lean research "NewsSentimentAlpha"
```

### Cloud (optional — not required for local development)

```bash
lean cloud push --project "NewsSentimentAlpha"
lean cloud backtest "NewsSentimentAlpha" --name "Description"
lean cloud pull --project "NewsSentimentAlpha"
```

`config.json` is created automatically on first `lean cloud push` — it does
not need to exist for local backtest/research.

## ObjectStore Data

### Files Created

| File | Description |
|------|-------------|
| `news_sentiment_alpha/daily_snapshots.csv` | Daily portfolio metrics |
| `news_sentiment_alpha/positions.csv` | Position-level data |
| `news_sentiment_alpha/trades.csv` | Trade executions |

See `docs/objectstore.md` for full schema documentation.

### Reading in Research Notebook

```python
from io import StringIO
import pandas as pd

snapshots_str = qb.ObjectStore.Read("news_sentiment_alpha/daily_snapshots.csv")
df = pd.read_csv(StringIO(snapshots_str), parse_dates=['date'])
```

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | 2020-01-01 |
| End Date | 2021-04-30 |
| Starting Cash | $100,000 |
| Benchmark | SPY |
| Brokerage | Interactive Brokers, Margin account, $0 commission (`ConstantFeeModel(0)`) |

This is the held-out test window from the train/validate/test
methodology in `docs/strategy.md`, trimmed from the full 2020-2021 test
block to exclude a trade-free tail after GDELT coverage collapsed. The
bundled sentiment panel covers
2017-2021, wider than this window, so the same data also supports
train/validate backtests if the window is changed for research.

## Git Version Control

Standalone repo, initialized locally (`git init -b main`), no remote added.

### Files Tracked

- `main.py`, `models/*.py`, `domain/*.py`, `domain/signals/news_tone.py` (symlink — git stores the link)
- `tools/refresh_sentiment.py`, `data/*.csv` (bundled data)
- Documentation (`docs/`, `claude.md`, `README.md`, `AGENTS.md`)
- `.gitignore`

### Files NOT Tracked

- `config.json` (contains QC organization/cloud IDs, not created yet)
- `backtests/` (regeneratable)
- `__pycache__/`

## Common Issues

### "lean: command not found"

```bash
source ~/Documents/Q-agent/venv/bin/activate
```

### "No module named 'domain.signals.news_tone'" in a local backtest

Use `bash scripts/lean-backtest.sh "NewsSentimentAlpha"`, not plain `lean backtest` — see "Local Backtest" above.

### "lean.json not found" / no data locally

`MyProjects/lean.json` already points at the WRDS lean-data folder for this
workspace. If it's missing entirely: `cd MyProjects && lean init`, then set
`data-folder` to `../infrastructure/pipelines/wrds/lean-data`.
