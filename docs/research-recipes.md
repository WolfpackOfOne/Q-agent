# Research Recipes

A recipe is a focused, reproducible research task: a hypothesis, the data needed to test it, and a starting point for the notebook. Each recipe can be completed in a few hours with the data pipelines already in this repo.

---

## Macro & Policy

### Fed Policy Probability vs. Equity Sectors
**Hypothesis:** Polymarket probabilities for Fed rate decisions lead sector ETF returns.

**Data:** Polymarket (Fed FOMC markets) + yfinance (XLK, XLF, XLE, XLU, XLY sector ETFs)

**Research questions:**
- Do rising rate-cut probabilities predict utility and REIT outperformance?
- Is there a lead/lag structure between prediction market prices and ETF returns?
- Does the effect strengthen in the 5 days before an FOMC meeting?

**Status:** Example notebook included — see [Election & Industry Returns](notebooks.md)

---

### Treasury Yield Curve vs. Bank Stocks
**Hypothesis:** Yield curve steepening predicts bank stock outperformance.

**Data:** Treasury.gov rate data + WRDS (JPM, BAC, GS, MS)

**Research questions:**
- What is the rolling correlation between the 10Y-2Y spread and bank stock returns?
- Does the effect hold after controlling for market beta?
- Is the signal stronger at curve inversions?

**Status:** Coming soon — Treasury pipeline not yet built

---

## Crypto & Prediction Markets

### Crypto Returns vs. Polymarket Election Probabilities
**Hypothesis:** Crypto prices are sensitive to political event probabilities.

**Data:** Coinbase/Kraken (BTC, ETH, SOL) + Polymarket (election/policy markets) + yfinance (COIN)

**Research questions:**
- Does BTC correlate with Trump election probability?
- Does the correlation change sign between primary and general election periods?
- Is COIN (Coinbase stock) a better proxy than BTC for political sensitivity?

**Status:** Example notebook included — see [Crypto & Polymarket Correlation](notebooks.md)

---

### Crypto Volatility Regimes
**Hypothesis:** Crypto volatility clusters and is predictable short-term.

**Data:** Coinbase/Kraken OHLCV (BTC, ETH, SOL)

**Research questions:**
- Do GARCH-family models outperform realized volatility as a one-day-ahead forecast?
- Do volatility regimes cluster by asset class (BTC vs. ETH vs. SOL)?
- Does the correlation between BTC and ETH increase during high-volatility regimes?

**Status:** Ready to build — data available from crypto pipeline

---

## Equities & Fundamentals

### Piotroski F-Score Cross-Sectional Strategy
**Hypothesis:** High F-score stocks outperform low F-score stocks over 12-month holding periods.

**Data:** WRDS/CRSP (prices) + SEC EDGAR (Piotroski F-scores)

**Research questions:**
- Does the classic Piotroski (2000) result hold in the 30-stock universe?
- What is the Sharpe ratio of a long/short F-score portfolio?
- Is the effect concentrated in small-cap or value stocks?

**Status:** Ready to build — both pipelines available

---

### Analyst Earnings Surprises and Drift
**Hypothesis:** Stocks that beat analyst EPS estimates drift upward over the following 30 days (PEAD).

**Data:** IBES analyst estimates (WRDS additional entitlements) + WRDS/CRSP prices

**Research questions:**
- Is post-earnings announcement drift present in the 30-stock universe?
- Does the drift magnitude correlate with earnings surprise magnitude?
- Does the effect decay faster in large-cap stocks?

**Status:** IBES data available with additional WRDS entitlements

---

### ETF Constituent Crowding
**Hypothesis:** Stocks with high ETF ownership show lower idiosyncratic volatility (crowding discount) and larger drawdowns during market stress.

**Data:** WRDS ETF constituents + WRDS/CRSP prices

**Research questions:**
- Do high-ETF-ownership stocks have lower residual volatility relative to their factors?
- Do they show larger drawdowns during VIX spikes?
- Is the effect stronger in passive vs. active ETFs?

**Status:** Coming soon — ETF constituent pipeline not yet built

---

## Backtesting Diagnostics

### Rolling Sharpe Stability
**Hypothesis:** Strategies with unstable rolling Sharpe ratios are overfit.

**Data:** LEAN backtest ObjectStore output

**Research questions:**
- How does the 12-month rolling Sharpe ratio evolve over the backtest period?
- Is performance stable across market regimes (2008, 2020, 2022)?
- Is the out-of-sample Sharpe within one standard deviation of the in-sample Sharpe?

**Status:** Ready to build for any backtest — use ObjectStore results

---

### Trade Attribution
**Hypothesis:** A small number of trades drive the majority of backtest P&L.

**Data:** LEAN backtest trade log

**Research questions:**
- What fraction of trades account for 80% of gross P&L?
- Is performance driven by a few outlier trades or distributed across many small winners?
- Does trade concentration increase or decrease after parameter tuning?

**Status:** Ready to build for any backtest — use ObjectStore results

---

## How to use a recipe

1. Pick a recipe that interests you
2. Make sure the required pipelines are running locally (see [Data Pipelines](pipelines/index.md))
3. Create a new Marimo notebook in `infrastructure/marimo/notebooks/`
4. Work through the research questions, documenting findings as you go
5. If it's interesting, open a PR to share it

Good research recipes make good contributions.
