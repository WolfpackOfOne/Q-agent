---
path: "MyProjects/ElectionIndustryBeta/models/execution.py"
hub: "ElectionIndustryBeta"
layer: "Organism"
lines: 25
tags:
  - "code/python"
  - "projects/ElectionIndustryBeta"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/execution.py"
---
# execution.py

`MyProjects/ElectionIndustryBeta/models/execution.py` · hub [[Hubs/Projects/ElectionIndustryBeta|ElectionIndustryBeta]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/execution.py)

## Dependencies


**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]]

**Imported by:** [[Code/MyProjects/ElectionIndustryBeta/models/__init__.py|__init__.py]]

## Classes

### class `MarketOrderExecutor`

[line 6](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/execution.py#L6)

Execution organism for ElectionIndustryBeta.

Applies target weights via SetHoldings — market orders only.
Tickers absent from `targets` (or with weight 0.0) are liquidated.

Layer: ORGANISM (orchestrates order execution).

- `def execute(self, algorithm: QCAlgorithm, universe: list[str], targets: dict[str, float]) -> None` — [L16](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/execution.py#L16)

## Source

> [!example]- MyProjects/ElectionIndustryBeta/models/execution.py (25 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> # endregion
>
>
> class MarketOrderExecutor:
>     """
>     Execution organism for ElectionIndustryBeta.
>
>     Applies target weights via SetHoldings — market orders only.
>     Tickers absent from `targets` (or with weight 0.0) are liquidated.
>
>     Layer: ORGANISM (orchestrates order execution).
>     """
>
>     def execute(
>         self,
>         algorithm: QCAlgorithm,
>         universe: list[str],
>         targets: dict[str, float],
>     ) -> None:
>         for ticker in universe:
>             weight = targets.get(ticker, 0.0)
>             algorithm.SetHoldings(ticker, weight)
> ```
