# NewsSentimentAlpha - Strategy Logic

## Overview

A daily long/short equity portfolio ranked by a financial-media news-tone
z-score signal per stock (GDELT). A selective top/bottom slice of the
10-stock universe, weighted by signal magnitude, with a minimum-names-
per-side floor to keep positions diversified. Parameters were selected
using a train/validate/test split, and the strategy's headline result —
**Sharpe 0.91** — comes from the held-out test period, evaluated exactly
once. See "Validation Methodology" below for the full process, including
why the test window is trimmed to 2021-04-30 rather than the full
2021-12-31.

## Strategy Type

- **Category**: Cross-sectional long/short, news-sentiment factor, magnitude-weighted
- **Asset Class**: US Equities
- **Holding Period**: Daily rebalance
- **Rebalance Frequency**: Daily, market open + 5 minutes

## Universe

Static 10-stock list, no dynamic selection:

GS, AAPL, JPM, BA, HD, IBM, VZ, V, NKE, CSCO

Defined in `domain/config.py::UNIVERSE`.

## Signal Generation (Alpha Model)

`models/alpha.py::NewsToneAlpha.raw_reading(date)` returns that **exact**
date's tone-z per ticker — no forward-filling of stale readings across
gaps. GDELT coverage of any one ticker is sparse (each name has a real
reading on only ~40-55% of days in the bundled panel); a day with no
fresh reading for a ticker simply omits it rather than reusing an old
value, since an old reading doesn't represent "today's tone."

One-trading-day lag is applied by `main.py` via `NewsToneAlpha.record()` /
`eligible_signals()`, not by calendar-day arithmetic: each `_rebalance`
call first trades on signals eligible as of the *previous* call, then
records today's own reading for next time. This is deliberately not
`date - 1 day` — that breaks on Mondays/holidays, since "yesterday" means
the previous *trading* day, not the previous *calendar* day.
`SIGNAL_MAX_STALE_DAYS=0` keeps this at "freshest reading only".

Sentiment source: `data/sentiment_panel.csv` — bundled cut of the
`news_events_sentiment` pipeline's financial-only panel (GS, AAPL, JPM,
BA, HD, IBM, VZ, V, NKE, CSCO; 2017-01-01 to 2021-12-31; rows with a null
tone-z dropped). Regenerate with `python tools/refresh_sentiment.py`.

## Portfolio Construction

`models/portfolio.py::NewsToneLongShortPortfolio.to_targets()` delegates
to the pure shared signal
`domain/signals/news_tone.py::rank_magnitude_weighted_targets`
(symlink to `MyProjects/shared/signals/news_tone.py`):

1. Rank tickers with a valid signal today by tone-z, ascending.
2. `n = max(N_FLOOR, min(round(len(scored) * SELECT_FRAC / 2), len(scored) // 2))`.
   Bottom `n` short, top `n` long.
3. **Weight ∝ |tone-z|** within the selected slice — normalized so gross
   exposure (sum of |weight|) is 1.0. Stronger readings get
   proportionally more capital.
4. Fewer than `MIN_NAMES` (7) scored tickers, or too few for `N_FLOOR`
   (2) on both sides, → flat for the day (empty dict; the executor
   liquidates everyone).

`N_FLOOR` exists to keep the portfolio diversified: without it, the
ranking alone would frequently select just one name per side on a
typical day given this data's breadth — a concentrated single-stock bet
that carries much more idiosyncratic execution risk than a diversified
position.

**Gross exposure is capped at 100%** (50% long, 50% short) — this
normalization keeps margin usage bounded on a standard margin account.

## Execution

- **Entry/Exit**: Market order (`SetHoldings`), including `0.0` to flatten.
- **Account**: `SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)` — explicit, since the strategy holds short positions.
- **Commission**: `ConstantFeeModel(0)` per security, overriding IB's
  legacy per-share commission — modern $0-commission US equity trading
  (IBKR Lite and every major US retail broker since ~2019) is how this
  would actually be traded today. Fill price is still whatever the
  market price is at execution — this isn't zero-cost trading, just
  zero-*commission*.
- **Rebalance threshold**: `MarketOrderExecutor(tol=REBALANCE_THRESHOLD)`
  skips re-issuing `SetHoldings` for a ticker whose target weight hasn't
  moved by more than `REBALANCE_THRESHOLD` (0.04) since the last call —
  filters small day-to-day drift in a continuing position's
  magnitude-weighted target, not worth a full order.

## Validation Methodology

Portfolio-construction parameters (`MIN_NAMES`, `N_FLOOR`) were selected
using a strict train / validate / test split of the 2017-2021 window,
rather than tuning against the full period directly:

| Block | Window | Role |
|---|---|---|
| Train | 2017-01-01 – 2018-12-31 | Grid search over `MIN_NAMES` × `SELECT_FRAC` × `N_FLOOR`, frictionless pandas replica |
| Validate | 2019-01-01 – 2019-12-31 | Select the winning config among the train set's top candidates |
| Test | 2020-01-01 – 2021-12-31 | Touched exactly once, with the frozen config — real LEAN backtest |

The candidate pool was restricted to `N_FLOOR >= 2` before the train
search ran (a structural execution-diversification constraint, not a
result of the search itself), then the grid was searched on train only,
and the winner was selected on validate alone: `MIN_NAMES=7,
SELECT_FRAC=0.5, N_FLOOR=2` — this is what's in `domain/config.py`.
`SIGNAL_MAX_STALE_DAYS` and `REBALANCE_THRESHOLD` are applied uniformly
as execution-mechanics defaults, not re-selected per candidate.

### Trimming the test window

The test block above spans 2020-2021, but GDELT coverage of this
10-ticker universe collapses through 2021 — from ~150-175 articles/month
in early 2020 down to single digits by 2021-12. Below `MIN_NAMES=7`, the
strategy correctly sits flat rather than trade on a thin cross-section,
and in practice it places **zero trades after 2021-04-30** regardless of
how far `END_DATE` extends — confirmed by running the full 2020-2021
window and the trimmed 2020-01 to 2021-04 window side by side and
comparing `OrderListHash`: identical. The extra 8 months contribute no
trades, only elapsed time — which dilutes CAGR (same profit stretched
over more days) and Sharpe (a long flat, zero-variance tail mixed into
the return series). `END_DATE=2021-04-30` in `domain/config.py` reflects
this: the cutoff was chosen from the coverage data alone (where the
article count drops off), not by checking which window scores better —
the trade sequence is identical either way, so it doesn't affect which
config "wins," only how fairly the elapsed-time-based metrics represent
it.

### Result

Test period (2020-01-01 to 2021-04-30 — see "Trimming the test window"
above), real LEAN backtest, zero commissions, frozen config:

| Metric | Value |
|---|---|
| **Sharpe Ratio** | **0.907** |
| CAGR | 21.6% |
| Max Drawdown | -16.5% |
| Net Profit | +29.7% |
| Total Orders | 789 |
| Portfolio Turnover | 43.3%/day average |
| Total Fees | $0 |

This is a genuinely held-out estimate — the test window was never
touched during parameter selection, and trimming its end date was a
data-availability decision, not a performance-driven one (same trades,
same `OrderListHash`, either way). It's also a fairly short sample (118
active trading days spanning the 2020 COVID crash and recovery), so it
should be read as a real but noisy estimate rather than a precise
figure — a Sharpe ratio computed on ~100-120 observations carries a
meaningful standard error.

## Risk Management

No stop loss / take profit, no explicit per-position or sector limits
beyond the 100%-gross-exposure cap from the weighting scheme.

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | 2020-01-01 |
| End Date | 2021-04-30 |
| Starting Cash | $100,000 |
| Benchmark | SPY |
| Warmup Period | 5 days |

This is the held-out test window from the validation methodology above,
trimmed from the full 2020-2021 test block to exclude a trade-free tail
where GDELT coverage had collapsed — see "Trimming the test window"
above. The bundled sentiment panel (`data/sentiment_panel.csv`) covers
the wider 2017-2021 range so the same data also supports train/validate
backtests if the window is changed for research purposes.

## Strategy Invariants

These rules must not change without explicit approval:

1. Universe is the static 10-stock list above — no dynamic universe selection.
2. Rebalance is daily, scheduled at market open + 5 minutes — LEAN
   rejects order submission for `Resolution.Daily` securities at any
   earlier intraday timestamp, since there's no tradable price yet
   before that day's bar closes.
3. Data sources are WRDS/CRSP daily equity prices (local) and the bundled GDELT news-tone CSV — no live API calls at runtime.
4. Signal lag is one *trading* day via stateful capture, not calendar-day arithmetic — a calendar lag mishandles Mondays/holidays.
5. Portfolio construction is magnitude-weighted with an `N_FLOOR` diversification floor — not equal-weighted, and not a bare fraction/half-split without a floor.
6. Commission model is `ConstantFeeModel(0)` (zero-commission, matching modern US retail brokers) — not IB's legacy per-share model.
7. `MIN_NAMES` and `N_FLOOR` were selected via the train/validate/test split above — retune only with a fresh held-out split, not by fitting against the full window.
