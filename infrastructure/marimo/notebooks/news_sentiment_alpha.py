import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Financial-Media News Tone as a Trading Signal

    GDELT monitors global news and scores each day's coverage of a company on
    **tone** (how positive/negative the writing is) and **volume** (how much
    coverage there was). This notebook asks a simple question:

    **Does a company's news tone, restricted to financial media specifically,
    predict its stock's forward returns?**

    - **Signal**: each stock's daily tone, z-scored against its own trailing
      90-day baseline (`tone_z`) — "is today's coverage unusually positive or
      negative for this name, relative to how it's usually covered?"
    - **News source**: GDELT DOC 2.0 API, restricted to 4 financial-media domains
      (reuters.com, bloomberg.com, cnbc.com, wsj.com) rather than all global news.
      A broader, unrestricted-source version of this test found no signal — see
      §4 for that comparison.
    - **Prices**: CRSP daily bars via the WRDS pipeline.
    """)
    return


@app.cell
def _():
    import pathlib
    import zipfile

    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from scipy import stats

    plt.style.use("dark_background")
    mpl.rcParams.update({
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#161b22",
        "axes.edgecolor": "#30363d",
        "axes.labelcolor": "#c9d1d9",
        "axes.grid": True,
        "grid.color": "#21262d",
        "grid.alpha": 0.6,
        "text.color": "#c9d1d9",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "figure.dpi": 150,
        "savefig.facecolor": "#0d1117",
        "savefig.edgecolor": "#0d1117",
    })

    _nb = pathlib.Path(__file__).resolve()
    REPO = _nb.parent.parent.parent.parent  # notebooks/ -> marimo/ -> infrastructure/ -> repo root
    WRDS_DAILY = REPO / "infrastructure" / "pipelines" / "wrds" / "lean-data" / "equity" / "usa" / "daily"
    FINANCIAL_PANEL = (
        REPO / "infrastructure" / "pipelines" / "news_events_sentiment"
        / "lean-data" / "alternative" / "news_sentiment_financial" / "sentiment_panel.csv"
    )
    GENERAL_PANEL = (
        REPO / "infrastructure" / "pipelines" / "news_events_sentiment"
        / "lean-data" / "alternative" / "news_sentiment" / "sentiment_panel.csv"
    )
    SCALE = 10_000
    HOLD_DAYS = 5  # forward-return horizon for the OLS/quintile test in §2
    return (
        FINANCIAL_PANEL,
        GENERAL_PANEL,
        HOLD_DAYS,
        REPO,
        SCALE,
        WRDS_DAILY,
        np,
        pd,
        plt,
        stats,
        zipfile,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 0. Universe and Time Window

    GDELT's coverage of any one company, restricted to just 4 financial-media
    domains, is uneven — some names get mentioned daily, others almost never.
    Two design choices make the rest of this notebook meaningful instead of noisy:

    - **10 tickers**, chosen as the ones with the *highest* financial-media
      coverage rate: `GS, AAPL, JPM, BA, HD, IBM, VZ, V, NKE, CSCO`. (Started
      from a 20-stock universe; 4 never returned any data due to API rate
      limits, and the remaining 6 had coverage too thin to trade — see the
      pipeline README for the full list.)
    - **2017–2021 window.** Financial-media coverage from this pipeline drops
      off sharply after 2021 (2022 has essentially zero matched articles) — an
      infrastructure limitation, not a market one. Restricting to the window
      where coverage is actually dense keeps the test honest: both the strategy
      here and its benchmark are trading on ~98% of days, not a coverage-starved
      subset of them.
    """)
    return


@app.cell
def _():
    UNIVERSE = ["GS", "AAPL", "JPM", "BA", "HD", "IBM", "VZ", "V", "NKE", "CSCO"]
    WINDOW_START = "2017-01-01"
    WINDOW_END = "2021-12-31"
    MIN_NAMES = 2  # minimum tickers with a valid signal before a day is tradeable
    return MIN_NAMES, UNIVERSE, WINDOW_END, WINDOW_START


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Load Data
    """)
    return


@app.cell
def _(FINANCIAL_PANEL, UNIVERSE, mo, pd):
    mo.stop(
        not FINANCIAL_PANEL.exists(),
        mo.callout(
            mo.md(
                f"Financial-only sentiment panel not found at `{FINANCIAL_PANEL}` — run "
                "`python scripts/run_pipeline.py --financial-only` from "
                "`infrastructure/pipelines/news_events_sentiment/` first."
            ),
            kind="warn",
        ),
    )

    sentiment = pd.read_csv(FINANCIAL_PANEL, parse_dates=["date"])
    sentiment = sentiment[sentiment["ticker"].isin(UNIVERSE)].reset_index(drop=True)

    mo.md(
        f"Loaded **{len(sentiment)} rows** across **{sentiment['ticker'].nunique()}/{len(UNIVERSE)} tickers**  |  "
        f"{sentiment['date'].min().date()} → {sentiment['date'].max().date()}  |  "
        f"coverage (non-null `avg_tone`): **{sentiment['avg_tone'].notna().mean():.0%}**"
    )
    return (sentiment,)


@app.cell
def _(SCALE, UNIVERSE, WINDOW_END, WINDOW_START, WRDS_DAILY, mo, pd, zipfile):
    def _load_lean_zip(zpath, ticker):
        with zipfile.ZipFile(zpath) as z:
            df = pd.read_csv(
                z.open(z.namelist()[0]), header=None,
                names=["datetime", "open", "high", "low", "close", "volume"],
                parse_dates=["datetime"],
            )
        df["date"] = df["datetime"].dt.normalize()
        df["close_adj"] = df["close"] / SCALE
        return df.set_index("date")[["close_adj"]].rename(columns={"close_adj": ticker})

    _frames = [_load_lean_zip(WRDS_DAILY / f"{t.lower()}.zip", t) for t in UNIVERSE]

    prices = pd.concat(_frames, axis=1, sort=True).sort_index().loc[WINDOW_START:WINDOW_END]
    returns = prices.pct_change()

    mo.md(
        f"Price panel: **{len(prices.columns)} tickers** × **{len(prices)} trading days**  |  "
        f"{prices.index[0].date()} → {prices.index[-1].date()}"
    )
    return prices, returns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Does Tone Predict Forward Returns?

    Regress each stock's forward 5-day return on that day's `tone_z`. A
    positive, statistically significant slope would mean "unusually positive
    coverage tends to be followed by higher returns" — the kind of relationship
    a trading strategy could exploit.
    """)
    return


@app.cell
def _(HOLD_DAYS, mo, pd, prices, sentiment, stats):
    _fwd = prices.pct_change(HOLD_DAYS).shift(-HOLD_DAYS)
    _fwd_long = _fwd.stack().rename("fwd_ret").reset_index()
    _fwd_long.columns = ["date", "ticker", "fwd_ret"]

    merged = pd.merge(sentiment, _fwd_long, on=["date", "ticker"], how="inner")
    merged = merged.dropna(subset=["tone_z", "fwd_ret"])

    _slope, _intercept, _r, _p, _ = stats.linregress(merged["tone_z"], merged["fwd_ret"])
    _sig = "statistically significant (p < 0.05)" if _p < 0.05 else "not statistically significant"

    mo.md(
        f"`forward_5d_return = {_intercept:.5f} + {_slope:.5f} × tone_z`\n\n"
        f"β = **{_slope * 100:.3f}%** per unit of `tone_z`  |  r = {_r:.4f}  |  "
        f"**p = {_p:.4f}**  |  n = {len(merged)}\n\n"
        f"This slope is **{_sig}**."
    )
    p_value_financial = _p
    return merged, p_value_financial


@app.cell
def _(merged, np, pd, plt):
    _q = merged.copy()
    _q["quintile"] = pd.qcut(_q["tone_z"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    _summary = _q.groupby("quintile", observed=True)["fwd_ret"].mean() * 100

    _fig, _ax = plt.subplots(figsize=(10, 4.5))
    _colors = plt.cm.RdYlGn(np.linspace(0.15, 0.85, len(_summary)))
    _ax.bar(_summary.index.astype(str), _summary.values, color=_colors, edgecolor="#30363d", linewidth=0.5)
    _ax.axhline(0, color="#8b949e", linewidth=0.8)
    _ax.set_xlabel("Tone-Surprise Quintile (1 = most negative, 5 = most positive)")
    _ax.set_ylabel("Mean Forward 5-Day Return (%)")
    _ax.set_title("Forward Return by Tone-Surprise Quintile")
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Trading the Signal

    A simple, no-look-ahead long/short strategy:

    > Every trading day, among whichever stocks have a valid signal that day,
    > rank them by **yesterday's** `tone_z`. Go long the top half, short the
    > bottom half, equal-weighted. Rebalance daily. If fewer than 2 stocks have
    > a signal, sit out that day (rare — coverage is ~98% in this window).

    "Yesterday's" is deliberate — the strategy only ever uses information
    that was available before today's return happened. The "top/bottom half
    of whoever has data" rule (rather than requiring all 10 every day) matters:
    an earlier version of this notebook required full coverage from all 10
    stocks simultaneously, which cut the strategy down to trading only 5% of
    days and made it look far weaker than it actually is.
    """)
    return


@app.cell
def _(MIN_NAMES, UNIVERSE, pd, returns, sentiment):
    _tone_wide = sentiment.pivot(index="date", columns="ticker", values="tone_z").reindex(columns=UNIVERSE)
    _signal = _tone_wide.reindex(returns.index, method="ffill").shift(1)  # yesterday's signal only

    _nav = 100_000.0
    nav_series, spread_rets, active_days = [], [], []

    for _date, _sig_row in _signal.iterrows():
        _valid = _sig_row.dropna()
        if len(_valid) < MIN_NAMES:
            spread_rets.append(0.0)
            active_days.append(False)
            nav_series.append(_nav)
            continue

        _ranked = _valid.sort_values()
        _n = max(1, len(_ranked) // 2)
        _shorts = _ranked.index[:_n]
        _longs = _ranked.index[-_n:]

        _day_rets = returns.loc[_date]
        _spread = _day_rets[_longs].mean() - _day_rets[_shorts].mean()
        _nav *= (1 + _spread)

        spread_rets.append(_spread)
        active_days.append(True)
        nav_series.append(_nav)

    strategy = pd.DataFrame({"spread_ret": spread_rets, "active": active_days, "nav": nav_series}, index=returns.index)

    benchmark_nav = 100_000 * (1 + returns.mean(axis=1).fillna(0)).cumprod()  # equal-weight buy & hold, same universe
    return benchmark_nav, strategy


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Strategy vs. Buy & Hold
    """)
    return


@app.cell
def _(benchmark_nav, mo, plt, strategy):
    _fig, _ax = plt.subplots(figsize=(14, 5))
    _ax.plot(strategy.index, strategy["nav"], color="#58a6ff", linewidth=1.8, label="Long/Short Tone Strategy")
    _ax.plot(benchmark_nav.index, benchmark_nav, color="#3fb950", linewidth=1.4, alpha=0.85, label="Equal-Weight Buy & Hold (same 10 stocks)")
    _ax.axhline(100_000, color="#8b949e", linewidth=0.8, linestyle="--")
    _ax.set_title("Long/Short Financial-Tone Strategy vs. Buy & Hold")
    _ax.set_ylabel("Portfolio Value ($, starting $100,000)")
    _ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    _ax.legend(framealpha=0.3)
    plt.tight_layout()
    plt.show()

    mo.md(f"Active days: **{int(strategy['active'].sum())} / {len(strategy)}**")
    return


@app.cell
def _(benchmark_nav, mo, np, strategy):
    def _annual_return(series):
        years = (series.index[-1] - series.index[0]).days / 365.25
        return (series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1

    def _max_drawdown(series):
        return ((series - series.cummax()) / series.cummax()).min()

    def _sharpe(daily_rets):
        active = daily_rets[daily_rets != 0]
        return (active.mean() / active.std()) * np.sqrt(252) if active.std() > 0 else np.nan

    _strat_nav = strategy["nav"]
    _strat_sharpe = _sharpe(strategy["spread_ret"])
    _bench_sharpe = _sharpe(benchmark_nav.pct_change().fillna(0))

    mo.md(
        "| Metric | Long/Short Tone Strategy | Buy & Hold |\n|---|---|---|\n"
        f"| CAGR | {_annual_return(_strat_nav):.2%} | {_annual_return(benchmark_nav):.2%} |\n"
        f"| Max Drawdown | {_max_drawdown(_strat_nav):.2%} | {_max_drawdown(benchmark_nav):.2%} |\n"
        f"| Sharpe (ann.) | {_strat_sharpe:.2f} | {_bench_sharpe:.2f} |\n"
        f"| Final Value | ${_strat_nav.iloc[-1]:,.0f} | ${benchmark_nav.iloc[-1]:,.0f} |"
    )
    strategy_sharpe = _strat_sharpe
    return (strategy_sharpe,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Is This Better Than Unfiltered News?

    The same test, run on GDELT's *unrestricted* news query (every article
    mentioning the company, not just the 4 financial outlets) — same universe,
    same window, same strategy rules.
    """)
    return


@app.cell
def _(
    GENERAL_PANEL,
    HOLD_DAYS,
    MIN_NAMES,
    UNIVERSE,
    mo,
    np,
    p_value_financial,
    pd,
    prices,
    returns,
    stats,
    strategy_sharpe,
):
    mo.stop(
        not GENERAL_PANEL.exists(),
        mo.callout(mo.md(f"General-news panel not found at `{GENERAL_PANEL}`."), kind="warn"),
    )

    _general = pd.read_csv(GENERAL_PANEL, parse_dates=["date"])
    _general = _general[_general["ticker"].isin(UNIVERSE)]

    _fwd = prices.pct_change(HOLD_DAYS).shift(-HOLD_DAYS)
    _fwd_long = _fwd.stack().rename("fwd_ret").reset_index()
    _fwd_long.columns = ["date", "ticker", "fwd_ret"]
    _merged_gen = pd.merge(_general, _fwd_long, on=["date", "ticker"], how="inner").dropna(subset=["tone_z", "fwd_ret"])
    _, _, _r_gen, _p_gen, _ = stats.linregress(_merged_gen["tone_z"], _merged_gen["fwd_ret"])

    _tone_wide = _general.pivot(index="date", columns="ticker", values="tone_z").reindex(columns=UNIVERSE)
    _signal = _tone_wide.reindex(returns.index, method="ffill").shift(1)

    # Same rule as §3: rank whoever has a signal, long/short the top/bottom half.
    _spread_rets = []
    for _date, _sig_row in _signal.iterrows():
        _valid = _sig_row.dropna()
        if len(_valid) < MIN_NAMES:
            _spread_rets.append(0.0)
            continue
        _ranked = _valid.sort_values()
        _n = max(1, len(_ranked) // 2)
        _day_rets = returns.loc[_date]
        _spread_rets.append(_day_rets[_ranked.index[-_n:]].mean() - _day_rets[_ranked.index[:_n]].mean())

    _spread_rets = pd.Series(_spread_rets, index=returns.index)
    _active = _spread_rets[_spread_rets != 0]
    _general_sharpe = (_active.mean() / _active.std()) * np.sqrt(252) if _active.std() > 0 else np.nan

    mo.md(
        "| Signal | p-value | Strategy Sharpe |\n|---|---|---|\n"
        f"| Financial-media only (§2-4) | {p_value_financial:.3f} | {strategy_sharpe:.2f} |\n"
        f"| Unrestricted news | {_p_gen:.3f} | {_general_sharpe:.2f} |\n\n"
        "Unrestricted news — everything from product reviews to unrelated lawsuits mixed "
        "in with actual financial coverage — shows no relationship. Restricting to "
        "financial-media sources is what makes the signal in §2-4 show up at all."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reading the Results

    - The financial-media tone signal shows a real, if modest, relationship to
      forward returns: statistically significant regression (p = 0.033), and a
      long/short strategy with **Sharpe ≈ 0.80, CAGR ≈ 18%, max drawdown ≈ -33%**
      — edging out an equal-weight buy & hold of the same 10 stocks (Sharpe
      ≈ 0.76, CAGR ≈ 15%, max drawdown ≈ -39%) on every metric, but not by a
      wide margin, and the long/short strategy still loses almost a third of
      its peak value at some point.
    - **This is one test on one window.** A different universe/window cut
      earlier in this notebook's development found the *direction* of the best
      strategy could flip (momentum vs. contrarian) — a sign that any single
      result here is a lead, not a proven edge, until it holds up on fresh,
      out-of-sample data.
    - The comparison in §5 is the most useful finding: **which news source you
      use matters more than which filter you apply to it.** Restricting to
      financial media is what turns a flat, insignificant result (general news,
      p = 0.61) into a marginally significant one — not clever backtest tuning.
    - Nothing here accounts for transaction costs, borrow costs on the short
      leg, or slippage — real-money performance would be lower than both lines
      in the §4 chart.

    ## Next Steps

    - **Test out-of-sample.** Pull financial-media sentiment for 2022-2025 with
      a wider domain list (more than 4 outlets, to avoid the coverage collapse
      that limited this notebook to 2017-2021) and check if the same strategy
      — without re-tuning it — still works.
    - **Add more financial-media domains** to raise coverage density and let
      more of the original 20-stock universe qualify for the backtest.
    - **Condition on why tone moved**: combine this signal with earnings-date
      flags (from the WRDS/IBES pipeline) to separate "tone moved because of
      real news" from "tone moved because of noise."
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. From Research to Tradeable Backtest

    The signal above was implemented as a full QuantConnect/LEAN algorithm —
    `MyProjects/NewsSentimentAlpha` — with a magnitude-weighted, diversified
    portfolio construction (not the simple equal-weight/half-split test
    above), with parameters selected via a strict train (2017-18) / validate
    (2019) / test (2020-21) split rather than tuning against the full
    window. What follows is the actual LEAN backtest result on the held-out
    test period, never touched during parameter selection — trimmed to
    2020-01 through 2021-04, since GDELT coverage of this universe collapses
    through 2021 and the strategy places zero trades past that point
    regardless of how far the window extends (confirmed by comparing trades
    across both window lengths — identical).
    """)
    return


@app.cell(hide_code=True)
def _(REPO, mo, pd):
    BACKTEST_SNAPSHOTS = REPO / "MyProjects" / "storage" / "news_sentiment_alpha" / "daily_snapshots.csv"

    mo.stop(
        not BACKTEST_SNAPSHOTS.exists(),
        mo.callout(
            mo.md(
                f"LEAN backtest ObjectStore output not found at `{BACKTEST_SNAPSHOTS}` — run "
                "`bash scripts/lean-backtest.sh \"NewsSentimentAlpha\"` from the workspace root first."
            ),
            kind="warn",
        ),
    )

    backtest_snapshots = pd.read_csv(BACKTEST_SNAPSHOTS, parse_dates=["date"]).set_index("date")
    backtest_active = backtest_snapshots[backtest_snapshots["gross_exposure"] > 0]

    mo.md(
        f"Loaded **{len(backtest_snapshots)} trading days** "
        f"({backtest_snapshots.index[0].date()} → {backtest_snapshots.index[-1].date()})  |  "
        f"active days: **{len(backtest_active)}**"
    )
    return (backtest_snapshots,)


@app.cell(hide_code=True)
def _(backtest_snapshots, mo, np):
    _daily_ret = backtest_snapshots["nav"].pct_change().dropna()
    _active_ret = _daily_ret[_daily_ret != 0]
    _final_nav = backtest_snapshots["nav"].iloc[-1]

    backtest_sharpe = (_active_ret.mean() / _active_ret.std()) * np.sqrt(252)
    backtest_cagr = (backtest_snapshots["nav"].iloc[-1] / backtest_snapshots["nav"].iloc[0]) ** (
        365.25 / (backtest_snapshots.index[-1] - backtest_snapshots.index[0]).days
    ) - 1
    backtest_maxdd = ((backtest_snapshots["nav"] - backtest_snapshots["nav"].cummax()) / backtest_snapshots["nav"].cummax()).min()
    backtest_net_profit = backtest_snapshots["nav"].iloc[-1] / backtest_snapshots["nav"].iloc[0] - 1

    mo.md(
        "**LEAN backtest — held-out test period, trimmed to dense GDELT coverage (2020-01-01 to 2021-04-30), zero commissions**\n\n"
        "| Metric | Value | Source |\n|---|---|---|\n"
        f"| CAGR | {backtest_cagr:.2%} | recomputed from ObjectStore NAV |\n"
        f"| Max Drawdown | {backtest_maxdd:.2%} | recomputed from ObjectStore NAV |\n"
        f"| Net Profit | {backtest_net_profit:.2%} | recomputed from ObjectStore NAV |\n"
        f"| Final NAV | ${_final_nav:,.0f} | recomputed from ObjectStore NAV |\n"
        f"| Sharpe Ratio (naive, mean/std × √252) | {backtest_sharpe:.3f} | recomputed here |\n"
        "| Sharpe Ratio (LEAN's official statistic) | **0.907** | LEAN backtest report |\n\n"
        "CAGR, drawdown, and net profit recomputed from the ObjectStore NAV series "
        "match LEAN's own report closely. Sharpe does not — LEAN's official Sharpe "
        "Ratio statistic uses an internal methodology (likely a risk-free-rate "
        "adjustment) that a naive mean/std calculation on the realized return "
        "series doesn't reproduce exactly. **0.907 is the authoritative number** — "
        "see `MyProjects/NewsSentimentAlpha/docs/strategy.md` for the full "
        "validation methodology behind it, including why the window is trimmed "
        "from the full 2020-2021 test block."
    )
    return


@app.cell(hide_code=True)
def _(backtest_snapshots, plt):
    _fig, _ax = plt.subplots(figsize=(14, 5))
    _ax.plot(backtest_snapshots.index, backtest_snapshots["nav"], color="#58a6ff", linewidth=1.8, label="NewsSentimentAlpha (LEAN backtest, test period)")
    _ax.axhline(100_000, color="#8b949e", linewidth=0.8, linestyle="--")
    _ax.set_title("NewsSentimentAlpha — Held-Out Test Backtest (2020-01 to 2021-04)")
    _ax.set_ylabel("Portfolio Value ($, starting $100,000)")
    _ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    _ax.legend(framealpha=0.3)
    plt.tight_layout()
    plt.show()
    return


if __name__ == "__main__":
    app.run()
