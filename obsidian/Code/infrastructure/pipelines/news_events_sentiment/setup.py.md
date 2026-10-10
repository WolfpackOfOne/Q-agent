---
path: "infrastructure/pipelines/news_events_sentiment/setup.py"
hub: "news_events_sentiment"
lines: 12
tags:
  - "code/python"
  - "pipelines/news_events_sentiment"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/setup.py"
---
# setup.py

`infrastructure/pipelines/news_events_sentiment/setup.py` · hub [[Hubs/Pipelines/news_events_sentiment|news_events_sentiment]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/setup.py)

## Dependencies


**Imports (external):** [[Indexes/External packages#setuptools|setuptools]]

## Source

> [!example]- infrastructure/pipelines/news_events_sentiment/setup.py (12 lines)
> ```python
> from setuptools import setup, find_packages
>
> setup(
>     name='news_events_sentiment_lean',
>     packages=find_packages('src'),
>     package_dir={'': 'src'},
>     install_requires=[
>         'requests>=2.34.2',
>         'pandas>=2.2.0',
>     ],
> )
> ```
