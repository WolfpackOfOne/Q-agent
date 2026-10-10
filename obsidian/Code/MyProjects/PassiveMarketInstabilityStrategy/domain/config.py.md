---
path: "MyProjects/PassiveMarketInstabilityStrategy/domain/config.py"
hub: "PassiveMarketInstabilityStrategy"
layer: "Molecule / Atom"
lines: 30
tags:
  - "code/python"
  - "projects/PassiveMarketInstabilityStrategy"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py"
---
# config.py

`MyProjects/PassiveMarketInstabilityStrategy/domain/config.py` · hub [[Hubs/Projects/PassiveMarketInstabilityStrategy|PassiveMarketInstabilityStrategy]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py)

## Purpose

Strategy configuration for PassiveMarketInstabilityStrategy.

## Dependencies


**Imported by:** [[Code/MyProjects/PassiveMarketInstabilityStrategy/main.py|main.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py|alpha.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/portfolio.py|portfolio.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `START_DATE` | `(2018, 1, 1)` | [4](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L4) |
| `END_DATE` | `(2024, 1, 1)` | [5](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L5) |
| `CASH` | `1000000` | [6](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L6) |
| `BENCHMARK` | `'SPY'` | [8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L8) |
| `UNIVERSE` | `['SPY', 'QQQ', 'IWM', 'MDY', 'VTI']` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L11) |
| `PRESSURE_QUINTILE_THRESHOLD` | `4` | [15](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L15) |
| `HIGH_PRESSURE_EXPOSURE_SCALE` | `0.5` | [18](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L18) |
| `PASSIVE_SHARE_ALPHA` | `0.106` | [21](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L21) |
| `PASSIVE_SHARE_T0` | `30.0` | [22](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L22) |
| `PASSIVE_SHARE_REF` | `1994` | [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L23) |
| `PRESSURE_LOOKBACK_DAYS` | `63` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L26) |
| `REBALANCE_DAYS` | `21` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py#L29) |

## Source

> [!example]- MyProjects/PassiveMarketInstabilityStrategy/domain/config.py (30 lines)
> ```python
> """Strategy configuration for PassiveMarketInstabilityStrategy."""
>
> # Backtest window
> START_DATE = (2018, 1, 1)
> END_DATE   = (2024, 1, 1)
> CASH       = 1_000_000
>
> BENCHMARK = "SPY"
>
> # Universe — broad US equity ETFs (same as PMI notebook)
> UNIVERSE = ["SPY", "QQQ", "IWM", "MDY", "VTI"]
>
> # Risk-overlay parameters
> # Passive-pressure quintile at or above which we apply the overlay
> PRESSURE_QUINTILE_THRESHOLD = 4  # quintile 4 or 5 = high pressure
>
> # When passive pressure is high, scale gross exposure by this factor (< 1 = reduce)
> HIGH_PRESSURE_EXPOSURE_SCALE = 0.50
>
> # Passive-share logistic calibration (Haddad et al.)
> PASSIVE_SHARE_ALPHA = 0.106
> PASSIVE_SHARE_T0    = 30.0       # midpoint year relative to 1994
> PASSIVE_SHARE_REF   = 1994       # t=0 calendar year
>
> # Rolling lookback for passive-pressure diagnostics (calendar days)
> PRESSURE_LOOKBACK_DAYS = 63      # ~3 months
>
> # Rebalance frequency
> REBALANCE_DAYS = 21              # monthly
> ```
