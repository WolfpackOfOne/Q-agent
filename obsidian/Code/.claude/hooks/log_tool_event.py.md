---
path: ".claude/hooks/log_tool_event.py"
hub: "Claude agents and skills"
lines: 116
tags:
  - "code/python"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py"
---
# log_tool_event.py

`.claude/hooks/log_tool_event.py` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py)

## Purpose

Log Claude Code tool-use events as JSONL.

This is intentionally conservative:
- logs Bash commands and selected tool metadata
- avoids storing secrets
- keeps output snippets short
- writes to .claude/logs/tool-events.jsonl

The SessionEnd hook can later summarize this raw evidence into
`.claude/memory/pending.md`.

## Dependencies


**Imports (external):** [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#json|json]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#re|re]], [[Indexes/External packages#sys|sys]]

## Constants

| Name | Value | Line |
|---|---|---|
| `MAX_OUTPUT_CHARS` | `2000` | [23](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py#L23) |
| `SECRET_PATTERNS` | `[re.compile('(?i)\\b([A-Z0-9_]*(?:PASSWORD\|TOKEN\|SECRET\|API_KEY\|ACCESS_KEY\|PRIVATE_KEY)[A-Z0-9_]*)\\s*([:=])\\s*[\'\\"]?[^\'\\"\\s,}]+'), re.compile('(?i)\\b...` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py#L26) |
| `AUTHORIZATION_PATTERN` | `re.compile('(?i)(authorization:\\s*bearer\\s+)[A-Za-z0-9._\\-]+')` | [36](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py#L36) |

## Functions

### `redact()`

```python
def redact(text: str) -> str
```
[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py#L39)

### `redact_json()`

```python
def redact_json(value)
```
[line 50](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py#L50)

Redact nested tool input/response before writing logs.

### `main()`

```python
def main() -> int
```
[line 59](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/hooks/log_tool_event.py#L59)

## Source

> [!example]- .claude/hooks/log_tool_event.py (116 lines)
> ```python
> #!/usr/bin/env python3
> """
> Log Claude Code tool-use events as JSONL.
>
> This is intentionally conservative:
> - logs Bash commands and selected tool metadata
> - avoids storing secrets
> - keeps output snippets short
> - writes to .claude/logs/tool-events.jsonl
>
> The SessionEnd hook can later summarize this raw evidence into
> `.claude/memory/pending.md`.
> """
>
> import json
> import os
> import re
> import sys
> from datetime import datetime
> from pathlib import Path
>
>
> MAX_OUTPUT_CHARS = 2000
>
>
> SECRET_PATTERNS = [
>     re.compile(
>         r"(?i)\b([A-Z0-9_]*(?:PASSWORD|TOKEN|SECRET|API_KEY|ACCESS_KEY|PRIVATE_KEY)"
>         r"[A-Z0-9_]*)\s*([:=])\s*['\"]?[^'\"\s,}]+"
>     ),
>     re.compile(r"(?i)\b((?:WRDS|QC|LEAN|QUANTCONNECT)_[A-Z0-9_]+)\s*([:=])\s*['\"]?[^'\"\s,}]+"),
>     re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*([:=])\s*['\"]?[^'\"\s,}]+"),
>     re.compile(r"(?i)\b(organization-id|user-id|project-id|api-token)\s*([:=])\s*['\"]?[^'\"\s,}]+"),
> ]
>
> AUTHORIZATION_PATTERN = re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._\-]+")
>
>
> def redact(text: str) -> str:
>     if not isinstance(text, str):
>         return text
>
>     redacted = text
>     for pattern in SECRET_PATTERNS:
>         redacted = pattern.sub(r"\1\2[REDACTED_SECRET]", redacted)
>     redacted = AUTHORIZATION_PATTERN.sub(r"\1[REDACTED_SECRET]", redacted)
>     return redacted
>
>
> def redact_json(value):
>     """Redact nested tool input/response before writing logs."""
>     try:
>         text = json.dumps(value, ensure_ascii=False, default=str)
>         return json.loads(redact(text))
>     except Exception:
>         return redact(str(value))
>
>
> def main() -> int:
>     raw = sys.stdin.read()
>
>     try:
>         event = json.loads(raw)
>     except json.JSONDecodeError:
>         return 0
>
>     project_dir = Path(
>         os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd", "."))
>     ).resolve()
>
>     log_dir = project_dir / ".claude" / "logs"
>     log_dir.mkdir(parents=True, exist_ok=True)
>     log_file = log_dir / "tool-events.jsonl"
>
>     tool_name = event.get("tool_name") or event.get("toolName")
>     tool_input = event.get("tool_input") or event.get("toolInput") or {}
>
>     # Claude Code event schemas can evolve, so keep this flexible.
>     tool_response = (
>         event.get("tool_response")
>         or event.get("toolResponse")
>         or event.get("response")
>         or {}
>     )
>
>     record = {
>         "timestamp": datetime.now().isoformat(timespec="seconds"),
>         "event_name": event.get("hook_event_name") or event.get("hookEventName"),
>         "session_id": event.get("session_id") or event.get("sessionId"),
>         "cwd": str(project_dir),
>         "tool_name": tool_name,
>         "tool_input": redact_json(tool_input),
>         "tool_response_snippet": None,
>     }
>
>     if tool_name == "Bash":
>         command = tool_input.get("command", "")
>         record["bash_command"] = redact(command)
>
>     response_text = json.dumps(tool_response, ensure_ascii=False, default=str)
>     response_text = redact(response_text)
>
>     if len(response_text) > MAX_OUTPUT_CHARS:
>         response_text = response_text[:MAX_OUTPUT_CHARS] + "...[truncated]"
>
>     record["tool_response_snippet"] = response_text
>
>     with log_file.open("a", encoding="utf-8") as f:
>         f.write(json.dumps(record, ensure_ascii=False) + "\n")
>
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
