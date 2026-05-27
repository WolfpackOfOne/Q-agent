# region imports
from AlgorithmImports import *
import pandas as pd

from domain.config import K
from domain.signals.election_beta import top_bottom_k_betaweighted
# endregion


class ElectionBetaPortfolio:
    """
    Portfolio construction organism for ElectionIndustryBeta.

    Converts a Series of per-ticker betas into a target-weight dict.
    Long top-K (largest beta), short bottom-K (smallest beta), weights
    proportional to beta, normalised to gross exposure 100%.

    Layer: ORGANISM (orchestrates portfolio construction).
    """

    def __init__(self, k: int = K):
        self.k = k

    def to_targets(self, betas: pd.Series) -> dict[str, float]:
        """Build target-weight dict for the full universe."""
        return top_bottom_k_betaweighted(betas, self.k)
