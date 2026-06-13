"""Bootstrap significance testing of a Sharpe ratio.

A Sharpe of 0.8 over ~500 daily observations has a standard error of roughly
``1/sqrt(500) ≈ 0.045`` on the estimator itself, but the deeper question is
whether the *mean* return is distinguishable from zero at all. A true zero-alpha
strategy can produce a respectable Sharpe by chance, especially with fat tails.

This module answers that with a one-sided permutation/bootstrap test of
H0: ``E[r] = 0``. We impose the null by de-meaning the observed returns, draw
many resampled null series, compute each one's Sharpe, and report the fraction
whose Sharpe meets or exceeds the observed value. That fraction is the p-value:
if it exceeds, say, 0.10, the strategy cannot be told apart from noise.

Two resampling modes:

- **iid** (default, ``block_size=None``): resample de-meaned returns with
  replacement. Appropriate when daily returns are roughly independent.
- **block** (``block_size > 1``): stationary-style block bootstrap that draws
  contiguous circular blocks, preserving short-horizon autocorrelation. Use for
  strategies with serial correlation (momentum lookbacks, mean-reversion bands).

Everything is NumPy-vectorized — no pandas in the hot loop — so 10k permutations
stay fast.

References: Bailey & López de Prado, "The Deflated Sharpe Ratio" (2014);
Politis & Romano, stationary block bootstrap (1994).
"""

from __future__ import annotations

import numpy as np

from agent_graph_system.analysis.walkforward import TRADING_DAYS

try:  # optional analytical sanity check; never required for the p-value
    from scipy.stats import norm as _norm  # type: ignore
    _HAS_SCIPY = True
except Exception:  # pragma: no cover - scipy is an optional dependency
    _norm = None
    _HAS_SCIPY = False


def _row_sharpe(matrix: np.ndarray, periods: int = TRADING_DAYS) -> np.ndarray:
    """Annualized Sharpe for each row of a ``(n_perm, n)`` matrix."""
    mean = matrix.mean(axis=1)
    sd = matrix.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = np.where(sd > 0, mean / sd * np.sqrt(periods), 0.0)
    return sharpe


def bootstrap_sharpe_pvalue(
    oos_returns: np.ndarray,
    observed_sharpe: float,
    n_permutations: int = 10_000,
    *,
    seed: int | None = 42,
    block_size: int | None = None,
    periods: int = TRADING_DAYS,
) -> float:
    """One-sided bootstrap p-value for ``observed_sharpe`` under H0: E[r]=0.

    Returns the fraction of resampled null Sharpe ratios ``>= observed_sharpe``.
    ``block_size`` of ``None`` or ``1`` runs the iid bootstrap; an integer ``>1``
    runs the circular block bootstrap.
    """
    r = np.asarray(oos_returns, dtype=float)
    n = r.size
    if n < 2:
        # Cannot estimate variance — refuse to claim significance.
        return 1.0

    rng = np.random.default_rng(seed)
    centered = r - r.mean()  # impose H0: zero mean

    if block_size is None or block_size <= 1:
        idx = rng.integers(0, n, size=(n_permutations, n))
        samples = centered[idx]
    else:
        bs = min(block_size, n)
        n_blocks = int(np.ceil(n / bs))
        starts = rng.integers(0, n, size=(n_permutations, n_blocks))
        offsets = np.arange(bs)
        # (n_perm, n_blocks, bs) circular indices, flattened and trimmed to n.
        block_idx = (starts[:, :, None] + offsets[None, None, :]) % n
        flat = block_idx.reshape(n_permutations, n_blocks * bs)[:, :n]
        samples = centered[flat]

    null_sharpe = _row_sharpe(samples, periods=periods)
    return float(np.mean(null_sharpe >= observed_sharpe))


def analytic_sharpe_pvalue(observed_sharpe: float, n_obs: int) -> float | None:
    """Normal-approximation one-sided p-value, as a cheap sanity check.

    Returns ``None`` when SciPy is unavailable so callers can fall back to the
    bootstrap result. Uses SE(SR) ≈ ``1/sqrt(n)`` on the annualized Sharpe's
    per-period equivalent — a rough cross-check, not a replacement for the
    bootstrap, which makes no normality assumption.
    """
    if not _HAS_SCIPY or n_obs < 2:
        return None
    per_period = observed_sharpe / np.sqrt(TRADING_DAYS)
    z = per_period * np.sqrt(n_obs)
    return float(1.0 - _norm.cdf(z))
