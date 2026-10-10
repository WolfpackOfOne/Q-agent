---
path: "MyProjects/Alpha101Portfolio/models/logger.py"
hub: "Alpha101Portfolio"
layer: "Organism"
lines: 57
tags:
  - "code/python"
  - "projects/Alpha101Portfolio"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py"
---
# logger.py

`MyProjects/Alpha101Portfolio/models/logger.py` · hub [[Hubs/Projects/Alpha101Portfolio|Alpha101Portfolio]] · layer **Organism** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py)

## Dependencies

**Imports (workspace):** [[Code/MyProjects/Alpha101Portfolio/domain/config.py|config.py]]

**Imports (external):** [[Indexes/External packages#AlgorithmImports|AlgorithmImports]]

**Imported by:** [[Code/MyProjects/Alpha101Portfolio/models/__init__.py|__init__.py]]

## Classes

### class `PortfolioLogger`

[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L8)

Logging organism for Alpha101Portfolio.

Accumulates per-rebalance snapshots, position rows, and fills in memory, then
writes three CSVs to the ObjectStore when the algorithm ends. Persisting data
for research analysis rather than trading decisions, so nothing here feeds
back into the book.

Layer: ORGANISM (orchestrates persistence).

- `def __init__(self, algorithm: QCAlgorithm)` — [L20](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L20)
- `def log_daily_snapshot(self, date, nav: float, gross_exposure: float, n_long: int, n_short: int) -> None` — [L31](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L31)
- `def log_position(self, date, symbol: str, quantity: float, price: float, target_weight: float) -> None` — [L34](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L34)
- `def log_trade(self, date, symbol, action: str, quantity: float, price: float) -> None` — [L37](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L37)
- `def save_all(self) -> None` — [L44](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L44)
- `def _save(self, filename: str, header: str, rows: list[str]) -> None` — [L51](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/models/logger.py#L51)

## Source

> [!example]- MyProjects/Alpha101Portfolio/models/logger.py (57 lines)
> ```python
> # region imports
> from AlgorithmImports import *
>
> from domain.config import OBJECTSTORE_NAMESPACE
> # endregion
>
>
> class PortfolioLogger:
>     """
>     Logging organism for Alpha101Portfolio.
>
>     Accumulates per-rebalance snapshots, position rows, and fills in memory, then
>     writes three CSVs to the ObjectStore when the algorithm ends. Persisting data
>     for research analysis rather than trading decisions, so nothing here feeds
>     back into the book.
>
>     Layer: ORGANISM (orchestrates persistence).
>     """
>
>     def __init__(self, algorithm: QCAlgorithm):
>         self.algorithm = algorithm
>         self.namespace = OBJECTSTORE_NAMESPACE
>         self._snapshots: list[str] = []
>         self._positions: list[str] = []
>         self._trades: list[str] = []
>
>     # ------------------------------------------------------------------
>     # Collection
>     # ------------------------------------------------------------------
>
>     def log_daily_snapshot(self, date, nav: float, gross_exposure: float, n_long: int, n_short: int) -> None:
>         self._snapshots.append(f"{date:%Y-%m-%d},{nav},{gross_exposure},{n_long},{n_short}")
>
>     def log_position(self, date, symbol: str, quantity: float, price: float, target_weight: float) -> None:
>         self._positions.append(f"{date:%Y-%m-%d},{symbol},{quantity},{price},{target_weight}")
>
>     def log_trade(self, date, symbol, action: str, quantity: float, price: float) -> None:
>         self._trades.append(f"{date:%Y-%m-%d},{symbol},{action},{quantity},{price}")
>
>     # ------------------------------------------------------------------
>     # Persistence
>     # ------------------------------------------------------------------
>
>     def save_all(self) -> None:
>         self._save("daily_snapshots.csv", "date,nav,gross_exposure,n_long,n_short", self._snapshots)
>         self._save("positions.csv", "date,symbol,quantity,price,target_weight", self._positions)
>         self._save("trades.csv", "date,symbol,action,quantity,price", self._trades)
>         self.algorithm.Log(f"Saved {len(self._snapshots)} snapshots, {len(self._positions)} positions, "
>                            f"{len(self._trades)} trades to ObjectStore")
>
>     def _save(self, filename: str, header: str, rows: list[str]) -> None:
>         key = f"{self.namespace}/{filename}"
>         try:
>             self.algorithm.ObjectStore.Save(key, "\n".join([header] + rows) + "\n")
>         except Exception as e:
>             self.algorithm.Error(f"[PortfolioLogger] could not save {key}: {type(e).__name__}: {e}")
> ```
