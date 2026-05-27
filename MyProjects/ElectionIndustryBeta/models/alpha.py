# region imports
from AlgorithmImports import *
import pandas as pd

from domain.config import LOOKBACK
from domain.signals.election_beta import rolling_beta
# endregion


class ElectionBetaAlpha:
    """
    Alpha organism for ElectionIndustryBeta.

    Computes each ETF's rolling-window beta to ΔP(Trump).
    Delegates the math to the pure shared signal at
    `domain/signals/election_beta.py` (symlink to MyProjects/shared/signals/).

    Layer: ORGANISM (orchestrates signal generation).
    """

    def __init__(self, lookback: int = LOOKBACK):
        self.name = "ElectionBetaAlpha"
        self.lookback = lookback

    def compute_signals(
        self,
        returns: pd.DataFrame,
        trump_prob: pd.Series,
    ) -> pd.Series:
        """Latest rolling-beta per ticker against ΔP(Trump).

        Args:
            returns:    DataFrame indexed by date, one column per ticker
                        (daily simple returns in percent — matches the notebook).
            trump_prob: Series indexed by date, daily Polymarket Trump win
                        probability (level, not change — we diff here).

        Returns:
            Series of latest betas, indexed by ticker.
        """
        delta_prob = trump_prob.sort_index().diff().dropna()
        return rolling_beta(returns, delta_prob, self.lookback)
