# ElectionIndustryBeta — long/short industry rotation on Polymarket election odds

## Repository

- **GitHub URL:** (to be set on first `git remote add`)
- **Default Branch:** main

## Project Overview

Replication-flavoured example strategy for the Q-agent workspace. Each US sector or industry ETF has a measurable sensitivity (β) to daily changes in Polymarket's Trump win probability — the marimo notebook `infrastructure/marimo/notebooks/election_industry_returns.py` documents the regression. This project turns that β into a deployable QuantConnect algorithm:

- universe = 19 sector + industry ETFs (XLE, XLF, XLV, …, ICLN, TAN, GDX, ITB)
- each market day, compute a 60-day rolling β per ETF against ΔP(Trump)
- long the top-3 βs, short the bottom-3 βs, weights ∝ β, gross exposure 100%
- market orders via `SetHoldings`

The reusable β math lives in `MyProjects/shared/signals/election_beta.py` and is symlinked into this project. Polymarket history is shipped as `data/trump_prob.csv`, refreshed manually by `tools/refresh_trump_prob.py` — the algorithm itself makes no HTTP calls.

## Project Structure

```
ElectionIndustryBeta/
├── main.py                  # Composition root (QCAlgorithm)
├── models/
│   ├── alpha.py             # ElectionBetaAlpha
│   ├── portfolio.py         # ElectionBetaPortfolio
│   ├── execution.py         # MarketOrderExecutor
│   └── logger.py            # PortfolioLogger → ObjectStore
├── domain/
│   ├── config.py            # UNIVERSE, LOOKBACK, K, dates, namespace
│   ├── models.py            # DTOs, enums
│   └── signals/
│       └── election_beta.py # SYMLINK → ../../../shared/signals/election_beta.py
├── data/
│   └── trump_prob.csv       # Bundled Polymarket snapshot (committed)
├── tools/
│   └── refresh_trump_prob.py
├── docs/
│   ├── architecture.md
│   ├── strategy.md
│   └── objectstore.md
├── research/                # Jupyter notebooks for ObjectStore analysis
├── config.json              # QC cloud config (DO NOT COMMIT)
├── claude.md                # This file
├── AGENTS.md                # Project-specific agent rules
└── README.md
```

## Strategy Parameters

### Signal Generation

| Parameter | Value | Description |
|---|---|---|
| `LOOKBACK` | 60 | trading days used in the rolling β regression |
| Driver | `prob_trump` (Polymarket) | Daily YES-token probability; signal uses its first difference |

### Portfolio Construction

| Parameter | Value | Description |
|---|---|---|
| `K` | 3 | long top-K, short bottom-K |
| Weighting | ∝ β | each selected weight = β_i / Σ\|β_j\| over selected |
| Gross exposure | 1.0 | target |

### Execution

| Parameter | Value | Description |
|---|---|---|
| Order type | Market | via `SetHoldings` |
| Schedule | Daily, +5 min after SPY open | `Schedule.On(DateRules.EveryDay("SPY"), TimeRules.AfterMarketOpen("SPY", 5), …)` |

## LEAN CLI Commands

### Setup (once per terminal session)

```bash
cd /path/to/Q-agent
source venv/bin/activate
cd MyProjects
```

### Refresh Polymarket data (manual, when you want a fresher snapshot)

```bash
python ElectionIndustryBeta/tools/refresh_trump_prob.py
```

### Push + backtest

```bash
lean cloud push --project "ElectionIndustryBeta" --force
lean cloud backtest "ElectionIndustryBeta" --name "v1 baseline 60d K=3"
```

### Local backtest (Docker)

```bash
bash /path/to/Q-agent/scripts/lean-backtest.sh "ElectionIndustryBeta"
```

The wrapper appends an `--extra-docker-config` mount so the shared-signal symlink at `domain/signals/election_beta.py` resolves inside the container. Plain `lean backtest "ElectionIndustryBeta"` would fail with `No module named 'domain.signals.election_beta'`.

Local backtest also requires the workspace's `data/equity/usa/daily/` to contain real zip files for the 19 ETFs + SPY (not symlinks). The yfinance pipeline produces them:
```bash
cd /path/to/Q-agent/infrastructure/pipelines/yfinance
python scripts/run_pipeline.py --tickers XLE XLF XLV XLI XLK XLP XLY XLU XLB XLRE XLC XOP ITA KBE IBB ICLN TAN GDX ITB SPY --start 2023-12-01 --end 2024-11-15
cp lean-data/equity/usa/daily/*.zip /path/to/Q-agent/MyProjects/data/equity/usa/daily/
cp lean-data/equity/usa/factor_files/*.csv /path/to/Q-agent/MyProjects/data/equity/usa/factor_files/
cp lean-data/equity/usa/map_files/*.csv /path/to/Q-agent/MyProjects/data/equity/usa/map_files/
```

### Pull from cloud

```bash
lean cloud pull --project "ElectionIndustryBeta"
```

## ObjectStore Data

### Files Created

| Key | Description |
|---|---|
| `electionbeta/daily_snapshots.csv` | NAV, gross exposure, #long/#short, p_trump, Δp per rebalance |
| `electionbeta/positions.csv` | Per-position quantity / price / target weight at each rebalance |
| `electionbeta/trades.csv` | Fill log from `OnOrderEvent` |

Full schemas: `docs/objectstore.md`.

### Reading in a research notebook

```python
from io import StringIO
import pandas as pd

snapshots = pd.read_csv(StringIO(qb.ObjectStore.Read("electionbeta/daily_snapshots.csv")),
                        parse_dates=["date"])
positions = pd.read_csv(StringIO(qb.ObjectStore.Read("electionbeta/positions.csv")),
                        parse_dates=["date"])
trades    = pd.read_csv(StringIO(qb.ObjectStore.Read("electionbeta/trades.csv")),
                        parse_dates=["date"])
```

## Backtest Configuration

| Setting | Value |
|---|---|
| Start Date | 2024-03-15 |
| End Date | 2024-11-07 |
| Starting Cash | $100,000 |
| Benchmark | SPY |

## Git Version Control

### Tracked

- `main.py`, `models/*.py`, `domain/*.py`, `domain/signals/election_beta.py` (symlink — git stores the link)
- `tools/refresh_trump_prob.py`, `data/trump_prob.csv` (bundled snapshot)
- Documentation: `claude.md`, `AGENTS.md`, `README.md`, `docs/`
- `.gitignore`

### NOT tracked

- `config.json` (QC org/cloud IDs)
- `backtests/`, `__pycache__/`

## Common Issues

### "Cannot push — collaboration lock"

```bash
lean cloud push --project "ElectionIndustryBeta" --force
```

### `trump_prob.csv` not on disk

```bash
python ElectionIndustryBeta/tools/refresh_trump_prob.py
```

### Symlink shows as a normal file on QC cloud

That is the intended behaviour — `lean cloud push` follows symlinks and uploads the file *content*. QC never sees the link.
