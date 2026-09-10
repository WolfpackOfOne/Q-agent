# EDGAR Fundamentals Pipeline

SEC EDGAR fundamental data extraction for the 30-stock equity universe via [`edgartools`](https://github.com/dgunning/edgartools).

## Layout

```
infrastructure/edgar/
├── pipeline.py        # main extractor; writes to MyProjects/data/edgar/
└── README.md          # this file
```

Output: `MyProjects/data/edgar/fundamentals_annual.csv` (and `fundamentals_quarterly.csv` with `--quarterly`).

## Usage

```bash
cd /path/to/Q-agent && source venv/bin/activate

# Full 30-stock equity universe, annual only
python infrastructure/edgar/pipeline.py

# Add quarterly (10-Q) data
python infrastructure/edgar/pipeline.py --quarterly

# Subset of tickers
python infrastructure/edgar/pipeline.py --tickers AAPL MSFT GOOGL
```

## Output schema (wide format)

| Column | Description |
|---|---|
| `ticker` | Stock symbol |
| `period` | Fiscal period end date (YYYY-MM-DD) |
| `Revenue`, `GrossProfit`, `OperatingIncomeLoss`, `NetIncome` | Income statement |
| `Assets`, `Liabilities`, `AllEquityBalance`, `LongTermDebt`, `CashAndMarketableSecurities` | Balance sheet |
| `NetCashFromOperatingActivities`, `CapitalExpenses` | Cash flow |
| `SharesFullyDilutedAverage` | Share count |

## Gotchas

- **Identity is required**: SEC EDGAR mandates a user-agent identity. Set the `SEC_EDGAR_IDENTITY` env var to `"Your Name your.email@domain"` before running, or edit the fallback in `pipeline.py`. Do NOT leave the placeholder in production — SEC may rate-limit or block the placeholder pattern.
- **10-K reports 2 years of balance sheet, 3 years of P&L**: oldest year will show `NaN` for balance sheet metrics. This is expected.
- **Rate limit**: 10 req/s max per SEC policy. Pipeline sleeps 0.2s between tickers.
- **Balance sheet columns**: edgartools uses plain dates (`2025-09-27`) for balance sheets vs tagged (`2025-09-27 (FY)`) for income/cash-flow — the extractor handles both.

## Adding new metrics

Append the `standard_concept` name to the relevant list at the top of `pipeline.py`:
- `INCOME_CONCEPTS`
- `BALANCE_CONCEPTS`
- `CASHFLOW_CONCEPTS`

To discover available concepts:
```python
import edgar
edgar.set_identity("Name email@example.com")
fin = edgar.Company("AAPL").get_financials()
df = fin.income_statement().to_dataframe()
print(df[df["standard_concept"].notna()][["label","standard_concept"]])
```
