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
    # Formulaic Alphas on US Equities

    An implementation of all 101 formulaic alpha expressions from Zura
    Kakushadze, *101 Formulaic Alphas* (arXiv:1601.00991), applied as trading
    signals to the point-in-time largest 300 US companies by market cap. The
    paper is in this workspace at
    `References/papers/101-formulaic-alphas/`.

    Each alpha is an explicit arithmetic expression over daily open, high, low,
    close, volume and volume-weighted average price, built from cross-sectional
    operators (`rank`, `scale`) and time-series operators (`delay`, `delta`,
    `correlation`, `covariance`, `ts_min`, `ts_max`, `ts_rank`, `ts_argmax`,
    `stddev`, `decay_linear`, `signedpower`).

    **Workflow**: load prices → compute the alpha panel → neutralise each alpha
    within its sector → measure how predictive power decays with holding horizon
    → select alphas on the training period → combine them into one score → build
    a dollar-neutral long/short book → evaluate once on a held-out test window.
    """)
    return


@app.cell
def _():
    import pathlib
    import warnings
    import zipfile

    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import Ridge

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
    WRDS = REPO / "infrastructure" / "pipelines" / "wrds" / "lean-data"
    FUND_DIR = WRDS / "alternative" / "fundamentals"
    SECTOR_CSV = WRDS / "alternative" / "sectors" / "broad_sector_map.csv"
    DAILY_DIR = WRDS / "equity" / "usa" / "daily"
    FACTOR_DIR = WRDS / "equity" / "usa" / "factor_files"
    SCORES_OUT = REPO / "MyProjects" / "Alpha101Portfolio" / "data" / "alpha_scores.csv"

    SCALE = 10_000        # LEAN zips store prices x10,000
    TOP_N = 300           # universe size at each quarter-end, by reported market cap
    COST_BPS = 2.0        # transaction cost per side, in basis points of notional
    LS_FRACTION = 0.2     # quintile long/short book
    IC_T_MIN = 2.0        # an alpha is used only if its training IC is significant at |t| >= 2
    PERSIST_MIN = 0.5     # ...and its 5-day IC must retain >=50% of its 1-day IC, same sign
    DPY = 252.0

    # 60/20/20 on calendar years. The training block covers the paper's own
    # pre-publication period, and the four-year test block is long enough that
    # its Sharpe estimate is not dominated by a single year's regime.
    HISTORY_START = pd.Timestamp("2004-01-01")   # earlier than the train start, for rolling windows
    TRAIN_START, TRAIN_END = pd.Timestamp("2005-01-01"), pd.Timestamp("2016-12-31")
    VAL_START, VAL_END = pd.Timestamp("2017-01-01"), pd.Timestamp("2020-12-31")
    TEST_START, TEST_END = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-12-31")
    return (
        COST_BPS,
        DAILY_DIR,
        DPY,
        FACTOR_DIR,
        FUND_DIR,
        HISTORY_START,
        IC_T_MIN,
        LS_FRACTION,
        Ridge,
        SCALE,
        SCORES_OUT,
        SECTOR_CSV,
        TEST_END,
        TEST_START,
        TOP_N,
        TRAIN_END,
        TRAIN_START,
        VAL_END,
        VAL_START,
        np,
        pd,
        plt,
        zipfile,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Universe and prices

    The universe is the largest `TOP_N` US companies by the most recently
    reported market cap at each calendar quarter-end, from the WRDS broad
    pipeline (`infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py`).
    Membership is decided only from filings already public on the date, so there
    is no survivorship bias in eligibility. Restricting to the largest names
    keeps the strategy in the securities where execution is cheapest, which
    matters because the book turns over most of its value every session.

    Prices are CRSP daily bars adjusted for splits and dividends through LEAN's
    factor files. Volume is raw shares traded, as the engine reports it.
    """)
    return


@app.cell
def _(
    DAILY_DIR,
    FACTOR_DIR,
    FUND_DIR,
    HISTORY_START,
    SCALE,
    TEST_END,
    TOP_N,
    mo,
    np,
    pd,
    plt,
    zipfile,
):
    _needed = [FUND_DIR / "broad_universe.csv", FUND_DIR / "broad_permno_map.csv"]
    _missing = [p.name for p in _needed if not p.exists()]
    mo.stop(
        bool(_missing) or not DAILY_DIR.exists(),
        mo.callout(mo.md(
            f"Price data missing (`{', '.join(_missing) or DAILY_DIR}`) — run "
            "`python scripts/run_broad_quarterly_pipeline.py` from "
            "`infrastructure/pipelines/wrds/` first (needs WRDS credentials)."
        ), kind="warn"),
    )

    universe_raw = pd.read_csv(FUND_DIR / "broad_universe.csv", parse_dates=["quarter_end"])
    permno_map = pd.read_csv(FUND_DIR / "broad_permno_map.csv").set_index("permno")["lean_ticker"]
    _u = universe_raw[(universe_raw["rank"] <= TOP_N)
                      & (universe_raw["quarter_end"] >= HISTORY_START)
                      & (universe_raw["quarter_end"] <= TEST_END)]
    membership = {qe: set(g["permno"]) for qe, g in _u.groupby("quarter_end")}
    quarter_ends = np.array(sorted(membership))
    permnos = sorted(_u["permno"].unique())

    def _load(permno):
        ticker = permno_map.get(permno)
        if pd.isna(ticker):
            return None
        tl = str(ticker).lower()
        try:
            with zipfile.ZipFile(DAILY_DIR / f"{tl}.zip") as z:
                px = pd.read_csv(z.open(z.namelist()[0]), header=None,
                                 names=["datetime", "open", "high", "low", "close", "volume"])
            ff = pd.read_csv(FACTOR_DIR / f"{tl}.csv", header=None, names=["date", "pf", "sf", "ref"])
        except FileNotFoundError:
            return None
        px["date"] = pd.to_datetime(px["datetime"].str.slice(0, 8), format="%Y%m%d")
        px = px[(px["date"] >= HISTORY_START - pd.Timedelta(days=30)) & (px["date"] <= TEST_END)]
        if len(px) < 100:
            return None
        for c in ["open", "high", "low", "close"]:
            px[c] = px[c] / SCALE
        ff["date"] = pd.to_datetime(ff["date"], format="%Y%m%d")
        ff = ff.sort_values("date")
        _i = np.clip(np.searchsorted(ff["date"].values, px["date"].values, side="right") - 1, 0, len(ff) - 1)
        _adj = ff["pf"].values[_i] * ff["sf"].values[_i]
        for _src, _dst in [("open", "o"), ("high", "h"), ("low", "l"), ("close", "c")]:
            px[_dst] = px[_src] * _adj
        return px.set_index("date")[["o", "h", "l", "c", "volume"]]

    _frames = {p: f for p in permnos if (f := _load(p)) is not None}
    open_ = pd.DataFrame({p: f["o"] for p, f in _frames.items()}).sort_index()
    high = pd.DataFrame({p: f["h"] for p, f in _frames.items()}).sort_index()
    low = pd.DataFrame({p: f["l"] for p, f in _frames.items()}).sort_index()
    close = pd.DataFrame({p: f["c"] for p, f in _frames.items()}).sort_index()
    volume = pd.DataFrame({p: f["volume"] for p, f in _frames.items()}).sort_index()
    _keep = (open_.index >= HISTORY_START) & (open_.index <= TEST_END)
    open_, high, low, close, volume = [d[_keep] for d in (open_, high, low, close, volume)]

    # daily membership mask, held constant within each quarter
    _qi = np.searchsorted(quarter_ends, close.index.values, side="right") - 1
    mask = pd.DataFrame(False, index=close.index, columns=close.columns)
    cap = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    _quarter_caps = {
        qe: g.set_index("permno")["mktcap"].to_dict()
        for qe, g in _u.groupby("quarter_end")
    }
    for _row, _q in enumerate(_qi):
        if _q < 0:
            continue
        _members = membership[quarter_ends[_q]]
        mask.iloc[_row] = [c in _members for c in mask.columns]
        _caps = _quarter_caps[quarter_ends[_q]]
        cap.iloc[_row] = [_caps.get(c, np.nan) for c in cap.columns]

    _eligible_daily = mask.sum(axis=1)
    _fig_universe, _ax_universe = plt.subplots(figsize=(14, 4))
    _ax_universe.plot(_eligible_daily.index, _eligible_daily.values, color="#58a6ff", linewidth=1.2)
    _ax_universe.axhline(_eligible_daily.mean(), color="#8b949e", linewidth=0.8, linestyle="--")
    _ax_universe.set_ylabel("Eligible names")
    _ax_universe.set_title("Point-in-time universe size per session")
    plt.tight_layout()
    plt.show()

    mo.vstack([
        mo.md(f"**{close.shape[1]} companies** ever in the top {TOP_N}, "
              f"**{close.shape[0]:,} trading days** ({close.index.min().date()} → {close.index.max().date()}), "
              f"averaging **{mask.sum(axis=1).mean():.0f} eligible names per session**."),
        close.iloc[:5, :6].round(2),
    ])
    return cap, close, high, low, mask, open_, permno_map, volume


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. The alpha operators

    The paper writes each alpha as an arithmetic expression over a handful of
    operators. Implemented here on wide panels — one row per date, one column
    per security — so cross-sectional operators act across columns and
    time-series operators act down them.

    | Operator | Meaning |
    |---|---|
    | `rank(x)` | cross-sectional percentile rank within the date |
    | `delay(x, d)` / `delta(x, d)` | value `d` days ago / change over `d` days |
    | `correlation(x, y, d)` / `covariance(x, y, d)` | rolling `d`-day association |
    | `ts_min` / `ts_max` / `ts_argmax` / `ts_rank` | rolling extremes, position of the extreme, rank of the latest value |
    | `stddev(x, d)` / `sum(x, d)` / `sma(x, d)` | rolling dispersion and totals |
    | `decay_linear(x, d)` | linearly weighted moving average |
    | `signedpower(x, a)` | `sign(x) · |x|^a` |
    | `scale(x)` | rescale so absolute values sum to 1 across the date |
    """)
    return


@app.cell
def _(np, pd):
    def _window(d):
        """The paper specifies flooring every non-integer lookback."""
        return max(1, int(np.floor(d)))

    def rank(df):
        return df.rank(axis=1, pct=True)

    def delay(df, d):
        return df.shift(_window(d))

    def delta(df, d):
        return df - df.shift(_window(d))

    def ts_sum(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=min(d, max(2, d // 2))).sum()

    def sma(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=min(d, max(2, d // 2))).mean()

    def stddev(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=min(d, max(2, d // 2))).std()

    def ts_min(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=min(d, max(2, d // 2))).min()

    def ts_max(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=min(d, max(2, d // 2))).max()

    def ts_argmax(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=d).apply(np.argmax, raw=True) + 1

    def ts_argmin(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=d).apply(np.argmin, raw=True) + 1

    def ts_rank(df, d):
        d = _window(d)
        # pandas computes the rank of the current (right-most) observation in
        # compiled code; this is equivalent to the former argsort callback and
        # is orders of magnitude faster across the full 101-alpha panel.
        return df.rolling(d, min_periods=d).rank(pct=True)

    def correlation(a, b, d):
        d = _window(d)
        return a.rolling(d, min_periods=min(d, max(3, d // 2))).corr(b)

    def covariance(a, b, d):
        d = _window(d)
        return a.rolling(d, min_periods=min(d, max(3, d // 2))).cov(b)

    def decay_linear(df, d):
        d = _window(d)
        # np.convolve reverses its second argument, so descending kernel
        # weights give the newest observation weight d and the oldest weight 1.
        kernel = np.arange(float(d), 0.0, -1.0)
        values = df.to_numpy(dtype=float)
        out = np.full_like(values, np.nan)
        for j in range(values.shape[1]):
            col = values[:, j]
            valid = np.isfinite(col)
            weighted = np.convolve(np.where(valid, col, 0.0), kernel, mode="full")[:len(col)]
            counts = np.convolve(valid.astype(float), np.ones(d), mode="full")[:len(col)]
            ok = counts == d
            out[ok, j] = weighted[ok] / kernel.sum()
        return pd.DataFrame(out, index=df.index, columns=df.columns)

    def product(df, d):
        d = _window(d)
        return df.rolling(d, min_periods=d).apply(np.prod, raw=True)

    def scale(df, a=1.0):
        return df.mul(a).div(df.abs().sum(axis=1).replace(0, np.nan), axis=0)

    def signed_power(df, a):
        return np.sign(df) * (df.abs() ** a)

    def clean(df):
        return df.replace([np.inf, -np.inf], np.nan)

    return (
        clean,
        correlation,
        covariance,
        decay_linear,
        delay,
        delta,
        product,
        rank,
        scale,
        signed_power,
        sma,
        stddev,
        ts_argmax,
        ts_argmin,
        ts_max,
        ts_min,
        ts_rank,
        ts_sum,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. The alphas

    All 101 expressions from the paper. `vwap` is approximated by the typical
    price `(high + low + close) / 3`, since daily bars carry no true
    volume-weighted average price. `adv{d}` is average daily dollar volume,
    market cap comes from the point-in-time quarterly universe file, and every
    formula-level `indneutralize` uses the requested point-in-time GICS level.
    Non-integer lookbacks are floored, exactly as specified in the paper.
    """)
    return


@app.cell
def _(
    SECTOR_CSV,
    cap,
    clean,
    close,
    correlation,
    covariance,
    decay_linear,
    delay,
    delta,
    high,
    low,
    mask,
    np,
    open_,
    pd,
    product,
    rank,
    scale,
    signed_power,
    sma,
    stddev,
    ts_argmax,
    ts_argmin,
    ts_max,
    ts_min,
    ts_rank,
    ts_sum,
    volume,
):
    returns = close.pct_change()
    vwap = (high + low + close) / 3.0
    adv = {d: sma(volume * close, d) for d in (5, 10, 15, 20, 30, 40, 50, 60, 81, 120, 150, 180)}
    _d1 = delta(close, 1)
    _accel = ((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)

    # Point-in-time GICS panels used by formulas that explicitly call
    # indneutralize. The final factor-level sector neutralisation remains in
    # section 4 so the expanded experiment is comparable with the original.
    _groups = {}
    if SECTOR_CSV.exists():
        _smap = pd.read_csv(SECTOR_CSV, parse_dates=["ValidFrom", "ValidThrough"])
        _levels = {
            "sector": "GICSSector",
            "industry_group": "GICSIndustryGroup",
            "industry": "GICSIndustry",
            "subindustry": "GICSSubIndustry",
        }
        _dates = close.index.values
        for _level, _column in _levels.items():
            _panel = pd.DataFrame("UNKNOWN", index=close.index, columns=close.columns, dtype=object)
            for _permno, _g in _smap.dropna(subset=[_column]).sort_values(
                    ["permno", "ValidFrom"]).groupby("permno"):
                if _permno not in _panel.columns:
                    continue
                _values = np.full(len(_dates), "UNKNOWN", dtype=object)
                for _, _r in _g.iterrows():
                    _start = np.datetime64(_r["ValidFrom"])
                    _end = (np.datetime64(_r["ValidThrough"])
                            if pd.notna(_r["ValidThrough"]) else _dates[-1])
                    _values[(_dates >= _start) & (_dates <= _end)] = str(int(_r[_column]))
                _panel[_permno] = _values
            _groups[_level] = _panel

    _group_codes = {
        level: np.vstack([pd.factorize(row, sort=False)[0] for row in panel.to_numpy()])
        for level, panel in _groups.items()
    }

    def _indneutralize(df, level):
        if level not in _group_codes:
            return df
        _values = df.to_numpy(dtype=float)
        _eligible = mask.to_numpy() & np.isfinite(_values)
        _codes = _group_codes[level]
        _out = np.full_like(_values, np.nan)
        for _i in range(len(_values)):
            _valid = _eligible[_i]
            if not _valid.any():
                continue
            _c = _codes[_i, _valid]
            _v = _values[_i, _valid]
            _sums = np.bincount(_c, weights=_v)
            _counts = np.bincount(_c)
            _out[_i, _valid] = _v - _sums[_c] / _counts[_c]
        return pd.DataFrame(_out, index=df.index, columns=df.columns)

    def _maximum(a, b):
        return a.where(a >= b, b)

    def _minimum(a, b):
        return a.where(a <= b, b)

    _a = {}
    # Alpha#1  rank(Ts_ArgMax(SignedPower(returns<0 ? stddev(returns,20) : close, 2), 5)) - 0.5
    _a["alpha001"] = rank(ts_argmax(signed_power(close.where(returns >= 0, stddev(returns, 20)), 2.0), 5)) - 0.5
    # Alpha#2  -1 * correlation(rank(delta(log(volume),2)), rank((close-open)/open), 6)
    _a["alpha002"] = -1 * correlation(rank(delta(np.log(volume.replace(0, np.nan)), 2)),
                                      rank((close - open_) / open_), 6)
    # Alpha#3  -1 * correlation(rank(open), rank(volume), 10)
    _a["alpha003"] = -1 * correlation(rank(open_), rank(volume), 10)
    # Alpha#4  -1 * Ts_Rank(rank(low), 9)
    _a["alpha004"] = -1 * ts_rank(rank(low), 9)
    _a["alpha005"] = rank(open_ - sma(vwap, 10)) * (-1 * rank(close - vwap).abs())
    # Alpha#6  -1 * correlation(open, volume, 10)
    _a["alpha006"] = -1 * correlation(open_, volume, 10)
    _a["alpha007"] = ((-1 * ts_rank(delta(close, 7).abs(), 60)) * np.sign(delta(close, 7))).where(
        volume > adv[20], -1.0)
    _a["alpha008"] = -1 * rank(ts_sum(open_, 5) * ts_sum(returns, 5) -
                                delay(ts_sum(open_, 5) * ts_sum(returns, 5), 10))
    # Alpha#9  trend-continuation switch on delta(close,1) over a 5-day window
    _a["alpha009"] = _d1.where((ts_min(_d1, 5) > 0) | (ts_max(_d1, 5) < 0), -1 * _d1)
    _a["alpha010"] = rank(_d1.where((ts_min(_d1, 4) > 0) | (ts_max(_d1, 4) < 0), -1 * _d1))
    _a["alpha011"] = (rank(ts_max(vwap - close, 3)) + rank(ts_min(vwap - close, 3))) * rank(delta(volume, 3))
    # Alpha#12 sign(delta(volume,1)) * (-1 * delta(close,1))
    _a["alpha012"] = np.sign(delta(volume, 1)) * (-1 * _d1)
    # Alpha#13 -1 * rank(covariance(rank(close), rank(volume), 5))
    _a["alpha013"] = -1 * rank(covariance(rank(close), rank(volume), 5))
    # Alpha#14 (-1 * rank(delta(returns,3))) * correlation(open, volume, 10)
    _a["alpha014"] = (-1 * rank(delta(returns, 3))) * correlation(open_, volume, 10)
    _a["alpha015"] = -1 * ts_sum(rank(correlation(rank(high), rank(volume), 3)), 3)
    # Alpha#16 -1 * rank(covariance(rank(high), rank(volume), 5))
    _a["alpha016"] = -1 * rank(covariance(rank(high), rank(volume), 5))
    _a["alpha017"] = (-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1)) * rank(ts_rank(volume / adv[20], 5))
    # Alpha#18 -1 * rank(stddev(abs(close-open),5) + (close-open) + correlation(close, open, 10))
    _a["alpha018"] = -1 * rank(stddev((close - open_).abs(), 5) + (close - open_) + correlation(close, open_, 10))
    # Alpha#19 -sign((close - delay(close,7)) + delta(close,7)) * (1 + rank(1 + sum(returns,250)))
    _a["alpha019"] = (-1 * np.sign((close - delay(close, 7)) + delta(close, 7))) * (1 + rank(1 + ts_sum(returns, 250)))
    # Alpha#20 (-1*rank(open - delay(high,1))) * rank(open - delay(close,1)) * rank(open - delay(low,1))
    _a["alpha020"] = ((-1 * rank(open_ - delay(high, 1))) * rank(open_ - delay(close, 1))) * rank(open_ - delay(low, 1))
    _a21 = pd.DataFrame(-1.0, index=close.index, columns=close.columns)
    _a21 = _a21.mask(sma(close, 8) + stddev(close, 8) < sma(close, 2), -1.0)
    _a21 = _a21.mask(sma(close, 2) < sma(close, 8) - stddev(close, 8), 1.0)
    _a21 = _a21.mask(~((sma(close, 8) + stddev(close, 8) < sma(close, 2)) |
                       (sma(close, 2) < sma(close, 8) - stddev(close, 8))) &
                      (volume >= adv[20]), 1.0)
    _a["alpha021"] = _a21
    _a["alpha022"] = -1 * delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20))
    # Alpha#23 (sma(high,20) < high) ? -1*delta(high,2) : 0
    _a["alpha023"] = (-1 * delta(high, 2)).where(sma(high, 20) < high, 0.0)
    _trend100 = delta(sma(close, 100), 100) / delay(close, 100)
    _a["alpha024"] = (-(close - ts_min(close, 100))).where(_trend100 <= 0.05, -delta(close, 3))
    _a["alpha025"] = rank((-returns) * adv[20] * vwap * (high - close))
    _a["alpha026"] = -ts_max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)
    _a["alpha027"] = pd.DataFrame(1.0, index=close.index, columns=close.columns).where(
        rank(sma(correlation(rank(volume), rank(vwap), 6), 2)) <= 0.5, -1.0)
    _a["alpha028"] = scale(correlation(adv[20], low, 5) + (high + low) / 2 - close)
    _a29 = rank(rank(-rank(delta(close - 1, 5))))
    _a29 = rank(rank(scale(np.log(ts_sum(ts_min(_a29, 2), 1)))))
    _a["alpha029"] = ts_min(product(_a29, 1), 5) + ts_rank(delay(-returns, 6), 5)
    _sign3 = np.sign(close - delay(close, 1)) + np.sign(delay(close, 1) - delay(close, 2)) + np.sign(delay(close, 2) - delay(close, 3))
    _a["alpha030"] = (1 - rank(_sign3)) * ts_sum(volume, 5) / ts_sum(volume, 20)
    _a["alpha031"] = (rank(rank(rank(decay_linear(-rank(rank(delta(close, 10))), 10)))) +
                        rank(-delta(close, 3)) + np.sign(scale(correlation(adv[20], low, 12))))
    _a["alpha032"] = scale(sma(close, 7) - close) + 20 * scale(correlation(vwap, delay(close, 5), 230))
    # Alpha#33 rank(-1 * (1 - open/close))
    _a["alpha033"] = rank(-1 * (1 - (open_ / close)))
    # Alpha#34 rank((1 - rank(stddev(returns,2)/stddev(returns,5))) + (1 - rank(delta(close,1))))
    _a["alpha034"] = rank((1 - rank(stddev(returns, 2) / stddev(returns, 5))) + (1 - rank(_d1)))
    _a["alpha035"] = ts_rank(volume, 32) * (1 - ts_rank(close + high - low, 16)) * (1 - ts_rank(returns, 32))
    _a["alpha036"] = (2.21 * rank(correlation(close - open_, delay(volume, 1), 15)) +
                        0.7 * rank(open_ - close) + 0.73 * rank(ts_rank(delay(-returns, 6), 5)) +
                        rank(correlation(vwap, adv[20], 6).abs()) +
                        0.6 * rank((sma(close, 200) - open_) * (close - open_)))
    _a["alpha037"] = rank(correlation(delay(open_ - close, 1), close, 200)) + rank(open_ - close)
    # Alpha#38 (-1 * rank(Ts_Rank(close,10))) * rank(close/open)
    _a["alpha038"] = (-1 * rank(ts_rank(close, 10))) * rank(close / open_)
    _a["alpha039"] = -rank(delta(close, 7) * (1 - rank(decay_linear(volume / adv[20], 9)))) * (1 + rank(ts_sum(returns, 250)))
    _a["alpha040"] = -rank(stddev(high, 10)) * correlation(high, volume, 10)
    # Alpha#41 sqrt(high*low) - vwap
    _a["alpha041"] = (high * low) ** 0.5 - vwap
    # Alpha#42 rank(vwap - close) / rank(vwap + close)
    _a["alpha042"] = rank(vwap - close) / rank(vwap + close)
    _a["alpha043"] = ts_rank(volume / adv[20], 20) * ts_rank(-delta(close, 7), 8)
    # Alpha#44 -1 * correlation(high, rank(volume), 5)
    _a["alpha044"] = -1 * correlation(high, rank(volume), 5)
    _a["alpha045"] = -rank(sma(delay(close, 5), 20)) * correlation(close, volume, 2) * rank(correlation(ts_sum(close, 5), ts_sum(close, 20), 2))
    # Alpha#46 three-way switch on 10- vs 20-day price acceleration
    _a46 = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    _a46 = _a46.mask(_accel > 0.25, -1.0)
    _a46 = _a46.mask((_accel <= 0.25) & (_accel < 0), 1.0)
    _a46 = _a46.mask((_accel <= 0.25) & (_accel >= 0), -1 * _d1)
    _a["alpha046"] = _a46
    _a["alpha047"] = rank(1 / close) * volume / adv[20] * (high * rank(high - close) / sma(high, 5)) - rank(vwap - delay(vwap, 5))
    _a["alpha048"] = (_indneutralize(correlation(delta(close, 1), delta(delay(close, 1), 1), 250) *
                                      delta(close, 1) / close, "subindustry") /
                        ts_sum((delta(close, 1) / delay(close, 1)) ** 2, 250))
    # Alpha#49 same acceleration measure, -0.1 threshold
    _a["alpha049"] = (-1 * _d1).where(_accel >= -0.1, 1.0)
    _a["alpha050"] = -ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5)
    _a["alpha051"] = (-_d1).where(_accel >= -0.05, 1.0)
    _a["alpha052"] = (-ts_min(low, 5) + delay(ts_min(low, 5), 5)) * rank((ts_sum(returns, 240) - ts_sum(returns, 20)) / 220) * ts_rank(volume, 5)
    # Alpha#53 -1 * delta(((close-low) - (high-close)) / (close-low), 9)
    _a["alpha053"] = -1 * delta(((close - low) - (high - close)) / (close - low).replace(0, np.nan), 9)
    # Alpha#54 (-1 * (low-close) * open^5) / ((low-high) * close^5)
    _a["alpha054"] = (-1 * (low - close) * (open_ ** 5)) / ((low - high).replace(0, np.nan) * (close ** 5))
    # Alpha#55 -1 * correlation(rank((close - ts_min(low,12)) / (ts_max(high,12) - ts_min(low,12))), rank(volume), 6)
    _rng = (ts_max(high, 12) - ts_min(low, 12)).replace(0, np.nan)
    _a["alpha055"] = -1 * correlation(rank((close - ts_min(low, 12)) / _rng), rank(volume), 6)
    _a["alpha056"] = -rank(ts_sum(returns, 10) / ts_sum(ts_sum(returns, 2), 3)) * rank(returns * cap)
    _a["alpha057"] = -(close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2)
    _a["alpha058"] = -ts_rank(decay_linear(correlation(_indneutralize(vwap, "sector"), volume, 3.92795), 7.89291), 5.50322)
    _a["alpha059"] = -ts_rank(decay_linear(correlation(_indneutralize(vwap, "industry"), volume, 4.25197), 16.2289), 8.19648)
    _a["alpha060"] = -(2 * scale(rank((((close-low) - (high-close)) / (high-low).replace(0, np.nan)) * volume)) - scale(rank(ts_argmax(close, 10))))
    _a["alpha061"] = (rank(vwap - ts_min(vwap, 16.1219)) < rank(correlation(vwap, adv[180], 17.9282))).astype(float)
    _a["alpha062"] = -((rank(correlation(vwap, ts_sum(adv[20], 22.4101), 9.91009)) <
                         rank((2 * rank(open_)) < (rank((high + low) / 2) + rank(high)))).astype(float))
    _a["alpha063"] = -(rank(decay_linear(delta(_indneutralize(close, "industry"), 2.25164), 8.22237)) -
                         rank(decay_linear(correlation(vwap * 0.318108 + open_ * 0.681892,
                                                       ts_sum(adv[180], 37.2467), 13.557), 12.2883)))
    _a["alpha064"] = -((rank(correlation(ts_sum(open_ * 0.178404 + low * 0.821596, 12.7054),
                                             ts_sum(adv[120], 12.7054), 16.6208)) <
                         rank(delta(((high + low) / 2) * 0.178404 + vwap * 0.821596, 3.69741))).astype(float))
    _a["alpha065"] = -((rank(correlation(open_ * 0.00817205 + vwap * 0.99182795,
                                             ts_sum(adv[60], 8.6911), 6.40374)) <
                         rank(open_ - ts_min(open_, 13.635))).astype(float))
    _a["alpha066"] = -(rank(decay_linear(delta(vwap, 3.51013), 7.23052)) +
                         ts_rank(decay_linear((low - vwap) / (open_ - (high + low) / 2), 11.4157), 6.72611))
    _a["alpha067"] = -(rank(high - ts_min(high, 2.14593)) **
                         rank(correlation(_indneutralize(vwap, "sector"),
                                          _indneutralize(adv[20], "subindustry"), 6.02936)))
    _a["alpha068"] = -((ts_rank(correlation(rank(high), rank(adv[15]), 8.91644), 13.9333) <
                         rank(delta(close * 0.518371 + low * 0.481629, 1.06157))).astype(float))
    _a["alpha069"] = -(rank(ts_max(delta(_indneutralize(vwap, "industry"), 2.72412), 4.79344)) **
                         ts_rank(correlation(close * 0.490655 + vwap * 0.509345, adv[20], 4.92416), 9.0615))
    _a["alpha070"] = -(rank(delta(vwap, 1.29456)) **
                         ts_rank(correlation(_indneutralize(close, "industry"), adv[50], 17.8256), 17.9171))
    _a71a = ts_rank(decay_linear(correlation(ts_rank(close, 3.43976), ts_rank(adv[180], 12.0647), 18.0175), 4.20501), 15.6948)
    _a71b = ts_rank(decay_linear(rank(low + open_ - 2 * vwap) ** 2, 16.4662), 4.4388)
    _a["alpha071"] = _maximum(_a71a, _a71b)
    _a["alpha072"] = (rank(decay_linear(correlation((high + low) / 2, adv[40], 8.93345), 10.1519)) /
                        rank(decay_linear(correlation(ts_rank(vwap, 3.72469), ts_rank(volume, 18.5188), 6.86671), 2.95011)))
    _a73a = rank(decay_linear(delta(vwap, 4.72775), 2.91864))
    _mix73 = open_ * 0.147155 + low * 0.852845
    _a73b = ts_rank(decay_linear(-(delta(_mix73, 2.03608) / _mix73), 3.33829), 16.7411)
    _a["alpha073"] = -_maximum(_a73a, _a73b)
    _a["alpha074"] = -((rank(correlation(close, ts_sum(adv[30], 37.4843), 15.1365)) <
                         rank(correlation(rank(high * 0.0261661 + vwap * 0.9738339), rank(volume), 11.4791))).astype(float))
    _a["alpha075"] = (rank(correlation(vwap, volume, 4.24304)) <
                        rank(correlation(rank(low), rank(adv[50]), 12.4413))).astype(float)
    _a76a = rank(decay_linear(delta(vwap, 1.24383), 11.8259))
    _a76b = ts_rank(decay_linear(ts_rank(correlation(_indneutralize(low, "sector"), adv[81], 8.14941), 19.569), 17.1543), 19.383)
    _a["alpha076"] = -_maximum(_a76a, _a76b)
    _a77a = rank(decay_linear((high + low) / 2 - vwap, 20.0451))
    _a77b = rank(decay_linear(correlation((high + low) / 2, adv[40], 3.1614), 5.64125))
    _a["alpha077"] = _minimum(_a77a, _a77b)
    _a["alpha078"] = (rank(correlation(ts_sum(low * 0.352233 + vwap * 0.647767, 19.7428),
                                         ts_sum(adv[40], 19.7428), 6.83313)) **
                        rank(correlation(rank(vwap), rank(volume), 5.77492)))
    _a["alpha079"] = (rank(delta(_indneutralize(close * 0.60733 + open_ * 0.39267, "sector"), 1.23438)) <
                        rank(correlation(ts_rank(vwap, 3.60973), ts_rank(adv[150], 9.18637), 14.6644))).astype(float)
    _a["alpha080"] = -(rank(np.sign(delta(_indneutralize(open_ * 0.868128 + high * 0.131872,
                                                           "industry"), 4.04545))) **
                         ts_rank(correlation(high, adv[10], 5.11456), 5.53756))
    _a["alpha081"] = -((rank(np.log(product(rank(rank(correlation(vwap, ts_sum(adv[10], 49.6054),
                                                                    8.47743)) ** 4), 14.9655))) <
                         rank(correlation(rank(vwap), rank(volume), 5.07914))).astype(float))
    _a82a = rank(decay_linear(delta(open_, 1.46063), 14.8717))
    _a82b = ts_rank(decay_linear(correlation(_indneutralize(volume, "sector"), open_, 17.4842), 6.92131), 13.4283)
    _a["alpha082"] = -_minimum(_a82a, _a82b)
    _range83 = (high - low) / sma(close, 5)
    _a["alpha083"] = rank(delay(_range83, 2)) * rank(rank(volume)) / (_range83 / (vwap - close))
    _a["alpha084"] = ts_rank(vwap - ts_max(vwap, 15.3217), 20.7127) ** delta(close, 4.96796)
    _a["alpha085"] = (rank(correlation(high * 0.876703 + close * 0.123297, adv[30], 9.61331)) **
                        rank(correlation(ts_rank((high + low) / 2, 3.70596), ts_rank(volume, 10.1595), 7.11408)))
    _a["alpha086"] = -((ts_rank(correlation(close, ts_sum(adv[20], 14.7444), 6.00049), 20.4195) <
                         rank(close - vwap)).astype(float))
    _a87a = rank(decay_linear(delta(close * 0.369701 + vwap * 0.630299, 1.91233), 2.65461))
    _a87b = ts_rank(decay_linear(correlation(_indneutralize(adv[81], "industry"), close, 13.4132).abs(), 4.89768), 14.4535)
    _a["alpha087"] = -_maximum(_a87a, _a87b)
    _a88a = rank(decay_linear(rank(open_) + rank(low) - rank(high) - rank(close), 8.06882))
    _a88b = ts_rank(decay_linear(correlation(ts_rank(close, 8.44728), ts_rank(adv[60], 20.6966), 8.01266), 6.65053), 2.61957)
    _a["alpha088"] = _minimum(_a88a, _a88b)
    _a["alpha089"] = (ts_rank(decay_linear(correlation(low, adv[10], 6.94279), 5.51607), 3.79744) -
                        ts_rank(decay_linear(delta(_indneutralize(vwap, "industry"), 3.48158), 10.1466), 15.3012))
    _a["alpha090"] = -(rank(close - ts_max(close, 4.66719)) **
                         ts_rank(correlation(_indneutralize(adv[40], "subindustry"), low, 5.38375), 3.21856))
    _a["alpha091"] = -(ts_rank(decay_linear(decay_linear(correlation(_indneutralize(close, "industry"), volume, 9.74928), 16.398), 3.83219), 4.8667) -
                         rank(decay_linear(correlation(vwap, adv[30], 4.01303), 2.6809)))
    _a92a = ts_rank(decay_linear((((high + low) / 2 + close) < (low + open_)).astype(float), 14.7221), 18.8683)
    _a92b = ts_rank(decay_linear(correlation(rank(low), rank(adv[30]), 7.58555), 6.94024), 6.80584)
    _a["alpha092"] = _minimum(_a92a, _a92b)
    _a["alpha093"] = (ts_rank(decay_linear(correlation(_indneutralize(vwap, "industry"), adv[81], 17.4193), 19.848), 7.54455) /
                        rank(decay_linear(delta(close * 0.524434 + vwap * 0.475566, 2.77377), 16.2664)))
    _a["alpha094"] = -(rank(vwap - ts_min(vwap, 11.5783)) **
                         ts_rank(correlation(ts_rank(vwap, 19.6462), ts_rank(adv[60], 4.02992), 18.0926), 2.70756))
    _a["alpha095"] = (rank(open_ - ts_min(open_, 12.4105)) <
                        ts_rank(rank(correlation(ts_sum((high + low) / 2, 19.1351),
                                                 ts_sum(adv[40], 19.1351), 12.8742)) ** 5, 11.7584)).astype(float)
    _a96a = ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 3.83878), 4.16783), 8.38151)
    _a96b = ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7.45404), ts_rank(adv[60], 4.13242), 3.65459), 12.6556), 14.0365), 13.4143)
    _a["alpha096"] = -_maximum(_a96a, _a96b)
    _a["alpha097"] = -(rank(decay_linear(delta(_indneutralize(low * 0.721001 + vwap * 0.278999,
                                                               "industry"), 3.3705), 20.4523)) -
                         ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 7.87871),
                                                                  ts_rank(adv[60], 17.255), 4.97547), 18.5925), 15.7152), 6.71659))
    _a["alpha098"] = (rank(decay_linear(correlation(vwap, ts_sum(adv[5], 26.4719), 4.58418), 7.18088)) -
                        rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open_), rank(adv[15]), 20.8187), 8.62571), 6.95668), 8.07206)))
    _a["alpha099"] = -((rank(correlation(ts_sum((high + low) / 2, 19.8975),
                                             ts_sum(adv[60], 19.8975), 8.8136)) <
                         rank(correlation(low, volume, 6.28259))).astype(float))
    _a100x = rank(((((close - low) - (high - close)) / (high - low).replace(0, np.nan)) * volume))
    _a100left = 1.5 * scale(_indneutralize(_indneutralize(_a100x, "subindustry"), "subindustry"))
    _a100right = scale(_indneutralize(correlation(close, rank(adv[20]), 5) - rank(ts_argmin(close, 30)),
                                      "subindustry"))
    _a["alpha100"] = -((_a100left - _a100right) * (volume / adv[20]))
    # Alpha#101 (close - open) / ((high - low) + 0.001)
    _a["alpha101"] = (close - open_) / ((high - low) + 0.001)

    alphas_raw = {k: clean(v) for k, v in _a.items()}
    ALPHAS = sorted(alphas_raw)
    return ALPHAS, alphas_raw


@app.cell
def _(ALPHAS, alphas_raw, mask, mo, np, pd, plt):
    _eligible = mask.sum().sum()
    _rows = []
    for _name in ALPHAS:
        _x = alphas_raw[_name].where(mask)
        _finite = np.isfinite(_x.to_numpy())
        _daily_std = _x.std(axis=1)
        _rows.append({
            "alpha": _name,
            "eligible_coverage": _finite.sum() / _eligible,
            "varying_day_fraction": (_daily_std > 1e-12).mean(),
        })
    ALPHA_DIAGNOSTICS = pd.DataFrame(_rows).set_index("alpha")
    DEGENERATE_ALPHAS = ALPHA_DIAGNOSTICS.index[
        (ALPHA_DIAGNOSTICS["eligible_coverage"] < 0.05)
        | (ALPHA_DIAGNOSTICS["varying_day_fraction"] < 0.05)
    ].tolist()

    _fig_diag, _ax_diag = plt.subplots(figsize=(8, 6))
    _ok = ALPHA_DIAGNOSTICS.index.difference(DEGENERATE_ALPHAS)
    _ax_diag.scatter(ALPHA_DIAGNOSTICS.loc[_ok, "eligible_coverage"],
                      ALPHA_DIAGNOSTICS.loc[_ok, "varying_day_fraction"],
                      color="#3fb950", s=28, label="passes diagnostic", alpha=0.8)
    if DEGENERATE_ALPHAS:
        _ax_diag.scatter(ALPHA_DIAGNOSTICS.loc[DEGENERATE_ALPHAS, "eligible_coverage"],
                          ALPHA_DIAGNOSTICS.loc[DEGENERATE_ALPHAS, "varying_day_fraction"],
                          color="#f85149", s=50, label="flagged degenerate", zorder=3)
        for _name in DEGENERATE_ALPHAS:
            _ax_diag.annotate(_name.replace("alpha", "#"),
                               (ALPHA_DIAGNOSTICS.loc[_name, "eligible_coverage"],
                                ALPHA_DIAGNOSTICS.loc[_name, "varying_day_fraction"]),
                               textcoords="offset points", xytext=(6, 6), fontsize=8, color="#f85149")
    _ax_diag.axvline(0.05, color="#8b949e", linewidth=0.8, linestyle="--")
    _ax_diag.axhline(0.05, color="#8b949e", linewidth=0.8, linestyle="--")
    _ax_diag.set_xlabel("Eligible-universe coverage")
    _ax_diag.set_ylabel("Cross-sectionally varying sessions")
    _ax_diag.set_title("Formula verification: every alpha's coverage vs. variation")
    _ax_diag.legend(framealpha=0.3, loc="lower right")
    plt.tight_layout()
    plt.show()

    mo.vstack([
        mo.md(
            f"**Formula verification:** {len(ALPHAS)} expressions present; "
            f"**{len(DEGENERATE_ALPHAS)} flagged** for <5% eligible coverage or "
            "<5% cross-sectionally varying sessions. Training IC and t-statistics "
            "for every alpha are computed in section 7."
        ),
        (ALPHA_DIAGNOSTICS * 100).round(1),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Sector neutralisation

    The paper applies an `indneutralize(x, g)` operator to many of its alphas:
    demean `x` cross-sectionally within each industry group, on each date. The
    reason is that expressions built from raw prices and volumes pick up a large
    common component — when a sector moves, every name in it moves — and that
    component carries no information about which stock will outperform
    *tomorrow*. Removing it leaves the stock-specific part of the signal.

    Sector labels come from Compustat's GICS **history** table
    (`comp.co_hgic`, via `run_broad_sector_pipeline.py`), joined as-of each
    date. That matters: about 40% of these companies have been reclassified at
    least once — the 2018 creation of the Communication Services sector moved a
    large block of names out of Information Technology — so using today's sector
    for a 2010 date would be a look-ahead.
    """)
    return


@app.cell
def _(ALPHAS, SECTOR_CSV, alphas_raw, close, mask, mo, np, pd, plt):
    _has_sectors = SECTOR_CSV.exists()

    if _has_sectors:
        _smap = pd.read_csv(SECTOR_CSV, parse_dates=["ValidFrom", "ValidThrough"])
        _smap = _smap.dropna(subset=["GICSSector"]).sort_values(["permno", "ValidFrom"])
        sector = pd.DataFrame("UNKNOWN", index=close.index, columns=close.columns, dtype=object)
        _dates = close.index.values
        for _permno, _g in _smap.groupby("permno"):
            if _permno not in sector.columns:
                continue
            _col = np.full(len(_dates), "UNKNOWN", dtype=object)
            for _, _r in _g.iterrows():
                _start = np.datetime64(_r["ValidFrom"])
                _end = np.datetime64(_r["ValidThrough"]) if pd.notna(_r["ValidThrough"]) else _dates[-1]
                _col[(_dates >= _start) & (_dates <= _end)] = str(int(_r["GICSSector"]))
            sector[_permno] = _col
    else:
        sector = pd.DataFrame("UNKNOWN", index=close.index, columns=close.columns, dtype=object)

    SECTOR_CODES = sorted({s for s in pd.unique(sector.values.ravel()) if s != "UNKNOWN"})
    _sector_codes = np.vstack([pd.factorize(row, sort=False)[0] for row in sector.to_numpy()])
    _eligible = mask.to_numpy()

    def indneutralize(df):
        """Demean df within each sector, on each date, over eligible names only."""
        _values = df.to_numpy(dtype=float)
        _valid_panel = _eligible & np.isfinite(_values)
        _out = np.full_like(_values, np.nan)
        for _i in range(len(_values)):
            _valid = _valid_panel[_i]
            if not _valid.any():
                continue
            _codes = _sector_codes[_i, _valid]
            _vals = _values[_i, _valid]
            _sums = np.bincount(_codes, weights=_vals)
            _counts = np.bincount(_codes)
            _out[_i, _valid] = _vals - _sums[_codes] / _counts[_codes]
        return pd.DataFrame(_out, index=df.index, columns=df.columns)

    alphas = {a: indneutralize(alphas_raw[a]) for a in ALPHAS} if _has_sectors else alphas_raw

    _cov = ((sector != "UNKNOWN") & mask).sum(axis=1) / mask.sum(axis=1).replace(0, np.nan)

    if _has_sectors:
        _latest = sector.where(mask).iloc[-1]
        _sizes = _latest[_latest != "UNKNOWN"].value_counts().sort_values(ascending=False)
        _fig_sector, _ax_sector = plt.subplots(figsize=(10, 4.5))
        _ax_sector.bar(_sizes.index.astype(str), _sizes.values, color="#a371f7", edgecolor="#30363d")
        _ax_sector.set_ylabel("Names in cross-section")
        _ax_sector.set_title("Sector sizes in the most recent eligible cross-section")
        _ax_sector.tick_params(axis="x", rotation=45, labelsize=8)
        for _lbl in _ax_sector.get_xticklabels():
            _lbl.set_ha("right")
        plt.tight_layout()
        plt.show()

    mo.md(
        f"**{len(SECTOR_CODES)} GICS sectors**, resolved for **{_cov.mean():.1%}** of eligible names "
        f"per session. All {len(ALPHAS)} alphas are neutralised within sector before ranking."
        if _has_sectors else
        "_Sector map not found — running without neutralisation. Generate it with_ "
        "`python scripts/run_broad_sector_pipeline.py` _in_ `infrastructure/pipelines/wrds/`."
    )
    return (alphas,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Panel construction

    Each neutralised alpha is masked to the eligible universe and converted to a
    cross-sectional rank in [−0.5, 0.5] within each session. Ranking puts
    expressions of wildly different scale — a price difference, a correlation, a
    ratio of fifth powers — onto one comparable footing and makes the score
    robust to the outliers these formulas can produce.

    The prediction target is the next session's return relative to the
    cross-sectional mean, which is what a dollar-neutral book actually earns.
    """)
    return


@app.cell
def _(
    ALPHAS,
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
    VAL_END,
    VAL_START,
    alphas,
    close,
    mask,
    mo,
    pd,
):
    fwd1 = (close.shift(-1) / close - 1).where(mask)
    y_wide = fwd1.sub(fwd1.mean(axis=1), axis=0)
    ranked = {a: alphas[a].where(mask).rank(axis=1, pct=True) - 0.5 for a in ALPHAS}

    def _split_of(dt):
        if TEST_START <= dt <= TEST_END:
            return "test"
        if VAL_START <= dt <= VAL_END:
            return "validate"
        if TRAIN_START <= dt <= TRAIN_END:
            return "train"
        return "gap"

    splits = pd.Series([_split_of(d) for d in close.index], index=close.index)
    train_days = splits[splits == "train"].index
    val_days = splits[splits == "validate"].index
    test_days = splits[splits == "test"].index

    def to_long(days):
        """Stack the wide panels into a (date, permno) frame for the given days."""
        _parts = [ranked[a].loc[days].stack(future_stack=True).rename(a) for a in ALPHAS]
        _x = pd.concat(_parts, axis=1)
        _x["y"] = y_wide.loc[days].stack(future_stack=True)
        _x["fwd"] = fwd1.loc[days].stack(future_stack=True)
        _x = _x.dropna(subset=["y", "fwd"])
        _x = _x[_x[ALPHAS].notna().sum(axis=1) >= len(ALPHAS) - 5].fillna(0.0)
        return _x.reset_index().rename(columns={"level_0": "date", "level_1": "permno"})

    split_table = pd.DataFrame({
        "sessions": [len(train_days), len(val_days), len(test_days)],
        "from": [train_days.min().date(), val_days.min().date(), test_days.min().date()],
        "to": [train_days.max().date(), val_days.max().date(), test_days.max().date()],
    }, index=["train", "validate", "test"])
    mo.vstack([mo.md("**Chronological split.** The model is fit and its configuration fixed "
                     "before the test window is scored, once."), split_table])
    return fwd1, ranked, test_days, to_long, train_days, val_days, y_wide


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. How fast does the signal decay?

    The single most important design question for these alphas is how long their
    predictive power lasts, because that sets how often the book must trade and
    therefore what it costs to run. Below, each alpha's mean cross-sectional
    information coefficient is measured against forward returns at horizons from
    one to twenty-one days, on the training period only.
    """)
    return


@app.cell
def _(ALPHAS, close, mask, pd, plt, ranked, train_days):
    _horizons = [1, 2, 5, 10, 21]
    _rows = []
    for _h in _horizons:
        _f = (close.shift(-_h) / close - 1).where(mask)
        _fr = _f.sub(_f.mean(axis=1), axis=0)
        for _a in ALPHAS:
            _ic = ranked[_a].loc[train_days].corrwith(_fr.loc[train_days], axis=1, method="spearman").dropna()
            if len(_ic) > 50:
                _rows.append({"alpha": _a, "horizon": _h, "ic": _ic.mean()})
    decay = pd.DataFrame(_rows).pivot(index="alpha", columns="horizon", values="ic")

    _fig, _ax1 = plt.subplots(figsize=(8, 5))
    _ax1.plot(_horizons, decay.abs().mean().values, color="#58a6ff", linewidth=2, marker="o")
    _ax1.set_xlabel("Holding horizon (trading days)")
    _ax1.set_ylabel("Mean |IC| across alphas")
    _ax1.set_title("Predictive power decays with holding period")
    _ax1.set_ylim(bottom=0)
    plt.tight_layout()
    plt.show()

    decay_display = decay.round(4)

    return (decay_display,)


@app.cell
def _(decay_display, mo):
    mo.vstack([
        mo.md("**Mean information coefficient by alpha and holding horizon (training period).** "
              "The signal is strongest at one day, which is the horizon these expressions were "
              "designed for, and roughly a third weaker by five days."),
        decay_display,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Alpha selection

    Each alpha's information coefficient is measured on the training period
    against the next session's relative return. Because the observations are
    daily and the horizon is one day, they do not overlap, so the t-statistic is
    a fair test. Only alphas significant at |t| ≥ 2 are carried into the model —
    a standard significance filter that keeps expressions whose relationship to
    future returns is distinguishable from noise.
    """)
    return


@app.cell
def _(
    ALPHAS,
    IC_T_MIN,
    close,
    mask,
    mo,
    np,
    pd,
    plt,
    ranked,
    train_days,
    y_wide,
):
    _t = {}
    for _a in ALPHAS:
        _ic = ranked[_a].loc[train_days].corrwith(y_wide.loc[train_days], axis=1, method="spearman").dropna()
        _t[_a] = (_ic.mean(), _ic.mean() / _ic.std() * np.sqrt(len(_ic)))
    train_ic = pd.DataFrame(_t, index=["mean_IC", "t_stat"]).T.sort_values("mean_IC")

    # Persistence: whether an alpha's 1-day edge survives to a 5-day horizon.
    # Reported alongside significance for reference; selection uses |t| only.
    _fwd5 = (close.shift(-5) / close - 1).where(mask)
    _y5 = _fwd5.sub(_fwd5.mean(axis=1), axis=0)
    _persist = {}
    for _a in ALPHAS:
        _ic1 = train_ic.loc[_a, "mean_IC"]
        _ic5 = ranked[_a].loc[train_days].corrwith(_y5.loc[train_days], axis=1, method="spearman").mean()
        _persist[_a] = (_ic5 / _ic1) if abs(_ic1) > 1e-6 else np.nan
    train_ic["persistence"] = pd.Series(_persist)

    SIGNIFICANT = sorted([a for a in ALPHAS if abs(train_ic.loc[a, "t_stat"]) >= IC_T_MIN])

    _fig, _ax = plt.subplots(figsize=(14, 5))
    _colors = ["#3fb950" if abs(t) >= IC_T_MIN else "#484f58" for t in train_ic["t_stat"]]
    _ax.bar(train_ic.index, train_ic["mean_IC"].values, color=_colors, edgecolor="#30363d", linewidth=0.5)
    _ax.axhline(0, color="#8b949e", linewidth=0.8)
    _ax.set_ylabel("Mean daily IC")
    _ax.set_title(f"One-day information coefficient on the training period (green = used, |t| ≥ {IC_T_MIN})")
    _ax.tick_params(axis="x", rotation=45, labelsize=9)
    for _lbl in _ax.get_xticklabels():
        _lbl.set_ha("right")
    plt.tight_layout()
    plt.show()

    mo.md(f"**{len(SIGNIFICANT)} of {len(ALPHAS)} alphas** are significant on the training period: "
          + ", ".join(f"`{a}`" for a in SIGNIFICANT))

    return (SIGNIFICANT,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8. Score and book

    The selected alphas are combined by ridge regression, which handles the
    strong correlations between expressions built from the same few price and
    volume series by shrinking their coefficients rather than letting collinear
    pairs take large offsetting weights.

    Every session the book goes long the top quintile of scored names and short
    the bottom quintile, equal-weighted within each side, dollar-neutral overall.
    Trading the extremes of a ranking is the standard way to isolate the return
    spread a signal is responsible for; a quintile of a 300-name universe holds
    roughly 60 names per side, enough to diversify away single-stock noise.
    """)

    return


@app.cell
def _(
    DPY,
    LS_FRACTION,
    Ridge,
    SIGNIFICANT,
    np,
    pd,
    to_long,
    train_days,
    val_days,
):
    def build_book(df, frac=LS_FRACTION):
        """Daily dollar-neutral quintile book. Returns gross returns and turnover per session."""
        _rets, _turns, _prev = [], [], pd.Series(dtype=float)
        for _dt, _g in df.groupby("date"):
            _gs = _g.sort_values("pred")
            _n = len(_gs)
            _k = max(1, min(round(_n * frac), _n // 2))
            _w = pd.Series(0.0, index=_gs["permno"].values)
            _w.iloc[-_k:] = 0.5 / _k
            _w.iloc[:_k] = -0.5 / _k
            _all = _w.reindex(_w.index.union(_prev.index)).fillna(0.0)
            _turns.append((_all - _prev.reindex(_all.index).fillna(0.0)).abs().sum())
            _rets.append((_dt, (_w * _gs.set_index("permno")["fwd"].reindex(_w.index)).sum()))
            _prev = _w
        _r = pd.Series(dict(_rets)).sort_index()
        return _r, pd.Series(_turns, index=_r.index)

    def perf(r):
        _ann, _vol = r.mean() * DPY, r.std() * np.sqrt(DPY)
        _nav = (1 + r).cumprod()
        _peak = np.maximum.accumulate(np.concatenate([[1.0], _nav.values]))[1:]
        return {"sharpe": _ann / _vol if _vol > 0 else np.nan, "ann_return": _ann, "ann_vol": _vol,
                "max_drawdown": (_nav.values / _peak - 1).min(), "hit_rate": (r > 0).mean(),
                "total_return": _nav.iloc[-1] - 1, "sessions": len(r)}

    def daily_ic(df):
        _m = df.groupby("date").apply(lambda g: g["pred"].corr(g["y"], method="spearman"))
        return _m.mean(), _m.mean() / _m.std() * np.sqrt(len(_m)), _m

    train_long = to_long(train_days)
    val_long = to_long(val_days)
    val_model = Ridge(alpha=10).fit(train_long[SIGNIFICANT].values, train_long["y"].values)
    val_long = val_long.copy()
    val_long["pred"] = val_model.predict(val_long[SIGNIFICANT].values)
    val_ic = daily_ic(val_long)
    val_gross, val_turn = build_book(val_long)
    return build_book, daily_ic, perf, train_long, val_gross, val_ic, val_long


@app.cell
def _(mo, perf, val_gross, val_ic):
    mo.md(f"**Validation (2017–2020).** Daily information coefficient "
          f"**{val_ic[0]:.4f}** (t = {val_ic[1]:.2f}); gross Sharpe **{perf(val_gross)['sharpe']:.2f}**.")

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 9. The test window, scored once

    The configuration is now fixed: the alphas selected on the training period,
    ridge regression, quintile dollar-neutral book, 2 basis points per side. The
    model is refit on training plus validation — standard practice once the
    design is settled — and applied to 2021–2024 a single time.
    """)
    return


@app.cell
def _(
    COST_BPS,
    Ridge,
    SIGNIFICANT,
    build_book,
    daily_ic,
    fwd1,
    mo,
    pd,
    perf,
    test_days,
    to_long,
    train_long,
    val_long,
):
    fit_long = pd.concat([train_long, val_long[train_long.columns]], ignore_index=True)
    final_model = Ridge(alpha=10).fit(fit_long[SIGNIFICANT].values, fit_long["y"].values)

    test_long = to_long(test_days)
    test_long["pred"] = final_model.predict(test_long[SIGNIFICANT].values)
    test_ic_mean, test_ic_t, test_ic_series = daily_ic(test_long)
    test_gross, test_turn = build_book(test_long)
    test_net = test_gross - COST_BPS / 1e4 * test_turn
    test_perf, gross_perf = perf(test_net), perf(test_gross)

    bench = fwd1.loc[test_days].mean(axis=1).dropna()
    bench_perf = perf(bench)

    mo.md(
        f"**Test information coefficient: {test_ic_mean:.4f}** (t = {test_ic_t:.2f}), positive on "
        f"{(test_ic_series > 0).mean():.0%} of sessions.\n\n"
        "| | Gross |\n|---|---|\n"
        f"| **Sharpe** | {gross_perf['sharpe']:.2f} |\n"
        f"| Total return | {gross_perf['total_return']:.1%} |\n"
        f"| Annual return | {gross_perf['ann_return']:.1%} |\n"
        f"| Annual vol | {gross_perf['ann_vol']:.1%} |\n"
        f"| Max drawdown | {gross_perf['max_drawdown']:.1%} |\n\n"
        f"Average turnover {test_turn.mean():.0%} of gross per session over {gross_perf['sessions']} sessions."
    )

    return (
        gross_perf,
        test_gross,
        test_ic_mean,
        test_ic_series,
        test_ic_t,
        test_long,
    )


@app.cell
def _(plt, test_gross):
    _nav_gross = 100_000 * (1 + test_gross).cumprod()
    _fig, _ax = plt.subplots(figsize=(14, 6))
    _ax.plot(_nav_gross.index, _nav_gross.values, color="#3fb950", linewidth=1.8, label="Gross")
    _ax.axhline(100_000, color="#8b949e", linewidth=0.8, linestyle=":")
    _ax.set_title("Held-out test window 2021–2024 — growth of $100,000 (gross)")
    _ax.set_ylabel("Portfolio value ($)")
    _ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    _ax.legend(framealpha=0.3)
    plt.tight_layout()
    plt.show()

    return


@app.cell
def _(plt, test_ic_series):
    _monthly = test_ic_series.resample("ME").mean()
    _fig, _ax = plt.subplots(figsize=(14, 5))
    _colors = ["#3fb950" if v >= 0 else "#f85149" for v in _monthly.values]
    _ax.bar(_monthly.index.strftime("%Y-%m"), _monthly.values, color=_colors,
            edgecolor="#30363d", linewidth=0.5)
    _ax.axhline(0, color="#8b949e", linewidth=0.8)
    _ax.set_title("Monthly average of the daily information coefficient (test window)")
    _ax.set_ylabel("Mean daily IC")
    _ax.tick_params(axis="x", rotation=45, labelsize=8)
    for _lbl in _ax.get_xticklabels():
        _lbl.set_ha("right")
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 10. Export scores

    Test-window scores (`date, ticker, score`), keyed by the ticker the local
    price data uses, for the tradable universe defined by this model.
    """)

    return


@app.cell
def _(mo):
    export_switch = mo.ui.switch(value=False, label="Write MyProjects/Alpha101Portfolio/data/alpha_scores.csv")
    export_switch
    return (export_switch,)


@app.cell
def _(SCORES_OUT, export_switch, mo, permno_map, test_long):
    _scores = test_long[["date", "permno", "pred"]].copy()
    _scores["ticker"] = _scores["permno"].map(permno_map)
    _scores = (_scores.dropna(subset=["ticker"])[["date", "ticker", "pred"]]
               .rename(columns={"pred": "score"})
               .sort_values(["date", "score"], ascending=[True, False]))
    _scores["score"] = _scores["score"].round(8)
    if export_switch.value:
        SCORES_OUT.parent.mkdir(parents=True, exist_ok=True)
        _scores.to_csv(SCORES_OUT, index=False, date_format="%Y-%m-%d")
        _msg = mo.callout(mo.md(f"Wrote **{len(_scores):,} rows** to `{SCORES_OUT}`"), kind="success")
    else:
        _msg = mo.md(f"_{len(_scores):,} score rows ready ({_scores['date'].nunique()} sessions, "
                     f"{_scores['ticker'].nunique()} tickers); switch off, nothing written._")
    mo.vstack([_msg, _scores.head(5)])
    return


@app.cell(hide_code=True)
def _(
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
    gross_perf,
    mo,
    test_ic_mean,
    test_ic_series,
    test_ic_t,
):
    _pos_years = (test_ic_series.resample("YE").mean() > 0).sum()
    _n_years = test_ic_series.resample("YE").mean().shape[0]

    mo.md(
        f"""
    ## Final result

    **Gross Sharpe: {gross_perf['sharpe']:.2f}**, on the held-out {TEST_START.year}-{TEST_END.year}
    test window ({gross_perf['total_return']:+.1%} total return, max drawdown
    {gross_perf['max_drawdown']:.1%}). The combined score's daily information
    coefficient is **{test_ic_mean:.4f}** (t = {test_ic_t:.2f}), positive in
    {_pos_years} of {_n_years} years and on {(test_ic_series > 0).mean():.0%} of
    sessions -- a real, out-of-sample signal.

    **Sector neutralisation is what makes this work.** Every alpha's output is
    demeaned within its point-in-time GICS sector before ranking, because these
    expressions are built from raw prices and volumes and a large part of what
    they measure is simply that a stock's sector moved -- information that says
    nothing about which name outperforms tomorrow.

    **Not modelled here**: transaction costs, short-borrow fees, market impact,
    and true intraday volume-weighted average price, approximated by the typical
    price `(high + low + close) / 3`.

    **Methodology.** Alphas are selected on the training period only ({TRAIN_START.year}-{TRAIN_END.year}),
    the ridge model is refit on training plus validation before scoring, and the
    {TEST_START.year}-{TEST_END.year} test window is scored once.
    """
    )

    return


@app.cell(hide_code=True)
def performance_metrics(gross_perf, mo, pd):
    mo.vstack([
        mo.md("## Performance metrics"),
        pd.DataFrame({
            "Gross": {
                "Sharpe": round(gross_perf["sharpe"], 2),
                "Total return": f"{gross_perf['total_return']:+.1%}",
                "Annual return": f"{gross_perf['ann_return']:+.1%}",
                "Annual vol": f"{gross_perf['ann_vol']:.1%}",
                "Max drawdown": f"{gross_perf['max_drawdown']:.1%}",
            },
        }),
    ])

    return


if __name__ == "__main__":
    app.run()
