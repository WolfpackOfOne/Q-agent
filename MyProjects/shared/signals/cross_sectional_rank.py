"""
Cross-sectional rank portfolio construction.

Pure Python. No LEAN imports — must remain importable from a plain
Python environment so it can be symlinked into any QuantConnect project
and unit-tested locally.

Functions:
    tercile_long_short_targets(scores, frac, gross)
        Rank tickers by a model score; long the top `frac` of names,
        short the bottom `frac`, equal-weighted within each side,
        dollar-neutral, total gross exposure = `gross`.
"""

from __future__ import annotations


def tercile_long_short_targets(
    scores: dict[str, float],
    frac: float = 1.0 / 3.0,
    gross: float = 1.0,
    min_names: int = 6,
) -> dict[str, float]:
    """Equal-weight long top-`frac` / short bottom-`frac` by score.

    Args:
        scores: ticker -> model score (higher = more attractive), already
            filtered to tickers with a valid score for this rebalance.
        frac: fraction of the scored universe held on *each* side. The
            default third gives 10 long / 10 short on a 30-name universe.
        gross: total gross exposure (sum of |weight|); split half long,
            half short so the book is dollar-neutral.
        min_names: below this many scored tickers, return {} (flat) —
            a cross-section this thin isn't worth ranking.

    Returns:
        dict[ticker, weight]: +gross/(2k) for the top k, -gross/(2k) for
        the bottom k, where k = max(1, round(len(scores) * frac)) capped
        at half the universe so sides never overlap. Tickers in the
        middle are omitted (weight 0).
    """
    n = len(scores)
    if n < min_names:
        return {}

    ranked = sorted(scores, key=scores.get)
    k = max(1, min(round(n * frac), n // 2))
    shorts, longs = ranked[:k], ranked[-k:]

    w = gross / (2 * k)
    targets = {ticker: -w for ticker in shorts}
    targets.update({ticker: w for ticker in longs})
    return targets


if __name__ == "__main__":
    # Synthetic-data sanity check — run with a plain venv:
    #   python shared/signals/cross_sectional_rank.py
    scores = {f"T{i}": float(i) for i in range(30)}          # T0 lowest ... T29 highest
    t = tercile_long_short_targets(scores)
    longs = {k for k, v in t.items() if v > 0}
    shorts = {k for k, v in t.items() if v < 0}
    assert longs == {f"T{i}" for i in range(20, 30)}, longs
    assert shorts == {f"T{i}" for i in range(0, 10)}, shorts
    assert abs(sum(abs(v) for v in t.values()) - 1.0) < 1e-9
    assert abs(sum(t.values())) < 1e-9, "must be dollar-neutral"
    assert all(abs(v) == 0.05 for v in t.values())

    # Thin cross-section -> flat.
    assert tercile_long_short_targets({"A": 1.0, "B": 2.0}) == {}

    # Sides never overlap on a tiny-but-allowed universe.
    six = {f"S{i}": float(i) for i in range(6)}
    t6 = tercile_long_short_targets(six, frac=0.5)
    assert len(t6) == 6 and sum(1 for v in t6.values() if v > 0) == 3

    print("cross_sectional_rank.py: all checks passed")
