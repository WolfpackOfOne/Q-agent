---
path: "tests/hygiene/test_repository_policy.py"
hub: "Tests"
lines: 74
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_repository_policy.py"
---
# test_repository_policy.py

`tests/hygiene/test_repository_policy.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_repository_policy.py)

## Purpose

Tests for student-facing repository and scaffold controls.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#ast|ast]], [[Indexes/External packages#hashlib|hashlib]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#subprocess|subprocess]], [[Indexes/External packages#sys|sys]]

## Functions

### `test_current_tree_passes_repository_policy()`

```python
def test_current_tree_passes_repository_policy(repo_root: Path)
```
[line 12](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_repository_policy.py#L12)

### `test_grandfathered_policy_files_are_unchanged()`

```python
def test_grandfathered_policy_files_are_unchanged(repo_root: Path)
```
[line 22](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_repository_policy.py#L22)

### `test_scaffold_renders_valid_python()`

```python
def test_scaffold_renders_valid_python(repo_root: Path, tmp_path: Path)
```
[line 33](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_repository_policy.py#L33)

### `test_scaffold_refuses_to_overwrite()`

```python
def test_scaffold_refuses_to_overwrite(repo_root: Path, tmp_path: Path)
```
[line 58](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_repository_policy.py#L58)

## Source

> [!example]- tests/hygiene/test_repository_policy.py (74 lines)
> ```python
> """Tests for student-facing repository and scaffold controls."""
>
> from __future__ import annotations
>
> import ast
> import hashlib
> import subprocess
> import sys
> from pathlib import Path
>
>
> def test_current_tree_passes_repository_policy(repo_root: Path):
>     result = subprocess.run(
>         [sys.executable, "scripts/check_repository_policy.py", "--all"],
>         cwd=repo_root,
>         capture_output=True,
>         text=True,
>     )
>     assert result.returncode == 0, result.stderr
>
>
> def test_grandfathered_policy_files_are_unchanged(repo_root: Path):
>     policy_file = repo_root / ".github" / "repository-policy-grandfathered.txt"
>     for raw_line in policy_file.read_text(encoding="utf-8").splitlines():
>         line = raw_line.strip()
>         if not line or line.startswith("#"):
>             continue
>         expected, relative = line.split(maxsplit=1)
>         digest = hashlib.sha256((repo_root / relative).read_bytes()).hexdigest()
>         assert digest == expected, f"Grandfathered file changed: {relative}"
>
>
> def test_scaffold_renders_valid_python(repo_root: Path, tmp_path: Path):
>     destination = tmp_path / "StudentStrategy"
>     result = subprocess.run(
>         [
>             sys.executable,
>             "scripts/create_strategy.py",
>             "StudentStrategy",
>             "--destination",
>             str(destination),
>         ],
>         cwd=repo_root,
>         capture_output=True,
>         text=True,
>     )
>     assert result.returncode == 0, result.stderr
>
>     for path in destination.rglob("*"):
>         if not path.is_file():
>             continue
>         if path.suffix in {".py", ".md"}:
>             assert "{{" not in path.read_text(encoding="utf-8")
>         if path.suffix == ".py":
>             ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
>
>
> def test_scaffold_refuses_to_overwrite(repo_root: Path, tmp_path: Path):
>     destination = tmp_path / "ExistingStrategy"
>     destination.mkdir()
>     result = subprocess.run(
>         [
>             sys.executable,
>             "scripts/create_strategy.py",
>             "ExistingStrategy",
>             "--destination",
>             str(destination),
>         ],
>         cwd=repo_root,
>         capture_output=True,
>         text=True,
>     )
>     assert result.returncode != 0
> ```
