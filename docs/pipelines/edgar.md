# SEC EDGAR Pipeline

Quarterly fundamental data — income statements, balance sheets, and cash flow statements — from SEC EDGAR filings via the `edgartools` library.

## What it provides

- **Income statements**: revenue, gross profit, operating income, net income, EPS
- **Balance sheets**: assets, liabilities, equity, debt
- **Cash flow statements**: operating, investing, financing cash flows
- **Computed ratios**: Piotroski F-score, ROE, ROA, current ratio, debt/equity

## Prerequisites

No credentials required. SEC EDGAR is a public database.

```bash
cd ~/Documents/Q-agent/infrastructure
bash setup.sh
source .venv/bin/activate
```

## Running the pipeline

```bash
python infrastructure/pipelines/edgar/scripts/run_pipeline.py --tickers AAPL MSFT GOOGL
```

To run for the full 30-stock universe:

```bash
python infrastructure/pipelines/edgar/scripts/run_pipeline.py --universe wrds
```

## Output schema

`fundamentals_annual.csv`:
```
ticker,period,revenue,gross_profit,operating_income,net_income,total_assets,total_debt,equity
AAPL,2023-09-30,383285000000,169148000000,114301000000,96995000000,352583000000,109280000000,62146000000
```

`piotroski.csv`:
```
ticker,period,f_score,roa,delta_roa,cfo,accrual,delta_leverage,delta_liquidity,equity_offer,delta_margin,delta_turnover
AAPL,2023-09-30,7,0.283,0.021,0.312,-0.029,-0.041,0.038,0,0.031,0.044
```

## Using in a notebook

```python
import pandas as pd

fundamentals = pd.read_csv(
    "infrastructure/pipelines/edgar/data/fundamentals_annual.csv",
    parse_dates=["period"]
)

# Filter to recent years
recent = fundamentals[fundamentals["period"] >= "2015-01-01"]
```

## Notes

- EDGAR data is filed quarterly. Annual data (10-K) is the most reliable for fundamental analysis.
- `edgartools` fetches directly from SEC EDGAR's XBRL data. No third-party data vendor is involved.
- Some tickers have inconsistent XBRL tagging across years. The pipeline normalises field names where possible.
