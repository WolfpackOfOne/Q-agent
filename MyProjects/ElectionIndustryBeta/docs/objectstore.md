# ObjectStore schemas

Namespace: `electionbeta/`. All three keys are written by `models/logger.py` at `OnEndOfAlgorithm` and are part of the stable contract — do not rename without a migration plan.

## `electionbeta/daily_snapshots.csv`

One row per scheduled rebalance (skipped during warmup).

| Column | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Trading date of the rebalance |
| `nav` | float | `algorithm.Portfolio.TotalPortfolioValue` |
| `gross_exposure` | float | Σ\|target_weight\| over the universe |
| `n_long` | int | # ETFs with positive target weight |
| `n_short` | int | # ETFs with negative target weight |
| `p_trump` | float | Most recent Polymarket Trump win probability ≤ `date` |
| `delta_p` | float | `p_trump` – previous bundled observation |

## `electionbeta/positions.csv`

One row per (rebalance date, non-zero-weight ticker).

| Column | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Trading date |
| `symbol` | str | Ticker (matches `domain/config.UNIVERSE`) |
| `quantity` | float | Current holding quantity (post-`SetHoldings`) |
| `price` | float | Current Securities[symbol].Price |
| `target_weight` | float | Portfolio weight assigned this rebalance |

## `electionbeta/trades.csv`

One row per fill (from `OnOrderEvent`, status = Filled).

| Column | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Fill date |
| `symbol` | str | Ticker |
| `action` | str | "BUY" or "SELL" (sign of fill quantity) |
| `quantity` | float | Fill quantity (absolute or signed — value is `OrderEvent.FillQuantity`, signed) |
| `price` | float | Fill price |

## Reading in a research notebook

```python
from io import StringIO
import pandas as pd

def _read(key: str) -> pd.DataFrame:
    return pd.read_csv(StringIO(qb.ObjectStore.Read(key)), parse_dates=["date"])

snapshots = _read("electionbeta/daily_snapshots.csv")
positions = _read("electionbeta/positions.csv")
trades    = _read("electionbeta/trades.csv")
```
