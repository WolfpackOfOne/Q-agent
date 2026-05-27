# region imports
from AlgorithmImports import *
import csv
from io import StringIO
from datetime import datetime

from domain.config import OBJECTSTORE_NAMESPACE
# endregion


class PortfolioLogger:
    """
    Logging facade for ElectionIndustryBeta.

    Buffers snapshots/positions/trades in memory; writes three CSVs to
    ObjectStore in OnEndOfAlgorithm.

    Layer: ORGANISM (orchestrates logging).

    ObjectStore keys:
      electionbeta/daily_snapshots.csv
      electionbeta/positions.csv
      electionbeta/trades.csv
    """

    def __init__(self, algorithm: QCAlgorithm):
        self.algorithm = algorithm
        self.namespace = OBJECTSTORE_NAMESPACE
        self._snapshots: list[dict] = []
        self._positions: list[dict] = []
        self._trades: list[dict] = []

    def log_daily_snapshot(self, date: datetime, nav: float, **kwargs) -> None:
        self._snapshots.append({
            "date": date.strftime("%Y-%m-%d"),
            "nav": nav,
            **kwargs,
        })

    def log_position(self, date: datetime, symbol: str, quantity: float,
                     price: float, **kwargs) -> None:
        self._positions.append({
            "date": date.strftime("%Y-%m-%d"),
            "symbol": str(symbol),
            "quantity": quantity,
            "price": price,
            **kwargs,
        })

    def log_trade(self, date: datetime, symbol: str, action: str,
                  quantity: float, price: float, **kwargs) -> None:
        self._trades.append({
            "date": date.strftime("%Y-%m-%d"),
            "symbol": str(symbol),
            "action": action,
            "quantity": quantity,
            "price": price,
            **kwargs,
        })

    def save_all(self) -> None:
        self._save_csv(f"{self.namespace}/daily_snapshots.csv", self._snapshots)
        self._save_csv(f"{self.namespace}/positions.csv", self._positions)
        self._save_csv(f"{self.namespace}/trades.csv", self._trades)
        self.algorithm.Log(
            f"[{self.namespace}] Saved {len(self._snapshots)} snapshots, "
            f"{len(self._positions)} positions, {len(self._trades)} trades"
        )

    def _save_csv(self, key: str, rows: list[dict]) -> None:
        if not rows:
            return
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        self.algorithm.ObjectStore.Save(key, buffer.getvalue())
