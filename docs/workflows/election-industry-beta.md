# Canonical Workflow: ElectionIndustryBeta

`ElectionIndustryBeta` is Q-agent's flagship end-to-end workflow. The authoritative worked walkthrough is the [Golden Path](../golden-path.md); this page is the project reference that points to the files and commands used by that walkthrough.

The workflow demonstrates the full research lifecycle:

```text
committed Polymarket probability series
    ->
research notebook
    ->
shared signal
    ->
LEAN strategy
    ->
ObjectStore diagnostics
    ->
post-analysis notebook
```

It is intentionally educational. The goal is to show how a hypothesis moves from data to notebook research to strategy code and diagnostics, not to claim a profitable trading signal.

---

## What runs today

| Stage | Status | Credentials needed |
|---|---|---|
| Research notebook | Runs as-is | None |
| Signal code | Implemented | None |
| LEAN strategy | Implemented | QuantConnect account for cloud backtest |
| Diagnostics notebook | Implemented | ObjectStore output from a backtest |

The project uses a committed election probability file so the strategy does not need a live Polymarket API call during backtests.

---

## Key files

```text
MyProjects/ElectionIndustryBeta/
├── main.py
├── data/trump_prob.csv
├── domain/
│   ├── config.py
│   └── signals/election_beta.py
├── models/
│   ├── alpha.py
│   ├── portfolio.py
│   ├── execution.py
│   └── logger.py
├── research/pl_attribution.py
└── tools/refresh_trump_prob.py
```

Shared signal source:

```text
MyProjects/shared/signals/election_beta.py
```

Research notebook:

```text
infrastructure/marimo/notebooks/election_industry_returns.py
```

---

## 1. Refresh or inspect the Polymarket input

The committed strategy input is:

```text
MyProjects/ElectionIndustryBeta/data/trump_prob.csv
```

It contains daily YES-token prices for the 2024 Trump election market. Because the 2024 election is over, the file is stable and committed for reproducibility.

To refresh it from the project tool:

```bash
cd MyProjects/ElectionIndustryBeta
python tools/refresh_trump_prob.py
```

For broader Polymarket research, use the full [Polymarket pipeline](../pipelines/polymarket.md), which has separate market-metadata and price-history steps.

---

## 2. Run the research notebook

```bash
python -m venv infrastructure/marimo/venv
source infrastructure/marimo/venv/bin/activate
pip install -r infrastructure/marimo/requirements.txt
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

The notebook loads `trump_prob.csv`, fetches ETF prices from yfinance, estimates each ETF's sensitivity to changes in election probability, and helps decide whether the effect is worth turning into a signal.

---

## 3. Review the shared signal

Signal logic lives in pure Python, outside LEAN:

```text
MyProjects/shared/signals/election_beta.py
```

The project consumes that signal from:

```text
MyProjects/ElectionIndustryBeta/domain/signals/election_beta.py
```

This demonstrates the Q-agent architecture rule: signal math belongs in the `domain/` layer and should be testable without a LEAN algorithm instance.

---

## 4. Run the LEAN strategy

```bash
cd MyProjects
lean cloud push --project "ElectionIndustryBeta" --force
lean cloud backtest "ElectionIndustryBeta" --name "baseline"
```

The strategy:

1. Loads the election probability series
2. Pulls ETF return history
3. Computes rolling election betas
4. Longs the top-K positive-beta industries
5. Shorts the bottom-K negative-beta industries
6. Logs diagnostics to ObjectStore

---

## 5. Analyze ObjectStore outputs

After a backtest, run the diagnostics notebook:

```bash
marimo run MyProjects/ElectionIndustryBeta/research/pl_attribution.py
```

The diagnostics workflow is where you evaluate whether the backtest behavior matches the original hypothesis: P&L attribution, exposure, concentration, and realized performance.

---

## Architecture map

```text
main.py                     # composition root — wires the pieces
models/                     # orchestration: alpha, portfolio, execution, logging
domain/                     # pure signal/config logic
research/                   # diagnostics and post-analysis
data/                       # committed deterministic input for this project
tools/                      # refresh/maintenance scripts
```

See [Architecture](../architecture.md) for the general layer rules and [Golden Path](../golden-path.md) for the full narrative walkthrough.

---

## Why this workflow matters

Most quantitative finance repositories show only one piece of the research lifecycle. `ElectionIndustryBeta` connects the pieces:

```text
data -> notebook -> signal -> LEAN strategy -> backtest -> diagnostics
```

That is the canonical Q-agent workflow pattern.
