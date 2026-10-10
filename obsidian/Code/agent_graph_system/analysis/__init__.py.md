---
path: "agent_graph_system/analysis/__init__.py"
hub: "Agent Graph System"
lines: 9
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/analysis/__init__.py"
---
# __init__.py

`agent_graph_system/analysis/__init__.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/analysis/__init__.py)

## Purpose

Statistical validation of strategy performance.

Pure-Python analysis primitives with no graph or agent dependencies, so they
can be unit-tested in isolation and called from any layer:

- :mod:`walkforward` — rolling out-of-sample train/test evaluation.
- :mod:`bootstrap` — permutation significance testing of a Sharpe ratio.

## Source

> [!example]- agent_graph_system/analysis/__init__.py (9 lines)
> ```python
> """Statistical validation of strategy performance.
>
> Pure-Python analysis primitives with no graph or agent dependencies, so they
> can be unit-tested in isolation and called from any layer:
>
> - :mod:`walkforward` — rolling out-of-sample train/test evaluation.
> - :mod:`bootstrap` — permutation significance testing of a Sharpe ratio.
> """
> ```
