import marimo

__generated_with = "0.23.7"
app = marimo.App(width="wide")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Passive Market Instability Extension

    Michael Green, Hari P. Krishnan, and Stephan Sturm model the dollar value of the equity market, $S(t)$, as mean reverting toward a smooth fundamental value, $F(t)$.
    The key idea is that mean reversion weakens as passive share, $p(t)$, rises.

    $$
    dS(t) =
        \kappa (1 - p(t)) (F(t) - S(t)) dt
        + \sigma \sqrt{F(t)S(t)} dW(t)
    $$

    with:

    $$
    F(t) = F_0 e^{rt},
    \qquad
    p(t) = \frac{1}{1 + e^{-\alpha(t - t_0)}}.
    $$

    This notebook extends the paper in three connected ways:

    1. Compare passive-share curves from Haddad, Huebner, and Loualiche; Brightman and Harvey; and the David Dredge / Yahoo Finance chart as a visual benchmark.
    2. Add broad-market ETF flow-pressure proxies.
    3. Build stock-level passive-pressure diagnostics using estimated index weight and liquidity.
    """)
    return


@app.cell
def _():
    import sys
    import pathlib

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
    PACKAGE_SRC = REPO_ROOT / "MyProjects" / "PassiveMarketInstability" / "src"
    if str(PACKAGE_SRC) not in sys.path:
        sys.path.insert(0, str(PACKAGE_SRC))

    from passive_market_instability.config import (
        BROAD_MARKET_ETFS,
        DEMO_STOCK_UNIVERSE,
        EQUITY_LIQUIDITY_PANEL_FILE,
        ETF_PRICE_PANEL_FILE,
        F0,
        FIGURES_DIR,
        N_PATHS,
        PAPER_ALPHA_BRIGHTMAN_HARVEY,
        PAPER_ALPHA_HADDAD,
        PAPER_KAPPA,
        PAPER_R,
        PAPER_SIGMA,
        PAPER_T0,
        PASSIVE_THRESHOLDS,
        PASSIVE_SHARE_SCENARIOS_FILE,
        RANDOM_SEED,
        S0,
        SIM_YEARS,
        STEPS_PER_YEAR,
    )
    from passive_market_instability.flows import (
        add_returns,
        aggregate_etf_flow_pressure,
        estimate_flow_pressure_proxy,
        validate_etf_flow_proxy,
    )
    from passive_market_instability.liquidity import (
        add_drawdown,
        add_realized_volatility,
        add_rolling_adv,
    )
    from passive_market_instability.passive_share import (
        build_passive_share_scenarios,
        logistic_passive_share,
        threshold_crossing_year,
        validate_passive_share,
    )
    from passive_market_instability.plots import (
        plot_first_hitting_times,
        plot_flow_pressure,
        plot_latest_passive_pressure,
        plot_passive_share_scenarios,
        plot_pressure_quintile_summary,
        plot_simulated_paths,
        plot_terminal_distribution,
        plot_threshold_crossings,
    )
    from passive_market_instability.pressure import (
        assign_pressure_quintiles,
        compute_passive_dollar_pressure,
        compute_passive_pressure,
        estimate_index_weights_from_market_cap,
        summarize_pressure_quintiles,
    )
    from passive_market_instability.simulation import (
        compute_instantaneous_volatility,
        feller_threshold,
        lyapunov_threshold,
        simulate_market_paths,
    )
    from passive_market_instability.validation import checks_to_frame, make_check

    plt.style.use("dark_background")
    mpl.rcParams.update(
        {
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
        }
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    def repo_path_label(path):
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return path.name

    return (
        BROAD_MARKET_ETFS,
        DEMO_STOCK_UNIVERSE,
        EQUITY_LIQUIDITY_PANEL_FILE,
        ETF_PRICE_PANEL_FILE,
        F0,
        FIGURES_DIR,
        N_PATHS,
        PAPER_ALPHA_BRIGHTMAN_HARVEY,
        PAPER_ALPHA_HADDAD,
        PAPER_KAPPA,
        PAPER_R,
        PAPER_SIGMA,
        PAPER_T0,
        PASSIVE_THRESHOLDS,
        PASSIVE_SHARE_SCENARIOS_FILE,
        RANDOM_SEED,
        REPO_ROOT,
        S0,
        SIM_YEARS,
        STEPS_PER_YEAR,
        add_drawdown,
        add_realized_volatility,
        add_returns,
        add_rolling_adv,
        aggregate_etf_flow_pressure,
        assign_pressure_quintiles,
        build_passive_share_scenarios,
        checks_to_frame,
        compute_instantaneous_volatility,
        compute_passive_dollar_pressure,
        compute_passive_pressure,
        estimate_flow_pressure_proxy,
        estimate_index_weights_from_market_cap,
        feller_threshold,
        logistic_passive_share,
        lyapunov_threshold,
        make_check,
        np,
        pd,
        plot_first_hitting_times,
        plot_flow_pressure,
        plot_latest_passive_pressure,
        plot_passive_share_scenarios,
        plot_pressure_quintile_summary,
        plot_simulated_paths,
        plot_terminal_distribution,
        plot_threshold_crossings,
        plt,
        repo_path_label,
        simulate_market_paths,
        summarize_pressure_quintiles,
        threshold_crossing_year,
        validate_etf_flow_proxy,
        validate_passive_share,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.callout(
        mo.md(
            """
            This notebook uses three levels of data quality. Official data is downloaded directly from an authoritative source. Manual data is hand-entered or digitized from a paper, chart, appendix, or exhibit. Proxy data approximates a target variable when the true data is unavailable. ETF volume times return is a flow-pressure proxy, not an official ETF flow series. Estimated index weights from market capitalization are not the same as official S&P 500 index weights.
            """
        ),
        kind="info",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Paper Parameters

    The paper's baseline calibration gives a compact way to reproduce the market-level mechanism before adding extensions.
    The two threshold formulas below are rough instability landmarks from the model, not trading signals.
    """)
    return


@app.cell
def _(
    F0,
    PAPER_ALPHA_BRIGHTMAN_HARVEY,
    PAPER_ALPHA_HADDAD,
    PAPER_KAPPA,
    PAPER_R,
    PAPER_SIGMA,
    PAPER_T0,
    S0,
    feller_threshold,
    lyapunov_threshold,
    pd,
):
    paper_params = pd.DataFrame(
        [
            ("r", PAPER_R),
            ("kappa", PAPER_KAPPA),
            ("sigma", PAPER_SIGMA),
            ("alpha_haddad", PAPER_ALPHA_HADDAD),
            ("alpha_brightman_harvey", PAPER_ALPHA_BRIGHTMAN_HARVEY),
            ("t0", PAPER_T0),
            ("S0", S0),
            ("F0", F0),
        ],
        columns=["parameter", "value"],
    )

    threshold_values = {
        "lyapunov_threshold": lyapunov_threshold(PAPER_KAPPA, PAPER_SIGMA),
        "feller_threshold": feller_threshold(PAPER_KAPPA, PAPER_SIGMA),
    }

    print(f"Lyapunov threshold: {threshold_values['lyapunov_threshold']:.4f} (expected near 0.87)")
    print(f"Feller threshold:   {threshold_values['feller_threshold']:.4f} (expected near 0.91)")
    if abs(threshold_values["lyapunov_threshold"] - 0.87) > 0.02:
        print("WARNING: Lyapunov threshold differs materially from the expected paper sanity check.")
    if abs(threshold_values["feller_threshold"] - 0.91) > 0.02:
        print("WARNING: Feller threshold differs materially from the expected paper sanity check.")

    paper_params
    return paper_params, threshold_values


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Passive Share Curve Comparison

    This section treats `t = 0` as roughly 1994 and `t = 30` as roughly 2025.
    Haddad, Huebner, and Loualiche 2025 is the baseline passive-share curve source because the paper uses it to support the claim that active managers do not fully offset passive flows when passive share becomes large.
    Brightman and Harvey 2025 is an alternative curve source with a similar estimated growth rate through 2023.
    The David Dredge / Yahoo Finance chart is a visual benchmark only unless its values are manually digitized and clearly labeled as manual data.
    """)
    return


@app.cell
def _(
    PASSIVE_THRESHOLDS,
    PASSIVE_SHARE_SCENARIOS_FILE,
    build_passive_share_scenarios,
    logistic_passive_share,
    np,
    pd,
    repo_path_label,
    threshold_crossing_year,
    validate_passive_share,
):
    passive_years = np.arange(1994, 2055)
    if PASSIVE_SHARE_SCENARIOS_FILE.exists():
        passive_df = pd.read_csv(PASSIVE_SHARE_SCENARIOS_FILE)
        passive_data_note = f"committed processed pipeline snapshot: {repo_path_label(PASSIVE_SHARE_SCENARIOS_FILE)}"
    else:
        passive_df = build_passive_share_scenarios(passive_years)
        passive_data_note = "generated from paper calibration constants"
    passive_validation = validate_passive_share(passive_df)

    threshold_df = pd.concat(
        [threshold_crossing_year(passive_df, threshold) for threshold in PASSIVE_THRESHOLDS],
        ignore_index=True,
    )

    baseline_t0_share = logistic_passive_share(0.0, alpha=0.106, t0=30.0)
    baseline_t30_share = logistic_passive_share(30.0, alpha=0.106, t0=30.0)
    haddad_t40 = logistic_passive_share(40.0, alpha=0.106, t0=30.0)
    brightman_t40 = logistic_passive_share(40.0, alpha=0.100, t0=30.0)

    print(f"Baseline p(t=0):  {baseline_t0_share:.4f}")
    print(f"Baseline p(t=30): {baseline_t30_share:.4f}")
    print(f"Haddad p(t=40):   {haddad_t40:.4f}")
    print(f"B-H p(t=40):      {brightman_t40:.4f}")
    print(passive_data_note)

    passive_df.head()
    return (
        baseline_t0_share,
        baseline_t30_share,
        brightman_t40,
        haddad_t40,
        passive_data_note,
        passive_df,
        passive_validation,
        threshold_df,
    )


@app.cell
def _(FIGURES_DIR, mo, passive_df, plot_passive_share_scenarios, plot_threshold_crossings, threshold_df):
    _fig_curves = plot_passive_share_scenarios(
        passive_df,
        output_path=FIGURES_DIR / "fig_01_passive_share_curves.png",
    )

    _fig_crossings = plot_threshold_crossings(
        threshold_df,
        output_path=FIGURES_DIR / "fig_02_threshold_crossings.png",
    )
    mo.vstack([_fig_curves, _fig_crossings])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Reproduce Paper-Style Simulation Sanity Checks

    These simulations are lightweight reproduction checks, not a full paper replication.
    Scenario A sets passive share to zero.
    Scenario B uses the Haddad baseline logistic curve with `alpha = 0.106` and `t0 = 30`.
    The qualitative expectation is that rising passive share reduces the restoring force and creates more dispersion and downside tail risk after the midpoint of the simulation.
    Because the no-passive case compounds to a much higher terminal dollar level, the final summary reports relative dispersion as coefficient of variation and also shows absolute standard deviations.
    """)
    return


@app.cell
def _(
    F0,
    N_PATHS,
    PAPER_ALPHA_HADDAD,
    PAPER_KAPPA,
    PAPER_R,
    PAPER_SIGMA,
    PAPER_T0,
    RANDOM_SEED,
    S0,
    SIM_YEARS,
    STEPS_PER_YEAR,
    np,
    pd,
    simulate_market_paths,
):
    no_passive_sim = simulate_market_paths(
        n_paths=N_PATHS,
        years=SIM_YEARS,
        steps_per_year=STEPS_PER_YEAR,
        s0=S0,
        f0=F0,
        r=PAPER_R,
        kappa=PAPER_KAPPA,
        sigma=PAPER_SIGMA,
        alpha=PAPER_ALPHA_HADDAD,
        t0=PAPER_T0,
        passive_mode="no_passive",
        random_seed=RANDOM_SEED,
    )
    rising_passive_sim = simulate_market_paths(
        n_paths=N_PATHS,
        years=SIM_YEARS,
        steps_per_year=STEPS_PER_YEAR,
        s0=S0,
        f0=F0,
        r=PAPER_R,
        kappa=PAPER_KAPPA,
        sigma=PAPER_SIGMA,
        alpha=PAPER_ALPHA_HADDAD,
        t0=PAPER_T0,
        passive_mode="logistic",
        random_seed=RANDOM_SEED,
    )
    low_growth_sim = simulate_market_paths(
        n_paths=N_PATHS,
        years=SIM_YEARS,
        steps_per_year=STEPS_PER_YEAR,
        s0=S0,
        f0=F0,
        r=0.0815,
        kappa=PAPER_KAPPA,
        sigma=PAPER_SIGMA,
        alpha=PAPER_ALPHA_HADDAD,
        t0=PAPER_T0,
        passive_mode="logistic",
        random_seed=RANDOM_SEED,
    )

    def _path_cols(paths):
        return [col for col in paths.columns if col.startswith("path_")]

    no_terminal = no_passive_sim["paths"].iloc[-1][_path_cols(no_passive_sim["paths"])].astype(float)
    rising_terminal = rising_passive_sim["paths"].iloc[-1][_path_cols(rising_passive_sim["paths"])].astype(float)

    simulation_stats = pd.DataFrame(
        [
            {
                "scenario": "no_passive",
                "terminal_median": no_terminal.median(),
                "terminal_std": no_terminal.std(),
                "terminal_cv": no_terminal.std() / no_terminal.median(),
                "fraction_above_s0": (no_terminal > S0).mean(),
                "hitting_zero_count": no_passive_sim["hitting_times"]["hitting_time"].notna().sum(),
            },
            {
                "scenario": "rising_passive",
                "terminal_median": rising_terminal.median(),
                "terminal_std": rising_terminal.std(),
                "terminal_cv": rising_terminal.std() / rising_terminal.median(),
                "fraction_above_s0": (rising_terminal > S0).mean(),
                "hitting_zero_count": rising_passive_sim["hitting_times"]["hitting_time"].notna().sum(),
            },
        ]
    )
    print(simulation_stats.to_string(index=False))

    simulation_stats
    return low_growth_sim, no_passive_sim, no_terminal, rising_passive_sim, rising_terminal, simulation_stats


@app.cell
def _(
    FIGURES_DIR,
    mo,
    no_passive_sim,
    plot_simulated_paths,
    plot_terminal_distribution,
    rising_passive_sim,
):
    _fig_no_passive = plot_simulated_paths(
        no_passive_sim["paths"],
        "Figure Check A: No Passive Share Paths",
        output_path=FIGURES_DIR / "fig_03_no_passive_paths.png",
    )

    _fig_rising = plot_simulated_paths(
        rising_passive_sim["paths"],
        "Figure Check B: Rising Passive Share Paths",
        output_path=FIGURES_DIR / "fig_04_rising_passive_paths.png",
    )

    _fig_terminal = plot_terminal_distribution(rising_passive_sim["paths"], 40, output_path=None)
    mo.vstack([_fig_no_passive, _fig_rising, _fig_terminal])
    return


@app.cell
def _(FIGURES_DIR, no_passive_sim, pd, plt, rising_passive_sim):
    def _values_at(paths_df, horizon):
        _path_cols = [col for col in paths_df.columns if col.startswith("path_")]
        _idx = (paths_df["t"] - horizon).abs().idxmin()
        return paths_df.loc[_idx, _path_cols].astype(float)

    no_10y_from_2025 = _values_at(no_passive_sim["paths"], 40.0)
    rising_10y_from_2025 = _values_at(rising_passive_sim["paths"], 40.0)

    _fig, _ax = plt.subplots(figsize=(11, 5))
    _ax.hist(no_10y_from_2025, bins=25, alpha=0.55, label="no passive", color="#58a6ff", edgecolor="#30363d")
    _ax.hist(
        rising_10y_from_2025,
        bins=25,
        alpha=0.55,
        label="rising passive",
        color="#f85149",
        edgecolor="#30363d",
    )
    _ax.set_title("Figure Check C: 10-Year Forward Distribution From 2025")
    _ax.set_xlabel("S(t=40)")
    _ax.set_ylabel("path count")
    _ax.legend()
    plt.tight_layout()
    _fig.savefig(FIGURES_DIR / "fig_05_10y_forward_distribution.png", bbox_inches="tight")

    forward_10y_distribution = pd.DataFrame(
        {
            "no_passive": no_10y_from_2025.values,
            "rising_passive": rising_10y_from_2025.values,
        }
    )
    _fig
    return forward_10y_distribution, no_10y_from_2025, rising_10y_from_2025


@app.cell
def _(FIGURES_DIR, low_growth_sim, mo, plot_first_hitting_times, plt, rising_passive_sim):
    _fig_hitting = plot_first_hitting_times(
        rising_passive_sim["hitting_times"],
        output_path=FIGURES_DIR / "fig_06_first_hitting_times.png",
    )

    def _values_at(paths_df, horizon):
        _path_cols = [col for col in paths_df.columns if col.startswith("path_")]
        _idx = (paths_df["t"] - horizon).abs().idxmin()
        return paths_df.loc[_idx, _path_cols].astype(float)

    baseline_20y = _values_at(rising_passive_sim["paths"], 20.0)
    low_growth_20y = _values_at(low_growth_sim["paths"], 20.0)
    _fig, _ax = plt.subplots(figsize=(11, 5))
    _ax.hist(baseline_20y, bins=25, alpha=0.55, label="baseline r = 0.0917", color="#58a6ff", edgecolor="#30363d")
    _ax.hist(low_growth_20y, bins=25, alpha=0.55, label="lower r = 0.0815", color="#d29922", edgecolor="#30363d")
    _ax.set_title("Figure Check E: 20-Year Forward Distribution")
    _ax.set_xlabel("S(t=20)")
    _ax.set_ylabel("path count")
    _ax.legend()
    plt.tight_layout()
    _fig.savefig(FIGURES_DIR / "fig_07_20y_forward_distribution.png", bbox_inches="tight")

    mo.vstack([_fig_hitting, _fig])
    return baseline_20y, low_growth_20y


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4b. Instantaneous Volatility Amplification

    The model's diffusion term reveals a self-reinforcing fragility mechanism.
    The instantaneous volatility of $S(t)$ is not constant — it scales with the
    ratio of fundamental value to market price:

    $$
    V(t) = \sigma \sqrt{\frac{F(t)}{S(t)}}
    $$

    When $S(t) < F(t)$ (market below fundamental value), $V(t) > \sigma$ — volatility
    is amplified above the calibrated baseline.  When passive share is high, the
    restoring force $\kappa (1 - p(t))$ is weak, so a dislocation is slower to
    correct.  The market that dips below fundamental therefore experiences both
    **reduced mean reversion** and **amplified volatility** simultaneously —
    a self-reinforcing dynamic.

    The Feller and Lyapunov thresholds mark where this mechanism can dominate.

    - **Feller threshold** $p_F = 1 - \sigma^2 / (2\kappa)$: above this passive share,
      the process can reach zero in finite time (the boundary becomes accessible).
    - **Lyapunov threshold** $p_L = 1 - 3\sigma^2 / (4\kappa)$: above this passive share,
      mean log growth of $S(t)$ turns negative even when $S(0) = F(0)$.

    Both thresholds are fragility landmarks from the paper, not trading signals.
    At the baseline calibration $(\kappa = 0.0909, \sigma = 0.1247)$:
    $p_L \approx 0.87$ and $p_F \approx 0.91$.
    The logistic passive-share curve (Haddad et al.) reaches these levels
    between 2035 and 2045 in the baseline scenario.
    """)
    return


@app.cell
def _(
    FIGURES_DIR,
    PAPER_SIGMA,
    mo,
    np,
    compute_instantaneous_volatility,
    pd,
    plt,
    rising_passive_sim,
    threshold_values,
):
    _paths = rising_passive_sim["paths"]
    _state = rising_passive_sim["state"]
    _path_cols = [col for col in _paths.columns if col.startswith("path_")]

    _f_grid = _state["fundamental_value"].values
    _t_grid = _state["t"].values
    _year_grid = _state["year"].values

    _median_s = _paths[_path_cols].median(axis=1).values
    _p10_s = _paths[_path_cols].quantile(0.10, axis=1).values
    _p90_s = _paths[_path_cols].quantile(0.90, axis=1).values

    _vol_median = compute_instantaneous_volatility(_median_s, _f_grid, PAPER_SIGMA)
    _vol_p10 = compute_instantaneous_volatility(np.maximum(_p10_s, 1e-6), _f_grid, PAPER_SIGMA)

    _fig, (_ax1, _ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    _ax1.plot(_year_grid, _f_grid, label="F(t) fundamental", color="#58a6ff", linewidth=1.5, linestyle="--")
    _ax1.plot(_year_grid, _median_s, label="S(t) median path", color="#3fb950", linewidth=1.5)
    _ax1.fill_between(_year_grid, _p10_s, _p90_s, alpha=0.18, color="#3fb950", label="p10–p90 band")
    _ax1.axvline(x=1994 + threshold_values["lyapunov_threshold"] * 30 / 0.5, color="#d29922", linestyle=":", alpha=0.7, label=f"p_L ≈ {threshold_values['lyapunov_threshold']:.2f}")
    _ax1.axvline(x=1994 + threshold_values["feller_threshold"] * 30 / 0.5, color="#f85149", linestyle=":", alpha=0.7, label=f"p_F ≈ {threshold_values['feller_threshold']:.2f}")
    _ax1.set_ylabel("Market level S(t)")
    _ax1.set_title("Figure 4b-1: Simulated Market Level vs Fundamental (Rising Passive)")
    _ax1.legend(fontsize=9)

    _baseline_vol = np.full_like(_t_grid, PAPER_SIGMA)
    _ax2.plot(_year_grid, _vol_median * 100, label="V(t) at median S(t)", color="#3fb950", linewidth=1.5)
    _ax2.plot(_year_grid, _vol_p10 * 100, label="V(t) at p10 S(t)", color="#f85149", linewidth=1.5, linestyle="--")
    _ax2.axhline(y=PAPER_SIGMA * 100, color="#8b949e", linestyle="--", linewidth=1, label=f"σ = {PAPER_SIGMA * 100:.2f}%")
    _ax2.set_ylabel("Instantaneous volatility V(t) [%]")
    _ax2.set_xlabel("Year")
    _ax2.set_title("Figure 4b-2: Instantaneous Volatility Amplification — V(t) = σ √(F(t)/S(t))")
    _ax2.legend(fontsize=9)
    _ax2.set_ylim(bottom=0)

    plt.tight_layout()
    _fig.savefig(FIGURES_DIR / "fig_4b_volatility_amplification.png", bbox_inches="tight")

    vol_amplification_df = pd.DataFrame({
        "year": _year_grid,
        "t": _t_grid,
        "fundamental": _f_grid,
        "median_s": _median_s,
        "vol_at_median": _vol_median,
        "vol_at_p10": _vol_p10,
    })
    mo.vstack([_fig, mo.callout(
        mo.md("V(t) above the baseline σ line means the market's realized volatility exceeds the calibrated diffusion constant. "
              "The divergence is largest for low-S(t) paths — exactly those paths where passive share has already weakened mean reversion."),
        kind="warn",
    )])
    return (vol_amplification_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. ETF Flow-Pressure Extension

    The original paper intentionally begins with a zero-net-flow case. This section extends the paper by asking how passive-share fragility might behave when broad-market ETF flow pressure is positive or negative.

    The broad ETF universe is `SPY`, `IVV`, `VOO`, and `VTI`.
    If `yfinance` is unavailable, the notebook creates a clearly labeled synthetic placeholder panel so downstream cells remain readable.
    The proxy is:

    ```text
    flow_pressure_proxy = volume * return
    ```

    This is a weak proxy, not true ETF creations or redemptions.
    """)
    return


@app.cell
def _(np, pd):
    def fetch_yfinance_price_panel(tickers, start="2019-01-01", end=None):
        try:
            import yfinance as yf
        except Exception as exc:
            return pd.DataFrame(), f"yfinance unavailable: {exc}"

        try:
            raw = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=False,
                timeout=30,
            )
        except Exception as exc:
            return pd.DataFrame(), f"yfinance download failed: {exc}"

        if raw.empty:
            return pd.DataFrame(), "yfinance returned an empty panel"

        def _field(field, ticker):
            if isinstance(raw.columns, pd.MultiIndex):
                for key in ((field, ticker), (ticker, field)):
                    if key in raw.columns:
                        return raw.loc[:, key]
                if field in raw.columns.get_level_values(0):
                    sub = raw[field]
                    if ticker in sub.columns:
                        return sub[ticker]
            if field in raw.columns and len(tickers) == 1:
                return raw[field]
            return None

        records = []
        for ticker in tickers:
            close = _field("Close", ticker)
            adj_close = _field("Adj Close", ticker)
            volume = _field("Volume", ticker)
            if close is None or volume is None:
                continue
            if adj_close is None:
                adj_close = close
            ticker_df = pd.DataFrame(
                {
                    "date": pd.to_datetime(close.index).normalize(),
                    "ticker": ticker,
                    "adj_close": pd.to_numeric(adj_close, errors="coerce").values,
                    "close": pd.to_numeric(close, errors="coerce").values,
                    "volume": pd.to_numeric(volume, errors="coerce").fillna(0.0).values,
                }
            )
            records.append(ticker_df)

        if not records:
            return pd.DataFrame(), "yfinance did not return usable close and volume columns"
        return pd.concat(records, ignore_index=True).dropna(subset=["close"]), "official yfinance price-volume download"

    def build_synthetic_price_panel(tickers, start="2021-01-01", periods=756, include_market_cap=False):
        rng = np.random.default_rng(42)
        dates = pd.bdate_range(start=start, periods=periods)
        records = []
        for idx, ticker in enumerate(tickers):
            returns = rng.normal(0.0004, 0.018 + idx * 0.001, size=len(dates))
            close = 100.0 * np.cumprod(1.0 + returns)
            volume = rng.integers(10_000_000, 80_000_000, size=len(dates)).astype(float)
            frame = pd.DataFrame(
                {
                    "date": dates,
                    "ticker": ticker,
                    "adj_close": close,
                    "close": close,
                    "volume": volume,
                }
            )
            if include_market_cap:
                frame["market_cap"] = (len(tickers) - idx) * 500_000_000_000.0
            records.append(frame)
        return pd.concat(records, ignore_index=True)

    def attach_latest_market_caps(panel, tickers):
        try:
            import yfinance as yf
        except Exception:
            yf = None

        caps = {}
        if yf is not None:
            for ticker in tickers:
                try:
                    fast_info = yf.Ticker(ticker).fast_info
                    cap = fast_info.get("market_cap") if hasattr(fast_info, "get") else None
                    if cap is not None and np.isfinite(cap) and cap > 0:
                        caps[ticker] = float(cap)
                except Exception:
                    continue

        missing = [ticker for ticker in tickers if ticker not in caps]
        if missing:
            placeholder_caps = np.linspace(len(tickers), 1, len(tickers)) * 500_000_000_000.0
            for ticker, cap in zip(tickers, placeholder_caps):
                caps.setdefault(ticker, float(cap))
            note = "market caps use latest yfinance values where available; missing names use synthetic placeholders"
        else:
            note = "market caps use latest yfinance values repeated through history"

        out = panel.copy()
        out["market_cap"] = out["ticker"].map(caps)
        return out, note

    return attach_latest_market_caps, build_synthetic_price_panel, fetch_yfinance_price_panel


@app.cell
def _(
    BROAD_MARKET_ETFS,
    ETF_PRICE_PANEL_FILE,
    add_returns,
    aggregate_etf_flow_pressure,
    build_synthetic_price_panel,
    estimate_flow_pressure_proxy,
    fetch_yfinance_price_panel,
    logistic_passive_share,
    pd,
    repo_path_label,
    validate_etf_flow_proxy,
):
    if ETF_PRICE_PANEL_FILE.exists():
        etf_panel = pd.read_csv(ETF_PRICE_PANEL_FILE, parse_dates=["date"])
        etf_source_note = f"committed processed pipeline snapshot: {repo_path_label(ETF_PRICE_PANEL_FILE)}"
    else:
        etf_panel, etf_source_note = fetch_yfinance_price_panel(BROAD_MARKET_ETFS, start="2019-01-01")
        if etf_panel.empty:
            etf_panel = build_synthetic_price_panel(BROAD_MARKET_ETFS, start="2019-01-01", periods=756)
            etf_source_note = f"synthetic placeholder ETF panel because live download failed: {etf_source_note}"

    etf_panel = add_returns(etf_panel)
    etf_panel = estimate_flow_pressure_proxy(etf_panel)
    flow_proxy_ok = validate_etf_flow_proxy(etf_panel)
    etf_flow = aggregate_etf_flow_pressure(etf_panel)
    etf_flow["t"] = (pd.to_datetime(etf_flow["date"]) - pd.Timestamp("1994-01-01")).dt.days / 365.25
    etf_flow["passive_share"] = logistic_passive_share(etf_flow["t"], alpha=0.106, t0=30.0)

    print(etf_source_note)
    etf_flow.tail()
    return etf_flow, etf_panel, etf_source_note, flow_proxy_ok


@app.cell
def _(FIGURES_DIR, etf_flow, etf_source_note, mo, plot_flow_pressure):
    _note = mo.callout(mo.md(f"ETF data source note: `{etf_source_note}`"), kind="info")
    _fig_flow = plot_flow_pressure(etf_flow, output_path=FIGURES_DIR / "fig_08_etf_flow_pressure.png")
    mo.vstack([_note, _fig_flow])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Cross-Sectional Passive Pressure Extension

    The paper is market-level. This section creates a cross-sectional extension by asking whether stocks with larger index weights and lower liquidity are more exposed to passive-flow pressure.

    The demo universe is deliberately small: `AAPL`, `MSFT`, `NVDA`, `AMZN`, `META`, `GOOGL`, `BRK-B`, `LLY`, `JPM`, and `XOM`.
    If official historical index weights are unavailable, the notebook estimates index weight from market capitalization and labels it as an estimate.
    Do not interpret this demo universe as a full S&P 500 result.
    """)
    return


@app.cell
def _(
    DEMO_STOCK_UNIVERSE,
    EQUITY_LIQUIDITY_PANEL_FILE,
    add_drawdown,
    add_realized_volatility,
    add_rolling_adv,
    assign_pressure_quintiles,
    attach_latest_market_caps,
    build_synthetic_price_panel,
    compute_passive_dollar_pressure,
    compute_passive_pressure,
    estimate_index_weights_from_market_cap,
    fetch_yfinance_price_panel,
    logistic_passive_share,
    np,
    pd,
    repo_path_label,
    summarize_pressure_quintiles,
):
    if EQUITY_LIQUIDITY_PANEL_FILE.exists():
        equity_panel = pd.read_csv(EQUITY_LIQUIDITY_PANEL_FILE, parse_dates=["date"])
        equity_source_note = f"committed processed pipeline snapshot: {repo_path_label(EQUITY_LIQUIDITY_PANEL_FILE)}"
    else:
        equity_panel, equity_source_note = fetch_yfinance_price_panel(DEMO_STOCK_UNIVERSE, start="2021-01-01")
        if equity_panel.empty:
            equity_panel = build_synthetic_price_panel(
                DEMO_STOCK_UNIVERSE,
                start="2021-01-01",
                periods=756,
                include_market_cap=True,
            )
            equity_source_note = f"synthetic placeholder equity panel because live download failed: {equity_source_note}"
        else:
            equity_panel, cap_note = attach_latest_market_caps(equity_panel, DEMO_STOCK_UNIVERSE)
            equity_source_note = f"{equity_source_note}; {cap_note}"

    equity_panel = equity_panel.sort_values(["ticker", "date"])
    equity_panel["t"] = (pd.to_datetime(equity_panel["date"]) - pd.Timestamp("1994-01-01")).dt.days / 365.25
    equity_panel["passive_share"] = logistic_passive_share(equity_panel["t"], alpha=0.106, t0=30.0)

    pressure_panel = add_rolling_adv(equity_panel)
    pressure_panel = add_realized_volatility(pressure_panel)
    pressure_panel = add_drawdown(pressure_panel)
    pressure_panel = pressure_panel.sort_values(["ticker", "date"])
    pressure_panel["forward_5d_return"] = (
        pressure_panel.groupby("ticker")["adj_close"].shift(-5) / pressure_panel["adj_close"] - 1.0
    )
    pressure_panel["forward_20d_return"] = (
        pressure_panel.groupby("ticker")["adj_close"].shift(-20) / pressure_panel["adj_close"] - 1.0
    )

    pressure_panel = estimate_index_weights_from_market_cap(pressure_panel)
    pressure_panel = compute_passive_pressure(pressure_panel)
    pressure_panel = compute_passive_dollar_pressure(pressure_panel)
    pressure_panel = assign_pressure_quintiles(pressure_panel)
    pressure_summary = summarize_pressure_quintiles(pressure_panel)

    weight_sums = pressure_panel.groupby("date")["index_weight_estimate"].sum()
    index_weights_ok = bool(np.allclose(weight_sums.dropna(), 1.0, atol=1e-6))

    print(equity_source_note)
    pressure_summary
    return equity_panel, equity_source_note, index_weights_ok, pressure_panel, pressure_summary


@app.cell
def _(
    FIGURES_DIR,
    equity_source_note,
    mo,
    plot_latest_passive_pressure,
    plot_pressure_quintile_summary,
    pressure_panel,
    pressure_summary,
):
    _note = mo.callout(mo.md(f"Equity data source note: `{equity_source_note}`"), kind="info")

    _fig_latest = plot_latest_passive_pressure(
        pressure_panel,
        output_path=FIGURES_DIR / "fig_09_cross_sectional_pressure_latest.png",
    )

    _fig_summary = plot_pressure_quintile_summary(
        pressure_summary,
        raw_df=pressure_panel,
        output_path=FIGURES_DIR / "fig_10_pressure_quintile_summary.png",
    )
    mo.vstack([_note, _fig_latest, _fig_summary])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Sanity Check Summary

    The checks below are meant to keep the notebook honest.
    A failed check does not automatically invalidate the research idea, but it should be investigated before interpreting the figures.
    """)
    return


@app.cell
def _(
    S0,
    baseline_t30_share,
    checks_to_frame,
    etf_panel,
    flow_proxy_ok,
    index_weights_ok,
    make_check,
    no_passive_sim,
    no_terminal,
    np,
    passive_validation,
    rising_passive_sim,
    rising_terminal,
    threshold_values,
):
    _path_cols_no = [col for col in no_passive_sim["paths"].columns if col.startswith("path_")]
    _path_cols_rising = [col for col in rising_passive_sim["paths"].columns if col.startswith("path_")]
    no_negative_prices = bool(
        (no_passive_sim["paths"][_path_cols_no] >= 0.0).all().all()
        and (rising_passive_sim["paths"][_path_cols_rising] >= 0.0).all().all()
    )
    flow_proxy_finite = bool(
        flow_proxy_ok
        and np.isfinite(etf_panel.dropna(subset=["return"])["flow_pressure_proxy"]).all()
    )

    sanity_summary = checks_to_frame(
        [
            make_check(
                "passive_share_bounds",
                passive_validation["passive_share_bounds"],
                "all passive shares between 0 and 1",
            ),
            make_check(
                "passive_share_monotonic",
                passive_validation["passive_share_monotonic"],
                "logistic curves non-decreasing",
            ),
            make_check(
                "baseline_t30_near_50pct",
                abs(baseline_t30_share - 0.50) <= 0.01,
                f"p(t=30) = {baseline_t30_share:.3f}",
            ),
            make_check(
                "lyapunov_threshold_near_87pct",
                abs(threshold_values["lyapunov_threshold"] - 0.87) <= 0.02,
                f"threshold = {threshold_values['lyapunov_threshold']:.3f}",
            ),
            make_check(
                "feller_threshold_near_91pct",
                abs(threshold_values["feller_threshold"] - 0.91) <= 0.02,
                f"threshold = {threshold_values['feller_threshold']:.3f}",
            ),
            make_check(
                "no_passive_terminal_growth",
                no_terminal.median() > S0,
                f"median terminal S = {no_terminal.median():.2f}",
            ),
            make_check(
                "rising_passive_more_dispersion",
                (rising_terminal.std() / rising_terminal.median()) > (no_terminal.std() / no_terminal.median()),
                (
                    f"relative dispersion higher; rising CV = {rising_terminal.std() / rising_terminal.median():.2f}, "
                    f"no-passive CV = {no_terminal.std() / no_terminal.median():.2f}; "
                    f"absolute stds = {rising_terminal.std():.2f} vs {no_terminal.std():.2f}"
                ),
            ),
            make_check(
                "no_negative_prices",
                no_negative_prices,
                "no negative S after numerical guards",
            ),
            make_check(
                "flow_proxy_finite",
                flow_proxy_finite,
                "ETF flow proxy finite after cleaning",
            ),
            make_check(
                "index_weights_sum_to_one",
                index_weights_ok,
                "estimated weights sum close to 1 by date",
            ),
        ]
    )

    sanity_summary
    return (sanity_summary,)


if __name__ == "__main__":
    app.run()
