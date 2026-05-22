"""Guard MyProjects/_template/ as a valid starting point for new projects."""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest


REQUIRED_PATHS = [
    "main.py",
    "models",
    "models/__init__.py",
    "domain",
    "domain/__init__.py",
    "claude.md",
    "README.md",
]


@pytest.mark.parametrize("rel", REQUIRED_PATHS)
def test_template_has_required_path(template_dir: Path, rel: str):
    assert (template_dir / rel).exists(), f"Template missing required path: {rel}"


def test_every_python_file_compiles(template_dir: Path):
    failures: list[str] = []
    for py in template_dir.rglob("*.py"):
        # Skip files containing Jinja-style {{PLACEHOLDER}} tokens — they're
        # scaffolding processed by new-strategy-coder, not standalone Python.
        text = py.read_text(encoding="utf-8")
        if "{{" in text and "}}" in text:
            continue
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{py.relative_to(template_dir)}: {exc.msg}")
    assert not failures, "Template files failed to compile:\n  " + "\n  ".join(failures)
