---
path: "MyProjects/PassiveMarketInstabilityStrategy/models/logger.py"
hub: "PassiveMarketInstabilityStrategy"
layer: "Organism"
lines: 20
tags:
  - "code/python"
  - "projects/PassiveMarketInstabilityStrategy"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/logger.py"
---
# logger.py

`MyProjects/PassiveMarketInstabilityStrategy/models/logger.py` · hub [[Hubs/Projects/PassiveMarketInstabilityStrategy|PassiveMarketInstabilityStrategy]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/logger.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py|models.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]]

**Imported by:** [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/__init__.py|__init__.py]]

## Classes

### class `PortfolioLogger`

[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/logger.py#L8)

- `def __init__(self, algorithm: QCAlgorithm)` — [L9](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/logger.py#L9)
- `def log_rebalance(self, signal: PassivePressureSignal, targets: PortfolioTargets) -> None` — [L12](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/logger.py#L12)

## Source

> [!example]- MyProjects/PassiveMarketInstabilityStrategy/models/logger.py (20 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> # endregion
>
> from domain.models import PassivePressureSignal, PortfolioTargets
>
>
> class PortfolioLogger:
>     def __init__(self, algorithm: QCAlgorithm):
>         self._algo = algorithm
>
>     def log_rebalance(self, signal: PassivePressureSignal, targets: PortfolioTargets) -> None:
>         self._algo.Log(
>             f"REBALANCE | {signal.date.date()} | "
>             f"p(t)={signal.passive_share:.3f} | "
>             f"avg_quintile={signal.avg_pressure_quintile:.1f} | "
>             f"overlay={'ON' if signal.overlay_active else 'OFF'} | "
>             f"scale={signal.exposure_scale:.2f}"
>         )
> ```
