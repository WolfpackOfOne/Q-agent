---
path: "MyProjects/ElectionIndustryBeta/models/portfolio.py"
hub: "ElectionIndustryBeta"
layer: "Organism"
lines: 27
tags:
  - "code/python"
  - "projects/ElectionIndustryBeta"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/portfolio.py"
---
# portfolio.py

`MyProjects/ElectionIndustryBeta/models/portfolio.py` · hub [[Hubs/Projects/ElectionIndustryBeta|ElectionIndustryBeta]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/portfolio.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/ElectionIndustryBeta/domain/config.py|config.py]], [[Code/MyProjects/ElectionIndustryBeta/domain/signals/election_beta.py|election_beta.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/MyProjects/ElectionIndustryBeta/models/__init__.py|__init__.py]]

## Classes

### class `ElectionBetaPortfolio`

[line 10](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/portfolio.py#L10)

Portfolio construction organism for ElectionIndustryBeta.

Converts a Series of per-ticker betas into a target-weight dict.
Long top-K (largest beta), short bottom-K (smallest beta), weights
proportional to beta, normalised to gross exposure 100%.

Layer: ORGANISM (orchestrates portfolio construction).

- `def __init__(self, k: int=K)` — [L21](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/portfolio.py#L21)
- `def to_targets(self, betas: pd.Series) -> dict[str, float]` — [L24](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/portfolio.py#L24)  
  Build target-weight dict for the full universe.

## Source

> [!example]- MyProjects/ElectionIndustryBeta/models/portfolio.py (27 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> import pandas as pd
>
> from domain.config import K
> from domain.signals.election_beta import top_bottom_k_betaweighted
> # endregion
>
>
> class ElectionBetaPortfolio:
>     """
>     Portfolio construction organism for ElectionIndustryBeta.
>
>     Converts a Series of per-ticker betas into a target-weight dict.
>     Long top-K (largest beta), short bottom-K (smallest beta), weights
>     proportional to beta, normalised to gross exposure 100%.
>
>     Layer: ORGANISM (orchestrates portfolio construction).
>     """
>
>     def __init__(self, k: int = K):
>         self.k = k
>
>     def to_targets(self, betas: pd.Series) -> dict[str, float]:
>         """Build target-weight dict for the full universe."""
>         return top_bottom_k_betaweighted(betas, self.k)
> ```
