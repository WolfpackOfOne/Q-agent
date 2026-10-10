---
path: "MyProjects/_template/models/portfolio.py"
hub: "_template"
layer: "Organism"
lines: 45
tags:
  - "code/python"
  - "projects/_template"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/models/portfolio.py"
---
# portfolio.py

`MyProjects/_template/models/portfolio.py` · hub [[Hubs/Projects/_template|_template]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/models/portfolio.py)

> [!warning] Could not parse
> invalid syntax (line 8)
## Source

> [!example]- MyProjects/_template/models/portfolio.py (45 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> from domain.config import *
> from domain.models import *
> # endregion
>
>
> class {{STRATEGY_NAME}}PortfolioModel(PortfolioConstructionModel):
>     """
>     Portfolio construction for {{STRATEGY_NAME}}.
>
>     Converts insights to portfolio targets with {{PORTFOLIO_DESCRIPTION}}.
>
>     Layer: ORGANISM (orchestrates portfolio construction)
>     Dependencies: domain.config, domain.models
>     """
>
>     def __init__(self):
>         # TODO: Initialize portfolio construction parameters
>         pass
>
>     def CreateTargets(self, algorithm: QCAlgorithm, insights: List[Insight]) -> List[PortfolioTarget]:
>         """
>         Convert insights to portfolio targets.
>
>         Args:
>             algorithm: The algorithm instance
>             insights: List of alpha insights
>
>         Returns:
>             List[PortfolioTarget]: Position targets
>         """
>         targets = []
>
>         # TODO: Implement portfolio construction
>         # 1. Process insights
>         # 2. Apply risk constraints (use pure functions from domain/)
>         # 3. Generate targets
>
>         return targets
>
>     def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
>         """Handle universe changes."""
>         pass
> ```
