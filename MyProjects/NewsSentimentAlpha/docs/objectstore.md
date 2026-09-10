# NewsSentimentAlpha - ObjectStore Schema

## Overview

This document describes the data persisted to ObjectStore during backtests.

**Namespace**: `news_sentiment_alpha/`

## Files

| File | Description |
|------|-------------|
| `news_sentiment_alpha/daily_snapshots.csv` | Daily portfolio metrics |
| `news_sentiment_alpha/positions.csv` | Position-level data |
| `news_sentiment_alpha/trades.csv` | Trade executions |

## Schema Stability

ObjectStore keys and column names should remain stable across backtests. When making changes:
- **Add** new columns at the end
- **Never** rename or remove existing columns
- **Document** changes in this file

## daily_snapshots.csv

Daily portfolio-level metrics.

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Trading date (YYYY-MM-DD) |
| `nav` | float | Net asset value |
| `gross_exposure` | float | sum(abs(weight)) across targets |
| `n_long` | int | Count of positive-weight positions |
| `n_short` | int | Count of negative-weight positions (0 until the ranked long/short signal is implemented) |

## positions.csv

Position-level data, one row per symbol per day.

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Trading date (YYYY-MM-DD) |
| `symbol` | string | Ticker symbol |
| `quantity` | float | Position quantity |
| `price` | float | Last price |
| `target_weight` | float | Target weight from portfolio construction |

## trades.csv

Trade execution records.

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Trade date (YYYY-MM-DD) |
| `symbol` | string | Ticker symbol |
| `action` | string | BUY, SELL |
| `quantity` | float | Trade quantity |
| `price` | float | Execution price |

## Reading in Research Notebook

```python
from io import StringIO
import pandas as pd

# Initialize QuantBook
qb = QuantBook()

# Read daily snapshots
snapshots_str = qb.ObjectStore.Read("news_sentiment_alpha/daily_snapshots.csv")
df_snapshots = pd.read_csv(StringIO(snapshots_str), parse_dates=['date'])

# Read positions
positions_str = qb.ObjectStore.Read("news_sentiment_alpha/positions.csv")
df_positions = pd.read_csv(StringIO(positions_str), parse_dates=['date'])

# Read trades
trades_str = qb.ObjectStore.Read("news_sentiment_alpha/trades.csv")
df_trades = pd.read_csv(StringIO(trades_str), parse_dates=['date'])
```

## Adding New Output Files

When adding new ObjectStore outputs:

1. Add key to `domain/config.py`
2. Add logging method to `models/logger.py`
3. Document schema in this file
4. Update research notebook examples
