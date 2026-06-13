"""Statistical validation of strategy performance.

Pure-Python analysis primitives with no graph or agent dependencies, so they
can be unit-tested in isolation and called from any layer:

- :mod:`walkforward` — rolling out-of-sample train/test evaluation.
- :mod:`bootstrap` — permutation significance testing of a Sharpe ratio.
"""
