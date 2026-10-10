---
path: "MyProjects/PassiveMarketInstabilityStrategy/domain/models.py"
hub: "PassiveMarketInstabilityStrategy"
layer: "Molecule / Atom"
lines: 24
tags:
  - "code/python"
  - "projects/PassiveMarketInstabilityStrategy"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py"
---
# models.py

`MyProjects/PassiveMarketInstabilityStrategy/domain/models.py` · hub [[Hubs/Projects/PassiveMarketInstabilityStrategy|PassiveMarketInstabilityStrategy]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py)

## Purpose

Domain data-transfer objects for PassiveMarketInstabilityStrategy.

## Dependencies


**Imports (external):** [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/alpha.py|alpha.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/execution.py|execution.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/logger.py|logger.py]], [[Code/MyProjects/PassiveMarketInstabilityStrategy/models/portfolio.py|portfolio.py]]

## Classes

### class `PassivePressureSignal`

[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py#L8)

Snapshot of passive-pressure diagnostics at a single rebalance date.


### class `PortfolioTargets`

[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstabilityStrategy/domain/models.py#L19)

Target weights produced by the portfolio model.


## Source

> [!example]- MyProjects/PassiveMarketInstabilityStrategy/domain/models.py (24 lines)
> ```python
> """Domain data-transfer objects for PassiveMarketInstabilityStrategy."""
>
> from dataclasses import dataclass, field
> from typing import Dict
>
>
> @dataclass
> class PassivePressureSignal:
>     """Snapshot of passive-pressure diagnostics at a single rebalance date."""
>     date: object                           # datetime
>     passive_share: float                   # logistic p(t) estimate
>     avg_pressure_quintile: float           # mean pressure quintile across universe
>     high_pressure_fraction: float          # fraction of universe in top two quintiles
>     overlay_active: bool                   # True when risk overlay is triggered
>     exposure_scale: float                  # target gross exposure scalar (0.0–1.0)
>
>
> @dataclass
> class PortfolioTargets:
>     """Target weights produced by the portfolio model."""
>     weights: Dict[str, float] = field(default_factory=dict)
>     exposure_scale: float = 1.0
>     diagnostics: Dict[str, float] = field(default_factory=dict)
> ```
