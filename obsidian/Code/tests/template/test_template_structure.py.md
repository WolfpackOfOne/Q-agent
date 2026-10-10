---
path: "tests/template/test_template_structure.py"
hub: "Tests"
lines: 40
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/template/test_template_structure.py"
---
# test_template_structure.py

`tests/template/test_template_structure.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/template/test_template_structure.py)

## Purpose

Guard MyProjects/_template/ as a valid starting point for new projects.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#py_compile|py_compile]], [[Indexes/External packages#pytest|pytest]]

## Constants

| Name | Value | Line |
|---|---|---|
| `REQUIRED_PATHS` | `['main.py', 'models', 'models/__init__.py', 'domain', 'domain/__init__.py', 'claude.md', 'README.md']` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/template/test_template_structure.py#L11) |

## Functions

### `test_template_has_required_path()`

```python
def test_template_has_required_path(template_dir: Path, rel: str)
```
[line 23](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/template/test_template_structure.py#L23)

### `test_every_python_file_compiles()`

```python
def test_every_python_file_compiles(template_dir: Path)
```
[line 27](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/template/test_template_structure.py#L27)

## Source

> [!example]- tests/template/test_template_structure.py (40 lines)
> ```python
> """Guard MyProjects/_template/ as a valid starting point for new projects."""
>
> from __future__ import annotations
>
> import py_compile
> from pathlib import Path
>
> import pytest
>
>
> REQUIRED_PATHS = [
>     "main.py",
>     "models",
>     "models/__init__.py",
>     "domain",
>     "domain/__init__.py",
>     "claude.md",
>     "README.md",
> ]
>
>
> @pytest.mark.parametrize("rel", REQUIRED_PATHS)
> def test_template_has_required_path(template_dir: Path, rel: str):
>     assert (template_dir / rel).exists(), f"Template missing required path: {rel}"
>
>
> def test_every_python_file_compiles(template_dir: Path):
>     failures: list[str] = []
>     for py in template_dir.rglob("*.py"):
>         # Skip files containing Jinja-style {{PLACEHOLDER}} tokens — they're
>         # scaffolding processed by new-strategy-coder, not standalone Python.
>         text = py.read_text(encoding="utf-8")
>         if "{{" in text and "}}" in text:
>             continue
>         try:
>             py_compile.compile(str(py), doraise=True)
>         except py_compile.PyCompileError as exc:
>             failures.append(f"{py.relative_to(template_dir)}: {exc.msg}")
>     assert not failures, "Template files failed to compile:\n  " + "\n  ".join(failures)
> ```
