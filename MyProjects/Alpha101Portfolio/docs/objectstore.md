# Alpha101Portfolio - ObjectStore Schema

The algorithm writes three CSVs to the ObjectStore when a backtest ends. They
exist for research analysis; nothing written here feeds back into trading
decisions.

**Namespace**: `alpha101_portfolio/`

| File | Description |
|------|-------------|
| `alpha101_portfolio/daily_snapshots.csv` | Per-rebalance portfolio metrics |
| `alpha101_portfolio/positions.csv` | Position-level data at each rebalance |
| `alpha101_portfolio/trades.csv` | Trade executions (from `OnOrderEvent`) |

## daily_snapshots.csv

One row per weekly rebalance.

```
date,nav,gross_exposure,n_long,n_short
2022-01-03,1000000.0,1.0,30,30
```

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Rebalance date (first trading day of the week) |
| `nav` | float | Total portfolio value before the rebalance trades |
| `gross_exposure` | float | Sum of absolute target weights (1.0 when fully invested) |
| `n_long` | int | Names in the long decile |
| `n_short` | int | Names in the short decile |

## positions.csv

One row per non-zero target position per rebalance.

```
date,symbol,quantity,price,target_weight
2022-01-03,AAPL,-1200.0,182.01,-0.0167
```

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Rebalance date |
| `symbol` | string | Ticker |
| `quantity` | float | Shares held *before* the rebalance trade |
| `price` | float | Security price at the rebalance |
| `target_weight` | float | Target portfolio weight (negative = short) |

## trades.csv

One row per filled order, from `OnOrderEvent`.

```
date,symbol,action,quantity,price
2022-01-03,AAPL,SELL,-1200.0,182.01
```

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Fill date |
| `symbol` | string | Ticker |
| `action` | string | `BUY` or `SELL` |
| `quantity` | float | Filled quantity (negative for sells) |
| `price` | float | Fill price |

## Reading in a research notebook

```python
from io import StringIO
import pandas as pd

qb = QuantBook()
snapshots = pd.read_csv(StringIO(qb.ObjectStore.Read("alpha101_portfolio/daily_snapshots.csv")),
                        parse_dates=["date"])
positions = pd.read_csv(StringIO(qb.ObjectStore.Read("alpha101_portfolio/positions.csv")),
                        parse_dates=["date"])
trades = pd.read_csv(StringIO(qb.ObjectStore.Read("alpha101_portfolio/trades.csv")),
                     parse_dates=["date"])
```

Local backtests write these under `MyProjects/storage/alpha101_portfolio/`.

## Changing the schema

1. Update `models/logger.py` (the header string and the row format together)
2. Update this file
3. Update any research notebook that reads the affected file
