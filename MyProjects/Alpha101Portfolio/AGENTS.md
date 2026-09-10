# Alpha101Portfolio - Agent Instructions

This file defines project-specific instructions for AI agents working on this strategy.

For workspace-level guidelines, see the root `AGENTS.md`.

## Project Summary

- **Strategy**: Daily-rebalanced, dollar-neutral long/short on a formulaic-alpha
  score across the point-in-time largest 300 US companies. Long the top quintile
  by score, short the bottom quintile, equal-weighted, 100% total gross exposure.
- **Where the model lives**: `infrastructure/marimo/notebooks/alpha101_portfolio.py`
  — all 101 alpha expressions from Kakushadze (2016), an automated formula
  verification/diagnostic cell, sector neutralisation via the paper's
  `indneutralize` operator (at whatever GICS level each expression specifies,
  plus a blanket sector-level pass on every alpha), signal-decay analysis,
  selection by training significance, ridge score, quintile book, and the
  export of `data/alpha_scores.csv`. This project only *executes* those scores.
- **Current state**: implemented and evaluated on the held-out window
  (2021-01-01 – 2024-12-31), using the full 101-alpha model (90 significant, 2
  flagged and excluded as degenerate). Held-out daily information coefficient
  0.0128 (t = 3.86, positive in all 4 test years); gross Sharpe 1.50. Read
  `docs/strategy.md` before proposing changes.
- **Architecture**: Atomic Structure (Composition Root → Organisms → Molecules →
  Atoms), teaching pattern — direct `SetHoldings` calls from a scheduled
  `_rebalance` method.
- **Entry Point**: `main.py` (`Alpha101PortfolioAlgorithm`)

## Architecture

```
main.py              # Composition Root - subscribes the score file's tickers, daily rebalance
├── models/          # Organisms
│   ├── alpha.py     # FormulaicAlphaSignal - newest point-in-time score batch; `tickers` = universe
│   ├── portfolio.py # HysteresisQuintilePortfolio - dollar-neutral L/S with a turnover hold band
│   ├── execution.py # MarketOrderExecutor - SetHoldings on active names
│   └── logger.py    # PortfolioLogger - ObjectStore logging
├── domain/          # Molecules + Atoms
│   ├── config.py    # Dates, LONG_SHORT_FRACTION, GROSS_EXPOSURE, COST_BPS_PER_SIDE, MAX_SCORE_AGE_DAYS
│   ├── models.py    # DTOs, enums (ATOMS)
│   └── signals/
│       └── cross_sectional_rank.py  # SYMLINK → ../../../shared/signals/cross_sectional_rank.py
└── data/
    └── alpha_scores.csv             # date,ticker,score — notebook export (committed)
```

## Strategy Invariants

These rules must NOT change without explicit approval:

1. Dollar-neutral: long gross == short gross == 50%.
2. Scores are read point-in-time only (newest batch with `date <= today`, flat if older than `MAX_SCORE_AGE_DAYS`).
3. No HTTP calls at runtime — `data/alpha_scores.csv` is a bundled snapshot and defines the universe.
4. The score file comes from the notebook's frozen train + validate fit (2005–2020). Regenerating it must not involve refitting on 2021–2024.
5. **Entry-threshold** ranking math stays in `MyProjects/shared/signals/cross_sectional_rank.py` (shared, stateless — other projects use it as-is). The turnover **hold band** is project-local state in `models/portfolio.py::HysteresisQuintilePortfolio` and must not be pushed into the shared atom.
6. **Sector labels must be point-in-time.** Use the GICS history table (`broad_sector_map.csv`, joined as-of the date), never the current-classification snapshot in `sector_map.csv`.
7. **New or edited alpha formulas must pass the coverage/variation diagnostic** in the notebook before being trusted.
8. `HOLD_FRACTION` is fixed by the notebook's validation-window design and applied unchanged to the frozen 2021–2024 test window; do not retune it against the test window.
9. **The risk-free rate file must stay populated.** `infrastructure/pipelines/wrds/lean-data/alternative/interest-rate/usa/interest-rate.csv` needs a real rate series (WRDS Fama-French daily `rf`, annualized) for correct Sharpe/Sortino statistics.

## ObjectStore Keys

- `alpha101_portfolio/daily_snapshots.csv`
- `alpha101_portfolio/positions.csv`
- `alpha101_portfolio/trades.csv`

## Development Workflow

```bash
cd <Q-agent workspace root>
source venv/bin/activate
cd MyProjects
bash ../scripts/lean-backtest.sh "Alpha101Portfolio"   # wrapper mounts MyProjects/shared/
```

Data prerequisite: the broad WRDS pipeline must have been run on this machine.
The backtest issues ~125,000 orders (with hysteresis; ~135,000 under the plain
quintile rule) and takes roughly ten minutes.

## Validation

```bash
cd MyProjects/Alpha101Portfolio
python -m py_compile main.py models/*.py domain/*.py
python ../shared/signals/cross_sectional_rank.py
cd ../.. && bash scripts/lean-backtest.sh "Alpha101Portfolio"
```

Research side: `cd infrastructure/marimo && MPLBACKEND=Agg ./venv/bin/python
notebooks/alpha101_portfolio.py` (exit 0 = every cell ran; a few minutes).

## Scope Guidance

- **Safe**: Changes within a single layer that don't affect trading behaviour
- **Ask First**: Strategy parameter changes (universe rule, gross exposure,
  quintile fraction, rebalance frequency, cost assumption), ObjectStore schema
  changes, editing the shared signal (other projects use it — grep first)
- **Prohibited**: Refitting the model on the held-out backtest window, adding
  runtime HTTP calls, quoting a performance number without its cost assumption

## Alpha Coverage

The notebook implements all 101 expressions; 90 are used after training
significance filtering. True intraday VWAP is unavailable, so it consistently
uses typical price `(high + low + close) / 3`; disclose this proxy with
results. Formula-level neutralisation uses point-in-time sector, industry, or
sub-industry labels as requested by each expression. `data/alpha_scores.csv` is
the 101-alpha (90-used) export and the current execution artifact.

Two formulas are flagged degenerate by the coverage/variation diagnostic and
excluded regardless of significance.

## Layer Rules

| Layer | Can Import From |
|-------|------------------|
| `domain/` (excl. `signals/`) | Python stdlib only |
| `domain/signals/` | stdlib, pandas, numpy — no `AlgorithmImports` |
| `models/` | `domain/`, `AlgorithmImports` |
| `main.py` | All layers |

## Git Note

Tracked directly in the outer Q-agent workspace repo on the current branch
(`!MyProjects/Alpha101Portfolio/` negation in the root `.gitignore`); do not
`git init` inside this directory.
