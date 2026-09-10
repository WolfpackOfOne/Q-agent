# region imports
from AlgorithmImports import *

from domain.config import MIN_NAMES, SELECT_FRAC, N_FLOOR
from domain.signals.news_tone import rank_magnitude_weighted_targets
# endregion


class NewsToneLongShortPortfolio:
    """
    Portfolio construction organism for NewsSentimentAlpha.

    Converts raw tone-z scores into long/short targets: a selective
    top/bottom slice of whichever tickers have a signal today (at least
    `n_floor` names per side, to avoid a concentrated single-stock bet),
    weighted by signal magnitude within each side. Delegates the ranking
    math to the pure shared signal at `domain/signals/news_tone.py`
    (symlink to MyProjects/shared/signals/).

    Layer: ORGANISM (orchestrates portfolio construction).
    """

    def __init__(
        self,
        min_names: int = MIN_NAMES,
        frac: float = SELECT_FRAC,
        n_floor: int = N_FLOOR,
    ):
        self.min_names = min_names
        self.frac = frac
        self.n_floor = n_floor

    def to_targets(self, signals: dict[str, float]) -> dict[str, float]:
        """Ranked, magnitude-weighted long/short targets from raw tone-z scores.

        Args:
            signals: dict[ticker, tone_z] from NewsToneAlpha.

        Returns:
            dict[ticker, weight]: see rank_magnitude_weighted_targets.
            Empty dict (flat) if fewer than `min_names` tickers have a
            signal, or if the cross-section is too narrow to support
            `n_floor` names on both sides.
        """
        return rank_magnitude_weighted_targets(
            signals, frac=self.frac, min_names=self.min_names, n_floor=self.n_floor
        )
