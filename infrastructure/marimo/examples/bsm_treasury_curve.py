import marimo

__generated_with = "0.23.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # BSM Option Pricing: Treasury Yield Curve as Risk-Free Rate

    The Black-Scholes-Merton model takes a scalar **risk-free rate** `r`. The US Treasury
    curve offers several candidates — from short-dated bills to 30-year bonds.

    **Question:** how sensitive are BSM option prices to which tenor you choose as `r`,
    and does it matter more for some strikes or tickers than others?

    | Data | Pipeline |
    |---|---|
    | Equity daily prices | `yfinance` pipeline → LEAN zips |
    | Treasury average rates | `treasury_gov_rates` pipeline → CSV |
    | Option pricing | Analytic Black-Scholes-Merton |

    **Workflow:** run the two pipeline cells below to populate local data, then scroll
    through the analysis sections.

    > **Rate note:** the treasury pipeline reports the *average coupon rate* on all
    > outstanding marketable debt by category. Bills ≈ short end; Notes ≈ intermediate;
    > Bonds ≈ long end. These serve as representative anchors for the yield curve.
    """)
    return


@app.cell
def _():
    import sys
    import pathlib
    import warnings
    import zipfile
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from scipy.stats import norm

    warnings.filterwarnings("ignore")

    plt.style.use("dark_background")
    mpl.rcParams.update({
        "figure.facecolor": "#0d1117",
        "axes.facecolor":   "#161b22",
        "axes.edgecolor":   "#30363d",
        "axes.labelcolor":  "#c9d1d9",
        "axes.grid":        True,
        "grid.color":       "#21262d",
        "grid.alpha":       0.6,
        "text.color":       "#c9d1d9",
        "xtick.color":      "#8b949e",
        "ytick.color":      "#8b949e",
        "font.family":      "sans-serif",
        "font.size":        11,
        "axes.titlesize":   14,
        "axes.titleweight": "bold",
        "figure.dpi":       150,
        "savefig.facecolor":"#0d1117",
        "savefig.edgecolor":"#0d1117",
    })

    # Resolve infrastructure root relative to this notebook
    # notebook: infrastructure/marimo/examples/bsm_treasury_curve.py
    _nb = pathlib.Path(__file__).resolve()
    INFRA = _nb.parent.parent.parent           # infrastructure/

    YF_SRC       = INFRA / "pipelines" / "yfinance" / "src"
    YF_DAILY_DIR = INFRA / "pipelines" / "yfinance" / "lean-data" / "equity" / "usa" / "daily"
    TREASURY_DIR = INFRA / "pipelines" / "treasury_gov_rates"
    TREASURY_DATA = TREASURY_DIR / "data" / "treasury_rates"

    for _p in [str(YF_SRC), str(TREASURY_DIR)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)
    return TREASURY_DATA, YF_DAILY_DIR, norm, np, pd, plt, zipfile


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1  Pull Treasury Rate Data
    """)
    return


@app.cell
def _(mo):
    pull_treasury_btn = mo.ui.run_button(label="Pull treasury rates from API")
    pull_treasury_btn
    return (pull_treasury_btn,)


@app.cell
def _(TREASURY_DATA, mo, pull_treasury_btn):
    from download_treasury_rates import fetch_rates, build_curve_matrix
    import datetime as _dt

    mo.stop(not pull_treasury_btn.value, mo.md("*Click the button above to download treasury rates.*"))

    _raw = fetch_rates()

    TREASURY_DATA.mkdir(parents=True, exist_ok=True)
    _today = _dt.datetime.utcnow().strftime("%Y%m%d")
    _raw_path = TREASURY_DATA / f"treasury_rates_raw_{_today}.csv"
    _curve_path = TREASURY_DATA / f"treasury_curve_matrix_{_today}.csv"

    _raw.to_csv(_raw_path, index=False)
    build_curve_matrix(_raw).to_csv(_curve_path)

    _KEEP = {"Treasury Bills", "Treasury Notes", "Treasury Bonds"}
    treasury_rates = (
        _raw[_raw["security_desc"].isin(_KEEP)]
        .dropna(subset=["avg_interest_rate_amt"])
        .sort_values("record_date")
        .groupby("security_desc", as_index=False)
        .last()
        [["security_desc", "avg_interest_rate_amt", "record_date"]]
        .rename(columns={"security_desc": "tenor", "avg_interest_rate_amt": "rate_pct"})
        .assign(rate=lambda d: d["rate_pct"] / 100)
        .assign(_order=lambda d: d["tenor"].map(
            {"Treasury Bills": 0, "Treasury Notes": 1, "Treasury Bonds": 2}
        ))
        .sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )

    mo.callout(
        mo.md(f"Saved to `{_raw_path.name}`. "
              f"Loaded **{len(treasury_rates)} rate categories** "
              f"(as of {treasury_rates['record_date'].max().date()})."),
        kind="success",
    )
    return (treasury_rates,)


@app.cell
def _(mo, plt, treasury_rates):
    if treasury_rates.empty:
        mo.stop(True, mo.callout(mo.md("No treasury rates loaded yet."), kind="warn"))

    _colors = {
        "Treasury Bills":  "#58a6ff",
        "Treasury Notes":  "#3fb950",
        "Treasury Bonds":  "#f78166",
    }
    _fig, _ax = plt.subplots(figsize=(8, 4))
    for _, _r in treasury_rates.iterrows():
        _ax.bar(
            _r["tenor"], _r["rate_pct"],
            color=_colors.get(_r["tenor"], "#c9d1d9"),
            edgecolor="#30363d", linewidth=0.5,
        )
        _ax.text(_r["tenor"], _r["rate_pct"] + 0.04,
                 f"{_r['rate_pct']:.2f}%",
                 ha="center", va="bottom", fontsize=10, color="#c9d1d9")
    _ax.set_ylabel("Avg. Interest Rate (%)")
    _ax.set_title("Treasury Rate Anchors — Most Recent Average Rates by Category")
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2  Pull Equity Data via yfinance Pipeline
    """)
    return


@app.cell
def _(mo, pd):
    # Fetch current S&P 500 constituents from Wikipedia.
    # pd.read_html alone gets a 403 — Wikipedia blocks the default Python UA.
    # Use requests with a browser User-Agent, then parse the response body.
    # Tickers with dots (BRK.B, BF.B) are converted to hyphens (BRK-B, BF-B)
    # to match the format yfinance and the pipeline expect.
    import io, requests as _req
    try:
        _resp = _req.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        _resp.raise_for_status()
        _wiki = pd.read_html(io.StringIO(_resp.text), attrs={"id": "constituents"})[0]
        SP500 = _wiki["Symbol"].str.replace(".", "-", regex=False).tolist()
        _source = "Wikipedia (live)"
    except Exception:
        # Fallback: curated subset of large-caps if Wikipedia is unreachable
        SP500 = [
            "AAPL","ABBV","ABT","ACN","ADBE","AIG","AMD","AMGN","AMT","AMZN",
            "AVGO","AXP","BA","BAC","BK","BKNG","BLK","BMY","C","CAT",
            "CHTR","CL","CMCSA","COF","COP","COST","CRM","CSCO","CVS","CVX",
            "DE","DHR","DIS","DOW","DUK","EMR","EXC","F","FDX","GD",
            "GE","GILD","GM","GOOG","GS","HD","HON","IBM","INTC","INTU",
            "JNJ","JPM","KO","LIN","LLY","LMT","LOW","MA","MCD","MDLZ",
            "MDT","META","MMM","MO","MRK","MS","MSFT","NEE","NFLX","NKE",
            "NVDA","ORCL","OXY","PEP","PFE","PG","PM","PYPL","QCOM","RTX",
            "SBUX","SCHW","SO","SPG","T","TGT","TMO","TMUS","TXN","UNH",
            "UNP","UPS","USB","V","VZ","WFC","WMT","XOM",
        ]
        _source = "fallback (Wikipedia unreachable)"

    mo.callout(
        mo.md(f"Universe: **{len(SP500)} tickers** (S&P 500, {_source}). "
              "The pipeline downloads full history and writes LEAN-format zips. "
              "First run takes ~15–25 minutes."),
        kind="info",
    )
    return (SP500,)


@app.cell
def _(mo):
    pull_equity_btn = mo.ui.run_button(label="Pull equity data for all 100 tickers (~7–10 mins)")
    pull_equity_btn
    return (pull_equity_btn,)


@app.cell
def _(SP500, mo, pull_equity_btn):
    mo.stop(not pull_equity_btn.value, mo.md("*Click the button above to run the yfinance pipeline.*"))

    # Import pipeline modules directly from yfinance src
    from yfinance_lean.download import download_history, get_exchange_code
    from yfinance_lean.transform import (
        transform_daily_bars, transform_factor_file, transform_map_file
    )
    from yfinance_lean.publish import (
        publish_daily_bar, publish_factor_file, publish_map_file
    )

    _ok, _fail = [], []
    for _tk in SP500:
        try:
            _df = download_history(_tk)
            _ex = get_exchange_code(_tk)
            publish_daily_bar(_tk, transform_daily_bars(_df))
            publish_factor_file(_tk, transform_factor_file(_df))
            publish_map_file(_tk, transform_map_file(_tk, _ex, _df.index[0], _df.index[-1]))
            _ok.append(_tk)
        except Exception as _e:
            _fail.append(_tk)

    mo.callout(
        mo.md(f"Pipeline complete: **{len(_ok)} succeeded**, {len(_fail)} failed."
              + (f" Failed: {_fail}" if _fail else "")),
        kind="success" if not _fail else "warn",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3  BSM Price Curves Across Treasury Scenarios
    """)
    return


@app.cell
def _(YF_DAILY_DIR, mo):
    _zips = sorted(YF_DAILY_DIR.glob("*.zip"))
    if not _zips:
        mo.stop(True, mo.callout(
            mo.md("No LEAN zips found — run the equity pipeline in Section 2 first."),
            kind="warn",
        ))

    _available = [z.stem.upper() for z in _zips]

    ticker_dd = mo.ui.dropdown(
        options=_available,
        value="AAPL" if "AAPL" in _available else _available[0],
        label="Ticker",
    )
    option_type_dd = mo.ui.radio(
        options={"Call": "call", "Put": "put"},
        value="Call",
        label="Option type",
    )
    expiry_days_dd = mo.ui.dropdown(
        options={"30 days": 30, "60 days": 60, "90 days": 90,
                 "180 days": 180, "1 year": 365},
        value="30 days",
        label="Days to expiry",
    )
    mo.hstack([ticker_dd, option_type_dd, expiry_days_dd], gap=2)
    return expiry_days_dd, option_type_dd, ticker_dd


@app.cell
def _(YF_DAILY_DIR, mo, np, pd, ticker_dd, zipfile):
    _path = YF_DAILY_DIR / f"{ticker_dd.value.lower()}.zip"
    if not _path.exists():
        mo.stop(True, mo.callout(mo.md(f"Zip not found for **{ticker_dd.value}**."), kind="warn"))

    _COLS = ["datetime", "open", "high", "low", "close", "volume"]
    with zipfile.ZipFile(_path) as _z:
        _price_df = pd.read_csv(
            _z.open(_z.namelist()[0]),
            header=None, names=_COLS, parse_dates=["datetime"],
        )

    _price_df["close_adj"] = _price_df["close"] / 10_000
    _price_df = _price_df.sort_values("datetime").set_index("datetime")

    spot_price = float(_price_df["close_adj"].iloc[-1])
    _log_ret = np.log(_price_df["close_adj"] / _price_df["close_adj"].shift(1)).dropna()
    hist_vol = float(_log_ret.tail(60).std() * np.sqrt(252))

    mo.callout(
        mo.md(f"**{ticker_dd.value}** — last close **${spot_price:.2f}** | "
              f"60-day hist. vol **{hist_vol:.1%}**"),
        kind="info",
    )
    return hist_vol, spot_price


@app.cell
def _(
    expiry_days_dd,
    hist_vol,
    mo,
    norm,
    np,
    option_type_dd,
    plt,
    spot_price,
    ticker_dd,
    treasury_rates,
):
    if treasury_rates.empty:
        mo.stop(True, mo.callout(mo.md("Pull treasury rates first (Section 1)."), kind="warn"))

    _T = expiry_days_dd.value / 365.0
    _opt = option_type_dd.value

    def _bsm(S, K, T, r, sigma, opt="call"):
        if T < 1e-9 or sigma < 1e-9:
            return max(0.0, S - K) if opt == "call" else max(0.0, K - S)
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if opt == "call":
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    # Strike grid: 70% – 130% of spot
    strikes = np.linspace(0.70 * spot_price, 1.30 * spot_price, 80)

    _COLORS = {
        "Treasury Bills":  "#58a6ff",
        "Treasury Notes":  "#3fb950",
        "Treasury Bonds":  "#f78166",
    }

    _bsm_curves = {}
    for _, _row in treasury_rates.iterrows():
        _bsm_curves[_row["tenor"]] = np.array([
            _bsm(spot_price, K, _T, _row["rate"], hist_vol, _opt) for K in strikes
        ])

    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left: price curves per rate
    for _tenor, _prices in _bsm_curves.items():
        _ax1.plot(strikes, _prices, label=f"{_tenor} ({treasury_rates.loc[treasury_rates['tenor']==_tenor,'rate_pct'].values[0]:.2f}%)",
                  color=_COLORS.get(_tenor, "#c9d1d9"), linewidth=2)
    _ax1.axvline(spot_price, color="#f85149", alpha=0.7, linestyle="--", linewidth=1)
    _ax1.text(spot_price * 1.005, _ax1.get_ylim()[1] * 0.95, "spot",
              color="#f85149", fontsize=9)
    _ax1.set_xlabel("Strike ($)")
    _ax1.set_ylabel(f"BSM {_opt.capitalize()} Price ($)")
    _ax1.set_title(f"{ticker_dd.value} — BSM {_opt.capitalize()}  "
                   f"(σ={hist_vol:.1%}, T={expiry_days_dd.value}d)")
    _ax1.legend(fontsize=9)

    # Right: dollar spread vs mid-curve (Notes)
    _mid = _bsm_curves.get("Treasury Notes", list(_bsm_curves.values())[0])
    for _tenor, _prices in _bsm_curves.items():
        _ax2.plot(strikes, _prices - _mid,
                  label=_tenor, color=_COLORS.get(_tenor, "#c9d1d9"), linewidth=2)
    _ax2.axhline(0, color="#8b949e", linewidth=0.8, linestyle="--")
    _ax2.axvline(spot_price, color="#f85149", alpha=0.7, linestyle="--", linewidth=1)
    _ax2.set_xlabel("Strike ($)")
    _ax2.set_ylabel("Price − Notes BSM ($)")
    _ax2.set_title("Dollar Impact Relative to Treasury Notes Rate")
    _ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Reading the charts

    - **Left:** BSM price curves for each Treasury rate. Higher `r` raises call prices
      (the forward price of the stock rises) and lowers put prices (discounted strike shrinks).
    - **Right:** dollar difference versus the Treasury Notes rate. The spread widens
      away from ATM (deeper ITM/OTM) and grows with time to expiry.

    The gap between Bills and Bonds represents the **maximum pricing error** from
    mis-selecting the risk-free rate.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4  Cross-Ticker ATM Sensitivity

    For every downloaded ticker, price a synthetic **ATM call** (K = spot, 30-day expiry)
    under the Bills and Bonds rates. The bar shows the **% price spread** — tickers sorted
    by how much the rate choice moves the ATM price.

    > Run the equity pipeline in Section 2 first, then click the button below.
    """)
    return


@app.cell
def _(mo):
    run_cross_btn = mo.ui.run_button(label="Run cross-ticker sensitivity analysis")
    run_cross_btn
    return (run_cross_btn,)


@app.cell
def _(
    YF_DAILY_DIR,
    mo,
    norm,
    np,
    pd,
    plt,
    run_cross_btn,
    treasury_rates,
    zipfile,
):
    mo.stop(not run_cross_btn.value, mo.md("*Click the button above to run.*"))
    if treasury_rates.empty:
        mo.stop(True, mo.callout(mo.md("Pull treasury rates first (Section 1)."), kind="warn"))

    _zips = sorted(YF_DAILY_DIR.glob("*.zip"))
    if len(_zips) < 5:
        mo.stop(True, mo.callout(
            mo.md(f"Only **{len(_zips)} ticker(s)** found — run the equity pipeline "
                  "in Section 2 to download the full S&P 100 universe first."),
            kind="warn",
        ))

    _COLS = ["datetime", "open", "high", "low", "close", "volume"]
    _T30 = 30 / 365.0

    _bills_rate = treasury_rates.loc[treasury_rates["tenor"] == "Treasury Bills", "rate"]
    _bonds_rate = treasury_rates.loc[treasury_rates["tenor"] == "Treasury Bonds", "rate"]

    if _bills_rate.empty or _bonds_rate.empty:
        mo.stop(True, mo.callout(
            mo.md("Need both Bills and Bonds rates loaded."), kind="warn"
        ))

    _r_bills = float(_bills_rate.values[0])
    _r_bonds = float(_bonds_rate.values[0])

    def _bsm_atm(S, T, r, sigma):
        if sigma < 1e-9 or T < 1e-9:
            return 0.0
        d1 = (r + 0.5 * sigma**2) * T / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return S * norm.cdf(d1) - S * np.exp(-r * T) * norm.cdf(d2)

    _rows = []
    for _zp in _zips:
        _tk = _zp.stem.upper()
        try:
            with zipfile.ZipFile(_zp) as _z:
                _df = pd.read_csv(
                    _z.open(_z.namelist()[0]),
                    header=None,
                    names=_COLS,
                    parse_dates=["datetime"],
                )
            _df["close_adj"] = _df["close"] / 10_000
            _df = _df.sort_values("datetime")
            if len(_df) < 30:
                continue
            _spot = float(_df["close_adj"].iloc[-1])
            _vol = float(
                np.log(_df["close_adj"] / _df["close_adj"].shift(1))
                .dropna().tail(60).std() * np.sqrt(252)
            )
            if _vol < 0.01:
                continue
            _p_bills = _bsm_atm(_spot, _T30, _r_bills, _vol)
            _p_bonds = _bsm_atm(_spot, _T30, _r_bonds, _vol)
            _rows.append({
                "ticker":    _tk,
                "spot":      _spot,
                "vol":       _vol,
                "bills_$":   _p_bills,
                "bonds_$":   _p_bonds,
                "spread_$":  abs(_p_bills - _p_bonds),
                "spread_%":  abs(_p_bills - _p_bonds) / _p_bills * 100 if _p_bills > 0 else np.nan,
            })
        except Exception:
            continue

    if not _rows:
        mo.stop(True, mo.callout(mo.md("Could not compute ATM prices — check zip data."), kind="warn"))

    sens_df = (
        pd.DataFrame(_rows)
        .sort_values("spread_%", ascending=False)
        .reset_index(drop=True)
    )

    _top = sens_df.head(40)
    _bar_colors = [
        "#58a6ff" if i < 10 else "#3fb950" if i < 20 else "#8b949e"
        for i in range(len(_top))
    ]

    _fig, (_ax1, _ax2) = plt.subplots(2, 1, figsize=(14, 9))

    _ax1.bar(_top["ticker"], _top["spread_%"],
             color=_bar_colors, edgecolor="#30363d", linewidth=0.5)
    _ax1.set_ylabel("ATM Price Spread  Bills − Bonds (%)")
    _ax1.set_title(
        f"Cross-Ticker ATM Call Sensitivity to Treasury Rate Choice  "
        f"(30d, Bills={_r_bills:.2%} vs Bonds={_r_bonds:.2%})"
    )
    _ax1.tick_params(axis="x", rotation=45, labelsize=8)

    _ax2.bar(_top["ticker"], _top["spread_$"],
             color=_bar_colors, edgecolor="#30363d", linewidth=0.5)
    _ax2.set_ylabel("ATM Price Spread  Bills − Bonds ($)")
    _ax2.set_title("Same — in Dollar Terms")
    _ax2.tick_params(axis="x", rotation=45, labelsize=8)

    plt.tight_layout()
    plt.show()

    sens_df.head(15)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Why does sensitivity vary across tickers?

    The ATM BSM price is approximately `S · σ · √T / √(2π)` — the rate term `r` enters
    through the forward price and the discount on the strike. For ATM options these two
    effects partially cancel, so the net rate sensitivity (**rho**) is:

    $$\rho_{\text{call}} = K \cdot T \cdot e^{-rT} \cdot N(d_2)$$

    Tickers with **higher spot prices** dominate the dollar spread (top panel), while the
    **percentage spread** (bottom panel) surfaces stocks where the rate choice matters most
    relative to the option's value — typically lower-volatility names where `r` is a
    larger fraction of total drift.
    """)
    return


if __name__ == "__main__":
    app.run()
