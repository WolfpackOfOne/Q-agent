# FundamentalsPortfolio - Architecture

## Overview

Quarterly dollar-neutral long/short on a fundamental score across the
point-in-time top-1,000 US companies. The model is fit and evaluated in a
marimo research notebook on data from the broad WRDS pipeline; this LEAN
project consumes the exported point-in-time scores — which also define
its universe — and executes the identical portfolio rule. See
`strategy.md` for methodology and results.

## Three stages, one signal

```
infrastructure/pipelines/wrds/                infrastructure/marimo/notebooks/                MyProjects/FundamentalsPortfolio/
scripts/run_broad_quarterly_pipeline.py       fundamentals_portfolio.py
┌──────────────────────────────────┐          ┌──────────────────────────────────────┐        ┌──────────────────────────────────┐
│ comp.fundq ≥ $1B × CCM link      │          │ clean on fiscal clocks, 17 features   │        │ data/fundamental_scores.csv      │
│  → broad_quarterly_fundamentals  │  read    │  → point-in-time panel, rank scale    │ export │  → tickers = universe (AddEquity)│
│  → top-1000 universe per quarter │ ───────▶ │  → train 05-18 / val 19-21 / test 22-23│ ─────▶ │  → newest batch with date<=today │
│  → CRSP prices → LEAN zips       │          │  → gradient-boosted score, 8 features │        │  → decile L/S (shared signal)    │
│  → month-end TRI, permno map     │          │  → one test evaluation                │        │  → SetHoldings on active names   │
└──────────────────────────────────┘          └──────────────────────────────────────┘        └──────────────────────────────────┘
                                         notebook and LEAN apply the same rule: shared/signals/cross_sectional_rank.py
```

## Atomic Structure

```
FundamentalsPortfolio/
├── main.py                  # COMPOSITION ROOT — QCAlgorithm facade, universe from score file, quarterly rebalance
├── models/                  # ORGANISMS
│   ├── alpha.py              # FundamentalRankAlpha — loads score CSV once, exposes tickers, serves newest batch
│   ├── portfolio.py          # FundamentalRankPortfolio — decile long/short via shared signal
│   ├── execution.py          # MarketOrderExecutor — SetHoldings per active target, skips tickers without data
│   └── logger.py             # PortfolioLogger — ObjectStore logging facade
├── domain/                  # MOLECULES + ATOMS
│   ├── config.py             # Dates, rebalance months, construction parameters (ATOMS)
│   ├── models.py             # DTOs, enums, protocols (ATOMS)
│   └── signals/
│       └── cross_sectional_rank.py   # SYMLINK → ../../../shared/signals/cross_sectional_rank.py
├── data/
│   └── fundamental_scores.csv        # Bundled per-project data (committed)
└── docs/
    ├── architecture.md      # This file
    ├── strategy.md          # Strategy logic, validation methodology, results
    └── objectstore.md       # Data output schemas
```

## Layer Dependencies

```
main.py (Composition Root) → models/ (Organisms) → domain/ (Molecules + Atoms)
Organisms may import domain/ and AlgorithmImports; domain/ imports stdlib
only (signals/ may use pandas/numpy). Never import upward.
```

## Key Design Decisions

### 1. The score file is the universe

There is no hard-coded ticker list. `FundamentalRankAlpha` loads
`data/fundamental_scores.csv` first, and `main.py` subscribes to exactly
the tickers it contains (1,081 in the test window), skipping any without
local data. This keeps the LEAN universe identical to the notebook's
point-in-time top-1,000 without re-implementing the membership rule.

### 2. Model off-platform, execution in LEAN

Fitting the model on a 63k-row panel belongs in the notebook. Only
test-window scores are exported, so the backtest cannot see the model,
the raw fundamentals, or pre-2022 data.

### 3. Point-in-time by construction, twice

Notebook: features dated by `rdq`, valuation re-priced with the CRSP
total-return index, scores stamped with the quarter-end on which
everything was public. LEAN: only the newest batch with `date <= today`,
flat if stale, rebalancing on the first trading day after the quarter-end.

### 4. PERMNO identity, LEAN tickers

Research keys on CRSP PERMNO (tickers are reused across companies); the
pipeline assigns each PERMNO a unique tradable ticker and the export
translates through `broad_permno_map.csv`. LEAN never sees a PERMNO.

### 5. Touch only active names

`_rebalance` passes the executor the union of currently held and newly
targeted tickers, not all subscriptions, so a rebalance issues a few
hundred orders rather than a thousand no-ops.

### 6. Shared signal atom, quarterly schedule without `MonthStart(n)`

Ranking math lives in the symlinked shared signal (`frac = 0.1` for
deciles); the schedule fires on `DateRules.MonthStart(BENCHMARK)`
filtered to `REBALANCE_MONTHS = [1, 4, 7, 10]`, since `DateRules.MonthStart(n)`
with a bare integer treats `n` as a Symbol, not a day offset.

## Data Flow

```
[Bundled score CSV] → [Alpha: tickers → AddEquity; newest batch with date <= today]
                                        ↓
                        [Portfolio: decile L/S, equal-weight, 100% gross]
                                        ↓
                    [Execution: SetHoldings on held ∪ targeted, skip no-data]
                                        ↓
                                    [Logger] → [ObjectStore]
```
