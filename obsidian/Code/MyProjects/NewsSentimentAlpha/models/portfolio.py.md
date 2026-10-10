---
path: "MyProjects/NewsSentimentAlpha/models/portfolio.py"
hub: "NewsSentimentAlpha"
layer: "Organism"
lines: 48
tags:
  - "code/python"
  - "projects/NewsSentimentAlpha"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/portfolio.py"
---
# portfolio.py

`MyProjects/NewsSentimentAlpha/models/portfolio.py` · hub [[Hubs/Projects/NewsSentimentAlpha|NewsSentimentAlpha]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/portfolio.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/NewsSentimentAlpha/domain/config.py|config.py]], [[Code/MyProjects/NewsSentimentAlpha/domain/signals/news_tone.py|news_tone.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]]

**Imported by:** [[Code/MyProjects/NewsSentimentAlpha/models/__init__.py|__init__.py]]

## Classes

### class `NewsToneLongShortPortfolio`

[line 9](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/portfolio.py#L9)

Portfolio construction organism for NewsSentimentAlpha.

Converts raw tone-z scores into long/short targets: a selective
top/bottom slice of whichever tickers have a signal today (at least
`n_floor` names per side, to avoid a concentrated single-stock bet),
weighted by signal magnitude within each side. Delegates the ranking
math to the pure shared signal at `domain/signals/news_tone.py`
(symlink to MyProjects/shared/signals/).

Layer: ORGANISM (orchestrates portfolio construction).

- `def __init__(self, min_names: int=MIN_NAMES, frac: float=SELECT_FRAC, n_floor: int=N_FLOOR)` — [L23](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/portfolio.py#L23)
- `def to_targets(self, signals: dict[str, float]) -> dict[str, float]` — [L33](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/portfolio.py#L33)  
  Ranked, magnitude-weighted long/short targets from raw tone-z scores.

## Source

> [!example]- MyProjects/NewsSentimentAlpha/models/portfolio.py (48 lines)
> ```python
> # region imports
> from AlgorithmImports import *
>
> from domain.config import MIN_NAMES, SELECT_FRAC, N_FLOOR
> from domain.signals.news_tone import rank_magnitude_weighted_targets
> # endregion
>
>
> class NewsToneLongShortPortfolio:
>     """
>     Portfolio construction organism for NewsSentimentAlpha.
>
>     Converts raw tone-z scores into long/short targets: a selective
>     top/bottom slice of whichever tickers have a signal today (at least
>     `n_floor` names per side, to avoid a concentrated single-stock bet),
>     weighted by signal magnitude within each side. Delegates the ranking
>     math to the pure shared signal at `domain/signals/news_tone.py`
>     (symlink to MyProjects/shared/signals/).
>
>     Layer: ORGANISM (orchestrates portfolio construction).
>     """
>
>     def __init__(
>         self,
>         min_names: int = MIN_NAMES,
>         frac: float = SELECT_FRAC,
>         n_floor: int = N_FLOOR,
>     ):
>         self.min_names = min_names
>         self.frac = frac
>         self.n_floor = n_floor
>
>     def to_targets(self, signals: dict[str, float]) -> dict[str, float]:
>         """Ranked, magnitude-weighted long/short targets from raw tone-z scores.
>
>         Args:
>             signals: dict[ticker, tone_z] from NewsToneAlpha.
>
>         Returns:
>             dict[ticker, weight]: see rank_magnitude_weighted_targets.
>             Empty dict (flat) if fewer than `min_names` tickers have a
>             signal, or if the cross-section is too narrow to support
>             `n_floor` names on both sides.
>         """
>         return rank_magnitude_weighted_targets(
>             signals, frac=self.frac, min_names=self.min_names, n_floor=self.n_floor
>         )
> ```
