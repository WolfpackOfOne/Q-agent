import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # U.S. Presidential Elections and Stock Markets

    **Replicating Winterhalter (2025)** — _Evidence from the 2024 elections_

    This notebook regresses daily Fama-French 49 industry portfolio returns on changes
    in Polymarket's Trump win probability to identify which industries benefit or suffer
    from a rising Trump election probability.

    **Data sources — all fetched live, no local files required:**
    - **Polymarket CLOB API** — daily Trump YES-token probability (Jan–Nov 2024)
    - **Kenneth French Data Library** — 49 industry portfolio daily value-weighted returns
    - **yfinance** — factor ETF daily prices (MTUM, QUAL, VLUE, USMV, IWM, IWF, IWD, SPY)

    **Method:** OLS: $R_{i,t} = \\alpha_i + \\beta_i \\cdot \\Delta P(\\text{Trump})_t + \\varepsilon_{i,t}$
    """)
    return


@app.cell
def _():
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import requests
    import io
    import pathlib
    import zipfile
    from scipy import stats

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
    return io, np, pd, plt, requests, stats, zipfile


@app.cell
def _(mo):
    mo.callout(
        mo.md("""
        **All data is fetched live from public sources — no local files or credentials required.**

        - Polymarket CLOB API (Trump YES-token probability)
        - Kenneth French Data Library (49 industry portfolio returns)
        - yfinance (factor ETF prices: MTUM, QUAL, VLUE, USMV, IWM, IWF, IWD, SPY)
        """),
        kind="info",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Polymarket — Trump Win Probability (2024)

    Pull daily YES-token price history for "Will Donald Trump win the 2024 US Presidential Election?"
    from the Polymarket CLOB API. The price represents the market-implied probability of a Trump win.
    """)
    return


@app.cell
def _(pd, requests):
    # Trump YES token from the 2024 Presidential Election Winner event
    TRUMP_TOKEN = "21742633143463906290569050155826241533067272736897614950488156847949938836455"

    r = requests.get(
        "https://clob.polymarket.com/prices-history",
        params={"market": TRUMP_TOKEN, "interval": "max", "fidelity": 1440},
        timeout=30,
    )
    history = r.json().get("history", [])

    trump_prob = pd.DataFrame(history)
    trump_prob["date"] = pd.to_datetime(trump_prob["t"], unit="s").dt.normalize()
    trump_prob["prob_trump"] = trump_prob["p"].astype(float)
    trump_prob = trump_prob.set_index("date")[["prob_trump"]].sort_index()

    # Compute daily change in probability
    trump_prob["delta_prob"] = trump_prob["prob_trump"].diff()
    trump_prob = trump_prob.dropna()

    print(f"Trump probability: {len(trump_prob)} trading days")
    print(f"  Range: {trump_prob.index[0].date()} to {trump_prob.index[-1].date()}")
    print(f"  Prob range: {trump_prob['prob_trump'].min():.3f} – {trump_prob['prob_trump'].max():.3f}")
    print(f"  Mean daily ΔP: {trump_prob['delta_prob'].mean():.5f}")
    print(f"  Std daily ΔP:  {trump_prob['delta_prob'].std():.5f}")

    trump_prob
    return (trump_prob,)


@app.cell
def _(np, plt, trump_prob):

    _fig_prob, (_ax1, _ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[2, 1])

    # Top: Trump probability level
    _ax1.plot(trump_prob.index, trump_prob["prob_trump"], color="#58a6ff", linewidth=1.2)
    _ax1.axhline(0.5, color="#f85149", alpha=0.5, linestyle="--", label="50%")
    _ax1.fill_between(
        trump_prob.index,
        0.5,
        trump_prob["prob_trump"],
        where=trump_prob["prob_trump"] > 0.5,
        alpha=0.15,
        color="#3fb950",
    )
    _ax1.fill_between(
        trump_prob.index,
        0.5,
        trump_prob["prob_trump"],
        where=trump_prob["prob_trump"] < 0.5,
        alpha=0.15,
        color="#f85149",
    )
    _ax1.set_ylabel("P(Trump wins)")
    _ax1.set_title("Polymarket — Trump 2024 Election Probability")
    _ax1.legend(loc="upper left")
    _ax1.set_ylim(0.2, 0.8)

    # Bottom: daily change
    _colors_prob = np.where(trump_prob["delta_prob"] > 0, "#3fb950", "#f85149")
    _ax2.bar(trump_prob.index, trump_prob["delta_prob"], color=_colors_prob, width=1.0, alpha=0.7)
    _ax2.set_ylabel("ΔP(Trump)")
    _ax2.set_title("Daily Change in Trump Win Probability")
    _ax2.axhline(0, color="#30363d", linewidth=0.8)

    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Fama-French 49 Industry Portfolios

    Download daily value-weighted returns from Kenneth French's data library.
    Returns are in percent (0.50 = 0.50%). We filter to the 2024 election period.
    """)
    return


@app.cell
def _(io, pd, requests, zipfile):

    # Download FF 49 industry portfolios (daily)
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    _z = zipfile.ZipFile(io.BytesIO(resp.content))

    with _z.open(_z.namelist()[0]) as _f:
        _raw = _f.read().decode("utf-8")

    # Parse: find "Average Value Weighted Returns" section
    _lines = _raw.split("\n")
    _start_idx = None
    _end_idx = None
    for _i, _line in enumerate(_lines):
        if "Average Value Weighted Returns" in _line:
            _start_idx = _i + 1
            break

    _data_started = False
    for _i in range(_start_idx, len(_lines)):
        _stripped = _lines[_i].strip()
        if _stripped and _stripped[0].isdigit():
            _data_started = True
        elif _data_started and not _stripped:
            _end_idx = _i
            break

    _section = "\n".join(_lines[_start_idx:_end_idx])
    ff49 = pd.read_csv(io.StringIO(_section), index_col=0)
    ff49.index = pd.to_datetime(ff49.index.astype(str).str.strip(), format="%Y%m%d")
    ff49.index.name = "date"
    ff49.columns = ff49.columns.str.strip()

    # Replace missing values
    ff49 = ff49.replace([-99.99, -999.0], float("nan"))

    # Filter to 2024 election period
    ff49_2024 = ff49.loc["2024-01-01":"2024-11-06"].copy()

    print(f"FF49 industries: {ff49_2024.shape[1]}")
    print(f"Trading days in 2024 sample: {len(ff49_2024)}")
    print(f"Date range: {ff49_2024.index[0].date()} to {ff49_2024.index[-1].date()}")
    print(f"\nIndustry names:\n{list(ff49_2024.columns)}")

    ff49_2024
    return (ff49_2024,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. Merge: Industry Returns × ΔP(Trump)

    Align on trading dates. Polymarket trades 24/7 but FF returns are business-day only.
    We use the Polymarket daily close that maps to each trading date.
    """)
    return


@app.cell
def _(ff49_2024, pd, trump_prob):

    # Merge on date — inner join keeps only dates present in both
    merged = pd.merge(
        ff49_2024,
        trump_prob[["prob_trump", "delta_prob"]],
        left_index=True,
        right_index=True,
        how="inner",
    )

    print(f"Merged dataset: {len(merged)} trading days × {merged.shape[1]} columns")
    print(f"Date range: {merged.index[0].date()} to {merged.index[-1].date()}")
    print(f"\nCorrelation of ΔP(Trump) with selected industries:")
    _industries_to_show = ["Oil", "Guns", "Coal", "Drugs", "Hlth", "Util", "Fin", "Banks", "Steel", "Aero"]
    _available = [c for c in _industries_to_show if c in merged.columns]
    for _ind in _available:
        _corr = merged[_ind].corr(merged["delta_prob"])
        print(f"  {_ind:8s}: {_corr:+.4f}")

    merged
    return (merged,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 4. OLS Regressions: $R_{i,t} = \alpha_i + \beta_i \cdot \Delta P(\text{Trump})_t + \varepsilon_{i,t}$

    For each of the 49 industries, regress daily returns on the daily change in Trump
    win probability. The $\beta_i$ coefficient tells us how many basis points industry $i$
    moves per 1 percentage-point increase in Trump probability.

    Following Winterhalter (2025), we interpret statistically significant positive betas as
    "Trump-benefiting" industries and negative betas as "Trump-hurting" industries.
    """)
    return


@app.cell
def _(merged, np, pd, stats):

    industry_cols = [c for c in merged.columns if c not in ("prob_trump", "delta_prob")]

    _results = []
    for _ind in industry_cols:
        _y = merged[_ind].values
        _x = merged["delta_prob"].values

        _mask = ~(np.isnan(_y) | np.isnan(_x))
        if _mask.sum() < 30:
            continue

        _slope, _intercept, _r_value, _p_value, _se = stats.linregress(_x[_mask], _y[_mask])
        _t_stat = _slope / _se if _se > 0 else 0.0

        _results.append(
            {
                "industry": _ind,
                "beta": _slope,
                "alpha": _intercept,
                "t_stat": _t_stat,
                "p_value": _p_value,
                "r_squared": _r_value**2,
                "n_obs": int(_mask.sum()),
                "se": _se,
            }
        )

    ols_results = pd.DataFrame(_results).sort_values("beta", ascending=False).reset_index(drop=True)

    ols_results["sig_10"] = ols_results["p_value"] < 0.10
    ols_results["sig_5"] = ols_results["p_value"] < 0.05
    ols_results["sig_1"] = ols_results["p_value"] < 0.01

    _n_sig5 = ols_results["sig_5"].sum()
    _n_sig10 = ols_results["sig_10"].sum()

    print(f"OLS results for {len(ols_results)} industries")
    print(f"Significant at 5%: {_n_sig5} industries")
    print(f"Significant at 10%: {_n_sig10} industries")
    print(f"\nTop 10 Trump-benefiting industries (positive β):")
    print(ols_results[["industry", "beta", "t_stat", "p_value", "r_squared"]].head(10).to_string(index=False))
    print(f"\nTop 10 Trump-hurting industries (negative β):")
    print(ols_results[["industry", "beta", "t_stat", "p_value", "r_squared"]].tail(10).to_string(index=False))

    ols_results
    return (ols_results,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 5. Results: Industry Betas on ΔP(Trump)

    Bar chart of $\beta_i$ coefficients sorted by magnitude.
    Green = Trump-benefiting (positive β), Red = Trump-hurting (negative β).
    Stars indicate statistical significance: * p<0.10, ** p<0.05, *** p<0.01.
    """)
    return


@app.cell
def _(np, ols_results, plt):

    _fig_beta, _ax_beta = plt.subplots(figsize=(16, 8))

    _sorted_res = ols_results.sort_values("beta", ascending=True)
    _colors_beta = np.where(_sorted_res["beta"] > 0, "#3fb950", "#f85149")
    _edge_colors = np.where(_sorted_res["sig_5"], "#e3b341", "#30363d")
    _linewidths = np.where(_sorted_res["sig_5"], 1.5, 0.5)

    _ax_beta.barh(
        range(len(_sorted_res)),
        _sorted_res["beta"],
        color=_colors_beta,
        edgecolor=_edge_colors,
        linewidth=_linewidths,
        alpha=0.85,
    )

    for _i, (_, _row) in enumerate(_sorted_res.iterrows()):
        _stars = ""
        if _row["sig_1"]:
            _stars = "***"
        elif _row["sig_5"]:
            _stars = "**"
        elif _row["sig_10"]:
            _stars = "*"
        if _stars:
            _x_pos = _row["beta"] + (0.3 if _row["beta"] > 0 else -0.3)
            _ax_beta.text(_x_pos, _i, _stars, ha="center", va="center", fontsize=8, color="#e3b341")

    _ax_beta.set_yticks(range(len(_sorted_res)))
    _ax_beta.set_yticklabels(_sorted_res["industry"], fontsize=8)
    _ax_beta.set_xlabel("β coefficient (return bps per 1pp ΔP(Trump))")
    _ax_beta.set_title(
        "Industry Sensitivity to Trump Election Probability\n"
        "Winterhalter (2025) replication — Polymarket × FF49, Jan–Nov 2024"
    )
    _ax_beta.axvline(0, color="#8b949e", linewidth=0.8)

    from matplotlib.patches import Patch
    _legend_elements = [
        Patch(facecolor="#3fb950", label="Trump-benefiting (β > 0)"),
        Patch(facecolor="#f85149", label="Trump-hurting (β < 0)"),
        Patch(facecolor="none", edgecolor="#e3b341", linewidth=1.5, label="Significant at 5%"),
    ]
    _ax_beta.legend(handles=_legend_elements, loc="lower right", fontsize=9)

    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 6. Top Movers — Scatter Plots

    Scatter plots for the 3 most positive and 3 most negative β industries,
    showing the relationship between daily ΔP(Trump) and industry returns.
    """)
    return


@app.cell
def _(merged, np, ols_results, plt, stats):

    _top_pos = ols_results.head(3)["industry"].tolist()
    _top_neg = ols_results.tail(3)["industry"].tolist()
    _showcase = _top_pos + _top_neg

    _fig_scat, _axes_scat = plt.subplots(2, 3, figsize=(16, 10))

    for _ax_s, _ind_s in zip(_axes_scat.flatten(), _showcase):
        _x_s = merged["delta_prob"].values
        _y_s = merged[_ind_s].values
        _mask_s = ~(np.isnan(_x_s) | np.isnan(_y_s))

        _ax_s.scatter(_x_s[_mask_s] * 100, _y_s[_mask_s], alpha=0.4, s=12, color="#58a6ff", edgecolors="none")

        _slope_s, _intercept_s, _, _, _ = stats.linregress(_x_s[_mask_s], _y_s[_mask_s])
        _x_line = np.linspace(_x_s[_mask_s].min(), _x_s[_mask_s].max(), 100)
        _ax_s.plot(_x_line * 100, _intercept_s + _slope_s * _x_line, color="#f85149", linewidth=1.5)

        _beta_row = ols_results[ols_results["industry"] == _ind_s].iloc[0]
        _stars_s = "***" if _beta_row["sig_1"] else ("**" if _beta_row["sig_5"] else ("*" if _beta_row["sig_10"] else ""))

        _ax_s.set_title(f"{_ind_s} (β={_slope_s:.1f}{_stars_s})", fontsize=11)
        _ax_s.set_xlabel("ΔP(Trump) (pp)")
        _ax_s.set_ylabel("Return (%)")
        _ax_s.axhline(0, color="#30363d", linewidth=0.5)
        _ax_s.axvline(0, color="#30363d", linewidth=0.5)

    plt.suptitle(
        "Top 3 Trump-Benefiting and Trump-Hurting Industries",
        fontsize=14,
        fontweight="bold",
        color="#c9d1d9",
    )
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 7. Robustness: Rolling Beta Stability

    Compute 60-day rolling betas for selected industries to check whether
    the relationship is stable or driven by a few extreme days.
    """)
    return


@app.cell
def _(merged, np, pd, plt):

    def rolling_beta(_y_col, _x_col, _df, window=60):
        """Compute rolling OLS beta."""
        _betas = []
        for _j in range(window, len(_df)):
            _yy = _df[_y_col].iloc[_j - window : _j].values
            _xx = _df[_x_col].iloc[_j - window : _j].values
            _m = ~(np.isnan(_yy) | np.isnan(_xx))
            if _m.sum() < 20:
                _betas.append(np.nan)
                continue
            _cov = np.cov(_xx[_m], _yy[_m])
            _beta = _cov[0, 1] / _cov[0, 0] if _cov[0, 0] > 0 else np.nan
            _betas.append(_beta)
        _idx = _df.index[window:]
        return pd.Series(_betas, index=_idx)

    _showcase_industries = ["Oil", "Coal", "Guns", "Drugs", "Hlth", "Fin", "Banks", "Steel"]
    _available_showcase = [c for c in _showcase_industries if c in merged.columns]

    _fig_roll, _ax_roll = plt.subplots(figsize=(14, 6))
    _cmap = plt.cm.Set2
    for _k, _ind_r in enumerate(_available_showcase[:6]):
        _rb = rolling_beta(_ind_r, "delta_prob", merged, window=60)
        _ax_roll.plot(_rb.index, _rb.values, label=_ind_r, color=_cmap(_k), linewidth=1.2, alpha=0.8)

    _ax_roll.axhline(0, color="#f85149", alpha=0.5, linestyle="--")
    _ax_roll.set_ylabel("Rolling 60-day β")
    _ax_roll.set_title("Rolling Beta Stability — Industry Returns on ΔP(Trump)")
    _ax_roll.legend(loc="best", fontsize=9)
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 8. Event Windows — Key Dates

    Zoom into specific events that caused large probability swings:
    - **Biden dropout** (Jul 21, 2024) — Biden drops out, Harris enters
    - **Trump assassination attempt** (Jul 13, 2024) — probability spike
    - **Debate nights** — Sep 10, Jun 27
    - **Election day** (Nov 5, 2024) — resolution

    Show cumulative industry returns in narrow windows around these events.
    """)
    return


@app.cell
def _(merged, np, pd, plt):

    _events = {
        "Biden Dropout\n(Jul 21)": pd.Timestamp("2024-07-22"),
        "Trump Assassination\nAttempt (Jul 13)": pd.Timestamp("2024-07-15"),
        "Biden-Trump\nDebate (Jun 27)": pd.Timestamp("2024-06-28"),
        "Harris-Trump\nDebate (Sep 10)": pd.Timestamp("2024-09-10"),
        "Election Day\n(Nov 5)": pd.Timestamp("2024-11-05"),
    }

    _industry_cols_ev = [c for c in merged.columns if c not in ("prob_trump", "delta_prob")]
    _event_data = []

    for _label, _date in _events.items():
        _idx_ev = merged.index.get_indexer([_date], method="nearest")[0]
        if _idx_ev < 0 or _idx_ev >= len(merged):
            continue
        _actual_date = merged.index[_idx_ev]
        _dp = merged.loc[_actual_date, "delta_prob"]
        _returns = merged.loc[_actual_date, _industry_cols_ev]
        _top3 = _returns.nlargest(3)
        _bot3 = _returns.nsmallest(3)
        _event_data.append(
            {
                "event": _label,
                "date": _actual_date.date(),
                "delta_p": _dp,
                "top_3": ", ".join(f"{k} ({v:+.2f}%)" for k, v in _top3.items()),
                "bottom_3": ", ".join(f"{k} ({v:+.2f}%)" for k, v in _bot3.items()),
            }
        )

    _event_df = pd.DataFrame(_event_data)
    print(_event_df[["event", "date", "delta_p", "top_3", "bottom_3"]].to_string(index=False))

    _fig_ev, _ax_ev = plt.subplots(figsize=(14, 5))
    _x_ev = np.arange(len(_event_data))
    _dp_vals = [e["delta_p"] for e in _event_data]
    _colors_ev = ["#3fb950" if v > 0 else "#f85149" for v in _dp_vals]
    _ax_ev.bar(_x_ev, [v * 100 for v in _dp_vals], color=_colors_ev, edgecolor="#30363d", linewidth=0.5)
    _ax_ev.set_xticks(_x_ev)
    _ax_ev.set_xticklabels([e["event"] for e in _event_data], fontsize=9)
    _ax_ev.set_ylabel("ΔP(Trump) (pp)")
    _ax_ev.set_title("Key Event Days — Change in Trump Election Probability")
    _ax_ev.axhline(0, color="#8b949e", linewidth=0.8)
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 9. Summary & Interpretation

    **Key findings (replicating Winterhalter 2025 approach):**

    1. **Energy industries** (Oil, Coal) tend to have positive betas — a rising Trump probability
       is associated with higher energy returns, consistent with expectations of looser environmental
       regulation and more favorable fossil fuel policy.

    2. **Healthcare and Drugs** tend to have negative betas — markets price in higher regulation
       risk or policy uncertainty for healthcare under different administrations.

    3. **Financial sectors** (Banks, Fin, Insurance) show positive sensitivity — reflecting
       expectations of deregulation.

    4. **Defense/Aerospace** — positive betas consistent with expectations of higher defense spending.

    **Caveats:**
    - R² values are low (typical for daily cross-sectional regressions)
    - Polymarket liquidity varied significantly over the sample
    - Confounding macro factors (Fed policy, earnings season) are not controlled for
    - This is a simple bivariate regression; Winterhalter (2025) includes additional controls

    **References:**
    - Winterhalter, S. (2025). _U.S. presidential elections and stock markets: Evidence from the 2024 elections._ Aalto University thesis.
    - Amburgey, A.J. (2025). _How Election Shocks Move Markets._ arXiv.
    - Snowberg, Wolfers, & Zitzewitz (2007). _Partisan Impacts on the Economy._ QJE.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 10. Factor ETF Sensitivity to ΔP(Trump)

    For eight US equity factor ETFs, compute monthly total return and regress against
    monthly ΔP(Trump win). Positive beta = the factor style benefited when Trump's
    election odds rose; negative = it was hurt.

    ETFs: **MTUM** (momentum), **QUAL** (quality), **VLUE** (value), **USMV** (min-vol),
    **IWM** (size), **IWF** (growth), **IWD** (value R1000), **SPY** (market).
    """)
    return


@app.cell
def _(np, pd, trump_prob):
    import yfinance as _yf
    from scipy import stats as _stats

    _FACTOR_ETFS = {
        "MTUM": "Momentum",
        "QUAL": "Quality",
        "VLUE": "Value",
        "USMV": "Low Vol",
        "IWM":  "Size",
        "IWF":  "Growth",
        "IWD":  "Value (R1K)",
        "SPY":  "Market",
    }

    # ── 1. Download 2024 daily prices ────────────────────────────────────
    try:
        _raw = _yf.download(
            list(_FACTOR_ETFS), start="2024-01-01", end="2024-12-01",
            auto_adjust=True, progress=False,
        )["Close"]
        _monthly_ret = _raw.resample("ME").last().pct_change().dropna()
    except Exception as _e:
        print(f"yfinance download failed: {_e}")
        _monthly_ret = pd.DataFrame()

    # ── 2. Monthly ΔP(Trump) ─────────────────────────────────────────────
    _dp_trump = trump_prob["prob_trump"].resample("ME").last().diff().dropna()

    # ── 3. Align and run OLS per ETF ─────────────────────────────────────
    aligned = pd.concat([_monthly_ret, _dp_trump.rename("dp_trump")], axis=1).dropna(subset=["dp_trump"])

    _rows = []
    for _ticker, _label in _FACTOR_ETFS.items():
        if _ticker not in aligned.columns:
            continue
        _y = aligned[_ticker].dropna()
        _x = aligned.loc[_y.index, "dp_trump"].values
        if len(_y) < 5 or np.std(_y.values) < 1e-8:
            continue
        _slope, _intercept, _rv, _pv, _se = _stats.linregress(_x, _y.values)
        _rows.append({
            "ETF": _ticker,
            "Factor": _label,
            "beta": round(_slope, 4),
            "t_stat": round(_slope / _se, 3) if _se > 0 else np.nan,
            "p_value": round(_pv, 4),
            "r2": round(_rv**2, 4),
            "N": len(_y),
        })

    if _rows:
        factor_ols = pd.DataFrame(_rows).sort_values("beta", ascending=False).reset_index(drop=True)
    else:
        # Empty schema so downstream `factor_ols.empty` branch can render.
        factor_ols = pd.DataFrame(columns=["ETF", "Factor", "beta", "t_stat", "p_value", "r2", "N"])
    factor_ols
    return aligned, factor_ols


@app.cell
def _(aligned, factor_ols, np, plt):
    if factor_ols.empty:
        _fig_gf, _ax_gf = plt.subplots(figsize=(10, 5))
        _ax_gf.text(0.5, 0.5, "No data — yfinance download failed.", ha="center", va="center",
                    transform=_ax_gf.transAxes)
    else:
        _labels  = factor_ols["Factor"].tolist()
        _betas   = factor_ols["beta"].tolist()
        _pvals   = factor_ols["p_value"].tolist()
        _tstats  = factor_ols["t_stat"].tolist()
        _colors  = ["#10b981" if b > 0 else "#ef4444" for b in _betas]
        _alphas  = [0.9 if p < 0.1 else 0.45 for p in _pvals]

        _fig_gf, _ax_gf = plt.subplots(figsize=(11, 5))
        _bars = _ax_gf.barh(
            _labels, _betas, color=_colors,
            edgecolor="#30363d", linewidth=0.5,
        )
        for _bar, _a in zip(_bars, _alphas):
            _bar.set_alpha(_a)

        _ax_gf.axvline(0, color="gray", lw=0.8, ls="--")
        _ax_gf.set_xlabel("Beta  (monthly ETF return ~ ΔP(Trump win))")
        _ax_gf.set_title(
            "Factor ETF Sensitivity to ΔP(Trump Win)  |  Monthly, Jan–Nov 2024\n"
            "Green = benefited from rising Trump odds  |  Faded = p > 0.10",
            fontweight="bold", fontsize=11,
        )

        _pad = max(abs(b) for b in _betas) * 0.05
        for _bar, _t in zip(_bars, _tstats):
            _x = _bar.get_width()
            _ax_gf.text(
                _x + (_pad if _x >= 0 else -_pad),
                _bar.get_y() + _bar.get_height() / 2,
                f"t={_t:.2f}",
                va="center", ha="left" if _x >= 0 else "right", fontsize=9,
            )

        # Scatter insets for top-3 by |t-stat|
        _dp_vals = aligned["dp_trump"].values
        _top3 = factor_ols.reindex(factor_ols["t_stat"].abs().nlargest(3).index)
        _inset_colors = ["#3b82f6", "#f59e0b", "#8b5cf6"]

        for _i, ((_, _row), _clr) in enumerate(zip(_top3.iterrows(), _inset_colors)):
            _ax_ins = _fig_gf.add_axes([0.62 + _i * 0.125, 0.15, 0.10, 0.30])
            _col = _row["ETF"]
            if _col not in aligned.columns:
                continue
            _ys = aligned[_col].values
            _mask = ~np.isnan(_ys)
            _xi, _yi = _dp_vals[_mask], _ys[_mask]
            _ax_ins.scatter(_xi, _yi, color=_clr, s=25, zorder=3, alpha=0.85)
            _xline = np.linspace(_xi.min(), _xi.max(), 50)
            _ax_ins.plot(_xline, _row["beta"] * _xline + (_yi.mean() - _row["beta"] * _xi.mean()),
                         color=_clr, lw=1.5)
            _ax_ins.axhline(0, color="gray", lw=0.5, ls="--")
            _ax_ins.axvline(0, color="gray", lw=0.5, ls="--")
            _ax_ins.set_title(_row["Factor"], fontsize=7, fontweight="bold")
            _ax_ins.tick_params(labelsize=6)
            _ax_ins.set_facecolor("#161b22")

    plt.tight_layout()
    plt.gca()
    return


if __name__ == "__main__":
    app.run()
