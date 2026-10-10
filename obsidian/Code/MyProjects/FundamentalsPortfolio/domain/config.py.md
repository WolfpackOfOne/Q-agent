---
path: "MyProjects/FundamentalsPortfolio/domain/config.py"
hub: "FundamentalsPortfolio"
layer: "Molecule / Atom"
lines: 61
tags:
  - "code/python"
  - "projects/FundamentalsPortfolio"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py"
---
# config.py

`MyProjects/FundamentalsPortfolio/domain/config.py` · hub [[Hubs/Projects/FundamentalsPortfolio|FundamentalsPortfolio]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py)

## Purpose

Configuration constants for FundamentalsPortfolio.

Layer: ATOMS (pure constants, no dependencies except stdlib).

Usage:
    from domain.config import *

## Dependencies


**Imported by:** [[Code/MyProjects/FundamentalsPortfolio/domain/__init__.py|__init__.py]], [[Code/MyProjects/FundamentalsPortfolio/main.py|main.py]], [[Code/MyProjects/FundamentalsPortfolio/models/alpha.py|alpha.py]], [[Code/MyProjects/FundamentalsPortfolio/models/logger.py|logger.py]], [[Code/MyProjects/FundamentalsPortfolio/models/portfolio.py|portfolio.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `OBJECTSTORE_NAMESPACE` | `'fundamentals_portfolio'` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L11) |
| `BENCHMARK` | `'SPY'` | [22](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L22) |
| `REBALANCE_MONTHS` | `[1, 4, 7, 10]` | [31](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L31) |
| `FUNDAMENTAL_SCORES_CSV` | `'data/fundamental_scores.csv'` | [38](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L38) |
| `MAX_SCORE_AGE_DAYS` | `100` | [42](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L42) |
| `LONG_SHORT_FRACTION` | `0.1` | [52](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L52) |
| `GROSS_EXPOSURE` | `1.0` | [53](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L53) |
| `MIN_SCORED_NAMES` | `100` | [54](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L54) |
| `START_DATE` | `(2022, 1, 1)` | [58](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L58) |
| `END_DATE` | `(2023, 12, 31)` | [59](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L59) |
| `CASH` | `1000000` | [60](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/domain/config.py#L60) |

## Source

> [!example]- MyProjects/FundamentalsPortfolio/domain/config.py (61 lines)
> ```python
> """
> Configuration constants for FundamentalsPortfolio.
>
> Layer: ATOMS (pure constants, no dependencies except stdlib).
>
> Usage:
>     from domain.config import *
> """
>
> # === ObjectStore ===
> OBJECTSTORE_NAMESPACE = "fundamentals_portfolio"
>
> # === Universe ===
> # There is no hard-coded ticker list. The tradable universe is every ticker
> # that appears in data/fundamental_scores.csv — the point-in-time top-1000
> # US companies by reported market cap at each quarter-end, scored by the
> # research notebook (infrastructure/marimo/notebooks/fundamentals_portfolio.py).
> # main.py subscribes to those tickers at Initialize. Tickers are the
> # `lean_ticker` names from the WRDS broad pipeline (latest CRSP ticker,
> # suffixed with the PERMNO on collision) and have local daily bars at
> # infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip.
> BENCHMARK = "SPY"
>
> # === Rebalance schedule ===
> # Quarterly: first trading day of Jan / Apr / Jul / Oct — the first session
> # after each calendar-quarter scoring date (end of Mar / Jun / Sep / Dec).
> # NOTE: DateRules.MonthStart(n) with a bare int treats `n` as a Symbol, not
> # a day offset (workspace claude.md "LEAN API gotchas"). We schedule on
> # DateRules.MonthStart(BENCHMARK) and filter to REBALANCE_MONTHS inside
> # _rebalance.
> REBALANCE_MONTHS = [1, 4, 7, 10]
>
> # === Fundamental scores (bundled, point-in-time) ===
> # Schema: date,ticker,score — one row per stock per calendar-quarter scoring
> # date. Produced by the broad notebook's export switch from a model fit on
> # 2005-2021 only, for the held-out 2022-2023 test window. The algorithm only
> # ever uses the newest batch with date <= today — see models/alpha.py.
> FUNDAMENTAL_SCORES_CSV = "data/fundamental_scores.csv"
>
> # A score batch older than this on a rebalance day means the notebook
> # produced nothing for that quarter -> go flat rather than trade stale ranks.
> MAX_SCORE_AGE_DAYS = 100
>
> # === Portfolio construction ===
> # Dollar-neutral long/short: long the top LONG_SHORT_FRACTION of scored
> # names, short the bottom LONG_SHORT_FRACTION, equal-weighted within each
> # side, GROSS_EXPOSURE total (half long / half short). Decile buckets
> # balance a large enough basket per side to diversify single-stock risk
> # against staying concentrated in the strongest signal. Rank/weight math
> # lives in domain/signals/cross_sectional_rank.py (symlink to
> # ../../../shared/signals/cross_sectional_rank.py).
> LONG_SHORT_FRACTION = 0.1         # top/bottom decile
> GROSS_EXPOSURE = 1.0              # 50% long + 50% short
> MIN_SCORED_NAMES = 100            # thinner cross-section than this -> flat
>
> # === Backtest defaults ===
> # Held-out test window (train 2005-2018, validate 2019-2021, test 2022-2023).
> START_DATE = (2022, 1, 1)
> END_DATE = (2023, 12, 31)
> CASH = 1_000_000
> ```
