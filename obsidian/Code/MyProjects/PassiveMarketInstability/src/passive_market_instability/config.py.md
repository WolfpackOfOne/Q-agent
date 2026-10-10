---
path: "MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py"
hub: "PassiveMarketInstability"
lines: 69
tags:
  - "code/python"
  - "projects/PassiveMarketInstability"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py"
---
# config.py

`MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py` · hub [[Hubs/Projects/PassiveMarketInstability|PassiveMarketInstability]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py)

## Purpose

Constants and repository-relative paths for the research workflow.

## Dependencies


**Imports (external):** [[Indexes/External packages#pathlib|pathlib]]

## Constants

| Name | Value | Line |
|---|---|---|
| `PAPER_R` | `0.0917` | [5](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L5) |
| `PAPER_KAPPA` | `0.0909` | [6](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L6) |
| `PAPER_SIGMA` | `0.1247` | [7](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L7) |
| `PAPER_ALPHA_HADDAD` | `0.106` | [8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L8) |
| `PAPER_ALPHA_BRIGHTMAN_HARVEY` | `0.1` | [9](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L9) |
| `PAPER_T0` | `30.0` | [10](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L10) |
| `S0` | `100.0` | [12](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L12) |
| `F0` | `100.0` | [13](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L13) |
| `SIM_YEARS` | `60` | [15](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L15) |
| `N_PATHS` | `100` | [16](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L16) |
| `STEPS_PER_YEAR` | `252` | [17](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L17) |
| `RANDOM_SEED` | `42` | [18](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L18) |
| `PASSIVE_THRESHOLDS` | `[0.5, 0.6, 0.65, 0.7, 0.8, 0.87, 0.91]` | [20](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L20) |
| `BROAD_MARKET_ETFS` | `['SPY', 'IVV', 'VOO', 'VTI']` | [22](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L22) |
| `DEMO_STOCK_UNIVERSE` | `['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'BRK-B', 'LLY', 'JPM', 'XOM']` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L29) |
| `PACKAGE_ROOT` | `Path(__file__).resolve().parent` | [42](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L42) |
| `SRC_ROOT` | `PACKAGE_ROOT.parent` | [43](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L43) |
| `PROJECT_ROOT` | `SRC_ROOT.parent` | [44](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L44) |
| `MYPROJECTS_ROOT` | `PROJECT_ROOT.parent` | [45](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L45) |
| `REPO_ROOT` | `MYPROJECTS_ROOT.parent` | [46](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L46) |
| `OUTPUT_DIR` | `PROJECT_ROOT / 'output'` | [48](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L48) |
| `FIGURES_DIR` | `OUTPUT_DIR / 'figures'` | [49](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L49) |
| `PASSIVE_SHARE_PIPELINE_DIR` | `REPO_ROOT / 'infrastructure' / 'pipelines' / 'passive_share'` | [51](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L51) |
| `ETF_FLOWS_PIPELINE_DIR` | `REPO_ROOT / 'infrastructure' / 'pipelines' / 'etf_flows'` | [52](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L52) |
| `EQUITY_LIQUIDITY_PIPELINE_DIR` | `REPO_ROOT / 'infrastructure' / 'pipelines' / 'equity_liquidity'` | [53](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L53) |
| `PASSIVE_SHARE_SCENARIOS_FILE` | `PASSIVE_SHARE_PIPELINE_DIR / 'data' / 'processed' / 'passive_share_scenarios.csv'` | [55](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L55) |
| `PASSIVE_SHARE_THRESHOLDS_FILE` | `PASSIVE_SHARE_PIPELINE_DIR / 'data' / 'processed' / 'passive_share_threshold_crossings.csv'` | [58](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L58) |
| `ETF_PRICE_PANEL_FILE` | `ETF_FLOWS_PIPELINE_DIR / 'data' / 'processed' / 'broad_market_etf_prices.csv'` | [61](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L61) |
| `ETF_FLOW_PROXY_FILE` | `ETF_FLOWS_PIPELINE_DIR / 'data' / 'processed' / 'broad_market_etf_flow_pressure_proxy.csv'` | [62](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L62) |
| `EQUITY_LIQUIDITY_PANEL_FILE` | `EQUITY_LIQUIDITY_PIPELINE_DIR / 'data' / 'processed' / 'demo_equity_liquidity_panel.csv'` | [63](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L63) |
| `EQUITY_PRESSURE_PANEL_FILE` | `EQUITY_LIQUIDITY_PIPELINE_DIR / 'data' / 'processed' / 'demo_passive_pressure_panel.csv'` | [66](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py#L66) |

## Source

> [!example]- MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py (69 lines)
> ```python
> """Constants and repository-relative paths for the research workflow."""
>
> from pathlib import Path
>
> PAPER_R = 0.0917
> PAPER_KAPPA = 0.0909
> PAPER_SIGMA = 0.1247
> PAPER_ALPHA_HADDAD = 0.106
> PAPER_ALPHA_BRIGHTMAN_HARVEY = 0.100
> PAPER_T0 = 30.0
>
> S0 = 100.0
> F0 = 100.0
>
> SIM_YEARS = 60
> N_PATHS = 100
> STEPS_PER_YEAR = 252
> RANDOM_SEED = 42
>
> PASSIVE_THRESHOLDS = [0.50, 0.60, 0.65, 0.70, 0.80, 0.87, 0.91]
>
> BROAD_MARKET_ETFS = [
>     "SPY",
>     "IVV",
>     "VOO",
>     "VTI",
> ]
>
> DEMO_STOCK_UNIVERSE = [
>     "AAPL",
>     "MSFT",
>     "NVDA",
>     "AMZN",
>     "META",
>     "GOOGL",
>     "BRK-B",
>     "LLY",
>     "JPM",
>     "XOM",
> ]
>
> PACKAGE_ROOT = Path(__file__).resolve().parent
> SRC_ROOT = PACKAGE_ROOT.parent
> PROJECT_ROOT = SRC_ROOT.parent
> MYPROJECTS_ROOT = PROJECT_ROOT.parent
> REPO_ROOT = MYPROJECTS_ROOT.parent
>
> OUTPUT_DIR = PROJECT_ROOT / "output"
> FIGURES_DIR = OUTPUT_DIR / "figures"
>
> PASSIVE_SHARE_PIPELINE_DIR = REPO_ROOT / "infrastructure" / "pipelines" / "passive_share"
> ETF_FLOWS_PIPELINE_DIR = REPO_ROOT / "infrastructure" / "pipelines" / "etf_flows"
> EQUITY_LIQUIDITY_PIPELINE_DIR = REPO_ROOT / "infrastructure" / "pipelines" / "equity_liquidity"
>
> PASSIVE_SHARE_SCENARIOS_FILE = (
>     PASSIVE_SHARE_PIPELINE_DIR / "data" / "processed" / "passive_share_scenarios.csv"
> )
> PASSIVE_SHARE_THRESHOLDS_FILE = (
>     PASSIVE_SHARE_PIPELINE_DIR / "data" / "processed" / "passive_share_threshold_crossings.csv"
> )
> ETF_PRICE_PANEL_FILE = ETF_FLOWS_PIPELINE_DIR / "data" / "processed" / "broad_market_etf_prices.csv"
> ETF_FLOW_PROXY_FILE = ETF_FLOWS_PIPELINE_DIR / "data" / "processed" / "broad_market_etf_flow_pressure_proxy.csv"
> EQUITY_LIQUIDITY_PANEL_FILE = (
>     EQUITY_LIQUIDITY_PIPELINE_DIR / "data" / "processed" / "demo_equity_liquidity_panel.csv"
> )
> EQUITY_PRESSURE_PANEL_FILE = (
>     EQUITY_LIQUIDITY_PIPELINE_DIR / "data" / "processed" / "demo_passive_pressure_panel.csv"
> )
> ```
