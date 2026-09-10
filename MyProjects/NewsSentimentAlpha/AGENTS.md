# NewsSentimentAlpha - Agent Instructions

This file defines project-specific instructions for AI agents working on this strategy.

For workspace-level guidelines, see `~/Documents/Q-agent/AGENTS.md`.

## Project Summary

- **Strategy**: Daily long/short portfolio ranked by a financial-media
  news-tone z-score signal per stock (GDELT), magnitude-weighted (not
  equal-weighted) within a selective top/bottom slice with a
  diversification floor (`N_FLOOR`), 100% total gross exposure,
  rebalanced daily across a 10-stock universe (GS, AAPL, JPM, BA, HD,
  IBM, VZ, V, NKE, CSCO).
- **Current state**: Implemented and validated. Parameters
  (`MIN_NAMES=7, SELECT_FRAC=0.5, N_FLOOR=2` — current code) were
  selected via a train (2017-18) / validate (2019) / test (2020-21)
  split, documented in `docs/strategy.md` § "Validation Methodology".
  The backtest window (`domain/config.py::START_DATE/END_DATE`) is the
  held-out test period, trimmed to 2020-01-01 – 2021-04-30 (GDELT
  coverage of this universe collapses through 2021, and the strategy
  places zero trades past 2021-04-30 regardless of END_DATE — same
  `OrderListHash` either way, so the trim is a data-availability
  decision, not a performance-driven one). Produces **Sharpe 0.907** —
  real LEAN backtest, zero commissions. **Read that section before
  touching portfolio-construction parameters**: retuning `MIN_NAMES` or
  `N_FLOOR` against this window directly, without a fresh held-out
  split, would undermine the methodology that produced this result.
- **Architecture**: Atomic Structure (Composition Root → Organisms → Molecules → Atoms)
- **Entry Point**: `main.py` (`NewsSentimentAlphaAlgorithm`)

## Architecture

```
main.py              # Composition Root - wires models, scheduled daily rebalance,
                      # maintains the one-trading-day signal lag via NewsToneAlpha's staleness cache
├── models/           # Organisms - domain orchestrators
│   ├── alpha.py       # NewsToneAlpha — exact-date tone-z lookup, no ffill
│   ├── portfolio.py   # NewsToneLongShortPortfolio — delegates to shared ranking signal
│   ├── execution.py   # Order execution (SetHoldings)
│   └── logger.py      # ObjectStore logging
├── domain/            # Molecules + Atoms - pure business logic
│   ├── config.py       # Universe, dates, cash, MIN_NAMES, ObjectStore namespace, SENTIMENT_PANEL_CSV path
│   ├── models.py        # DTOs, enums (ATOMS)
│   └── signals/
│       └── news_tone.py  # SYMLINK → ../../../shared/signals/news_tone.py — pure ranking math
├── data/               # Bundled per-project CSV — sentiment_panel.csv
├── tools/
│   └── refresh_sentiment.py  # Regenerate the bundled CSV from the pipeline's output
└── research/           # Marimo notebooks (empty for now)
```

## Pattern Choice — Direct SetHoldings (teaching pattern)

This project uses the **teaching pattern**: `models/{alpha,portfolio,execution}.py`
are plain Python classes, not QC `AlphaModel`/`PortfolioConstructionModel`/
`ExecutionModel` subclasses. `main.py::_rebalance` (scheduled daily) trades
on `alpha.eligible_signals(SIGNAL_MAX_STALE_DAYS)` (state as of the prior call) → `portfolio.to_targets(...)`
→ `executor.execute(...)` → `SetHoldings(...)`, then captures today's own
reading for next time. This mirrors `MyProjects/ElectionIndustryBeta/`.

If this strategy later needs the full QC alpha-streaming/insight lifecycle
(e.g. to combine with other alpha models via `SetAlpha`), that's a deliberate
architecture change — ask before converting.

## Strategy Invariants

These rules must NOT change without explicit approval:

1. Universe is a static 10-stock list (GS, AAPL, JPM, BA, HD, IBM, VZ, V, NKE, CSCO) — no dynamic universe selection.
2. Rebalance is daily, scheduled at market open + 5 minutes — LEAN rejects every order for `Resolution.Daily` securities at any earlier intraday timestamp, since there's no tradable price yet before that day's bar closes.
3. Data sources are WRDS/CRSP daily equity prices (local) and the bundled GDELT news-tone CSV — no live API calls at runtime.
4. Signal lag is one *trading* day via stateful capture (`NewsToneAlpha.eligible_signals()` before `record()`), never calendar-day arithmetic (`date - timedelta(days=1)`) — a calendar lag silently mishandles Mondays/holidays.
5. Total gross exposure is 100% (50% long + 50% short) via `rank_magnitude_weighted_targets`'s normalization.
6. Portfolio construction is magnitude-weighted with an `N_FLOOR` diversification floor, not equal-weighted and not a bare fraction without a floor.
7. Commission model is `ConstantFeeModel(0)` — not IB's legacy per-share model.
8. `MIN_NAMES` and `N_FLOOR` were selected via the train/validate/test split in `docs/strategy.md` § "Validation Methodology" — retune only with a fresh held-out split, not by fitting against the current backtest window directly.

`SIGNAL_MAX_STALE_DAYS` (`0`), `SELECT_FRAC` (`0.5`), and
`REBALANCE_THRESHOLD` (`0.04`) are execution-mechanics defaults, not
part of the validated selection — reasonable as-is, but not as
rigorously justified as `MIN_NAMES`/`N_FLOOR`.

## ObjectStore Keys

Keep these keys stable unless migration is explicitly requested:

- `news_sentiment_alpha/daily_snapshots.csv`
- `news_sentiment_alpha/positions.csv`
- `news_sentiment_alpha/trades.csv`

## Development Workflow

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
```

**Local backtest — use the shared-signal-aware wrapper, not plain `lean backtest`:**

```bash
bash ~/Documents/Q-agent/scripts/lean-backtest.sh "NewsSentimentAlpha"
```

Plain `lean backtest "NewsSentimentAlpha"` fails with `No module named
'domain.signals.news_tone'` — the wrapper mounts `MyProjects/shared/` into
the container so the symlink resolves. See
`MyProjects/ElectionIndustryBeta/claude.md` for why.

```bash
lean research "NewsSentimentAlpha"
```

Cloud is optional for this project (not required for local development):

```bash
lean cloud push --project "NewsSentimentAlpha" --force
lean cloud backtest "NewsSentimentAlpha" --name "Description"
```

## Validation

Before handing off code changes:

```bash
python -m py_compile main.py models/*.py domain/*.py
python MyProjects/shared/signals/news_tone.py   # shared-signal sanity check
```

Then run a local backtest via `scripts/lean-backtest.sh` (or cloud, if requested).

## Scope Guidance

- **Safe**: Changes within a single layer that don't affect trading behavior
- **Ask First**: Cross-layer changes, strategy parameter changes (universe, dates, rebalance cadence, gross exposure), ObjectStore schema changes, editing `MyProjects/shared/signals/news_tone.py` (affects every consumer — grep the workspace first)
- **Prohibited**: Changes to `config.json`, violating layer dependencies

## Layer Rules

| Layer | Can Import From |
|-------|-----------------|
| `domain/` (excl. `signals/`) | Python stdlib only |
| `domain/signals/` | Python stdlib, pandas, numpy, scipy — no `AlgorithmImports` (shared-atom rule) |
| `models/` | `domain/`, `AlgorithmImports` |
| `main.py` | All layers |

Never import from a higher layer (e.g., `domain/` importing from `models/`).
