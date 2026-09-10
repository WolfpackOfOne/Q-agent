# region imports
from AlgorithmImports import *
import csv
from io import StringIO
from datetime import datetime
from domain.config import OBJECTSTORE_NAMESPACE
# endregion


class PortfolioLogger:
    """
    Logging facade for NewsSentimentAlpha.

    Persists data to ObjectStore for research analysis.

    Layer: ORGANISM (orchestrates logging)
    Dependencies: domain.config

    ObjectStore Keys:
    - {namespace}/daily_snapshots.csv
    - {namespace}/positions.csv
    - {namespace}/trades.csv
    """

    def __init__(self, algorithm: QCAlgorithm):
        self.algorithm = algorithm
        self.namespace = OBJECTSTORE_NAMESPACE

        # Data buffers
        self._snapshots = []
        self._positions = []
        self._trades = []

    def log_daily_snapshot(self, date: datetime, nav: float, **kwargs):
        """Log daily portfolio snapshot."""
        row = {
            'date': date.strftime('%Y-%m-%d'),
            'nav': nav,
            **kwargs
        }
        self._snapshots.append(row)

    def log_position(self, date: datetime, symbol: str, quantity: float, price: float, **kwargs):
        """Log position state."""
        row = {
            'date': date.strftime('%Y-%m-%d'),
            'symbol': str(symbol),
            'quantity': quantity,
            'price': price,
            **kwargs
        }
        self._positions.append(row)

    def log_trade(self, date: datetime, symbol: str, action: str, quantity: float, price: float, **kwargs):
        """Log trade execution."""
        row = {
            'date': date.strftime('%Y-%m-%d'),
            'symbol': str(symbol),
            'action': action,
            'quantity': quantity,
            'price': price,
            **kwargs
        }
        self._trades.append(row)

    def save_all(self):
        """Save all buffered data to ObjectStore."""
        self._save_csv(f"{self.namespace}/daily_snapshots.csv", self._snapshots)
        self._save_csv(f"{self.namespace}/positions.csv", self._positions)
        self._save_csv(f"{self.namespace}/trades.csv", self._trades)

        self.algorithm.Log(f"Saved {len(self._snapshots)} snapshots, "
                          f"{len(self._positions)} positions, "
                          f"{len(self._trades)} trades to ObjectStore")

    def _save_csv(self, key: str, rows: list):
        """Save rows to ObjectStore as CSV."""
        if not rows:
            return

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

        self.algorithm.ObjectStore.Save(key, buffer.getvalue())
