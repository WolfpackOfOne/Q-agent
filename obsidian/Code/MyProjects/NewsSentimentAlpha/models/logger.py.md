---
path: "MyProjects/NewsSentimentAlpha/models/logger.py"
hub: "NewsSentimentAlpha"
layer: "Organism"
lines: 87
tags:
  - "code/python"
  - "projects/NewsSentimentAlpha"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py"
---
# logger.py

`MyProjects/NewsSentimentAlpha/models/logger.py` · hub [[Hubs/Projects/NewsSentimentAlpha|NewsSentimentAlpha]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/NewsSentimentAlpha/domain/config.py|config.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]], [[Indexes/External packages#csv|csv]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#io|io]]

**Imported by:** [[Code/MyProjects/NewsSentimentAlpha/models/__init__.py|__init__.py]]

## Classes

### class `PortfolioLogger`

[line 10](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L10)

Logging facade for NewsSentimentAlpha.

Persists data to ObjectStore for research analysis.

Layer: ORGANISM (orchestrates logging)
Dependencies: domain.config

ObjectStore Keys:
- {namespace}/daily_snapshots.csv
- {namespace}/positions.csv
- {namespace}/trades.csv

- `def __init__(self, algorithm: QCAlgorithm)` — [L25](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L25)
- `def log_daily_snapshot(self, date: datetime, nav: float, **kwargs)` — [L34](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L34)  
  Log daily portfolio snapshot.
- `def log_position(self, date: datetime, symbol: str, quantity: float, price: float, **kwargs)` — [L43](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L43)  
  Log position state.
- `def log_trade(self, date: datetime, symbol: str, action: str, quantity: float, price: float, **kwargs)` — [L54](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L54)  
  Log trade execution.
- `def save_all(self)` — [L66](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L66)  
  Save all buffered data to ObjectStore.
- `def _save_csv(self, key: str, rows: list)` — [L76](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/models/logger.py#L76)  
  Save rows to ObjectStore as CSV.

## Source

> [!example]- MyProjects/NewsSentimentAlpha/models/logger.py (87 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> import csv
> from io import StringIO
> from datetime import datetime
> from domain.config import OBJECTSTORE_NAMESPACE
> # endregion
>
>
> class PortfolioLogger:
>     """
>     Logging facade for NewsSentimentAlpha.
>
>     Persists data to ObjectStore for research analysis.
>
>     Layer: ORGANISM (orchestrates logging)
>     Dependencies: domain.config
>
>     ObjectStore Keys:
>     - {namespace}/daily_snapshots.csv
>     - {namespace}/positions.csv
>     - {namespace}/trades.csv
>     """
>
>     def __init__(self, algorithm: QCAlgorithm):
>         self.algorithm = algorithm
>         self.namespace = OBJECTSTORE_NAMESPACE
>
>         # Data buffers
>         self._snapshots = []
>         self._positions = []
>         self._trades = []
>
>     def log_daily_snapshot(self, date: datetime, nav: float, **kwargs):
>         """Log daily portfolio snapshot."""
>         row = {
>             'date': date.strftime('%Y-%m-%d'),
>             'nav': nav,
>             **kwargs
>         }
>         self._snapshots.append(row)
>
>     def log_position(self, date: datetime, symbol: str, quantity: float, price: float, **kwargs):
>         """Log position state."""
>         row = {
>             'date': date.strftime('%Y-%m-%d'),
>             'symbol': str(symbol),
>             'quantity': quantity,
>             'price': price,
>             **kwargs
>         }
>         self._positions.append(row)
>
>     def log_trade(self, date: datetime, symbol: str, action: str, quantity: float, price: float, **kwargs):
>         """Log trade execution."""
>         row = {
>             'date': date.strftime('%Y-%m-%d'),
>             'symbol': str(symbol),
>             'action': action,
>             'quantity': quantity,
>             'price': price,
>             **kwargs
>         }
>         self._trades.append(row)
>
>     def save_all(self):
>         """Save all buffered data to ObjectStore."""
>         self._save_csv(f"{self.namespace}/daily_snapshots.csv", self._snapshots)
>         self._save_csv(f"{self.namespace}/positions.csv", self._positions)
>         self._save_csv(f"{self.namespace}/trades.csv", self._trades)
>
>         self.algorithm.Log(f"Saved {len(self._snapshots)} snapshots, "
>                           f"{len(self._positions)} positions, "
>                           f"{len(self._trades)} trades to ObjectStore")
>
>     def _save_csv(self, key: str, rows: list):
>         """Save rows to ObjectStore as CSV."""
>         if not rows:
>             return
>
>         buffer = StringIO()
>         writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
>         writer.writeheader()
>         writer.writerows(rows)
>
>         self.algorithm.ObjectStore.Save(key, buffer.getvalue())
> ```
