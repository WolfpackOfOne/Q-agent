# FundamentalsPortfolio - ObjectStore Schema

## Overview

This document describes the data persisted to ObjectStore during backtests.

**Namespace**: `fundamentals_portfolio/`

## Files

| File | Description |
|------|--------------|
| `fundamentals_portfolio/daily_snapshots.csv` | Per-rebalance portfolio metrics |
| `fundamentals_portfolio/positions.csv` | Position-level data at each rebalance |
| `fundamentals_portfolio/trades.csv` | Trade executions (from `OnOrderEvent`) |

## Schema Stability

ObjectStore keys and column names should remain stable across backtests. When making changes:
- **Add** new columns at the end
- **Never** rename or remove existing columns
- **Document** changes in this file

## daily_snapshots.csv

Logged once per quarterly rebalance (not daily, despite the filename —
kept for consistency with the shared `PortfolioLogger` convention).

| Column | Type | Description |
|--------|------|--------------|
| `date` | date | Rebalance date (YYYY-MM-DD) |
| `nav` | float | Net asset value at rebalance |
| `gross_exposure` | float | sum(abs(target weights)) |
| `n_long` | int | Count of positive-weight targets |
| `n_short` | int | Count of negative-weight targets |

## positions.csv

Position-level data, one row per symbol per rebalance.

| Column | Type | Description |
|--------|------|--------------|
| `date` | date | Rebalance date (YYYY-MM-DD) |
| `symbol` | string | Ticker symbol |
| `quantity` | float | Position quantity at time of logging |
| `price` | float | Last price |
| `target_weight` | float | Target weight assigned this rebalance |

## trades.csv

Trade execution records, logged from `OnOrderEvent` on every fill.

| Column | Type | Description |
|--------|------|--------------|
| `date` | date | Trade date (YYYY-MM-DD) |
| `symbol` | string | Ticker symbol |
| `action` | string | BUY, SELL |
| `quantity` | float | Fill quantity |
| `price` | float | Fill price |

## Reading in Research Notebook

```python
from io import StringIO
import pandas as pd

# Initialize QuantBook
qb = QuantBook()

snapshots_str = qb.ObjectStore.Read("fundamentals_portfolio/daily_snapshots.csv")
df_snapshots = pd.read_csv(StringIO(snapshots_str), parse_dates=['date'])

positions_str = qb.ObjectStore.Read("fundamentals_portfolio/positions.csv")
df_positions = pd.read_csv(StringIO(positions_str), parse_dates=['date'])

trades_str = qb.ObjectStore.Read("fundamentals_portfolio/trades.csv")
df_trades = pd.read_csv(StringIO(trades_str), parse_dates=['date'])
```

## Adding New Output Files

When adding new ObjectStore outputs:

1. Add key to `domain/config.py`
2. Add logging method to `models/logger.py`
3. Document schema in this file
4. Update research notebook examples
