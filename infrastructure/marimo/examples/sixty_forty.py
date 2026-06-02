import marimo

__generated_with = "0.23.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # 60/40 Portfolio Research — SPY + AGG

    A classic 60% equity / 40% bond portfolio, rebalanced quarterly.

    - **SPY** (S&P 500 ETF) — equity leg, sourced from WRDS/CRSP
    - **AGG** (US Aggregate Bond ETF) — bond leg, sourced from yfinance
    - **Rebalance**: first trading day of each quarter (Jan, Apr, Jul, Oct)

    Data paths (resolved relative to this notebook's location):
    - `infrastructure/pipelines/wrds/lean-data/equity/usa/daily/spy.zip`
    - `infrastructure/pipelines/yfinance/lean-data/equity/usa/daily/agg.zip`
    """)
    return


@app.cell
def _():
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import zipfile
    import pathlib

    plt.style.use('dark_background')
    mpl.rcParams.update({
        'figure.facecolor': '#0d1117',
        'axes.facecolor': '#161b22',
        'axes.edgecolor': '#30363d',
        'axes.labelcolor': '#c9d1d9',
        'axes.grid': True,
        'grid.color': '#21262d',
        'grid.alpha': 0.6,
        'text.color': '#c9d1d9',
        'xtick.color': '#8b949e',
        'ytick.color': '#8b949e',
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'figure.dpi': 150,
        'savefig.facecolor': '#0d1117',
        'savefig.edgecolor': '#0d1117',
    })

    _nb = pathlib.Path(__file__).resolve()
    _repo = _nb.parent.parent.parent.parent  # examples/ -> marimo/ -> infrastructure/ -> repo root
    WRDS_DAILY  = _repo / "infrastructure" / "pipelines" / "wrds" / "lean-data" / "equity" / "usa" / "daily"
    YF_DAILY    = _repo / "infrastructure" / "pipelines" / "yfinance" / "lean-data" / "equity" / "usa" / "daily"
    COLS        = ["datetime", "open", "high", "low", "close", "volume"]
    SCALE       = 10_000
    return COLS, SCALE, WRDS_DAILY, YF_DAILY, np, pd, plt, zipfile


@app.cell
def _(COLS, SCALE, WRDS_DAILY, YF_DAILY, mo, pd, zipfile):
    def load_lean_zip(zpath, ticker):
        with zipfile.ZipFile(zpath) as z:
            csv_name = z.namelist()[0]
            df = pd.read_csv(z.open(csv_name), header=None, names=COLS, parse_dates=["datetime"])
        df["date"] = df["datetime"].dt.normalize()
        df["close_adj"] = df["close"] / SCALE
        return df.set_index("date")[["close_adj"]].rename(columns={"close_adj": ticker})

    spy_path = WRDS_DAILY / "spy.zip"
    agg_path = YF_DAILY   / "agg.zip"

    mo.stop(not spy_path.exists(), mo.callout(mo.md(f"SPY not found at `{spy_path}` — run the WRDS pipeline first."), kind="warn"))
    mo.stop(not agg_path.exists(), mo.callout(mo.md(f"AGG not found at `{agg_path}` — run the yfinance pipeline first."), kind="warn"))

    spy = load_lean_zip(spy_path, "SPY")
    agg = load_lean_zip(agg_path, "AGG")

    prices = spy.join(agg, how="inner")
    print(f"Loaded {len(prices)} overlapping trading days  |  {prices.index[0].date()} → {prices.index[-1].date()}")
    prices.tail()
    return (prices,)


@app.cell
def _(mo):
    mo.md("""
    ## Quarterly Rebalance Simulation
    """)
    return


@app.cell
def _(pd, prices):
    TARGET = {"SPY": 0.60, "AGG": 0.40}

    # Identify first trading day of each quarter
    rebalance_dates = (
        prices.index.to_series()
        .groupby([prices.index.year, prices.index.quarter])
        .first()
        .values
    )

    # Portfolio simulation
    cash        = 100_000.0
    shares      = {"SPY": 0.0, "AGG": 0.0}
    nav_series  = []
    weight_spy  = []
    weight_agg  = []

    for date, row in prices.iterrows():
        # Mark-to-market
        portfolio_value = sum(shares[t] * row[t] for t in ["SPY", "AGG"])

        if date in rebalance_dates:
            if portfolio_value == 0:
                portfolio_value = cash
            for ticker, target_w in TARGET.items():
                target_value   = portfolio_value * target_w
                shares[ticker] = target_value / row[ticker]

        nav = sum(shares[t] * row[t] for t in ["SPY", "AGG"])
        nav_series.append(nav)

        total = nav or 1
        weight_spy.append(shares["SPY"] * row["SPY"] / total)
        weight_agg.append(shares["AGG"] * row["AGG"] / total)

    results = pd.DataFrame({
        "nav":        nav_series,
        "w_spy":      weight_spy,
        "w_agg":      weight_agg,
    }, index=prices.index)

    results["spy_only"] = 100_000 * prices["SPY"] / prices["SPY"].iloc[0]
    results["agg_only"] = 100_000 * prices["AGG"] / prices["AGG"].iloc[0]

    print(f"Rebalance events : {len(rebalance_dates)}")
    print(f"Final NAV        : ${results['nav'].iloc[-1]:,.0f}  (started $100,000)")
    results.tail()
    return rebalance_dates, results


@app.cell
def _(mo):
    mo.md("""
    ## Cumulative Growth
    """)
    return


@app.cell
def _(plt, rebalance_dates, results):
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(results.index, results["nav"],      color="#58a6ff", linewidth=2,   label="60/40 Portfolio")
    ax.plot(results.index, results["spy_only"], color="#3fb950", linewidth=1.2, label="SPY (100%)", alpha=0.8)
    ax.plot(results.index, results["agg_only"], color="#f0883e", linewidth=1.2, label="AGG (100%)", alpha=0.8)

    # Mark rebalance dates
    rb_dates_in_idx = [d for d in rebalance_dates if d in results.index]
    ax.scatter(rb_dates_in_idx,
               results.loc[rb_dates_in_idx, "nav"],
               color="#f85149", s=8, zorder=5, label="Rebalance", alpha=0.6)

    ax.set_title("60/40 Portfolio vs. SPY-only and AGG-only  (Quarterly Rebalance)")
    ax.set_ylabel("Portfolio Value ($)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(framealpha=0.3)
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md("""
    ## Portfolio Weights Over Time
    """)
    return


@app.cell
def _(plt, results):
    fig2, ax2 = plt.subplots(figsize=(14, 4))

    ax2.fill_between(results.index, results["w_spy"], color="#58a6ff", alpha=0.7, label="SPY weight")
    ax2.fill_between(results.index, results["w_spy"], 1, color="#f0883e", alpha=0.7, label="AGG weight")
    ax2.axhline(0.60, color="#f85149", linestyle="--", linewidth=1, alpha=0.7, label="60% target")

    ax2.set_ylim(0, 1)
    ax2.set_title("Actual Portfolio Weights Over Time")
    ax2.set_ylabel("Weight")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax2.legend(framealpha=0.3, loc="upper left")
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md("""
    ## Performance Summary
    """)
    return


@app.cell
def _(mo, np, results):
    def annual_return(series):
        total = series.iloc[-1] / series.iloc[0]
        years = (series.index[-1] - series.index[0]).days / 365.25
        return total ** (1 / years) - 1

    def max_drawdown(series):
        roll_max = series.cummax()
        drawdown = (series - roll_max) / roll_max
        return drawdown.min()

    def sharpe(series, rf=0.0):
        daily_ret = series.pct_change().dropna()
        excess    = daily_ret - rf / 252
        return (excess.mean() / excess.std()) * np.sqrt(252)

    stats = {
        "60/40":    results["nav"],
        "SPY only": results["spy_only"],
        "AGG only": results["agg_only"],
    }

    rows = []
    for name, s in stats.items():
        rows.append({
            "Strategy":       name,
            "CAGR":           f"{annual_return(s):.2%}",
            "Max Drawdown":   f"{max_drawdown(s):.2%}",
            "Sharpe (ann.)":  f"{sharpe(s):.2f}",
            "Final Value":    f"${s.iloc[-1]:,.0f}",
        })

    mo.md(
        "| Strategy | CAGR | Max Drawdown | Sharpe | Final Value |\n"
        "|---|---|---|---|---|\n" +
        "\n".join(
            f"| {r['Strategy']} | {r['CAGR']} | {r['Max Drawdown']} | {r['Sharpe (ann.)']} | {r['Final Value']} |"
            for r in rows
        )
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Next Steps

    - Add transaction costs and slippage to the rebalance simulation
    - Test alternative rebalance thresholds (e.g. drift >5% triggers rebalance)
    - Compare against monthly and annual rebalance frequencies
    - Export results to ObjectStore for use in a QC backtest
    """)
    return


if __name__ == "__main__":
    app.run()
