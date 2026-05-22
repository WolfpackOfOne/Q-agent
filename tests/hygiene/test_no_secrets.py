"""Scan tracked files for committed secrets.

This is a coarse last-line-of-defense check. The authoritative scanner runs in
.github/workflows/secret-scan.yml; this test catches obvious leaks during
local development before they reach CI.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


# Patterns that should never appear in tracked files. Each is paired with a
# short label used in failure messages.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    # Negative lookahead excludes shell/env-var refs ($VAR, ${VAR:-default}) and
    # Jinja-style placeholders ({{NAME}}) — those aren't hardcoded secrets.
    ("Generic API key assignment", re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*=\s*['\"](?![\${])[^'\"\s]{12,}['\"]")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("Slack bot token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("GitHub personal token", re.compile(r"ghp_[A-Za-z0-9]{36}")),
]

# File extensions worth scanning. Binary and lock files excluded.
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml",
    ".cfg", ".ini", ".sh", ".env", ".example",
}

# Paths exempt from scanning: documentation files that legitimately discuss
# secret formats (e.g., CREDENTIALS.md) or example placeholders.
EXEMPT_PATHS = {
    ".env.example",
    "CREDENTIALS.md",
    "SECURITY.md",
    "tests/hygiene/test_no_secrets.py",  # this file contains the patterns
}


def _tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [repo_root / line for line in result.stdout.splitlines() if line]


def test_no_secret_patterns_in_tracked_files(repo_root: Path):
    leaks: list[str] = []
    for path in _tracked_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        if rel in EXEMPT_PATHS:
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                leaks.append(f"{rel}: matched {label!r} → {match.group(0)[:40]}…")

    assert not leaks, "Secret-pattern matches in tracked files:\n  " + "\n  ".join(leaks)
