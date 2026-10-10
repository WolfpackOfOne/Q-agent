---
path: "tests/conftest.py"
hub: "Tests"
lines: 24
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/conftest.py"
---
# conftest.py

`tests/conftest.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/conftest.py)

## Purpose

Shared fixtures for the Q-agent workspace test suite.

## Dependencies


**Imports (external):** [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#pytest|pytest]]

## Constants

| Name | Value | Line |
|---|---|---|
| `REPO_ROOT` | `Path(__file__).resolve().parent.parent` | [8](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/conftest.py#L8) |

## Functions

### `repo_root()`

```python
def repo_root() -> Path
```
[line 12](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/conftest.py#L12)

### `template_dir()`

```python
def template_dir(repo_root: Path) -> Path
```
[line 17](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/conftest.py#L17)

### `pipelines_dir()`

```python
def pipelines_dir(repo_root: Path) -> Path
```
[line 22](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/conftest.py#L22)

## Source

> [!example]- tests/conftest.py (24 lines)
> ```python
> """Shared fixtures for the Q-agent workspace test suite."""
>
> from pathlib import Path
>
> import pytest
>
>
> REPO_ROOT = Path(__file__).resolve().parent.parent
>
>
> @pytest.fixture(scope="session")
> def repo_root() -> Path:
>     return REPO_ROOT
>
>
> @pytest.fixture(scope="session")
> def template_dir(repo_root: Path) -> Path:
>     return repo_root / "MyProjects" / "_template"
>
>
> @pytest.fixture(scope="session")
> def pipelines_dir(repo_root: Path) -> Path:
>     return repo_root / "infrastructure" / "pipelines"
> ```
