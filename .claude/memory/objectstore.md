# ObjectStore

Durable QuantConnect ObjectStore keys, schema notes, research read patterns, and migration cautions.

Do not change ObjectStore keys without a migration plan.

## ElectionIndustryBeta — `electionbeta/` namespace

Project: `MyProjects/ElectionIndustryBeta`. Three keys written by `models/logger.py` at `OnEndOfAlgorithm`. Full schemas live in the project's `docs/objectstore.md`.

| Key | Granularity | Purpose |
|---|---|---|
| `electionbeta/daily_snapshots.csv` | one row per rebalance | NAV, gross exposure, n_long/n_short, p_trump, delta_p |
| `electionbeta/positions.csv` | one row per (rebalance, non-zero ticker) | quantity, price, target_weight |
| `electionbeta/trades.csv` | one row per `OrderEvent.Filled` | action, signed fill quantity, fill price |

Read in research notebooks with `pd.read_csv(StringIO(qb.ObjectStore.Read(key)), parse_dates=["date"])`.
