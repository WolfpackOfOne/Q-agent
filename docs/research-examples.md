# Research Examples

Research examples are broader themes that can become notebooks, recipes, or full LEAN strategy projects. For a complete worked example, start with the [Golden Path](golden-path.md) and the [ElectionIndustryBeta workflow](workflows/election-industry-beta.md).

Use this page as an index. Use [Research Recipes](research-recipes.md) when you want a concrete hypothesis and starting checklist.

---

## Implemented example

### Election & Industry Returns

Combine:

- committed Polymarket election probability data
- yfinance sector and industry ETF returns
- reusable election-beta signal logic
- LEAN strategy implementation
- ObjectStore diagnostics

Start here:

- [Running Notebooks](notebooks.md)
- [Golden Path](golden-path.md)
- [Canonical Workflow: ElectionIndustryBeta](workflows/election-industry-beta.md)

---

## Candidate research themes

### WRDS Equity Returns and EDGAR Fundamentals

Combine:

- WRDS/CRSP equity returns
- SEC filing metrics
- fundamental ratios

Possible outputs:

- cross-sectional factor portfolios
- valuation diagnostics
- event studies

Related recipe: [Piotroski F-Score Cross-Sectional Strategy](research-recipes.md#piotroski-f-score-cross-sectional-strategy)

---

### ETF Constituents and Liquidity

Combine:

- ETF holdings
- daily volume
- volatility estimates

Possible outputs:

- fund crowding diagnostics
- liquidity stress metrics
- portfolio concentration metrics

Related recipe: [ETF Constituent Crowding](research-recipes.md#etf-constituent-crowding)

---

### Polymarket and Financial Markets

Combine:

- prediction market probabilities
- ETF returns
- crypto market data

Possible outputs:

- event sensitivity studies
- correlation analysis
- regime detection

Related recipes:

- [Fed Policy Probability vs. Equity Sectors](research-recipes.md#fed-policy-probability-vs-equity-sectors)
- [Crypto Returns vs. Election Prediction Markets](research-recipes.md#crypto-returns-vs-election-prediction-markets)

---

### QuantConnect Backtest Diagnostics

Combine:

- LEAN backtest outputs
- ObjectStore logs
- notebook diagnostics
- risk analytics

Possible outputs:

- rolling Sharpe analysis
- drawdown studies
- exposure decomposition
- trade attribution

Related recipes:

- [Rolling Sharpe Stability](research-recipes.md#rolling-sharpe-stability)
- [Trade Attribution](research-recipes.md#trade-attribution)
