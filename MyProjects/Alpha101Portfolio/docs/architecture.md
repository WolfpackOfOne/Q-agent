# Alpha101Portfolio - Architecture

## Overview

Daily dollar-neutral long/short on a formulaic-alpha score across the
point-in-time top-300 US companies. The alpha expressions are implemented and
evaluated in a marimo research notebook on data from the broad WRDS pipeline;
this LEAN project consumes the exported point-in-time scores — which also define
its universe — and executes the identical portfolio rule. See `strategy.md` for
methodology and results.

## Three stages, one signal

```
infrastructure/pipelines/wrds/            infrastructure/marimo/notebooks/            MyProjects/Alpha101Portfolio/
run_broad_quarterly_pipeline.py           alpha101_portfolio.py
┌──────────────────────────────┐          ┌──────────────────────────────────┐      ┌──────────────────────────────────┐
│ CRSP daily OHLCV + CCM link  │          │ 101 formulaic alphas (Kakushadze)│      │ data/alpha_scores.csv            │
│  → top-300 universe/quarter  │  read    │  → rank cross-sectionally        │export│  → tickers = universe (AddEquity)│
│  → adjusted daily bars       │ ───────▶ │  → decay analysis, select |t|>=2 │─────▶│  → newest batch with date<=today │
│  → broad_universe.csv        │          │  → ridge score, quintile book    │      │  → quintile L/S (shared signal)  │
│  → broad_permno_map.csv      │          │  → ONE test evaluation           │      │  → SetHoldings, daily            │
└──────────────────────────────┘          └──────────────────────────────────┘      └──────────────────────────────────┘
                                    notebook and LEAN apply the same rule: shared/signals/cross_sectional_rank.py
```

## Atomic Structure

```
Alpha101Portfolio/
├── main.py                  # COMPOSITION ROOT — QCAlgorithm facade, universe from score file, daily rebalance
├── models/                  # ORGANISMS
│   ├── alpha.py              # FormulaicAlphaSignal — loads score CSV once, exposes tickers, serves newest batch
│   ├── portfolio.py          # HysteresisQuintilePortfolio — quintile-entry long/short with a turnover hold band
│   ├── execution.py          # MarketOrderExecutor — SetHoldings per active target
│   └── logger.py             # PortfolioLogger — ObjectStore logging facade
├── domain/                  # MOLECULES + ATOMS
│   ├── config.py             # Dates, construction and cost parameters (ATOMS)
│   ├── models.py             # DTOs, enums (ATOMS)
│   └── signals/
│       └── cross_sectional_rank.py   # SYMLINK → ../../../shared/signals/cross_sectional_rank.py
├── data/
│   └── alpha_scores.csv              # Bundled per-project data (committed)
└── docs/
    ├── architecture.md      # This file
    ├── strategy.md          # Strategy logic, validation methodology, results
    └── objectstore.md       # Data output schemas
```

## Layer Dependencies

```
main.py (Composition Root) → models/ (Organisms) → domain/ (Molecules + Atoms)
Organisms may import domain/ and AlgorithmImports; domain/ imports stdlib only
(signals/ may use pandas/numpy). Never import upward.
```

## Key Design Decisions

### 1. The score file is the universe

There is no hard-coded ticker list. `FormulaicAlphaSignal` loads
`data/alpha_scores.csv` first and `main.py` subscribes to exactly the tickers it
contains, skipping any without local data. This keeps the LEAN universe
identical to the notebook's point-in-time top-300 without re-implementing the
quarterly membership rule.

### 2. Alphas off-platform, execution in LEAN

Computing 101 rolling-window expressions across the price panel belongs
in the notebook. Only test-window scores are exported, so the backtest cannot
see the formulas, the price panel, or any pre-2021 data.

### 3. An explicit basis-point cost model

The book replaces about 140% of its value per session, so the result is far more
sensitive to execution cost than to any modelling choice. `main.py` therefore
zeroes LEAN's per-share commission and applies a flat
`COST_BPS_PER_SIDE` slippage instead, so the engine charges exactly what the
notebook assumed and the assumption is visible in one constant.

### 4. Daily rebalance, matched to where the signal lives

The notebook's decay analysis measures each alpha's information coefficient at
horizons from 1 to 21 days. The average absolute IC falls from 0.0090 at one day
to 0.0065 at five, which is why the book rebalances daily despite the cost that
implies. `DateRules.EveryDay(BENCHMARK)` fires once per session on the
benchmark's calendar, matching the notebook's scoring dates.

### 5. Touch only active names

`_rebalance` passes the executor the union of currently held and newly targeted
tickers (~120 of ~300), so a session issues roughly 150 orders rather than 300.

## Data Flow

```
[Bundled score CSV] → [Alpha: tickers → AddEquity; newest batch with date <= today]
                                        ↓
                        [Portfolio: quintile L/S, equal-weight, 100% gross]
                                        ↓
                    [Execution: SetHoldings on held ∪ targeted, skip no-data]
                                        ↓
                                    [Logger] → [ObjectStore]
```
