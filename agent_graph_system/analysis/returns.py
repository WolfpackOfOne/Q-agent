"""Loading and discovery of daily return series for walk-forward analysis.

The walk-forward module (:mod:`agent_graph_system.analysis.walkforward`) is
deliberately data-source-agnostic — it takes a ``pd.Series`` with a
``DatetimeIndex`` and nothing else. This module is the boundary layer that turns
on-disk artifacts (a returns CSV, or a LEAN backtest result JSON) into such a
series, and that locates those artifacts for a named strategy.

Kept separate from both the CLI and the agents so the loading logic is shared by
``main.py``'s ``walkforward`` subcommand and the autonomous ``WalkforwardAgent``
without duplication.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid importing pandas at module load
    import pandas as pd

log = logging.getLogger(__name__)

# ``agent_graph_system/`` → repo root → ``MyProjects`` is the canonical place
# strategy projects live. Overridable for tests / non-standard checkouts.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def default_search_roots() -> list[Path]:
    """Directories under which per-strategy returns artifacts are looked for.

    ``WALKFORWARD_RETURNS_ROOT`` (``:``-separated) takes precedence; otherwise
    the workspace ``MyProjects`` directory is used.
    """
    env = os.getenv("WALKFORWARD_RETURNS_ROOT")
    if env:
        return [Path(p).expanduser() for p in env.split(os.pathsep) if p]
    return [_REPO_ROOT / "MyProjects"]


def load_returns(path: Path) -> "pd.Series":
    """Load a daily return Series (DatetimeIndex) from a CSV or LEAN result JSON.

    CSV: a date column (date/Date/time/timestamp) plus either a returns column
    (return/returns/ret/daily_return) or a level column (close/equity/value)
    from which percent-change returns are derived.

    JSON: a LEAN backtest result — the equity curve is located heuristically and
    converted to percent-change returns.
    """
    import pandas as pd

    if path.suffix.lower() == ".json":
        return returns_from_lean_json(path)

    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    date_col = next((cols[c] for c in ("date", "time", "timestamp", "datetime") if c in cols), None)
    if date_col is None:
        raise ValueError(f"{path} has no date/time column")
    idx = pd.to_datetime(df[date_col])

    ret_col = next((cols[c] for c in ("return", "returns", "ret", "daily_return") if c in cols), None)
    if ret_col is not None:
        series = pd.Series(df[ret_col].astype(float).values, index=idx)
    else:
        level_col = next((cols[c] for c in ("close", "equity", "value", "nav") if c in cols), None)
        if level_col is None:
            raise ValueError(f"{path} has no return or level (close/equity) column")
        series = pd.Series(df[level_col].astype(float).values, index=idx).pct_change()
    return series.dropna().sort_index()


def returns_from_lean_json(path: Path) -> "pd.Series":
    """Best-effort extraction of a daily return series from a LEAN result JSON."""
    import pandas as pd

    raw = json.loads(path.read_text())
    charts = raw.get("Charts") or raw.get("charts") or {}
    equity_chart = charts.get("Strategy Equity") or charts.get("Equity") or {}
    series_map = equity_chart.get("Series") or equity_chart.get("series") or {}
    equity_series = series_map.get("Equity") or next(iter(series_map.values()), {})
    values = equity_series.get("Values") or equity_series.get("values") or []
    if not values:
        raise ValueError(f"{path}: could not locate an equity curve in the LEAN result")

    times, levels = [], []
    for point in values:
        if isinstance(point, dict):
            times.append(point.get("x") or point.get("Time"))
            levels.append(point.get("y") or point.get("Close") or point.get("Value"))
        else:  # [timestamp, value] pairs
            times.append(point[0])
            levels.append(point[1])
    idx = pd.to_datetime(times, unit="s", errors="coerce")
    series = pd.Series([float(v) for v in levels], index=idx).dropna()
    # Collapse intraday points to a daily close before computing returns.
    daily = series.groupby(series.index.normalize()).last()
    return daily.pct_change().dropna()


# Conventional relative locations of a strategy's returns artifact, most
# specific first. ``*`` segments are globbed; the newest match wins.
_RETURNS_GLOBS = (
    "data/returns.csv",
    "research/returns.csv",
    "returns.csv",
    "backtests/*/result.json",
    "backtests/*/*.json",
)


def discover_returns_path(strategy: str, roots: list[Path] | None = None) -> Path | None:
    """Locate a returns artifact for ``strategy`` under the search roots.

    Returns the path to the first artifact found (newest mtime when a glob
    matches several), or ``None`` if nothing is found. The lookup is by project
    directory name == strategy name, matching how the rest of the system keys
    Strategy nodes off the project folder.
    """
    roots = roots or default_search_roots()
    for root in roots:
        project_dir = root / strategy
        if not project_dir.is_dir():
            continue
        for pattern in _RETURNS_GLOBS:
            matches = sorted(
                (p for p in project_dir.glob(pattern) if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if matches:
                return matches[0]
    return None


def discover_returns(strategy: str, roots: list[Path] | None = None) -> "pd.Series | None":
    """Discover and load a returns Series for ``strategy``; ``None`` if unfound.

    Loading failures (malformed CSV/JSON) are logged and swallowed to ``None``
    so an autonomous caller treats them the same as a missing artifact rather
    than crashing the whole scan.
    """
    path = discover_returns_path(strategy, roots)
    if path is None:
        return None
    try:
        return load_returns(path)
    except (ValueError, KeyError, OSError) as exc:
        log.warning("could not load returns for %s from %s: %s", strategy, path, exc)
        return None
