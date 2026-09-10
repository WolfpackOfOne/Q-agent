"""
Financial-media news-tone long/short ranking signal.

Pure Python. No LEAN imports — must remain importable from a plain
Python environment so it can be symlinked into any QuantConnect project
and unit-tested locally.

Functions:
    rank_magnitude_weighted_targets(scores, frac, min_names, n_floor)
        Build a long/short weight dict from a ticker -> score mapping:
        a selective top/bottom slice of the scored universe, weighted by
        signal magnitude, with a minimum-names-per-side floor.
"""

from __future__ import annotations


def rank_magnitude_weighted_targets(
    scores: dict[str, float],
    frac: float = 0.5,
    min_names: int = 5,
    n_floor: int = 2,
) -> dict[str, float]:
    """Rank tickers by score; trade a selective slice, weighted by |score|.

    Args:
        scores: ticker -> signal value (higher = more bullish), already
            filtered to tickers with a valid signal for this rebalance.
        frac: fraction of the *scored* universe to trade in total (half
            long, half short), before `n_floor` is applied. E.g. frac=0.5
            with 10 scored tickers longs/shorts round(10*0.5/2)=2-3 per
            side, capped at half the scored set so long/short never
            overlap.
        min_names: minimum number of scored tickers required to trade —
            a breadth filter, not just an emptiness check. Thin
            cross-sections (few tickers with news that day) produce a
            much noisier signal than high-breadth days.
        n_floor: minimum names per side whenever the cross-section is
            wide enough to support it (`n_floor <= len(scores) // 2`).
            Guards against an all-in single-stock bet, which is far
            noisier — and far more exposed to real-world execution
            slippage on a single name — than a diversified position.

    Returns:
        dict[ticker, weight]: signed weight proportional to |score|
        within the selected slice, normalised so gross exposure (sum of
        |weight|) is 1.0. Empty dict if fewer than `min_names` tickers
        have a score, or if the scored cross-section is too narrow to
        support `n_floor` names on both sides.
    """
    if len(scores) < min_names:
        return {}

    ranked = sorted(scores, key=scores.get)
    half = len(ranked) // 2
    if half < n_floor:
        return {}
    n = max(n_floor, min(round(len(ranked) * frac / 2), half))
    shorts, longs = ranked[:n], ranked[-n:]

    selected = {ticker: scores[ticker] for ticker in shorts + longs}
    gross = sum(abs(v) for v in selected.values())
    if gross == 0:
        return {}
    return {ticker: value / gross for ticker, value in selected.items()}


if __name__ == "__main__":
    # Synthetic-data sanity check — run with a plain venv:
    #   python shared/signals/news_tone.py
    scores10 = {
        "A": -2.5, "B": -1.8, "C": -0.5, "D": -0.2, "E": 0.1,
        "F": 0.3, "G": 0.6, "H": 1.2, "I": 1.9, "J": 2.8,
    }
    mag = rank_magnitude_weighted_targets(scores10, frac=0.3, min_names=5, n_floor=2)
    # frac=0.3 -> round(10*0.3/2) = round(1.5) = 2 per side; n_floor=2 agrees.
    assert set(mag) == {"A", "B", "I", "J"}, mag
    assert mag["A"] < 0 and mag["B"] < 0 and mag["I"] > 0 and mag["J"] > 0
    assert mag["J"] > mag["I"] > 0, "larger |score| must get larger weight"
    assert abs(sum(abs(w) for w in mag.values()) - 1.0) < 1e-9

    assert rank_magnitude_weighted_targets(scores10, frac=0.3, min_names=11) == {}
    assert rank_magnitude_weighted_targets({"A": 1.0, "B": -1.0}, frac=0.3, min_names=2, n_floor=1) != {}

    # n_floor too wide for the cross-section (half=2 < n_floor=3) -> flat,
    # even though min_names is satisfied — this is what stops the strategy
    # from taking a concentrated 1- or 2-name bet it can't diversify.
    assert rank_magnitude_weighted_targets(scores10, frac=0.3, min_names=5, n_floor=6) == {}

    print("news_tone.py: all checks passed")
