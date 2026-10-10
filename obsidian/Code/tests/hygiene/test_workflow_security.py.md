---
path: "tests/hygiene/test_workflow_security.py"
hub: "Tests"
lines: 37
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py"
---
# test_workflow_security.py

`tests/hygiene/test_workflow_security.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py)

## Purpose

Keep GitHub Actions permissions and dependency pins reviewable.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#re|re]]

## Constants

| Name | Value | Line |
|---|---|---|
| `ACTION_REF` | `re.compile('^\\s*-?\\s*uses:\\s*[^\\s@]+@([^\\s#]+)', re.MULTILINE)` | [9](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py#L9) |
| `FULL_SHA` | `re.compile('[0-9a-f]{40}')` | [10](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py#L10) |

## Functions

### `test_all_actions_use_immutable_commit_shas()`

```python
def test_all_actions_use_immutable_commit_shas(repo_root: Path)
```
[line 13](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py#L13)

### `test_docker_write_permission_is_publish_job_only()`

```python
def test_docker_write_permission_is_publish_job_only(repo_root: Path)
```
[line 23](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py#L23)

### `test_lean_pin_matches_course_constraints()`

```python
def test_lean_pin_matches_course_constraints(repo_root: Path)
```
[line 30](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/hygiene/test_workflow_security.py#L30)

## Source

> [!example]- tests/hygiene/test_workflow_security.py (37 lines)
> ```python
> """Keep GitHub Actions permissions and dependency pins reviewable."""
>
> from __future__ import annotations
>
> import re
> from pathlib import Path
>
>
> ACTION_REF = re.compile(r"^\s*-?\s*uses:\s*[^\s@]+@([^\s#]+)", re.MULTILINE)
> FULL_SHA = re.compile(r"[0-9a-f]{40}")
>
>
> def test_all_actions_use_immutable_commit_shas(repo_root: Path):
>     failures: list[str] = []
>     for workflow in sorted((repo_root / ".github" / "workflows").glob("*.yml")):
>         text = workflow.read_text(encoding="utf-8")
>         for ref in ACTION_REF.findall(text):
>             if not FULL_SHA.fullmatch(ref):
>                 failures.append(f"{workflow.name}: mutable action ref {ref!r}")
>     assert not failures, "\n".join(failures)
>
>
> def test_docker_write_permission_is_publish_job_only(repo_root: Path):
>     text = (repo_root / ".github" / "workflows" / "docker.yml").read_text()
>     assert text.count("packages: write") == 1
>     publish = text.index("  publish:")
>     assert text.index("packages: write") > publish
>
>
> def test_lean_pin_matches_course_constraints(repo_root: Path):
>     dockerfile = (repo_root / "Dockerfile").read_text()
>     constraints = (repo_root / "constraints-course.txt").read_text()
>     docker_version = re.search(r"^ARG LEAN_VERSION=(.+)$", dockerfile, re.MULTILINE)
>     constraint_version = re.search(r"^lean==(.+)$", constraints, re.MULTILINE)
>     assert docker_version and constraint_version
>     assert docker_version.group(1) == constraint_version.group(1)
> ```
