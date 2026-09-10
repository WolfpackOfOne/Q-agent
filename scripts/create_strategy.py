#!/usr/bin/env python3
"""Render a runnable strategy scaffold from MyProjects/_template."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "MyProjects" / "_template"
TOKEN = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
TEXT_SUFFIXES = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".toml"}


def _project_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
        raise argparse.ArgumentTypeError(
            "project name must be a Python identifier such as MyFirstStrategy"
        )
    return value


def _render(text: str, project: str, description: str) -> str:
    namespace = re.sub(r"(?<!^)(?=[A-Z])", "_", project).lower()
    values = {
        "PROJECT_NAME": project,
        "STRATEGY_NAME": project,
        "STRATEGY_CLASS": project,
        "STRATEGY_DESCRIPTION": description,
        "BRIEF_DESCRIPTION": description,
        "objectstore_namespace": namespace,
        "GITHUB_URL": "Add the strategy repository URL after creating it",
    }

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return values.get(key, f"TODO: {key.replace('_', ' ').lower()}")

    return TOKEN.sub(replace, text)


def create_strategy(project: str, destination: Path, description: str) -> Path:
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    shutil.copytree(TEMPLATE_ROOT, destination, symlinks=True)
    for path in destination.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            rendered = _render(path.read_text(encoding="utf-8"), project, description)
            path.write_text(rendered, encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=_project_identifier)
    parser.add_argument(
        "--description",
        default="A QuantConnect strategy scaffold ready for implementation.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        help="destination directory (default: MyProjects/<project>)",
    )
    args = parser.parse_args()

    destination = args.destination or REPO_ROOT / "MyProjects" / args.project
    destination = destination.expanduser().resolve()
    create_strategy(args.project, destination, args.description)
    print(f"Created {destination}")
    print("Next: create a separate Git repository there, implement the TODOs, and run a cloud backtest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
