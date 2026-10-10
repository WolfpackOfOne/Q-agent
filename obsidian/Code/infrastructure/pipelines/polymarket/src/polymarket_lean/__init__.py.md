---
path: "infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py"
hub: "polymarket"
lines: 12
tags:
  - "code/python"
  - "pipelines/polymarket"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py"
---
# __init__.py

`infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py` · hub [[Hubs/Pipelines/polymarket|polymarket]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py)

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py|clob.py]], [[Code/infrastructure/pipelines/polymarket/src/polymarket_lean/gamma.py|gamma.py]], [[Code/infrastructure/pipelines/polymarket/src/polymarket_lean/writer.py|writer.py]]

**Imported by:** [[Code/infrastructure/pipelines/polymarket/scripts/run_markets_pipeline.py|run_markets_pipeline.py]], [[Code/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py|run_prices_pipeline.py]]

## Source

> [!example]- infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py (12 lines)
> ```python
> from .gamma import GammaClient, DEFAULT_TAG_FILTER
> from .clob import ClobClient
> from .writer import write_markets_csv, write_market_prices_csv
>
> __all__ = [
>     "GammaClient",
>     "ClobClient",
>     "DEFAULT_TAG_FILTER",
>     "write_markets_csv",
>     "write_market_prices_csv",
> ]
> ```
