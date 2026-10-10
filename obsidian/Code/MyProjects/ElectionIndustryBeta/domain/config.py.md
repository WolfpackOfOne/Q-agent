---
path: "MyProjects/ElectionIndustryBeta/domain/config.py"
hub: "ElectionIndustryBeta"
layer: "Molecule / Atom"
lines: 38
tags:
  - "code/python"
  - "projects/ElectionIndustryBeta"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py"
---
# config.py

`MyProjects/ElectionIndustryBeta/domain/config.py` · hub [[Hubs/Projects/ElectionIndustryBeta|ElectionIndustryBeta]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py)

## Purpose

Configuration constants for ElectionIndustryBeta.

Layer: ATOMS (pure constants, no dependencies except stdlib).

Usage:
    from domain.config import *

## Dependencies


**Imported by:** [[Code/MyProjects/ElectionIndustryBeta/domain/__init__.py|__init__.py]], [[Code/MyProjects/ElectionIndustryBeta/main.py|main.py]], [[Code/MyProjects/ElectionIndustryBeta/models/alpha.py|alpha.py]], [[Code/MyProjects/ElectionIndustryBeta/models/logger.py|logger.py]], [[Code/MyProjects/ElectionIndustryBeta/models/portfolio.py|portfolio.py]], [[Code/MyProjects/ElectionIndustryBeta/research/pl_attribution.py|pl_attribution.py]], [[Code/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py|refresh_trump_prob.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `OBJECTSTORE_NAMESPACE` | `'electionbeta'` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L11) |
| `UNIVERSE` | `['XLE', 'XLF', 'XLV', 'XLI', 'XLK', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE', 'XLC', 'XOP', 'ITA', 'KBE', 'IBB', 'ICLN', 'TAN', 'GDX', 'ITB']` | [16](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L16) |
| `BENCHMARK` | `'SPY'` | [22](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L22) |
| `LOOKBACK` | `60` | [25](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L25) |
| `K` | `3` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L26) |
| `TRUMP_TOKEN` | `'21742633143463906290569050155826241533067272736897614950488156847949938836455'` | [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L30) |
| `POLYMARKET_PRICES_URL` | `'https://clob.polymarket.com/prices-history'` | [31](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L31) |
| `TRUMP_PROB_CSV` | `'data/trump_prob.csv'` | [32](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L32) |
| `START_DATE` | `(2024, 3, 15)` | [35](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L35) |
| `END_DATE` | `(2024, 11, 7)` | [36](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L36) |
| `CASH` | `100000` | [37](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/config.py#L37) |

## Source

> [!example]- MyProjects/ElectionIndustryBeta/domain/config.py (38 lines)
> ```python
> """
> Configuration constants for ElectionIndustryBeta.
>
> Layer: ATOMS (pure constants, no dependencies except stdlib).
>
> Usage:
>     from domain.config import *
> """
>
> # === ObjectStore ===
> OBJECTSTORE_NAMESPACE = "electionbeta"
>
> # === Universe ===
> # 19 US sector & industry ETFs from the replication notebook
> # (infrastructure/marimo/notebooks/election_industry_returns.py).
> UNIVERSE = [
>     # Broad SPDR Select Sector ETFs
>     "XLE", "XLF", "XLV", "XLI", "XLK", "XLP", "XLY", "XLU", "XLB", "XLRE", "XLC",
>     # Trump-themed industry slices
>     "XOP", "ITA", "KBE", "IBB", "ICLN", "TAN", "GDX", "ITB",
> ]
> BENCHMARK = "SPY"
>
> # === Signal ===
> LOOKBACK = 60   # trading days of history used in the rolling beta regression
> K = 3           # long top-K by beta, short bottom-K by beta
>
> # === Polymarket ===
> # Trump YES token from the 2024 Presidential Election Winner event.
> TRUMP_TOKEN = "21742633143463906290569050155826241533067272736897614950488156847949938836455"
> POLYMARKET_PRICES_URL = "https://clob.polymarket.com/prices-history"
> TRUMP_PROB_CSV = "data/trump_prob.csv"
>
> # === Backtest defaults ===
> START_DATE = (2024, 3, 15)
> END_DATE   = (2024, 11, 7)
> CASH       = 100_000
> ```
