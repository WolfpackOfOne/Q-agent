# Alpha101Portfolio - Strategy Logic

## Overview

Daily-rebalanced, dollar-neutral long/short equity strategy on the point-in-time
largest 300 US companies by market cap, built on all 101 formulaic alpha
expressions from Zura Kakushadze, *101 Formulaic Alphas* (arXiv:1601.00991) —
arithmetic formulas over daily open, high, low, close and volume. Every
session the strategy longs the top quintile of scored names and shorts the
bottom quintile, equal-weighted within each side, 100% total gross exposure.

The alpha implementations, selection protocol and evaluation live in the
research notebook `infrastructure/marimo/notebooks/alpha101_portfolio.py`; the
paper is at `References/papers/101-formulaic-alphas/`. This project executes
the notebook's exported point-in-time scores in LEAN.

**Result**: on the held-out 2021–2024 test window, the combined score has a
daily information coefficient of 0.0128 (t = 3.86, positive in every one of
the four test years) and a gross Sharpe of 1.50.

## Strategy Type

- **Category**: Cross-sectional equity long/short (price and volume signals)
- **Asset Class**: US Equity
- **Holding Period**: One trading session
- **Rebalance Frequency**: Daily, five minutes after the open

## Universe

At each calendar quarter-end, the 300 largest US companies by the most recently
reported market cap, from the WRDS broad pipeline. Membership is point-in-time —
decided only from filings already public on the date — and held constant within
each quarter. Over 2004–2024 that spans 811 distinct companies, averaging 296
eligible names per session; the 2021–2024 test window scores 409.

## Data Sources

| Data | Source | Status |
|------|--------|--------|
| Daily OHLCV (811 tickers + SPY) | WRDS/CRSP via `infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py` | Local, gitignored pipeline output |
| Point-in-time universe | Same pipeline → `lean-data/alternative/fundamentals/broad_universe.csv` | Local, gitignored |
| Point-in-time GICS sectors/industries | `scripts/run_broad_sector_pipeline.py` → `lean-data/alternative/sectors/broad_sector_map.csv` | Local, gitignored |
| Alpha scores | Bundled CSV, `data/alpha_scores.csv` (`date,ticker,score`), 283,446 rows | Committed |

The algorithm never computes the alpha formulas and never makes HTTP calls — it
reads the bundled score CSV point-in-time, and the tickers in that file are its
universe.

## Signal Generation

`models/alpha.py::FormulaicAlphaSignal` loads `data/alpha_scores.csv` once,
exposes its tickers as the universe, and on each rebalance returns the newest
score batch dated on or before today, going flat if that batch is older than
`MAX_SCORE_AGE_DAYS`.

How the scores are produced (notebook):

| Step | Detail | Why |
|---|---|---|
| Alphas | All 101 expressions; non-integer lookback windows are floored, per the paper | Full operator coverage — market cap, `adv{d}`, `decay_linear`, `product`, `ts_argmin`/`ts_argmax`, and formula-level `indneutralize` at sector, industry, or sub-industry, whichever each expression specifies |
| VWAP | Approximated by the typical price `(high + low + close) / 3` | Daily bars carry no true volume-weighted average price |
| Formula verification | Every alpha's eligible-name coverage and day-to-day variation is measured before selection; anything below 5% on either is flagged and excluded | Catches transcription bugs mechanically |
| Sector-level neutralisation | Every alpha's output is demeaned within its point-in-time GICS sector before ranking, in addition to whatever formula-level neutralisation the paper specifies | These expressions are built from raw prices and volumes, so much of what they measure is that a stock's sector moved, which carries no next-day information |
| Sector source | Compustat GICS **history** (`comp.co_hgic`), joined as-of each date, at sector/industry-group/industry/sub-industry levels | Point-in-time — a company's classification can change over its history |
| Scale | Each neutralised alpha converted to a cross-sectional rank in [−0.5, 0.5] per session | Puts price differences, correlations and ratios of fifth powers on one comparable footing, and bounds outliers |
| Selection | Alphas with a training-period information coefficient significant at \|t\| ≥ 2 at a one-day horizon | Daily one-day observations do not overlap, so the t-statistic is a fair test |
| Model | Ridge regression (α = 10) | The expressions share overlapping price/volume inputs and are strongly correlated; ridge shrinks them rather than letting collinear pairs take large offsetting weights |
| Target | Next session's return minus the cross-sectional mean | What a dollar-neutral book actually earns |
| Final fit | Refit on train + validate (2005–2020) before scoring the test window | Uses all pre-test data once the design is fixed |

## Portfolio Construction

`models/portfolio.py::HysteresisQuintilePortfolio` builds the book. A name is
added once it reaches the top/bottom quintile by score; once held, it stays in
the book as long as it remains within a wider band, and is only dropped once
its rank exits that band.

| Parameter | Value | Config |
|-----------|-------|--------|
| Entry: long bucket | Top quintile by score (~56 names) | `LONG_SHORT_FRACTION = 0.2` |
| Entry: short bucket | Bottom quintile by score (~56 names) | `LONG_SHORT_FRACTION` |
| Hold band | Top/bottom 30% — an already-held name stays until its rank exits this wider band | `HOLD_FRACTION = 0.3` |
| Weighting | Equal-weight within each side, recomputed each session over whoever is currently held | — |
| Gross exposure | 100% (50% long / 50% short) | `GROSS_EXPOSURE = 1.0` |
| Thin cross-section | < 50 scored names → flat | `MIN_SCORED_NAMES = 50` |

## Validation Methodology

A 60/20/20 split on calendar years:

| Block | Sessions | Share | Window | Role |
|---|---|---|---|---|
| Train | 3,021 | 60% | 2005-01-03 – 2016-12-30 | Fit the model; measure alpha significance |
| Validate | 1,007 | 20% | 2017-01-03 – 2020-12-31 | Design choices |
| Test | 1,004–1,005 | 20% | 2021-01-04 – 2024-12-30 | Held out; frozen configuration refit on train + validate, scored once |

The training block spans the paper's own pre-publication era, which is where
these expressions were documented as working. The four-year test block is long
enough that its Sharpe estimate is not dominated by any single year's regime.

## Results

### Formula verification and selection (2005–2016 training block)

All 101 expressions execute. Formulas with under 5% eligible-universe coverage
or under 5% cross-sectionally varying sessions are flagged and excluded before
selection. Of the remainder, alphas clearing \|t\| ≥ 2 on the training block are
carried into the model. The strongest alphas by training IC:

| Alpha | Mean daily IC | t |
|---|---|---|
| Alpha#54 | 0.0316 | 21.13 |
| Alpha#5 | 0.0219 | 13.39 |
| Alpha#83 | 0.0192 | 10.69 |
| Alpha#38 | 0.0190 | 10.74 |
| Alpha#33 | 0.0191 | 10.23 |
| Alpha#101 | −0.0188 | −11.71 |
| Alpha#53 | 0.0178 | 11.25 |
| Alpha#35 | 0.0170 | 10.74 |

### Signal decay

Mean absolute information coefficient across alphas, measured on the training
period at holding horizons from 1 to 21 trading days, falls off with horizon —
the strongest predictive power is at one day, which sets the daily rebalance
frequency.

### Validation (2017–2020)

Daily information coefficient and gross Sharpe on the validation window inform
design choices before the test window is touched once.

### Test (2021–2024), scored once

| Metric | Gross |
|---|---|
| Daily information coefficient | 0.0128 (t = 3.86) |
| Sharpe | 1.50 |
| Total return | +30.7% |
| Annual return | 6.8% |
| Annual volatility | 4.6% |
| Max drawdown | −4.9% |

| Year | Daily IC | t |
|---|---|---|
| 2021 | +0.0130 | 1.82 |
| 2022 | +0.0026 | 0.37 |
| 2023 | +0.0125 | 2.10 |
| 2024 | +0.0232 | 3.63 |

Every year is individually non-negative.

## Not Modelled

Transaction costs, short-borrow fees, market impact, and true intraday
volume-weighted average price (approximated by the typical price).

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | 2021-01-01 |
| End Date | 2024-12-31 |
| Starting Cash | $1,000,000 |
| Benchmark | SPY |
| Brokerage Model | Interactive Brokers, Margin (the strategy shorts) |

## Strategy Invariants

1. Dollar-neutral: long gross == short gross == 50%.
2. Scores are read point-in-time only (newest batch with `date <= today`).
3. No HTTP calls — `data/alpha_scores.csv` is a bundled snapshot and defines the universe.
4. The score file comes from the notebook's frozen train + validate fit (2005–2020); regenerating it must not involve refitting on 2021–2024.
5. Entry-threshold ranking math stays in the shared signal `MyProjects/shared/signals/cross_sectional_rank.py`; the hysteresis hold-band state is project-local (`models/portfolio.py::HysteresisQuintilePortfolio`) and must not be pushed into the shared atom, which other projects use stateless.
6. Sector/industry labels must come from the GICS **history** table, joined as-of the date — never the current-classification snapshot.
7. Formula changes to any alpha must be checked against the coverage/variation diagnostic before being trusted.
