---
path: "tests/hygiene/test_gitignore.py"
hub: "Tests"
lines: 50
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_gitignore.py"
---
# test_gitignore.py

`tests/hygiene/test_gitignore.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_gitignore.py)

## Purpose

Verify .gitignore excludes the sensitive paths the workspace promises to keep private.

## Dependencies


**Imports (external):** [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#pytest|pytest]], [[Indexes/External packages#subprocess|subprocess]]

## Constants

| Name | Value | Line |
|---|---|---|
| `MUST_BE_IGNORED` | `[('.env', 'environment files contain credentials'), ('lean.json', 'contains QuantConnect API token'), ('MyProjects/data/', 'local market data should never be...` | [9](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_gitignore.py#L9) |

## Functions

### `_check_ignore()`

```python
def _check_ignore(repo_root: Path, rel_path: str) -> bool
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_gitignore.py#L19)

Return True if `git check-ignore` says the path is ignored.

### `test_path_is_gitignored()`

```python
def test_path_is_gitignored(repo_root: Path, rel_path: str, reason: str)
```
[line 32](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_gitignore.py#L32)

### `test_template_is_tracked()`

```python
def test_template_is_tracked(repo_root: Path)
```
[line 38](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_gitignore.py#L38)

The template is an explicit exception to MyProjects/* being ignored.

## Source

> [!example]- tests/hygiene/test_gitignore.py (50 lines)
> ```python
> """Verify .gitignore excludes the sensitive paths the workspace promises to keep private."""
>
> from pathlib import Path
>
> import pytest
>
>
> # Each tuple: (path relative to repo root, why it must be ignored)
> MUST_BE_IGNORED = [
>     (".env", "environment files contain credentials"),
>     ("lean.json", "contains QuantConnect API token"),
>     ("MyProjects/data/", "local market data should never be committed"),
>     ("MyProjects/storage/", "ObjectStore outputs may contain proprietary results"),
>     ("MyProjects/SomeProject/config.json", "per-project config holds cloud IDs"),
>     ("Lean/some-file.cs", "Lean/ engine repo is reference only"),
> ]
>
>
> def _check_ignore(repo_root: Path, rel_path: str) -> bool:
>     """Return True if `git check-ignore` says the path is ignored."""
>     import subprocess
>
>     result = subprocess.run(
>         ["git", "check-ignore", "-q", rel_path],
>         cwd=repo_root,
>     )
>     # exit 0 = ignored, exit 1 = not ignored, exit 128 = other error
>     return result.returncode == 0
>
>
> @pytest.mark.parametrize("rel_path,reason", MUST_BE_IGNORED, ids=[p for p, _ in MUST_BE_IGNORED])
> def test_path_is_gitignored(repo_root: Path, rel_path: str, reason: str):
>     assert _check_ignore(repo_root, rel_path), (
>         f".gitignore must exclude {rel_path!r} — {reason}"
>     )
>
>
> def test_template_is_tracked(repo_root: Path):
>     """The template is an explicit exception to MyProjects/* being ignored."""
>     template_main = "MyProjects/_template/main.py"
>     import subprocess
>
>     result = subprocess.run(
>         ["git", "check-ignore", "-q", template_main],
>         cwd=repo_root,
>     )
>     assert result.returncode == 1, (
>         "MyProjects/_template/ must remain tracked despite the MyProjects/*/ exclusion."
>     )
> ```
