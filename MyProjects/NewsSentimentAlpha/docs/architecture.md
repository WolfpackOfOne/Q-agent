# NewsSentimentAlpha - Architecture

## Overview

Daily long/short equity portfolio ranked by a financial-media news-tone
z-score signal per stock, magnitude-weighted, rebalanced daily. See
`strategy.md` for signal timing details and the validation methodology
behind the current parameters.

## Atomic Structure

```
NewsSentimentAlpha/
├── main.py                  # COMPOSITION ROOT
│                            # QCAlgorithm facade, daily scheduled rebalance,
│                            # one-trading-day signal lag (stateful)
│
├── models/                  # ORGANISMS
│   ├── alpha.py              # NewsToneAlpha — exact-date tone-z lookup (no ffill)
│   ├── portfolio.py          # NewsToneLongShortPortfolio — magnitude-weighted ranked targets
│   ├── execution.py          # MarketOrderExecutor — SetHoldings per target
│   └── logger.py             # PortfolioLogger — ObjectStore logging facade
│
├── domain/                  # MOLECULES + ATOMS
│   ├── config.py             # Universe, dates, cash, strategy parameters, ObjectStore namespace (ATOMS)
│   ├── models.py             # DTOs, enums, protocols (ATOMS)
│   └── signals/
│       └── news_tone.py      # SYMLINK → ../../../shared/signals/news_tone.py
│
├── data/                    # Bundled per-project CSV (sentiment_panel.csv)
├── tools/
│   └── refresh_sentiment.py  # One-off refresher — no runtime HTTP calls
│
└── docs/                    # Documentation
    ├── architecture.md      # This file
    ├── strategy.md          # Strategy logic, signal timing, validation methodology
    └── objectstore.md       # Data output schemas
```

## Layer Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPOSITION ROOT                          │
│                      (main.py)                               │
│         Can import: ALL layers                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                       ORGANISMS                              │
│                    (models/*.py)                             │
│         Can import: domain/, AlgorithmImports                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   MOLECULES + ATOMS                          │
│              (domain/*.py, domain/signals/*.py)              │
│         Can import: Python stdlib, pandas/numpy (signals only)│
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Direct SetHoldings, not the QC AlphaModel framework

`models/{alpha,portfolio,execution}.py` are plain Python classes wired
directly from `main.py::_rebalance`, not `AlphaModel` /
`PortfolioConstructionModel` / `ExecutionModel` subclasses. See
`MyProjects/ElectionIndustryBeta/` for the pattern this mirrors.

### 2. Ranking math lives in a shared, pure-Python signal atom

`domain/signals/news_tone.py` is a symlink to
`MyProjects/shared/signals/news_tone.py` — no LEAN imports, unit-testable
with a plain `python` shell (`python MyProjects/shared/signals/news_tone.py`
runs its synthetic-data sanity check). `models/portfolio.py` delegates to
it rather than reimplementing the ranking logic inline.

### 3. One-trading-day signal lag via stateful capture, not calendar math

`NewsToneAlpha` keeps an internal `_last_seen` staleness cache. Each
`_rebalance` call trades on `eligible_signals()` (state as of the *prior*
call) first, then calls `record(raw_reading(today), ...)` to fold in
today's own reading for next time. This is what correctly makes "today's
trade" use "yesterday's reading" across weekends and holidays — a
calendar-day `date - 1` lookup gets Mondays wrong.

### 4. Gross exposure normalized to 100%

`rank_magnitude_weighted_targets` normalizes weights so total gross
exposure (long + short) is 100%, keeping margin usage bounded on a
standard margin account — matches `ElectionIndustryBeta`'s established
convention.

### 5. Magnitude-weighted, selective slice, diversification floor

`rank_magnitude_weighted_targets` weights positions by signal magnitude
rather than equal-weighting, trades a selective top/bottom slice
(`SELECT_FRAC`), and enforces a minimum names-per-side floor (`N_FLOOR`)
so the portfolio stays diversified rather than concentrating into one or
two names on a typical day. `MIN_NAMES` and `N_FLOOR` were selected via
a train/validate/test split — see `strategy.md` § "Validation
Methodology".

## Data Flow

```
[Bundled CSV] → [Alpha: exact-date lookup + staleness cache, 1-day lag]
                                                        ↓
                                            [Portfolio: rank + weight]
                                                        ↓
                                              [Execution: SetHoldings]
                                                        ↓
                                                    [Logger]
                                                        ↓
                                                 [ObjectStore]
```

## Module Responsibilities

| Module | Layer | Responsibility |
|--------|-------|----------------|
| `main.py` | Root | Wire models, schedule daily rebalance, maintain 1-day signal lag, handle order events |
| `models/alpha.py` | Organism | Exact-date tone-z lookup, no forward-fill |
| `models/portfolio.py` | Organism | Delegate to shared signal for magnitude-weighted ranked long/short targets |
| `models/execution.py` | Organism | Apply target weights via SetHoldings, skip sub-threshold drift |
| `models/logger.py` | Organism | Persist data to ObjectStore |
| `domain/config.py` | Atom | Universe, dates, cash, strategy parameters, namespace constants |
| `domain/models.py` | Atom | DTOs, enums, protocols |
| `domain/signals/news_tone.py` | Atom (shared) | Pure ranking math — magnitude-weighted top/bottom slice with a diversification floor |
