# region imports
from AlgorithmImports import *

from domain.config import GROSS_EXPOSURE, LONG_SHORT_FRACTION, MIN_SCORED_NAMES
from domain.signals.cross_sectional_rank import tercile_long_short_targets
# endregion


class FundamentalRankPortfolio:
    """
    Portfolio construction organism for FundamentalRankLS.

    Turns a cross-section of model scores into a dollar-neutral book: long
    the top LONG_SHORT_FRACTION of names by score, short the bottom
    LONG_SHORT_FRACTION, equal-weighted within each side, GROSS_EXPOSURE
    total (half long, half short). Delegates the ranking math to the pure
    shared signal `domain/signals/cross_sectional_rank.py` (symlink to
    MyProjects/shared/signals/) — the same rule the research notebook
    backtested, so the LEAN book matches the notebook's construction exactly.

    Layer: ORGANISM (orchestrates portfolio construction).
    """

    def __init__(
        self,
        frac: float = LONG_SHORT_FRACTION,
        gross: float = GROSS_EXPOSURE,
        min_names: int = MIN_SCORED_NAMES,
    ):
        self.frac = frac
        self.gross = gross
        self.min_names = min_names

    def to_targets(self, scores: dict[str, float]) -> dict[str, float]:
        """Return {ticker: target_weight}; {} (flat) if the cross-section is too thin."""
        return tercile_long_short_targets(scores, frac=self.frac, gross=self.gross, min_names=self.min_names)
