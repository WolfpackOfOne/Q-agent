---
path: "MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py"
hub: "PassiveMarketInstabilityStrategy"
layer: "Organism"
lines: 85
tags:
  - "code/python"
  - "projects/PassiveMarketInstabilityStrategy"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py"
---
# alpha.py

`MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py` · hub [[Hubs/Projects/PassiveMarketInstabilityStrategy|PassiveMarketInstabilityStrategy]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/PassiveMarketInstabilityStrategy/domain/config.py|config.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py|models.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/domain/signals/passive_pressure.py|passive_pressure.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]]

**Imported by:** [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/__init__.py|__init__.py]]

## Classes

### class `PassivePressureAlpha`

[line 21](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py#L21)

Computes the passive-pressure risk-overlay signal.

Logic:
1. Estimate current logistic passive share p(t).
2. For each symbol, compute the flow-pressure proxy: volume × return.
3. Rank symbols by flow-pressure quintile within the universe.
4. If average quintile >= threshold, activate the risk overlay.

This is a risk overlay, not an alpha signal.  It does not generate
directional bets — it scales gross exposure down when passive-flow
pressure is elevated across the universe.

- `def __init__(self, universe: list)` — [L36](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py#L36)
- `def compute(self, algorithm: QCAlgorithm, symbols: dict) -> PassivePressureSignal` — [L39](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py#L39)

## Source

> [!example]- MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py (85 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> # endregion
>
> from domain.models import PassivePressureSignal
> from domain.signals.passive_pressure import (
>     passive_share_at_date,
>     compute_flow_pressure_proxy,
>     passive_pressure_quintile,
>     risk_overlay_scale,
> )
> from domain.config import (
>     PRESSURE_QUINTILE_THRESHOLD,
>     HIGH_PRESSURE_EXPOSURE_SCALE,
>     PASSIVE_SHARE_ALPHA,
>     PASSIVE_SHARE_T0,
>     PASSIVE_SHARE_REF,
> )
>
>
> class PassivePressureAlpha:
>     """
>     Computes the passive-pressure risk-overlay signal.
>
>     Logic:
>     1. Estimate current logistic passive share p(t).
>     2. For each symbol, compute the flow-pressure proxy: volume × return.
>     3. Rank symbols by flow-pressure quintile within the universe.
>     4. If average quintile >= threshold, activate the risk overlay.
>
>     This is a risk overlay, not an alpha signal.  It does not generate
>     directional bets — it scales gross exposure down when passive-flow
>     pressure is elevated across the universe.
>     """
>
>     def __init__(self, universe: list):
>         self._universe = universe
>
>     def compute(self, algorithm: QCAlgorithm, symbols: dict) -> PassivePressureSignal:
>         date = algorithm.Time
>
>         passive_share = passive_share_at_date(
>             date,
>             ref_year=PASSIVE_SHARE_REF,
>             alpha=PASSIVE_SHARE_ALPHA,
>             t0=PASSIVE_SHARE_T0,
>         )
>
>         returns = {}
>         volumes = {}
>         for ticker, symbol in symbols.items():
>             bars = algorithm.History(symbol, 2, Resolution.Daily)
>             if bars.empty or len(bars) < 2:
>                 continue
>             closes = bars["close"]
>             vols   = bars["volume"]
>             if closes.iloc[-2] > 0:
>                 returns[ticker] = float(closes.iloc[-1] / closes.iloc[-2] - 1.0)
>                 volumes[ticker] = float(vols.iloc[-1])
>
>         pressures = compute_flow_pressure_proxy(returns, volumes)
>         pressure_values = list(pressures.values())
>
>         quintiles = {}
>         for ticker, p in pressures.items():
>             quintiles[ticker] = passive_pressure_quintile(p, pressure_values)
>
>         avg_quintile = float(sum(quintiles.values()) / len(quintiles)) if quintiles else 3.0
>         high_fraction = sum(1 for q in quintiles.values() if q >= PRESSURE_QUINTILE_THRESHOLD) / max(len(quintiles), 1)
>         overlay_active = avg_quintile >= PRESSURE_QUINTILE_THRESHOLD
>         exp_scale = risk_overlay_scale(
>             avg_quintile,
>             threshold=PRESSURE_QUINTILE_THRESHOLD,
>             scale_when_high=HIGH_PRESSURE_EXPOSURE_SCALE,
>         )
>
>         return PassivePressureSignal(
>             date=date,
>             passive_share=passive_share,
>             avg_pressure_quintile=avg_quintile,
>             high_pressure_fraction=high_fraction,
>             overlay_active=overlay_active,
>             exposure_scale=exp_scale,
>         )
> ```
