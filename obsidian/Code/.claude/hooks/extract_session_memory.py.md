---
path: ".claude/hooks/extract_session_memory.py"
hub: "Claude agents and skills"
lines: 149
tags:
  - "code/python"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py"
---
# extract_session_memory.py

`.claude/hooks/extract_session_memory.py` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py)

## Purpose

SessionEnd hook that extracts simple candidate memories from tool-events.jsonl.

This version does not call an LLM. It appends concise review candidates to
`.claude/memory/pending.md` instead of silently promoting them to durable memory.

## Dependencies


**Imports (external):** [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#json|json]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#sys|sys]]

## Constants

| Name | Value | Line |
|---|---|---|
| `IMPORTANT_COMMAND_HINTS` | `['pytest', 'python', 'pipenv', 'poetry', 'uv', 'npm', 'pnpm', 'yarn', 'docker', 'docker compose', 'lean', 'curl', 'git', 'make']` | [16](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py#L16) |
| `ERROR_HINTS` | `['error', 'exception', 'traceback', 'failed', 'not found', 'permission denied', 'module not found', 'no such file']` | [34](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py#L34) |

## Functions

### `load_jsonl()`

```python
def load_jsonl(path: Path) -> list[dict]
```
[line 46](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py#L46)

### `append_unique()`

```python
def append_unique(path: Path, heading: str, entries: list[str]) -> None
```
[line 64](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py#L64)

### `main()`

```python
def main() -> int
```
[line 91](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/extract_session_memory.py#L91)

## Source

> [!example]- .claude/hooks/extract_session_memory.py (149 lines)
> ```python
> #!/usr/bin/env python3
> """
> SessionEnd hook that extracts simple candidate memories from tool-events.jsonl.
>
> This version does not call an LLM. It appends concise review candidates to
> `.claude/memory/pending.md` instead of silently promoting them to durable memory.
> """
>
> import json
> import os
> import sys
> from datetime import datetime
> from pathlib import Path
>
>
> IMPORTANT_COMMAND_HINTS = [
>     "pytest",
>     "python",
>     "pipenv",
>     "poetry",
>     "uv",
>     "npm",
>     "pnpm",
>     "yarn",
>     "docker",
>     "docker compose",
>     "lean",
>     "curl",
>     "git",
>     "make",
> ]
>
>
> ERROR_HINTS = [
>     "error",
>     "exception",
>     "traceback",
>     "failed",
>     "not found",
>     "permission denied",
>     "module not found",
>     "no such file",
> ]
>
>
> def load_jsonl(path: Path) -> list[dict]:
>     if not path.exists():
>         return []
>
>     records = []
>     for line in path.read_text(encoding="utf-8").splitlines():
>         line = line.strip()
>         if not line:
>             continue
>
>         try:
>             records.append(json.loads(line))
>         except json.JSONDecodeError:
>             continue
>
>     return records
>
>
> def append_unique(path: Path, heading: str, entries: list[str]) -> None:
>     existing = path.read_text(encoding="utf-8") if path.exists() else ""
>
>     new_entries = []
>     for entry in entries:
>         entry = entry.strip()
>         if not entry or entry in existing:
>             continue
>         new_entries.append(entry)
>
>     if not new_entries:
>         return
>
>     path.parent.mkdir(parents=True, exist_ok=True)
>
>     if not existing.strip():
>         existing = f"# {heading}\n\n"
>         path.write_text(existing, encoding="utf-8")
>
>     today = datetime.now().strftime("%Y-%m-%d")
>
>     with path.open("a", encoding="utf-8") as f:
>         f.write(f"\n## Learned {today}\n\n")
>         for entry in new_entries:
>             f.write(f"- {entry}\n")
>
>
> def main() -> int:
>     # Read stdin so Claude Code can pass the hook event without breaking us.
>     raw = sys.stdin.read()
>
>     try:
>         event = json.loads(raw)
>     except json.JSONDecodeError:
>         event = {}
>
>     project_dir = Path(
>         os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd", "."))
>     ).resolve()
>
>     log_file = project_dir / ".claude" / "logs" / "tool-events.jsonl"
>     memory_dir = project_dir / ".claude" / "memory"
>
>     records = load_jsonl(log_file)
>
>     command_memories = []
>     api_memories = []
>     gotcha_memories = []
>
>     for record in records[-200:]:
>         tool_name = record.get("tool_name")
>         command = record.get("bash_command", "")
>         response = record.get("tool_response_snippet", "")
>
>         command_lower = command.lower()
>         response_lower = response.lower()
>
>         if tool_name == "Bash" and command:
>             if any(hint in command_lower for hint in IMPORTANT_COMMAND_HINTS):
>                 command_memories.append(f"`{command}` was used in this project.")
>
>             if "curl" in command_lower or "http" in command_lower:
>                 api_memories.append(
>                     f"API/Bash pattern observed: `{command}`. "
>                     "Review before reusing and do not store secrets."
>                 )
>
>             if any(hint in response_lower for hint in ERROR_HINTS):
>                 gotcha_memories.append(
>                     f"Command `{command}` produced an error-like result. "
>                     "Check logs before repeating."
>                 )
>
>     pending_entries = []
>     pending_entries.extend(f"Command candidate: {entry}" for entry in command_memories)
>     pending_entries.extend(f"API/data candidate: {entry}" for entry in api_memories)
>     pending_entries.extend(f"Gotcha candidate: {entry}" for entry in gotcha_memories)
>
>     append_unique(memory_dir / "pending.md", "Pending Memory Review", pending_entries)
>
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
