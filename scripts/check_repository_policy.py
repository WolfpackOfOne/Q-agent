#!/usr/bin/env python3
"""Enforce reviewable, credential-safe repository contributions."""

from __future__ import annotations

import argparse
import ast
import hashlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 6 * 1024 * 1024
MAX_TABLE_ROWS = 50_000
GRANDFATHERED_FILE = REPO_ROOT / ".github" / "repository-policy-grandfathered.txt"
REQUIRED_PROJECT_PATHS = (
    "main.py",
    "README.md",
    "AGENTS.md",
    "domain",
    "models",
)


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT)


def _tracked_files() -> list[str]:
    output = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return [item.decode() for item in output.split(b"\0") if item]


def _changed_files(base: str) -> list[str]:
    output = _git("diff", "--name-only", "--diff-filter=ACMR", "-z", f"{base}...HEAD")
    return [item.decode() for item in output.split(b"\0") if item]


def _forbidden_reason(relative: str) -> str | None:
    path = Path(relative)
    name = path.name.lower()
    parts = path.parts
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return "environment files may contain credentials"
    if name in {"lean.json", "credentials.json"}:
        return "credential-bearing configuration must remain local"
    if name == "config.json" and parts and parts[0] == "MyProjects":
        return "QuantConnect project config must remain local"
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return "private key material is prohibited"
    if "backtests" in parts and name != ".gitkeep":
        return "generated backtest artifacts are prohibited"
    return None


def _table_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grandfathered_files() -> dict[str, str]:
    """Return immutable, previously merged exceptions as path -> SHA-256."""
    if not GRANDFATHERED_FILE.exists():
        return {}

    exceptions: dict[str, str] = {}
    for number, raw_line in enumerate(
        GRANDFATHERED_FILE.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(
                f"{GRANDFATHERED_FILE.relative_to(REPO_ROOT)}:{number}: "
                "expected '<sha256>  <repository-relative path>'"
            )
        digest, relative = parts
        exceptions[relative.strip()] = digest.lower()
    return exceptions


def _new_projects(files: list[str], base: str | None) -> set[str]:
    projects: set[str] = set()
    for relative in files:
        parts = Path(relative).parts
        if len(parts) < 3 or parts[0] != "MyProjects":
            continue
        project = parts[1]
        if project in {"_template", "shared", ".claude"}:
            continue
        root = REPO_ROOT / "MyProjects" / project
        if not (root / "main.py").exists():
            continue
        if base is None:
            projects.add(project)
            continue
        existed = subprocess.run(
            ["git", "cat-file", "-e", f"{base}:MyProjects/{project}"],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if not existed:
            projects.add(project)
    return projects


def check(files: list[str], base: str | None) -> list[str]:
    errors: list[str] = []
    grandfathered = _grandfathered_files()
    for relative in files:
        path = REPO_ROOT / relative
        if not path.exists() or path.is_dir():
            continue

        reason = _forbidden_reason(relative)
        if reason:
            errors.append(f"{relative}: {reason}")

        size = path.stat().st_size
        expected_digest = grandfathered.get(relative)
        unchanged_exception = expected_digest is not None and _sha256(path) == expected_digest
        if size > MAX_FILE_BYTES and not unchanged_exception:
            errors.append(
                f"{relative}: {size:,} bytes exceeds the {MAX_FILE_BYTES:,}-byte review limit"
            )

        if path.suffix.lower() in {".csv", ".tsv"}:
            rows = _table_rows(path)
            if rows > MAX_TABLE_ROWS and not unchanged_exception:
                errors.append(
                    f"{relative}: {rows:,} rows exceeds the {MAX_TABLE_ROWS:,}-row review limit; "
                    "commit a small fixture and provide a reproducible refresh script instead"
                )

        if path.suffix == ".py" and "MyProjects/_template/" not in relative:
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=relative)
            except (SyntaxError, UnicodeDecodeError) as exc:
                errors.append(f"{relative}: Python syntax check failed: {exc}")

    for project in sorted(_new_projects(files, base)):
        root = REPO_ROOT / "MyProjects" / project
        for required in REQUIRED_PROJECT_PATHS:
            if not (root / required).exists():
                errors.append(f"MyProjects/{project}: missing required path {required}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--base", help="check files changed since this base commit")
    group.add_argument("--all", action="store_true", help="check all tracked files")
    args = parser.parse_args()

    files = _tracked_files() if args.all else _changed_files(args.base)
    try:
        errors = check(files, args.base)
    except ValueError as exc:
        print(f"Repository policy configuration error: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("Repository policy violations:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Repository policy passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
