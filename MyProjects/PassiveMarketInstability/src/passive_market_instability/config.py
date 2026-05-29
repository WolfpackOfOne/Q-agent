"""Constants and repository-relative paths for the research workflow."""

from pathlib import Path

PAPER_R = 0.0917
PAPER_KAPPA = 0.0909
PAPER_SIGMA = 0.1247
PAPER_ALPHA_HADDAD = 0.106
PAPER_ALPHA_BRIGHTMAN_HARVEY = 0.100
PAPER_T0 = 30.0

S0 = 100.0
F0 = 100.0

SIM_YEARS = 60
N_PATHS = 100
STEPS_PER_YEAR = 252
RANDOM_SEED = 42

PASSIVE_THRESHOLDS = [0.50, 0.60, 0.65, 0.70, 0.80, 0.87, 0.91]

BROAD_MARKET_ETFS = [
    "SPY",
    "IVV",
    "VOO",
    "VTI",
]

DEMO_STOCK_UNIVERSE = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "BRK-B",
    "LLY",
    "JPM",
    "XOM",
]

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent
MYPROJECTS_ROOT = PROJECT_ROOT.parent
REPO_ROOT = MYPROJECTS_ROOT.parent

OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"

PASSIVE_SHARE_PIPELINE_DIR = REPO_ROOT / "infrastructure" / "pipelines" / "passive_share"
ETF_FLOWS_PIPELINE_DIR = REPO_ROOT / "infrastructure" / "pipelines" / "etf_flows"
EQUITY_LIQUIDITY_PIPELINE_DIR = REPO_ROOT / "infrastructure" / "pipelines" / "equity_liquidity"

PASSIVE_SHARE_SCENARIOS_FILE = (
    PASSIVE_SHARE_PIPELINE_DIR / "data" / "processed" / "passive_share_scenarios.csv"
)
PASSIVE_SHARE_THRESHOLDS_FILE = (
    PASSIVE_SHARE_PIPELINE_DIR / "data" / "processed" / "passive_share_threshold_crossings.csv"
)
ETF_PRICE_PANEL_FILE = ETF_FLOWS_PIPELINE_DIR / "data" / "processed" / "broad_market_etf_prices.csv"
ETF_FLOW_PROXY_FILE = ETF_FLOWS_PIPELINE_DIR / "data" / "processed" / "broad_market_etf_flow_pressure_proxy.csv"
EQUITY_LIQUIDITY_PANEL_FILE = (
    EQUITY_LIQUIDITY_PIPELINE_DIR / "data" / "processed" / "demo_equity_liquidity_panel.csv"
)
EQUITY_PRESSURE_PANEL_FILE = (
    EQUITY_LIQUIDITY_PIPELINE_DIR / "data" / "processed" / "demo_passive_pressure_panel.csv"
)
