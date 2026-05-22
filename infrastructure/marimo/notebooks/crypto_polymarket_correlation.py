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
    # Crypto × Polymarket Correlation

    How do **Polymarket prediction-market probabilities** for crypto events move
    with actual **BTC / ETH / SOL prices**?

    **Data sources:**
    - Polymarket CLOB — local price CSVs for crypto-tagged markets (Dec 2025 → present)
    - yfinance — daily crypto prices (BTC-USD, ETH-USD, SOL-USD) fetched live
    - COIN — Coinbase stock (optional; proxy for crypto-equity sentiment)

    Local Polymarket files are **intentionally not committed** (see warning below).
    Run `infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py` to refresh.
    """)
    return


@app.cell
def _():
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import pathlib

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
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "figure.dpi": 150,
        "savefig.facecolor": "#0d1117",
    })
    return np, pathlib, pd, plt


@app.cell
def _(mo, pathlib):
    # Data path checks — warns if local data is missing
    # NOTE: local data files are intentionally not committed to git
    REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
    POLY_PRICES_DIR = REPO_ROOT / "infrastructure/pipelines/polymarket/lean-data/alternative/polymarket/prices"
    CRYPTO_DATA_DIR = REPO_ROOT / "infrastructure/pipelines/crypto/lean-data/crypto"

    poly_ok = POLY_PRICES_DIR.is_dir() and any(POLY_PRICES_DIR.glob("*.csv"))
    crypto_ok = CRYPTO_DATA_DIR.is_dir() and any(CRYPTO_DATA_DIR.rglob("*.zip"))

    _warnings = []
    if not poly_ok:
        _warnings.append(
            "**Polymarket prices not found.**  \n"
            f"Expected: `{POLY_PRICES_DIR}`  \n"
            "Run: `cd infrastructure/pipelines/polymarket && python scripts/run_prices_pipeline.py --skip-existing`"
        )
    if not crypto_ok:
        _warnings.append(
            "**Local crypto OHLCV not found** (no zips in crypto pipeline).  \n"
            "Using **yfinance live data** as fallback — no action needed.  \n"
            "To build local data: `cd infrastructure/pipelines/crypto && python scripts/run_pipeline.py --exchange coinbase`"
        )

    _callouts = []
    if _warnings:
        _callouts.append(mo.callout(mo.md("\n\n".join(_warnings)), kind="warn"))
    _callouts.append(mo.callout(
        mo.md(
            "**Local data files are intentionally not committed to git.**  \n"
            "Polymarket prices, crypto OHLCV zips, and COIN data live only on your machine.  \n"
            "Run the relevant pipelines to populate them before analysis."
        ),
        kind="info",
    ))
    mo.vstack(_callouts)
    return POLY_PRICES_DIR, poly_ok


@app.cell
def _(POLY_PRICES_DIR, mo, pd, poly_ok):
    # Load Polymarket crypto market price series
    _CRYPTO_KW = ["bitcoin", "btc", "ethereum", "eth", "solana", "sol", "xrp", "crypto", "ripple"]
    _ASSET_MAP = {
        "btc": ["bitcoin", "btc", "microstrategy"],
        "eth": ["ethereum", "eth", "eth-flipped"],
        "sol": ["solana", "sol"],
        "xrp": ["xrp", "ripple"],
        "crypto": ["crypto", "sp-500-company-buys", "us-national", "us-government",
                   "trump-eliminates", "record-crypto", "another-sp"],
    }

    if not poly_ok:
        meta_df = pd.DataFrame()
        series_map = {}
        _poly_note = mo.callout(mo.md("No Polymarket data — run the prices pipeline first."), kind="warn")
    else:
        _records = []
        for _fname in sorted(POLY_PRICES_DIR.glob("*.csv")):
            _slug = _fname.stem
            if not any(_k in _slug for _k in _CRYPTO_KW):
                continue
            try:
                _dfp = pd.read_csv(_fname)
                _dfp["datetime"] = pd.to_datetime(_dfp["datetime"], utc=True)
                _dfp = _dfp.set_index("datetime").sort_index()
                _daily = _dfp["price"].resample("D").last().dropna()
                if len(_daily) < 10:
                    continue
                _asset = "other"
                for _a, _kws in _ASSET_MAP.items():
                    if any(_k in _slug for _k in _kws):
                        _asset = _a
                        break
                _records.append({
                    "slug": _slug, "asset": _asset,
                    "n_days": len(_daily),
                    "start": _daily.index[0].date(),
                    "end": _daily.index[-1].date(),
                    "series": _daily,
                })
            except Exception:
                continue

        meta_df = pd.DataFrame([{k: v for k, v in r.items() if k != "series"} for r in _records])
        series_map = {r["slug"]: r["series"] for r in _records}
        _poly_note = mo.md(
            f"Loaded **{len(_records)} crypto Polymarket markets** across assets: "
            + ", ".join(f"`{a}`" for a in sorted(meta_df["asset"].unique()))
        )

    _poly_note
    return meta_df, series_map


@app.cell
def _(mo, pd):
    import yfinance as yf

    _raw = yf.download(["BTC-USD", "ETH-USD", "SOL-USD"], start="2025-11-01", progress=False, auto_adjust=True)
    prices_df = _raw["Close"].copy()
    prices_df.columns = ["btc", "eth", "sol"]
    prices_df.index = pd.to_datetime(prices_df.index, utc=True)
    prices_df = prices_df.sort_index().dropna(how="all")
    returns_df = prices_df.pct_change().dropna(how="all")

    mo.md(
        f"**Crypto prices (yfinance):** {prices_df.index[0].date()} → {prices_df.index[-1].date()}"
        f"  ·  {len(prices_df)} days  ·  BTC ${prices_df['btc'].iloc[-1]:,.0f}"
    )
    return prices_df, returns_df, yf


@app.cell(hide_code=True)
def _(mo, pd, yf):
    # Optional: Coinbase stock as crypto-equity proxy
    try:
        _raw_coin = yf.download("COIN", start="2025-11-01", progress=False, auto_adjust=True)
        if _raw_coin.empty:
            raise ValueError("empty")
        coin_prices = _raw_coin["Close"].copy()
        coin_prices.index = pd.to_datetime(coin_prices.index, utc=True)
        coin_prices.name = "coin"
        coin_ok = True
        _coin_note = mo.callout(mo.md("**COIN (Coinbase)** loaded — used as crypto-equity proxy."), kind="success")
    except Exception:
        coin_prices = pd.Series(dtype=float, name="coin")
        coin_ok = False
        _coin_note = mo.callout(mo.md("COIN data unavailable — skipping crypto-equity proxy."), kind="warn")

    _coin_note
    return coin_ok, coin_prices


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Polymarket Crypto Markets — Probability Overview

    Daily YES-token prices (= implied probability) for crypto prediction markets,
    grouped by underlying asset, alongside BTC / ETH spot prices.
    """)
    return


@app.cell
def _(meta_df, plt, prices_df, series_map):
    _ASSET_COLORS = {
        "btc": "#f7931a", "eth": "#627eea", "sol": "#9945ff",
        "xrp": "#00aae4", "crypto": "#aaaaaa", "other": "#555555",
    }
    _assets_order = ["btc", "eth", "sol", "xrp", "crypto"]

    _n = 0 if meta_df.empty else len([a for a in _assets_order if a in meta_df["asset"].values])
    fig_prob, axes_prob = plt.subplots(max(_n, 1) + 1, 1, figsize=(13, 3.2 * (max(_n, 1) + 1)), sharex=False)
    fig_prob.suptitle("Polymarket Crypto Market Probabilities", fontsize=14, color="#c9d1d9", y=1.01)

    _ax_idx = 0
    for _asset in _assets_order:
        if meta_df.empty:
            break
        _subset = meta_df[meta_df["asset"] == _asset]
        if _subset.empty:
            continue
        _ax = axes_prob[_ax_idx]
        _color = _ASSET_COLORS.get(_asset, "#aaa")
        for _, _row in _subset.iterrows():
            _s = series_map[_row["slug"]]
            _ax.plot(_s.index, _s.values, lw=0.9, alpha=0.7, label=_row["slug"][:45])
        _ax.set_ylabel("Prob", fontsize=9)
        _ax.set_ylim(-0.05, 1.05)
        _ax.set_title(f"{_asset.upper()} markets ({len(_subset)})", color=_color)
        if len(_subset) <= 8:
            _ax.legend(fontsize=6, loc="upper left", ncol=2, framealpha=0.3)
        _ax_idx += 1

    _ax_p = axes_prob[_ax_idx]
    if not prices_df.empty and "btc" in prices_df.columns:
        _ax_p.plot(prices_df.index, prices_df["btc"], color="#f7931a", lw=1.2)
        _ax_p2 = _ax_p.twinx()
        _ax_p2.plot(prices_df.index, prices_df["eth"], color="#627eea", lw=1.2, alpha=0.8)
        _ax_p2.tick_params(axis="y", colors="#627eea")
        _ax_p2.set_ylabel("ETH ($)", color="#627eea", fontsize=9)
    _ax_p.set_ylabel("BTC ($)", color="#f7931a", fontsize=9)
    _ax_p.set_title("Spot Prices (BTC / ETH)", color="#c9d1d9")
    _ax_p.tick_params(axis="y", colors="#f7931a")
    fig_prob.tight_layout()
    fig_prob
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Daily-Change Correlations

    Align daily **Polymarket probability changes** (Δprob) with **crypto price returns**.
    Higher positive correlation → market probability rises when the crypto price rises.
    """)
    return


@app.cell
def _(coin_ok, coin_prices, pd, returns_df, series_map):
    # Build aligned daily-change correlation matrix
    _poly_daily = {}
    for _slug, _s in series_map.items():
        _delta = _s.resample("D").last().dropna().diff().dropna()
        if len(_delta) >= 10:
            _poly_daily[_slug] = _delta

    poly_df = pd.DataFrame(_poly_daily)
    if not poly_df.empty:
        poly_df.index = poly_df.index.tz_localize("UTC") if poly_df.index.tzinfo is None else poly_df.index

    _combined = pd.concat([
        returns_df["btc"].rename("BTC_ret"),
        returns_df["eth"].rename("ETH_ret"),
        returns_df["sol"].rename("SOL_ret"),
    ], axis=1) if not returns_df.empty else pd.DataFrame()

    if coin_ok and len(coin_prices) > 0:
        _coin_ret = coin_prices.pct_change().dropna()
        _coin_ret.name = "COIN_ret"
        _combined = pd.concat([_combined, _coin_ret], axis=1)

    if not _combined.empty and not poly_df.empty:
        _combined.index = _combined.index.normalize()
        poly_df.index = poly_df.index.normalize()
        aligned = _combined.join(poly_df, how="inner").dropna(how="all")
    else:
        aligned = pd.DataFrame()

    crypto_cols = [c for c in ["BTC_ret", "ETH_ret", "SOL_ret", "COIN_ret"] if c in aligned.columns]
    poly_cols = [c for c in aligned.columns if c not in crypto_cols]

    if len(aligned) >= 5 and poly_cols and crypto_cols:
        corr_matrix = aligned.corr().loc[poly_cols, crypto_cols]
        corr_matrix.index.name = "market_slug"
    else:
        corr_matrix = pd.DataFrame()

    corr_matrix
    return aligned, corr_matrix


@app.cell
def _(corr_matrix, meta_df, mo, np, plt):
    if corr_matrix.empty:
        mo.callout(mo.md("Not enough overlapping data to compute correlations."), kind="warn")
    else:
        _cp = corr_matrix.copy()
        _cp = _cp.join(meta_df.set_index("slug")[["asset"]], how="left").sort_values("asset")
        _cols = [c for c in _cp.columns if c != "asset"]
        _mat = _cp[_cols].values.astype(float)

        fig_hm, ax_hm = plt.subplots(figsize=(max(6, len(_cols) * 2.2), max(8, len(_cp) * 0.28)))
        _im = ax_hm.imshow(_mat, aspect="auto", cmap="RdYlGn", vmin=-1, vmax=1)
        plt.colorbar(_im, ax=ax_hm, fraction=0.03, pad=0.02)

        ax_hm.set_xticks(range(len(_cols)))
        ax_hm.set_xticklabels([c.replace("_ret", "") for c in _cols], fontsize=10)
        ax_hm.set_yticks(range(len(_cp)))
        ax_hm.set_yticklabels(
            [f"[{r.asset}] {r.market_slug[:42]}" for r in _cp.reset_index().itertuples()],
            fontsize=7
        )
        for _i in range(_mat.shape[0]):
            for _j in range(_mat.shape[1]):
                _v = _mat[_i, _j]
                if not np.isnan(_v):
                    ax_hm.text(_j, _i, f"{_v:.2f}", ha="center", va="center",
                               fontsize=6, color="black" if abs(_v) > 0.4 else "#c9d1d9")
        ax_hm.set_title("Polymarket Δprob vs Crypto Returns — Daily Correlation", fontsize=12)
        fig_hm.tight_layout()
        fig_hm
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. Top Correlated Markets — BTC Scatter Plots

    Scatter plots for the 10 markets with strongest absolute correlation to BTC daily returns.
    """)
    return


@app.cell
def _(aligned, corr_matrix, meta_df, mo, np, plt):
    if corr_matrix.empty or "BTC_ret" not in corr_matrix.columns:
        mo.callout(mo.md("No BTC correlation data available."), kind="warn")
    else:
        _top10 = [s for s in corr_matrix["BTC_ret"].dropna().abs().sort_values(ascending=False).head(10).index
                  if s in aligned.columns]
        _COLORS = {"btc": "#f7931a", "eth": "#627eea", "sol": "#9945ff",
                   "xrp": "#00aae4", "crypto": "#aaaaaa", "other": "#888"}
        _n_rows = (len(_top10) + 1) // 2
        fig_sc, axes_sc = plt.subplots(_n_rows, 2, figsize=(13, 3.5 * _n_rows))
        _flat = axes_sc.flatten() if hasattr(axes_sc, "flatten") else [axes_sc]
        fig_sc.suptitle("Top-10 |BTC Corr| Markets vs BTC Daily Return", fontsize=13, color="#c9d1d9")

        for _i, _slug in enumerate(_top10):
            _ax = _flat[_i]
            _x = aligned["BTC_ret"].dropna()
            _y = aligned[_slug].reindex(_x.index).dropna()
            _x = _x.reindex(_y.index)

            _row = meta_df[meta_df["slug"] == _slug]
            _asset = _row["asset"].iloc[0] if not _row.empty else "other"
            _ax.scatter(_x * 100, _y * 100, s=12, alpha=0.6, color=_COLORS.get(_asset, "#aaa"))
            if len(_x) >= 5:
                _m, _b = np.polyfit(_x.values, _y.values, 1)
                _xl = np.linspace(_x.min(), _x.max(), 100)
                _ax.plot(_xl * 100, (_m * _xl + _b) * 100, color="white", lw=0.8, alpha=0.5)

            _r = corr_matrix.loc[_slug, "BTC_ret"] if _slug in corr_matrix.index else float("nan")
            _ax.set_title(f"[{_asset}] {_slug[:35]}  r={_r:.2f}", fontsize=7)
            _ax.set_xlabel("BTC return (%)", fontsize=8)
            _ax.set_ylabel("Δprob (%pts)", fontsize=8)
            _ax.axhline(0, color="#555", lw=0.5)
            _ax.axvline(0, color="#555", lw=0.5)

        for _j in range(len(_top10), len(_flat)):
            _flat[_j].set_visible(False)
        fig_sc.tight_layout()
        fig_sc
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 4. Rolling 30-Day Correlation

    Does the BTC ↔ Polymarket probability relationship strengthen or weaken over time?
    """)
    return


@app.cell
def _(aligned, corr_matrix, meta_df, mo, plt):
    if corr_matrix.empty or "BTC_ret" not in corr_matrix.columns or len(aligned) < 15:
        mo.callout(mo.md("Not enough data for rolling correlations."), kind="warn")
    else:
        _top5 = [s for s in corr_matrix["BTC_ret"].dropna().abs().sort_values(ascending=False).head(5).index
                 if s in aligned.columns]
        _COLORS = {"btc": "#f7931a", "eth": "#627eea", "sol": "#9945ff",
                   "xrp": "#00aae4", "crypto": "#aaaaaa", "other": "#888"}

        fig_roll, ax_roll = plt.subplots(figsize=(13, 5))
        for _slug in _top5:
            _row = meta_df[meta_df["slug"] == _slug]
            _asset = _row["asset"].iloc[0] if not _row.empty else "other"
            _pair = aligned[["BTC_ret", _slug]].dropna()
            if len(_pair) < 15:
                continue
            _roll = _pair["BTC_ret"].rolling(30).corr(_pair[_slug])
            ax_roll.plot(_roll.index, _roll.values, lw=1.2,
                         label=_slug[:40], color=_COLORS.get(_asset, "#aaa"), alpha=0.8)

        ax_roll.axhline(0, color="#444", lw=0.8)
        ax_roll.set_ylabel("30-day rolling corr")
        ax_roll.set_title("Rolling 30-Day Correlation: BTC returns vs Polymarket Δprob (top-5)")
        ax_roll.legend(fontsize=7, loc="lower left", framealpha=0.3)
        ax_roll.set_ylim(-1.1, 1.1)
        fig_roll.tight_layout()
        fig_roll
    return


if __name__ == "__main__":
    app.run()
