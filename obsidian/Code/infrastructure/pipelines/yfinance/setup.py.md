---
path: "infrastructure/pipelines/yfinance/setup.py"
hub: "yfinance"
lines: 12
tags:
  - "code/python"
  - "pipelines/yfinance"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/yfinance/setup.py"
---
# setup.py

`infrastructure/pipelines/yfinance/setup.py` · hub [[Hubs/Pipelines/yfinance|yfinance]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/yfinance/setup.py)

## Dependencies


**Imports (external):** [[Indexes/External packages#setuptools|setuptools]]

## Source

> [!example]- infrastructure/pipelines/yfinance/setup.py (12 lines)
> ```python
> from setuptools import setup, find_packages
>
> setup(
>     name='yfinance_lean',
>     packages=find_packages('src'),
>     package_dir={'': 'src'},
>     install_requires=[
>         'yfinance>=0.2.0',
>         'pandas>=2.2.0',
>     ],
> )
> ```
