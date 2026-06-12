"""Matplotlib plotting helpers for the passive market instability notebook."""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _save_if_requested(fig, output_path):
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")
    return fig


def _path_columns(paths_df):
    return [col for col in paths_df.columns if col.startswith("path_")]


def plot_passive_share_scenarios(df, output_path=None):
    """
    Plot passive-share scenarios over time with horizontal threshold lines at:
    50%, 65%, 80%, 87%, 91%.
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    x_col = "year" if "year" in df.columns else "t"
    for scenario, group in df.sort_values(x_col).groupby("scenario"):
        ax.plot(group[x_col], group["passive_share"], linewidth=2.0, label=scenario)
    for threshold in [0.50, 0.65, 0.80, 0.87, 0.91]:
        ax.axhline(threshold, color="#8b949e", linestyle="--", linewidth=0.8, alpha=0.7)
        ax.text(df[x_col].max(), threshold, f" {threshold:.0%}", va="center", fontsize=9)
    ax.set_title("Passive Share Scenarios")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Passive share")
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="upper left", ncol=2)
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_threshold_crossings(threshold_df, output_path=None):
    """
    Plot or tabulate threshold crossing years by scenario.
    """
    display_cols = [col for col in ["scenario", "threshold", "crossing_year", "crossing_t"] if col in threshold_df]
    table_df = threshold_df[display_cols].copy()
    if "threshold" in table_df:
        table_df["threshold"] = table_df["threshold"].map(lambda x: f"{x:.0%}")
    if "crossing_year" in table_df:
        table_df["crossing_year"] = table_df["crossing_year"].map(lambda x: "" if pd.isna(x) else f"{x:.0f}")
    if "crossing_t" in table_df:
        table_df["crossing_t"] = table_df["crossing_t"].map(lambda x: "" if pd.isna(x) else f"{x:.1f}")

    fig, ax = plt.subplots(figsize=(12, max(3, 0.35 * len(table_df) + 1.5)))
    ax.axis("off")
    table = ax.table(cellText=table_df.values, colLabels=table_df.columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.25)
    ax.set_title("Passive Share Threshold Crossings")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_simulated_paths(paths_df, title, output_path=None):
    """
    Plot simulated S(t) paths.
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    x_col = "t"
    for col in _path_columns(paths_df):
        ax.plot(paths_df[x_col], paths_df[col], linewidth=0.6, alpha=0.35)
    ax.set_title(title)
    ax.set_xlabel("t")
    ax.set_ylabel("S(t)")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_terminal_distribution(paths_df, horizon_years, output_path=None):
    """
    Histogram of S(t) at a selected horizon.
    """
    idx = (paths_df["t"] - horizon_years).abs().idxmin()
    values = paths_df.loc[idx, _path_columns(paths_df)].astype(float)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(values, bins=25, color="#58a6ff", edgecolor="#30363d", alpha=0.85)
    ax.axvline(values.median(), color="#f85149", linewidth=2, label=f"Median: {values.median():.1f}")
    ax.set_title(f"Distribution of S(t) at t = {horizon_years:g}")
    ax.set_xlabel("S(t)")
    ax.set_ylabel("Path count")
    ax.legend()
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_first_hitting_times(hitting_times_df, output_path=None):
    """
    Histogram of first time S(t) hits 0.
    """
    hits = hitting_times_df["hitting_time"].dropna()
    fig, ax = plt.subplots(figsize=(10, 5))
    if hits.empty:
        ax.text(0.5, 0.5, "No paths hit zero", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    else:
        ax.hist(hits, bins=20, color="#f85149", edgecolor="#30363d", alpha=0.85)
    ax.set_title("First Hitting Times")
    ax.set_xlabel("t")
    ax.set_ylabel("Path count")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_flow_pressure(flow_df, output_path=None):
    """
    Plot aggregate ETF flow-pressure proxy.
    """
    n_rows = 3 if "passive_share" in flow_df.columns else 2
    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 3.5 * n_rows), sharex=True)
    ax1, ax2 = axes[0], axes[1]
    ax1.plot(flow_df["date"], flow_df["aggregate_flow_pressure_proxy"], color="#58a6ff", linewidth=1.1)
    ax1.axhline(0.0, color="#8b949e", linewidth=0.8)
    ax1.set_title("Aggregate ETF Flow-Pressure Proxy")
    ax1.set_ylabel("sum(volume * return)")
    ax2.plot(flow_df["date"], flow_df["aggregate_flow_pressure_z"], color="#d29922", linewidth=1.1)
    ax2.axhline(0.0, color="#8b949e", linewidth=0.8)
    ax2.axhline(2.0, color="#f85149", linestyle="--", linewidth=0.8)
    ax2.axhline(-2.0, color="#f85149", linestyle="--", linewidth=0.8)
    ax2.set_ylabel("rolling z-score")
    ax2.set_xlabel("date")
    if n_rows == 3:
        ax3 = axes[2]
        ax3.plot(flow_df["date"], flow_df["aggregate_flow_pressure_z"], color="#d29922", linewidth=1.0, label="flow z-score")
        ax3b = ax3.twinx()
        ax3b.plot(flow_df["date"], flow_df["passive_share"], color="#3fb950", linewidth=1.4, label="passive share")
        ax3.axhline(0.0, color="#8b949e", linewidth=0.8)
        ax3.set_title("Flow Pressure Overlaid With Passive Share")
        ax3.set_ylabel("flow z-score")
        ax3b.set_ylabel("passive share")
        ax3.set_xlabel("date")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_pressure_quintile_summary(summary_df, raw_df=None, output_path=None):
    """
    Plot passive-pressure quintile diagnostics.
    """
    n_cols = 3 if raw_df is not None else 2
    fig, axes = plt.subplots(1, n_cols, figsize=(5.5 * n_cols, 5))
    x = summary_df["pressure_quintile"].astype(str)
    if "realized_vol_20d" in summary_df:
        axes[0].bar(x, summary_df["realized_vol_20d"], color="#58a6ff", edgecolor="#30363d")
        axes[0].set_title("Average Realized Volatility")
        axes[0].set_xlabel("Pressure quintile")
    if "drawdown_63d" in summary_df:
        axes[1].bar(x, summary_df["drawdown_63d"], color="#f85149", edgecolor="#30363d")
        axes[1].set_title("Average Rolling Drawdown")
        axes[1].set_xlabel("Pressure quintile")
    if raw_df is not None:
        cleaned = raw_df.dropna(subset=["passive_pressure", "realized_vol_20d"])
        axes[2].scatter(cleaned["passive_pressure"], cleaned["realized_vol_20d"], alpha=0.55, color="#3fb950")
        axes[2].set_title("Pressure vs. Realized Volatility")
        axes[2].set_xlabel("passive pressure")
        axes[2].set_ylabel("20-day realized volatility")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_latest_passive_pressure(df, output_path=None):
    """Plot the latest passive-pressure score by ticker."""
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].sort_values("passive_pressure", ascending=False)
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(latest["ticker"], latest["passive_pressure"], color="#3fb950", edgecolor="#30363d")
    ax.set_title(f"Latest Passive Pressure by Ticker ({pd.Timestamp(latest_date).date()})")
    ax.set_xlabel("ticker")
    ax.set_ylabel("passive pressure")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)


def plot_pressure_vs_volatility(df, output_path=None):
    """Scatter passive pressure against realized volatility."""
    cleaned = df.dropna(subset=["passive_pressure", "realized_vol_20d"])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(cleaned["passive_pressure"], cleaned["realized_vol_20d"], alpha=0.55, color="#58a6ff")
    ax.set_title("Passive Pressure vs. Realized Volatility")
    ax.set_xlabel("passive pressure")
    ax.set_ylabel("20-day realized volatility")
    plt.tight_layout()
    return _save_if_requested(fig, output_path)
