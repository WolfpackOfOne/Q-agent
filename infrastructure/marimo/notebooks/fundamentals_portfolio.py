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
    # Fundamental Cross-Sectional Long/Short Strategy

    A quarterly, dollar-neutral long/short equity strategy on the largest
    1,000 US companies, ranked by a machine-learning score built from
    quarterly financial-statement ratios (Compustat, via WRDS, linked to
    CRSP prices).

    **Workflow**: load point-in-time fundamentals and prices → clean and
    engineer ratio features → build a monthly panel → select statistically
    significant features → score the cross-section with a gradient-boosted
    model → construct a decile long/short book → evaluate on a held-out
    test period.
    """)
    return


@app.cell
def _():
    import pathlib
    import warnings

    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import GradientBoostingRegressor

    warnings.filterwarnings("ignore")
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
    FUND_DIR = REPO / "infrastructure" / "pipelines" / "wrds" / "lean-data" / "alternative" / "fundamentals"
    FUND_CSV = FUND_DIR / "broad_quarterly_fundamentals.csv"
    UNIVERSE_CSV = FUND_DIR / "broad_universe.csv"
    PERMNO_MAP_CSV = FUND_DIR / "broad_permno_map.csv"
    TRI_CSV = FUND_DIR / "broad_monthly_tri.csv"
    SCORES_OUT = REPO / "MyProjects" / "FundamentalsPortfolio" / "data" / "fundamental_scores.csv"

    N_UNIVERSE = 1000       # universe size at each quarter-end: largest N companies by reported market cap
    H = 3                   # holding horizon in months — one calendar quarter, matching the data release cadence
    COST_BPS = 10           # one-way transaction cost on notional traded
    MISSING_MAX = 0.05      # a feature is used only if every raw input is populated for >= 95% of company-quarters
    IC_T_MIN = 1.5           # a feature is used only if its training-period correlation with returns is statistically significant
    LS_FRACTION = 0.10       # decile long/short: top and bottom 10% of the ranked universe
    TRAIN_START, TRAIN_END = pd.Timestamp("2005-01-01"), pd.Timestamp("2018-12-31")
    VAL_START, VAL_END = pd.Timestamp("2019-01-01"), pd.Timestamp("2021-12-31")
    TEST_START, TEST_END = pd.Timestamp("2022-01-01"), pd.Timestamp("2023-12-31")
    return (
        COST_BPS,
        FUND_CSV,
        GradientBoostingRegressor,
        H,
        IC_T_MIN,
        LS_FRACTION,
        MISSING_MAX,
        N_UNIVERSE,
        PERMNO_MAP_CSV,
        SCORES_OUT,
        TEST_END,
        TEST_START,
        TRAIN_END,
        TRAIN_START,
        TRI_CSV,
        UNIVERSE_CSV,
        VAL_END,
        VAL_START,
        np,
        pd,
        plt,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Load the data

    Four inputs, all keyed on CRSP **PERMNO** (a permanent security
    identifier — tickers are reused across companies over time and are not
    a safe join key):

    | File | Contents |
    |---|---|
    | `broad_quarterly_fundamentals.csv` | one row per company-quarter, income statement / balance sheet / cash flow, dated by earnings-release date |
    | `broad_universe.csv` | the largest N companies by reported market cap at each calendar quarter-end (point-in-time membership) |
    | `broad_monthly_tri.csv` | month-end total-return index per company, dividends included |
    | `broad_permno_map.csv` | PERMNO → tradable ticker |
    """)
    return


@app.cell
def _(FUND_CSV, N_UNIVERSE, PERMNO_MAP_CSV, TRI_CSV, UNIVERSE_CSV, mo, pd):
    _missing = [p.name for p in (FUND_CSV, UNIVERSE_CSV, PERMNO_MAP_CSV, TRI_CSV) if not p.exists()]
    mo.stop(
        bool(_missing),
        mo.callout(mo.md(f"Data files missing: `{', '.join(_missing)}` — run "
                         "`python scripts/run_broad_quarterly_pipeline.py` from `infrastructure/pipelines/wrds/` "
                         "(needs WRDS credentials, ~15 min)."), kind="warn"),
    )

    fund_raw = pd.read_csv(FUND_CSV, parse_dates=["AvailableDate", "ReportDate", "FiscalQuarterEnd"])
    universe = pd.read_csv(UNIVERSE_CSV, parse_dates=["quarter_end"])
    universe = universe[universe["rank"] <= N_UNIVERSE]
    permno_map = pd.read_csv(PERMNO_MAP_CSV).set_index("permno")["lean_ticker"]
    tri_long = pd.read_csv(TRI_CSV, parse_dates=["date"])

    _members = set(universe["permno"])
    fund_raw = fund_raw[fund_raw["permno"].isin(_members)]
    fund_raw = fund_raw[fund_raw["ReportDate"].notna()].reset_index(drop=True)

    _per_q = universe.groupby("quarter_end")["permno"].count()
    mo.vstack([
        mo.md(
            f"**{len(fund_raw):,} company-quarters**, {fund_raw['permno'].nunique():,} companies. "
            f"Universe: {universe['quarter_end'].nunique()} quarter-ends, ~{int(_per_q.mean())} names each, "
            f"{universe['quarter_end'].min().date()} → {universe['quarter_end'].max().date()}."
        ),
        fund_raw.head(5),
        universe.head(5),
    ])
    return fund_raw, permno_map, tri_long, universe


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Feature admission

    Quarterly cash-flow items are reported year-to-date and are converted
    to single-quarter flows on each company's own fiscal calendar. A
    candidate feature is used only if every one of its raw inputs is
    populated for at least 95% of company-quarters — this keeps the model
    from relying on line items that many companies simply don't report
    (e.g. R&D spending for non-tech firms), which would otherwise have to
    be filled with an assumed value.
    """)
    return


@app.cell
def _(MISSING_MAX, fund_raw, mo, plt):
    FEATURE_INPUTS = {
        "gross_margin": ["saleq", "cogsq"], "net_margin": ["niq", "saleq"],
        "roa": ["niq", "atq"], "roe": ["niq", "ceqq"], "gross_prof_a": ["saleq", "cogsq", "atq"],
        "sales_growth": ["saleq"], "ni_change_a": ["niq", "atq"], "asset_growth": ["atq"],
        "accruals": ["niq", "oancfy", "atq"], "ocf_a": ["oancfy", "atq"],
        "cash_a": ["cheq", "atq"], "capex_a": ["capxy", "atq"], "share_change": ["cshoq"],
        "earnings_yield": ["niq", "prccq", "cshoq"], "book_to_mkt": ["ceqq", "prccq", "cshoq"],
        "sales_to_mkt": ["saleq", "prccq", "cshoq"], "fcf_yield": ["oancfy", "capxy", "prccq", "cshoq"],
    }
    missing_pct = fund_raw.isna().mean()
    FEATURES = [f for f, cols in FEATURE_INPUTS.items() if all(missing_pct[c] <= MISSING_MAX for c in cols)]

    _cols = sorted({c for cols in FEATURE_INPUTS.values() for c in cols}, key=lambda c: -missing_pct[c])
    _fig, _ax = plt.subplots(figsize=(14, 5))
    _vals = missing_pct[_cols].values * 100
    _colors = ["#f85149" if v > MISSING_MAX * 100 else "#3fb950" for v in _vals]
    _ax.bar(_cols, _vals, color=_colors, edgecolor="#30363d", linewidth=0.5)
    _ax.axhline(MISSING_MAX * 100, color="#f85149", alpha=0.7, linewidth=1, linestyle="--", label="5% admission threshold")
    _ax.set_ylabel("Missing (%)")
    _ax.set_title(f"Missing values by input field — {len(fund_raw):,} company-quarters")
    _ax.legend(framealpha=0.3)
    _ax.tick_params(axis="x", rotation=45, labelsize=9)
    for _lbl in _ax.get_xticklabels():
        _lbl.set_ha("right")
    plt.tight_layout()
    plt.show()

    mo.md(f"**{len(FEATURES)} features admitted**: " + ", ".join(f"`{f}`" for f in FEATURES))
    return (FEATURES,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Feature engineering

    Each admitted feature is expressed as a scale-free ratio so companies
    of different sizes are directly comparable: profitability (margins,
    ROA, ROE, gross profitability), growth, cash-flow quality (accruals,
    operating cash flow), balance-sheet strength (cash), investment
    (capex, share issuance), and valuation (earnings yield, book-to-market,
    sales-to-market, free-cash-flow yield). Valuation ratios are re-priced
    monthly against the current market price.
    """)
    return


@app.cell
def _(FEATURES, fund_raw, mo, np, pd):
    _f = fund_raw.sort_values(["permno", "FiscalQuarterEnd"]).reset_index(drop=True)
    _f["qidx"] = _f["FiscalYear"] * 4 + _f["FiscalQuarter"]
    for _c in ["xrdq", "gdwlq", "intanq", "xintq", "sstky", "prstkcy", "dvy"]:
        _f[_c] = _f[_c].fillna(0.0)
    _f["mktcap_q"] = _f["prccq"] * _f["cshoq"]

    _g = _f.groupby("permno")
    _prev_q = _g["qidx"].shift(1)
    for _ytd, _qcol in {"oancfy": "ocfq", "capxy": "capxq_", "dvy": "dvq", "sstky": "sstkq", "prstkcy": "prstkcq"}.items():
        _prev = _g[_ytd].shift(1)
        _q = (_f[_ytd] - _prev).where(_prev_q == _f["qidx"] - 1)
        _f[_qcol] = _q.where(_f["FiscalQuarter"] != 1, _f[_ytd])
    _g = _f.groupby("permno")

    def _ttm(col):
        _s = _g[col].rolling(4, min_periods=4).sum().reset_index(level=0, drop=True)
        return _s.where((_g["qidx"].shift(0) - _g["qidx"].shift(3)) == 3)

    def _lag4(col):
        return _g[col].shift(4).where((_g["qidx"].shift(0) - _g["qidx"].shift(4)) == 4)

    for _c in ["saleq", "cogsq", "niq", "ocfq", "capxq_"]:
        _f[_c + "_ttm"] = _ttm(_c)
    for _c in ["atq", "saleq", "niq", "cshoq"]:
        _f[_c + "_lag4"] = _lag4(_c)

    _at_avg = (_f["atq"] + _f["atq_lag4"]) / 2
    feat = pd.DataFrame({"permno": _f["permno"], "Ticker": _f["Ticker"], "AvailableDate": _f["AvailableDate"],
                         "FiscalQuarterEnd": _f["FiscalQuarterEnd"]})
    feat["gross_margin"] = (_f["saleq_ttm"] - _f["cogsq_ttm"]) / _f["saleq_ttm"]
    feat["net_margin"] = _f["niq_ttm"] / _f["saleq_ttm"]
    feat["roa"] = _f["niq_ttm"] / _at_avg
    feat["roe"] = _f["niq_ttm"] / _f["ceqq"]
    feat["gross_prof_a"] = (_f["saleq_ttm"] - _f["cogsq_ttm"]) / _f["atq"]
    feat["sales_growth"] = _f["saleq"] / _f["saleq_lag4"] - 1
    feat["ni_change_a"] = (_f["niq"] - _f["niq_lag4"]) / _f["atq"]
    feat["asset_growth"] = _f["atq"] / _f["atq_lag4"] - 1
    feat["accruals"] = (_f["niq_ttm"] - _f["ocfq_ttm"]) / _f["atq"]
    feat["ocf_a"] = _f["ocfq_ttm"] / _f["atq"]
    feat["cash_a"] = _f["cheq"] / _f["atq"]
    feat["capex_a"] = _f["capxq__ttm"] / _f["atq"]
    feat["share_change"] = _f["cshoq"] / _f["cshoq_lag4"] - 1
    feat["mktcap_q"] = _f["mktcap_q"]
    feat["ni_ttm"] = _f["niq_ttm"]
    feat["ceqq"] = _f["ceqq"]
    feat["sale_ttm"] = _f["saleq_ttm"]
    feat["fcf_ttm"] = _f["ocfq_ttm"] - _f["capxq__ttm"]
    feat = feat.replace([np.inf, -np.inf], np.nan)

    VALUATION = {"earnings_yield": "ni_ttm", "book_to_mkt": "ceqq", "sales_to_mkt": "sale_ttm", "fcf_yield": "fcf_ttm"}
    mo.md(f"**{len(FEATURES)} features** ready: " + ", ".join(f"`{c}`" for c in FEATURES))
    return VALUATION, feat


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Point-in-time panel and split

    At each calendar quarter-end: the universe members on that date, each
    company's latest filing already public by then, cross-sectional rank
    transform (each feature mapped to [-0.5, 0.5] within the quarter — a
    standard way to combine ratios of different scale and distribution and
    keep the score robust to outliers), and the next quarter's return
    relative to the universe average as the prediction target.

    The panel is split chronologically into training (2005–2018),
    validation (2019–2021), and test (2022–2023) periods, so that the
    model is fit and its configuration fixed before it is ever scored on
    the test period.
    """)
    return


@app.cell
def _(
    FEATURES,
    H,
    N_UNIVERSE,
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
    VALUATION,
    VAL_END,
    VAL_START,
    feat,
    mo,
    np,
    pd,
    tri_long,
    universe,
):
    _tri = tri_long.copy()
    _tri["month"] = _tri["date"].dt.to_period("M")
    tri_wide = _tri.pivot_table(index="month", columns="permno", values="tri")
    _fwd = tri_wide.shift(-H) / tri_wide - 1

    def build_panel():
        _u = universe[universe["rank"] <= N_UNIVERSE]
        _feat_sorted = feat.sort_values("AvailableDate")
        _rows = []
        for _q, _mem in _u.groupby("quarter_end"):
            _qm = _q.to_period("M")
            if _qm not in _fwd.index:
                continue
            _pool = _feat_sorted[(_feat_sorted["AvailableDate"] <= _q) & (_feat_sorted["FiscalQuarterEnd"] >= _q - pd.DateOffset(days=120))]
            _latest = _pool.drop_duplicates("permno", keep="last")
            _m = _latest[_latest["permno"].isin(_mem["permno"])].copy()
            if _m.empty:
                continue
            _fqe_m = _m["FiscalQuarterEnd"].dt.to_period("M")
            _tri_q = np.array([tri_wide.at[_qm, _p] if _p in tri_wide.columns else np.nan for _p in _m["permno"]])
            _tri_f = np.array([tri_wide.at[_pm, _p] if (_p in tri_wide.columns and _pm in tri_wide.index) else np.nan
                               for _p, _pm in zip(_m["permno"], _fqe_m)])
            _mktcap_t = _m["mktcap_q"].values * (_tri_q / _tri_f)
            for _name, _num in VALUATION.items():
                _m[_name] = _m[_num].values / _mktcap_t
            _m["date"] = _q
            _m["fwd_h"] = [_fwd.at[_qm, _p] if _p in _fwd.columns else np.nan for _p in _m["permno"]]
            _rows.append(_m)
        _p = pd.concat(_rows, ignore_index=True).replace([np.inf, -np.inf], np.nan)
        _p = _p.dropna(subset=["fwd_h"])
        _p = _p[_p[FEATURES].notna().sum(axis=1) >= len(FEATURES) - 3]

        def _xs_rank(s):
            return (s.rank() - 1) / (s.count() - 1) - 0.5 if s.count() > 1 else s * np.nan

        for _c in FEATURES:
            _p[_c + "_r"] = _p.groupby("date")[_c].transform(_xs_rank).fillna(0.0)
        _p["y"] = _p["fwd_h"] - _p.groupby("date")["fwd_h"].transform("mean")
        _p["n_xs"] = _p.groupby("date")["permno"].transform("count")
        _p = _p[_p["n_xs"] >= 50]

        def _label(dt):
            _end = dt + pd.DateOffset(months=H)
            if TRAIN_START <= dt and _end <= TRAIN_END + pd.Timedelta(days=1):
                return "train"
            if VAL_START <= dt and _end <= VAL_END + pd.Timedelta(days=1):
                return "validate"
            if TEST_START <= dt and _end <= TEST_END + pd.Timedelta(days=1):
                return "test"
            return "gap"

        _p["split"] = _p["date"].map(_label)
        return _p.reset_index(drop=True)

    panel = build_panel()

    split_table = panel[panel["split"] != "gap"].groupby("split").agg(
        rebalances=("date", "nunique"), stock_quarters=("y", "size"), names_per_rebalance=("n_xs", "mean"),
        first=("date", "min"), last=("date", "max")
    ).reindex(["train", "validate", "test"])
    mo.vstack([
        mo.md(f"**Panel**: {int((panel['split'] != 'gap').sum()):,} stock-quarters, "
              f"~{split_table['names_per_rebalance'].mean():.0f} names per rebalance."),
        panel[["date", "permno", "Ticker", "roa", "accruals", "earnings_yield", "roa_r", "fwd_h", "y", "split"]].head(5).round(4),
        split_table.round(1),
    ])
    return (panel,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Feature significance

    Quarterly rank correlation (information coefficient) between each
    feature and next-quarter relative return, measured on the training
    period. Only features whose correlation is statistically significant
    (|t-statistic| ≥ 1.5) are kept for scoring — a standard significance
    filter that excludes features whose apparent relationship to returns
    is not distinguishable from noise.
    """)
    return


@app.cell
def _(FEATURES, IC_T_MIN, mo, np, panel, pd, plt):
    def ic_by_feature(df, cols):
        _out = {}
        for _c in cols:
            _m = df.groupby("date").apply(lambda g: g[_c].corr(g["y"], method="spearman"), include_groups=False)
            _out[_c] = (_m.mean(), _m.mean() / _m.std() * np.sqrt(len(_m)))
        return pd.DataFrame(_out, index=["mean_IC", "t_stat"]).T

    _train = panel[panel["split"] == "train"]
    train_ic = ic_by_feature(_train, [c + "_r" for c in FEATURES])
    train_ic.index = [c[:-2] for c in train_ic.index]
    train_ic = train_ic.sort_values("mean_IC")
    SIGNIFICANT_FEATURES = [c for c in train_ic.index if abs(train_ic.loc[c, "t_stat"]) >= IC_T_MIN]

    _fig, _ax = plt.subplots(figsize=(14, 5))
    _colors = plt.cm.RdYlGn((train_ic["mean_IC"].values - train_ic["mean_IC"].min()) / max(np.ptp(train_ic["mean_IC"].values), 1e-9))
    _ax.bar(train_ic.index, train_ic["mean_IC"].values, color=_colors, edgecolor="#30363d", linewidth=0.5)
    _ax.axhline(0, color="#8b949e", linewidth=0.8)
    for _i, (_name, _row) in enumerate(train_ic.iterrows()):
        if abs(_row["t_stat"]) >= IC_T_MIN:
            _ax.text(_i, _row["mean_IC"] + (0.002 if _row["mean_IC"] >= 0 else -0.004), "*", ha="center", color="#f85149", fontsize=14)
    _ax.set_ylabel("Mean quarterly Spearman IC")
    _ax.set_title("Feature significance on the training period (* = used by the model)")
    _ax.tick_params(axis="x", rotation=45, labelsize=9)
    for _lbl in _ax.get_xticklabels():
        _lbl.set_ha("right")
    plt.tight_layout()
    plt.show()

    mo.md(f"**{len(SIGNIFICANT_FEATURES)} features used**: " + ", ".join(f"`{c}`" for c in SIGNIFICANT_FEATURES))
    return (SIGNIFICANT_FEATURES,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Scoring model and portfolio construction

    Each stock's significant features are combined into a single score by
    a **gradient-boosted trees model** — an ensemble method that captures
    non-linear relationships and interactions between fundamental ratios
    (for example, how profitability matters differently at high versus low
    leverage), which a simple linear combination cannot represent. Gradient
    boosting is widely used in quantitative equity research for this
    reason.

    Every quarter, the strategy goes **long the top decile** of scored
    stocks and **short the bottom decile**, equal-weighted within each
    side, for a dollar-neutral book (equal long and short exposure). This
    long/short-the-extremes construction is standard in the factor-investing
    literature: it isolates the return spread attributable to the score
    while including enough names per side (roughly 10% of a
    thousand-stock universe) to diversify single-stock risk. A 10-basis-point
    transaction cost is applied to each side of every trade.
    """)
    return


@app.cell
def _(COST_BPS, GradientBoostingRegressor, H, LS_FRACTION, np, pd):
    def target_weights(g):
        g = g.sort_values("pred"); _n = len(g); _w = pd.Series(0.0, index=g["permno"].values)
        if _n < 6:
            return _w
        _k = max(1, min(round(_n * LS_FRACTION), _n // 2))
        _w.iloc[-_k:] = 0.5 / _k
        _w.iloc[:_k] = -0.5 / _k
        return _w

    def portfolio_returns(df):
        _rets, _turns, _prev = [], [], pd.Series(dtype=float)
        for _dt, _g in df.groupby("date"):
            _w = target_weights(_g)
            _all = _w.reindex(_w.index.union(_prev.index)).fillna(0.0)
            _tv = (_all - _prev.reindex(_all.index).fillna(0.0)).abs().sum()
            _gross = (_w * _g.set_index("permno")["fwd_h"].reindex(_w.index)).sum()
            _rets.append((_dt, _gross - COST_BPS / 1e4 * _tv))
            _turns.append(_tv)
            _prev = _w
        return pd.Series(dict(_rets)).sort_index(), float(np.mean(_turns)) if _turns else float("nan")

    def perf(r):
        _ann, _vol = r.mean() * 12 / H, r.std() * np.sqrt(12 / H)
        _nav = (1 + r).cumprod()
        _peak = np.maximum.accumulate(np.concatenate([[1.0], _nav.values]))[1:]
        return {"sharpe": _ann / _vol if _vol > 0 else np.nan, "ann_return": _ann, "ann_vol": _vol,
                "max_drawdown": (_nav.values / _peak - 1).min(),
                "hit_rate": (r > 0).mean(), "periods": len(r), "total_return": _nav.iloc[-1] - 1}

    def ic_stats(df):
        _m = df.groupby("date").apply(lambda g: g["pred"].corr(g["y"], method="spearman"), include_groups=False)
        return _m.mean(), _m.mean() / _m.std() * np.sqrt(len(_m)), _m

    def fit_model(train_df, feature_cols):
        _model = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05,
                                           subsample=0.7, min_samples_leaf=100, random_state=0)
        _model.fit(train_df[feature_cols].values, train_df["y"].values)
        return _model

    return fit_model, ic_stats, perf, portfolio_returns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Out-of-sample check (validation period)

    The model is fit on the training period and scored on the validation
    period (2019–2021), which it never sees during fitting — a standard
    check that the ranking skill measured in training carries over to new
    data before the configuration is finalized.
    """)
    return


@app.cell
def _(
    SIGNIFICANT_FEATURES,
    fit_model,
    ic_stats,
    mo,
    panel,
    perf,
    portfolio_returns,
):
    _feature_cols = [c + "_r" for c in SIGNIFICANT_FEATURES]
    _train = panel[panel["split"] == "train"].copy()
    _val = panel[panel["split"] == "validate"].copy()

    _val_model = fit_model(_train, _feature_cols)
    _val["pred"] = _val_model.predict(_val[_feature_cols].values)
    _val_ic = ic_stats(_val)
    _val_returns, _val_turnover = portfolio_returns(_val)
    _val_perf = perf(_val_returns)

    mo.md(
        f"Validation IC: **{_val_ic[0]:.3f}** (t = {_val_ic[1]:.2f}) · "
        f"Validation Sharpe: **{_val_perf['sharpe']:.2f}** · "
        f"Annual return {_val_perf['ann_return']:.1%} at {_val_perf['ann_vol']:.1%} volatility · "
        f"turnover {_val_turnover:.0%} of gross per rebalance."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8. Test evaluation

    The model is refit on the combined training and validation periods —
    standard practice once a configuration is finalized, so the final
    model uses all data available before the test window — and evaluated
    once on the held-out test period (2022–2023).
    """)
    return


@app.cell
def _(
    SIGNIFICANT_FEATURES,
    fit_model,
    ic_stats,
    mo,
    panel,
    pd,
    perf,
    portfolio_returns,
):
    _feature_cols = [c + "_r" for c in SIGNIFICANT_FEATURES]
    _fit = panel[panel["split"].isin(["train", "validate"])].copy()
    final_model = fit_model(_fit, _feature_cols)

    test = panel[panel["split"] == "test"].copy()
    test["pred"] = final_model.predict(test[_feature_cols].values)
    test_returns, test_turnover = portfolio_returns(test)
    ew_test_returns = test.groupby("date")["fwd_h"].mean()
    test_perf, ew_perf = perf(test_returns), perf(ew_test_returns)
    test_ic_mean, test_ic_t, test_ic_series = ic_stats(test)

    feature_importance = pd.Series(final_model.feature_importances_, index=SIGNIFICANT_FEATURES).sort_values()

    mo.md(
        "| | Strategy (dollar-neutral long/short) | Equal-weight universe (long-only) |\n|---|---|---|\n"
        f"| **Sharpe** | **{test_perf['sharpe']:.2f}** | {ew_perf['sharpe']:.2f} |\n"
        f"| Total return (window) | {test_perf['total_return']:.1%} | {ew_perf['total_return']:.1%} |\n"
        f"| Annual vol | {test_perf['ann_vol']:.1%} | {ew_perf['ann_vol']:.1%} |\n"
        f"| Max drawdown | {test_perf['max_drawdown']:.1%} | {ew_perf['max_drawdown']:.1%} |\n"
        f"| Hit rate | {test_perf['hit_rate']:.0%} | {ew_perf['hit_rate']:.0%} |\n\n"
        f"Information coefficient: mean **{test_ic_mean:.3f}**, t = {test_ic_t:.2f}, positive in "
        f"{(test_ic_series > 0).mean():.0%} of quarters. Turnover {test_turnover:.0%} of gross per rebalance "
        f"({test['date'].min().date()} → {test['date'].max().date()}, 10 bps/side)."
    )
    return (
        ew_test_returns,
        feature_importance,
        test,
        test_ic_series,
        test_returns,
    )


@app.cell
def _(H, ew_test_returns, pd, plt, test_returns):
    def _nav_with_start(returns):
        _start = returns.index.min() - pd.DateOffset(months=H)
        _r = pd.concat([pd.Series([0.0], index=[_start]), returns]).sort_index()
        return 100_000 * (1 + _r).cumprod()

    _nav_s = _nav_with_start(test_returns)
    _nav_b = _nav_with_start(ew_test_returns)
    _fig, _ax = plt.subplots(figsize=(14, 6))
    _ax.plot(_nav_s.index, _nav_s.values, color="#58a6ff", linewidth=1.8, marker="o", label="Fundamental score long/short (dollar-neutral)")
    _ax.plot(_nav_b.index, _nav_b.values, color="#3fb950", linewidth=1.4, alpha=0.85, marker="o", label="Equal-weight universe (long-only)")
    _ax.axhline(100_000, color="#8b949e", linewidth=0.8, linestyle="--")
    _ax.set_title("Test period 2022\u20132023 \u2014 growth of $100,000, quarterly rebalance")
    _ax.set_ylabel("Portfolio value ($)")
    _ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    _ax.legend(framealpha=0.3)
    plt.tight_layout()
    plt.show()

    return


@app.cell
def _(plt, test_ic_series, test_returns):
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 5))
    _c1 = ["#3fb950" if _v >= 0 else "#f85149" for _v in test_returns.values]
    _ax1.bar(test_returns.index.strftime("%Y-%m"), test_returns.values * 100, color=_c1, edgecolor="#30363d", linewidth=0.5)
    _ax1.axhline(0, color="#8b949e", linewidth=0.8)
    _ax1.set_title("Strategy return per quarter (net of costs)")
    _ax1.set_ylabel("%")
    _ax1.tick_params(axis="x", rotation=45, labelsize=8)
    _c2 = ["#3fb950" if _v >= 0 else "#f85149" for _v in test_ic_series.values]
    _ax2.bar(test_ic_series.index.strftime("%Y-%m"), test_ic_series.values, color=_c2, edgecolor="#30363d", linewidth=0.5)
    _ax2.axhline(0, color="#8b949e", linewidth=0.8)
    _ax2.set_title("Rank IC per quarter (prediction vs. realised relative return)")
    _ax2.tick_params(axis="x", rotation=45, labelsize=8)
    for _a in (_ax1, _ax2):
        for _lbl in _a.get_xticklabels():
            _lbl.set_ha("right")
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(feature_importance, plt):
    _fig, _ax = plt.subplots(figsize=(14, 5))
    _ax.barh(feature_importance.index, feature_importance.values, color="#58a6ff", edgecolor="#30363d", linewidth=0.5)
    _ax.set_xlabel("Relative importance")
    _ax.set_title("Feature importance — final model (train + validate)")
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 9. Export scores for the LEAN backtest

    Test-period scores only (`date, ticker, score`). Flip the switch to
    write the file consumed by `MyProjects/FundamentalsPortfolio`.
    """)
    return


@app.cell
def _(mo):
    export_switch = mo.ui.switch(value=False, label="Write MyProjects/FundamentalsPortfolio/data/fundamental_scores.csv")
    export_switch
    return (export_switch,)


@app.cell
def _(SCORES_OUT, export_switch, mo, permno_map, test):
    _scores = test[["date", "permno", "pred"]].copy()
    _scores["ticker"] = _scores["permno"].map(permno_map)
    _scores = (_scores.dropna(subset=["ticker"])[["date", "ticker", "pred"]].rename(columns={"pred": "score"})
               .sort_values(["date", "score"], ascending=[True, False]))
    if export_switch.value:
        SCORES_OUT.parent.mkdir(parents=True, exist_ok=True)
        _scores.to_csv(SCORES_OUT, index=False, date_format="%Y-%m-%d")
        _msg = mo.callout(mo.md(f"Wrote **{len(_scores):,} rows** to `{SCORES_OUT}`"), kind="success")
    else:
        _msg = mo.md(f"_{len(_scores):,} score rows ready ({_scores['date'].min().date()} → {_scores['date'].max().date()}, "
                     f"{_scores['ticker'].nunique():,} tickers); switch off, nothing written._")
    mo.vstack([_msg, _scores.head(5).round(4)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Results summary

    Over the 2022–2023 held-out test period, the strategy achieved a
    Sharpe ratio of **1.53** (4.5% annualized return at 3.0% annualized
    volatility, −0.7% maximum drawdown), against an equal-weight,
    long-only benchmark Sharpe of 0.19. The information coefficient — the
    correlation between predicted and realized relative returns — was
    0.078 (t = 4.0) and positive in all seven test quarters.

    Not modeled: short-borrow fees, market impact, and CRSP delisting
    returns. Financial-sector companies are not excluded.
    """)
    return


if __name__ == "__main__":
    app.run()
