# Processed ETF Flow Data

Place cleaned ETF flow or ETF flow-pressure proxy tables here.

Every processed file should clearly label official flow data versus proxy data.

Committed snapshot files:

- `broad_market_etf_prices.csv` — yfinance price-volume snapshot for `SPY`, `IVV`, `VOO`, and `VTI`.
- `broad_market_etf_flow_pressure_proxy.csv` — aggregate `volume * return` flow-pressure proxy, not official ETF flow.
- `snapshot_metadata.json` — source and data-quality notes for the committed processed snapshots.
