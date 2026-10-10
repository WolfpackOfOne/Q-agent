---
path: "tests/qc_integration/test_lean_cli_smoke.py"
hub: "Tests"
lines: 32
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/qc_integration/test_lean_cli_smoke.py"
---
# test_lean_cli_smoke.py

`tests/qc_integration/test_lean_cli_smoke.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/qc_integration/test_lean_cli_smoke.py)

## Purpose

Smoke tests for the LEAN CLI environment.

Marked `integration` because they require `lean` to be installed and a
working Docker/Python environment. CI skips these by default; run locally
with `pytest -m integration` to exercise them.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#pytest|pytest]], [[Indexes/External packages#shutil|shutil]], [[Indexes/External packages#subprocess|subprocess]]

## Functions

### `test_lean_cli_is_installed()`

```python
def test_lean_cli_is_installed()
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/qc_integration/test_lean_cli_smoke.py#L19)

### `test_lean_version_runs()`

```python
def test_lean_version_runs()
```
[line 23](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/qc_integration/test_lean_cli_smoke.py#L23)

## Source

> [!example]- tests/qc_integration/test_lean_cli_smoke.py (32 lines)
> ```python
> """Smoke tests for the LEAN CLI environment.
>
> Marked `integration` because they require `lean` to be installed and a
> working Docker/Python environment. CI skips these by default; run locally
> with `pytest -m integration` to exercise them.
> """
>
> from __future__ import annotations
>
> import shutil
> import subprocess
>
> import pytest
>
>
> pytestmark = pytest.mark.integration
>
>
> def test_lean_cli_is_installed():
>     assert shutil.which("lean"), "lean CLI is not on PATH — activate the venv first"
>
>
> def test_lean_version_runs():
>     result = subprocess.run(
>         ["lean", "--version"],
>         capture_output=True,
>         text=True,
>         timeout=30,
>     )
>     assert result.returncode == 0, f"`lean --version` failed: {result.stderr}"
>     assert result.stdout.strip(), "`lean --version` produced no output"
> ```
