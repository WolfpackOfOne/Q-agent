# FundamentalsPortfolio - Agent Instructions

This file defines project-specific instructions for AI agents working on this strategy.

For workspace-level guidelines, see the root `AGENTS.md`.

## Project Summary

- **Strategy**: Quarterly-rebalanced, dollar-neutral long/short on a
  fundamental score across the point-in-time largest 1,000 US companies.
  Long the top decile by score, short the bottom decile, equal-weighted
  within each side, 100% total gross exposure (50% long / 50% short).
- **Where the model lives**: `infrastructure/marimo/notebooks/fundamentals_portfolio.py`
  — broad-pipeline data (`infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py`),
  cleaning, feature admission (inputs > 5% missing excluded), feature
  selection by statistical significance, a gradient-boosted trees model,
  decile long/short construction, and the export of
  `data/fundamental_scores.csv`. This project only *executes* those
  scores.
- **Current state**: implemented and backtested on the held-out window
  (2022-01-01 – 2023-12-31). Test IC 0.078 (t = 4.0, positive in 7 of 7
  quarters); notebook Sharpe 1.53 at 3.0% vol. See `docs/strategy.md`.
- **Architecture**: Atomic Structure (Composition Root → Organisms →
  Molecules → Atoms), teaching pattern — direct `SetHoldings` calls from
  a scheduled `_rebalance` method, not the QC `AlphaModel` framework.
- **Entry Point**: `main.py` (`FundamentalsPortfolioAlgorithm`)

## Architecture

```
main.py              # Composition Root - subscribes the score file's tickers, quarterly scheduled rebalance
├── models/          # Organisms - domain orchestrators
│   ├── alpha.py     # FundamentalRankAlpha - newest point-in-time score batch; `tickers` = the universe
│   ├── portfolio.py # FundamentalRankPortfolio - decile dollar-neutral L/S via shared signal
│   ├── execution.py # MarketOrderExecutor - SetHoldings on active names; skips tickers with no price bar
│   └── logger.py    # PortfolioLogger - ObjectStore logging
├── domain/          # Molecules + Atoms - pure business logic
│   ├── config.py    # Dates, REBALANCE_MONTHS, LONG_SHORT_FRACTION, GROSS_EXPOSURE, MAX_SCORE_AGE_DAYS
│   ├── models.py    # DTOs, enums (ATOMS)
│   └── signals/
│       └── cross_sectional_rank.py  # SYMLINK → ../../../shared/signals/cross_sectional_rank.py
├── data/
│   └── fundamental_scores.csv       # date,ticker,score — exported by the notebook (committed)
└── research/        # Marimo research notebooks (.py, not .ipynb)
```

## Strategy Invariants

These rules must NOT change without explicit approval:

1. Dollar-neutral: long gross == short gross == 50% (100% total gross exposure).
2. Rebalance is quarterly only — first trading day of Jan/Apr/Jul/Oct, no intra-quarter trading.
3. Scores are read point-in-time only (newest batch with `date <= today`, flat if older than `MAX_SCORE_AGE_DAYS`).
4. No HTTP calls from the algorithm at runtime — `data/fundamental_scores.csv` is a bundled snapshot and defines the universe.
5. The score file is produced by the notebook's frozen train + validate fit (2005–2021); regenerating it must not involve refitting on 2022–2023.
6. Ranking/weighting math stays in the shared signal (`MyProjects/shared/signals/cross_sectional_rank.py`); the notebook's inline `target_weights` mirrors it — change both or neither.

## ObjectStore Keys

- `fundamentals_portfolio/daily_snapshots.csv`
- `fundamentals_portfolio/positions.csv`
- `fundamentals_portfolio/trades.csv`

## Development Workflow

```bash
cd <Q-agent workspace root>
source venv/bin/activate
cd MyProjects
bash ../scripts/lean-backtest.sh "FundamentalsPortfolio"   # wrapper mounts MyProjects/shared/
```

Data prerequisite: the broad WRDS pipeline must have been run on this
machine (`infrastructure/pipelines/wrds/lean-data/equity/usa/daily/` holds
~2,750 zips). No cloud push / `config.json` is required.

## Validation

```bash
cd MyProjects/FundamentalsPortfolio
python -m py_compile main.py models/*.py domain/*.py
python ../shared/signals/cross_sectional_rank.py
cd ../.. && bash scripts/lean-backtest.sh "FundamentalsPortfolio"
```

Research side: `cd infrastructure/marimo && MPLBACKEND=Agg
./venv/bin/python notebooks/fundamentals_portfolio.py` (exit 0 = every
cell ran).

## Scope Guidance

- **Safe**: Changes within a single layer that don't affect trading behavior
- **Ask First**: Cross-layer changes, strategy parameter changes (universe rule, gross exposure, decile fraction, rebalance schedule), ObjectStore schema changes, editing the shared signal (grep the workspace first)
- **Prohibited**: Changes to `config.json` (if later added), violating layer dependencies, refitting the model on the held-out backtest window, adding runtime HTTP calls to the algorithm

## Layer Rules

| Layer | Can Import From |
|-------|------------------|
| `domain/` (excl. `signals/`) | Python stdlib only |
| `domain/signals/` | Python stdlib, pandas, numpy, scipy — no `AlgorithmImports` (shared-atom rule) |
| `models/` | `domain/`, `AlgorithmImports` |
| `main.py` | All layers |

## Git Note

Tracked directly in the outer Q-agent workspace repo on the current branch
(`!MyProjects/FundamentalsPortfolio/` negation in the root `.gitignore`);
do not `git init` inside this directory.
