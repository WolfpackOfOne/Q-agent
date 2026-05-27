# Strategy

## Hypothesis

US industry / sector returns load on **changes in the market-implied probability of a Trump 2024 win**, with the loading β_i differing systematically by industry:

> R_{i,t} = α_i + β_i · ΔP(Trump)_t + ε_{i,t}

Winterhalter (2025), replicated in [`infrastructure/marimo/notebooks/election_industry_returns.py`](../../../infrastructure/marimo/notebooks/election_industry_returns.py), reports positive β for energy / defense / banks and negative β for clean-energy / biotech.

If those β's are persistent enough, a daily cross-sectional bet that goes long the high-β ETFs and short the low-β ETFs should earn a return proportional to the prevailing drift in ΔP — and at the very least serve as a clear pedagogical example of consuming an alt-data signal in a LEAN algorithm.

## Trade rule

Each market day, 5 minutes after `SPY` open:

1. **Returns window** — pull `LOOKBACK + 5 = 65` days of daily history for the 19-ETF universe via `self.History(...)`, pct-change, in percent.
2. **Driver** — load the bundled Polymarket Trump-probability series; take its first difference.
3. **β estimate** — `rolling_beta(returns, ΔP, lookback=60)` from `shared/signals/election_beta.py`. Latest window only.
4. **Targets** — `top_bottom_k_betaweighted(betas, k=3)`:
   - Long the 3 ETFs with largest β
   - Short the 3 ETFs with smallest β
   - Weight ∝ β within each sleeve, normalised so Σ\|w\| = 1.0
5. **Execute** — `SetHoldings(ticker, weight)` for every universe ticker (zeros liquidate).
6. **Snapshot** — append a row to `electionbeta/daily_snapshots.csv` and per-position rows to `electionbeta/positions.csv` (saved in `OnEndOfAlgorithm`).

## Universe

```
SPDR Select Sector ETFs:  XLE XLF XLV XLI XLK XLP XLY XLU XLB XLRE XLC
Trump-themed industries:  XOP ITA KBE IBB ICLN TAN GDX ITB
```

## Parameters

| Parameter | Default | Where set |
|---|---|---|
| Lookback (β regression window) | 60 trading days | `domain/config.LOOKBACK` |
| K (longs and shorts per sleeve) | 3 | `domain/config.K` |
| Backtest window | 2024-03-15 → 2024-11-07 | `domain/config.START_DATE / END_DATE` |
| Starting cash | $100,000 | `domain/config.CASH` |
| Benchmark | SPY | `domain/config.BENCHMARK` |

## Warmup

`self.SetWarmUp(timedelta(days=LOOKBACK + 10))` — enough to fill the rolling regression before the first live `_rebalance` fires.

## Caveats

- R² values for daily ΔP regressions are low; the signal is noisy and only meaningful in aggregate.
- The β's drift with the political news cycle. Rolling 60 days is a reasonable compromise; shorter windows would chase noise, longer windows would dilute the election effect.
- Polymarket liquidity varied through 2024 — earlier-sample β's are less reliable.
- Cumulative P&L will be dominated by the largest ΔP events (Jul 13, Jul 21, Nov 5). This is by construction, not a bug.

## References

- Winterhalter, S. (2025). *U.S. presidential elections and stock markets: Evidence from the 2024 elections.* Aalto University.
- Amburgey, A. J. (2025). *How Election Shocks Move Markets.* arXiv.
- Snowberg, Wolfers, Zitzewitz (2007). *Partisan Impacts on the Economy.* QJE.
