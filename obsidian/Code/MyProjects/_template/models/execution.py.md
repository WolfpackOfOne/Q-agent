---
path: "MyProjects/_template/models/execution.py"
hub: "_template"
layer: "Organism"
lines: 46
tags:
  - "code/python"
  - "projects/_template"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/models/execution.py"
---
# execution.py

`MyProjects/_template/models/execution.py` · hub [[Hubs/Projects/_template|_template]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/models/execution.py)

> [!warning] Could not parse
> invalid syntax (line 8)
## Source

> [!example]- MyProjects/_template/models/execution.py (46 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> from domain.config import *
> from domain.models import *
> # endregion
>
>
> class {{STRATEGY_NAME}}ExecutionModel(ExecutionModel):
>     """
>     Execution model for {{STRATEGY_NAME}}.
>
>     Executes portfolio targets with {{EXECUTION_DESCRIPTION}}.
>
>     Layer: ORGANISM (orchestrates order execution)
>     Dependencies: domain.config, domain.models
>     """
>
>     def __init__(self):
>         # TODO: Initialize execution parameters
>         pass
>
>     def Execute(self, algorithm: QCAlgorithm, targets: List[PortfolioTarget]):
>         """
>         Execute portfolio targets.
>
>         Args:
>             algorithm: The algorithm instance
>             targets: List of portfolio targets
>         """
>         for target in targets:
>             # TODO: Implement execution logic
>             # 1. Calculate order quantity
>             # 2. Determine order type (market, limit, etc.)
>             # 3. Submit order
>
>             # Example: Simple market order
>             # security = algorithm.Securities[target.Symbol]
>             # quantity = target.Quantity - security.Holdings.Quantity
>             # if quantity != 0:
>             #     algorithm.MarketOrder(target.Symbol, quantity)
>             pass
>
>     def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
>         """Handle universe changes."""
>         pass
> ```
