---
path: "MyProjects/ElectionIndustryBeta/models/logger.py"
hub: "ElectionIndustryBeta"
layer: "Organism"
lines: 78
tags:
  - "code/python"
  - "projects/ElectionIndustryBeta"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py"
---
# logger.py

`MyProjects/ElectionIndustryBeta/models/logger.py` · hub [[Hubs/Projects/ElectionIndustryBeta|ElectionIndustryBeta]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/ElectionIndustryBeta/domain/config.py|config.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]], [[Indexes/External packages#csv|csv]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#io|io]]

**Imported by:** [[Code/MyProjects/ElectionIndustryBeta/models/__init__.py|__init__.py]]

## Classes

### class `PortfolioLogger`

[line 11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L11)

Logging facade for ElectionIndustryBeta.

Buffers snapshots/positions/trades in memory; writes three CSVs to
ObjectStore in OnEndOfAlgorithm.

Layer: ORGANISM (orchestrates logging).

ObjectStore keys:
  electionbeta/daily_snapshots.csv
  electionbeta/positions.csv
  electionbeta/trades.csv

- `def __init__(self, algorithm: QCAlgorithm)` — [L26](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L26)
- `def log_daily_snapshot(self, date: datetime, nav: float, **kwargs) -> None` — [L33](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L33)
- `def log_position(self, date: datetime, symbol: str, quantity: float, price: float, **kwargs) -> None` — [L40](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L40)
- `def log_trade(self, date: datetime, symbol: str, action: str, quantity: float, price: float, **kwargs) -> None` — [L50](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L50)
- `def save_all(self) -> None` — [L61](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L61)
- `def _save_csv(self, key: str, rows: list[dict]) -> None` — [L70](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/models/logger.py#L70)

## Source

> [!example]- MyProjects/ElectionIndustryBeta/models/logger.py (78 lines)
> ```python
> # region imports
> from AlgorithmImports import *
> import csv
> from io import StringIO
> from datetime import datetime
>
> from domain.config import OBJECTSTORE_NAMESPACE
> # endregion
>
>
> class PortfolioLogger:
>     """
>     Logging facade for ElectionIndustryBeta.
>
>     Buffers snapshots/positions/trades in memory; writes three CSVs to
>     ObjectStore in OnEndOfAlgorithm.
>
>     Layer: ORGANISM (orchestrates logging).
>
>     ObjectStore keys:
>       electionbeta/daily_snapshots.csv
>       electionbeta/positions.csv
>       electionbeta/trades.csv
>     """
>
>     def __init__(self, algorithm: QCAlgorithm):
>         self.algorithm = algorithm
>         self.namespace = OBJECTSTORE_NAMESPACE
>         self._snapshots: list[dict] = []
>         self._positions: list[dict] = []
>         self._trades: list[dict] = []
>
>     def log_daily_snapshot(self, date: datetime, nav: float, **kwargs) -> None:
>         self._snapshots.append({
>             "date": date.strftime("%Y-%m-%d"),
>             "nav": nav,
>             **kwargs,
>         })
>
>     def log_position(self, date: datetime, symbol: str, quantity: float,
>                      price: float, **kwargs) -> None:
>         self._positions.append({
>             "date": date.strftime("%Y-%m-%d"),
>             "symbol": str(symbol),
>             "quantity": quantity,
>             "price": price,
>             **kwargs,
>         })
>
>     def log_trade(self, date: datetime, symbol: str, action: str,
>                   quantity: float, price: float, **kwargs) -> None:
>         self._trades.append({
>             "date": date.strftime("%Y-%m-%d"),
>             "symbol": str(symbol),
>             "action": action,
>             "quantity": quantity,
>             "price": price,
>             **kwargs,
>         })
>
>     def save_all(self) -> None:
>         self._save_csv(f"{self.namespace}/daily_snapshots.csv", self._snapshots)
>         self._save_csv(f"{self.namespace}/positions.csv", self._positions)
>         self._save_csv(f"{self.namespace}/trades.csv", self._trades)
>         self.algorithm.Log(
>             f"[{self.namespace}] Saved {len(self._snapshots)} snapshots, "
>             f"{len(self._positions)} positions, {len(self._trades)} trades"
>         )
>
>     def _save_csv(self, key: str, rows: list[dict]) -> None:
>         if not rows:
>             return
>         buffer = StringIO()
>         writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
>         writer.writeheader()
>         writer.writerows(rows)
>         self.algorithm.ObjectStore.Save(key, buffer.getvalue())
> ```
