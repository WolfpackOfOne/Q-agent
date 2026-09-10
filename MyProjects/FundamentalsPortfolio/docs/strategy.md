# FundamentalsPortfolio - Strategy Logic

## Overview

Quarterly-rebalanced, dollar-neutral long/short equity strategy on the
point-in-time largest 1,000 US companies by market cap. Each stock is
scored by a gradient-boosted trees model on cross-sectionally ranked
quarterly financial-statement features (Compustat `comp.fundq` via WRDS,
joined to CRSP through the CRSP–Compustat link). Every calendar quarter
the strategy longs the top decile of scored names (~90 stocks) and shorts
the bottom decile, equal-weighted within each side, 100% total gross
exposure (50% long / 50% short).

The model, the feature set, and the evaluation protocol live in the
research notebook `infrastructure/marimo/notebooks/fundamentals_portfolio.py`;
this project executes its exported point-in-time scores in LEAN.

**Result**: test IC 0.078 (t = 4.0), positive in all 7 test quarters;
notebook Sharpe 1.53 at 3.0% annualized volatility (+8.2% over
2022–2023, max drawdown −0.7%). See "Results" below.

## Strategy Type

- **Category**: Cross-sectional equity long/short (fundamental factor)
- **Asset Class**: US Equity
- **Holding Period**: One calendar quarter (non-overlapping)
- **Rebalance Frequency**: Quarterly — first trading day of Jan / Apr / Jul / Oct, aligned to the release cadence of quarterly financial statements

## Universe

At each calendar quarter-end, the 1,000 largest US-dollar-reporting
companies by the most recently reported market cap (`prccq × cshoq` from
the latest filing already public by that date). Membership is
point-in-time — decided only from information available on the date, so
there is no survivorship bias in eligibility. Over 2004–2024 that spans
2,754 distinct companies; the 2022–2023 test window scores 1,081.

Companies are keyed on CRSP PERMNO in research and translated to a
tradable ticker for LEAN, because tickers are reused across companies
over time.

Financial-sector companies are not excluded (the pipeline does not yet
carry a sector classification). CRSP delisting returns are not included
in the month-end return series used to build the training data.

## Data Sources

| Data | Source | Status |
|------|--------|--------|
| Daily equity prices (2,754 tickers + SPY) | WRDS/CRSP via `infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py` → `lean-data/equity/usa/daily/{ticker}.zip` | Local, gitignored pipeline output (~15 min to regenerate) |
| Quarterly fundamentals, universe, month-end returns (research only) | Same pipeline → `lean-data/alternative/fundamentals/broad_{quarterly_fundamentals,universe,permno_map,monthly_tri}.csv` | Local, gitignored |
| Fundamental scores | Bundled CSV, `data/fundamental_scores.csv` (`date,ticker,score`) — exported by the notebook for the test window only, 6,223 rows | Committed |

The algorithm never makes HTTP calls and never computes the model — it
reads the bundled score CSV point-in-time (newest batch with
`date <= today`), and the tickers in that file are its universe.

## Signal Generation (Alpha Model)

`models/alpha.py::FundamentalRankAlpha`:

1. Load `data/fundamental_scores.csv` once (`__file__`-relative path, plain
   relative path, then ObjectStore fallback); expose its tickers as the
   universe `main.py` subscribes to.
2. On each rebalance, take rows with `date <= today`, keep the newest date,
   and return `{ticker: score}` for that batch.
3. If the newest batch is older than `MAX_SCORE_AGE_DAYS` (100), return `{}`
   — the strategy goes flat rather than trade a stale ranking.

How the scores are produced (notebook):

| Step | Detail | Why |
|---|---|---|
| Point-in-time | Each fiscal quarter's figures usable from `rdq` (earnings release date); valuation ratios re-priced monthly with the CRSP total-return index | Prevents look-ahead — a figure is only used once it was actually public |
| Cleaning | Year-to-date cash flows differenced to single quarters on each company's own fiscal clock; trailing-4-quarter sums require 4 consecutive quarters | Compustat reports cash-flow items cumulatively within the fiscal year |
| Feature admission | A feature is used only if every raw input is populated for ≥ 95% of company-quarters — 17 of 22 candidates pass | Avoids relying on assumed values for line items many companies don't report |
| Feature scale | Cross-sectional rank, mapped to [−0.5, 0.5] within each quarter | Puts ratios of different scale and distribution on a common footing and limits the influence of outliers |
| Feature selection | Only features with a statistically significant training-period correlation to next-quarter relative return (|t| ≥ 1.5) — 8 of 17: gross profit/assets, OCF/assets, FCF yield, ROA, ROE (positive); share issuance, accruals, book-to-market (negative) | Standard significance filter — a feature must show a real, not noisy, relationship to future returns |
| Model | Gradient-boosted decision trees (100 trees, depth 3) | Captures non-linear interactions between fundamental ratios that a linear combination cannot represent; a standard model family in quantitative equity research |
| Final fit | Refit on train + validate (2005–2021) before scoring the test period | Uses all pre-test data once the configuration is fixed |

## Portfolio Construction

`models/portfolio.py::FundamentalRankPortfolio` delegates to
`domain/signals/cross_sectional_rank.py::tercile_long_short_targets`
(symlink to `MyProjects/shared/signals/`):

| Parameter | Value | Config |
|-----------|-------|--------|
| Long bucket | Top decile by score (~90 names) | `LONG_SHORT_FRACTION = 0.1` |
| Short bucket | Bottom decile by score (~90 names) | `LONG_SHORT_FRACTION` |
| Weighting | Equal-weight within each side | — |
| Gross exposure | 100% (50% long / 50% short) | `GROSS_EXPOSURE = 1.0` |
| Net exposure | 0% (dollar-neutral) | — |
| Thin cross-section | < 100 scored names → flat | `MIN_SCORED_NAMES = 100` |

Ranking the universe and trading the top and bottom deciles is the
standard construction in the factor-investing literature: it isolates the
return spread attributable to the score from the broader market, while
including enough names per side to diversify single-stock risk.
Dollar-neutrality (equal long and short exposure) removes overall market
exposure so the result reflects stock-selection skill rather than beta.

## Execution

- Market orders via `SetHoldings` (`models/execution.py::MarketOrderExecutor`) on the active names only (currently held or newly targeted); names leaving both deciles are liquidated.
- A ticker with no price bar yet is skipped with a log line.
- Brokerage: Interactive Brokers margin model (the strategy shorts); IB's default per-share commissions apply.

## Validation Methodology

Chronological split with purge gaps (a rebalance whose 3-month holding
window crosses a split boundary is dropped):

| Block | Rebalances | Names / rebalance | Window | Role |
|---|---|---|---|---|
| Train | 55 | ~856 | 2005-03 – 2018-09 | Fit the model; measure feature significance |
| Validate | 11 | ~863 | 2019-03 – 2021-09 | Out-of-sample check before finalizing the configuration |
| Test | 7 | ~889 | 2022-03 – 2023-09 | Held out; frozen configuration refit on train + validate; evaluated once |

## Results

Test window 2022-03 → 2023-12, 7 quarterly holding periods:

| | Notebook (10 bps/side) | LEAN (IB commissions) | Equal-weight universe, long-only |
|---|---|---|---|
| Sharpe | **1.53** | 0.55 † (≈ 1.2 raw) | 0.19 |
| Annual return | 4.5% | 4.3% | 3.7% |
| Annual vol | 3.0% | 3.6% ‡ | 19.9% |
| Max drawdown | −0.7% | −3.5% ‡ | −20.4% |
| Total return (window) | +8.2% | +8.7% | +3.5% |
| Hit rate (quarters) | 71% | 71% | 57% |
| Test IC | **0.078 (t = 3.97, positive in 7 of 7 quarters)** | — | — |
| Turnover per rebalance | ~78% of gross | 1,006 orders, $1,369 fees on $1M | — |

† LEAN's Sharpe subtracts a risk-free rate (≈ 4–5% over this window). ‡
LEAN marks daily; the notebook marks quarterly, so LEAN's vol and
drawdown reflect intra-quarter movement the notebook's figures don't
capture. Roughly 88 names per side each quarter.

Quarterly strategy returns: −0.7%, +0.1%, −0.0%, +1.0%, +3.2%, +3.0%,
+1.4%.

## Caveats

- The Sharpe ratio is measured over 7 quarters and carries a standard
  error on the order of ±0.7; the information coefficient (t = 4.0 over
  ~6,200 stock-quarters) is the more precise measurement.
- Turnover is ~80% of gross per quarter; the reported cost assumption is
  10 bps per side.
- Not modeled: short-borrow fees on the short book, market impact, and
  CRSP delisting returns. Financial-sector companies are not excluded.

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | 2022-01-01 |
| End Date | 2023-12-31 |
| Starting Cash | $1,000,000 |
| Benchmark | SPY |
| Warmup Period | 10 days |

2022-01-01 to 2023-12-31 is the held-out test period. The first
rebalance with scores is 2022-04-01 (first scoring date 2022-03-31); the
strategy is in cash before that.

## Strategy Invariants

These rules must not change without explicit approval:

1. Dollar-neutral: long gross == short gross == 50% (100% total gross).
2. Rebalance is quarterly only (first trading day of Jan / Apr / Jul / Oct) — no intra-quarter trading.
3. Scores are read point-in-time only (newest batch with `date <= today`) — never a look-ahead read.
4. No HTTP calls from the algorithm — `data/fundamental_scores.csv` is a bundled, pre-computed snapshot and defines the universe.
5. The score file is produced by the notebook's frozen train + validate fit (2005–2021); regenerating it must not involve refitting on 2022–2023.
6. Feature admission follows the > 5%-missing-input rule; feature selection follows the |t| ≥ 1.5 significance rule.
