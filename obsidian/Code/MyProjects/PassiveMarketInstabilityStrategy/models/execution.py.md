---
path: "MyProjects/PassiveMarketInstabilityStrategy/models/execution.py"
hub: "PassiveMarketInstabilityStrategy"
layer: "Organism"
lines: 15
tags:
  - "code/python"
  - "projects/PassiveMarketInstabilityStrategy"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/execution.py"
---
# execution.py

`MyProjects/PassiveMarketInstabilityStrategy/models/execution.py` · hub [[Hubs/Projects/PassiveMarketInstabilityStrategy|PassiveMarketInstabilityStrategy]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/execution.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py|models.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]]

**Imported by:** [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/__init__.py|__init__.py]]

## Classes

### class `MarketOrderExecutor`

[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/execution.py#L8)

Apply portfolio targets via SetHoldings (market orders).

- `def execute(self, algorithm: QCAlgorithm, targets: PortfolioTargets, symbols: dict) -> None` — [L11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/models/execution.py#L11)

## Source

> [!example]- MyProjects/PassiveMarketInstabilityStrategy/models/execution.py (15 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> # endregion
>
> from domain.models import PortfolioTargets
>
>
> class MarketOrderExecutor:
>     """Apply portfolio targets via SetHoldings (market orders)."""
>
>     def execute(self, algorithm: QCAlgorithm, targets: PortfolioTargets, symbols: dict) -> None:
>         for ticker, weight in targets.weights.items():
>             if ticker in symbols:
>                 algorithm.SetHoldings(symbols[ticker], weight)
> ```
