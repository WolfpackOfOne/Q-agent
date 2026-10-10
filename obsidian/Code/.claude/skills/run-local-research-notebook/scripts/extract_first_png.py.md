---
path: ".claude/skills/run-local-research-notebook/scripts/extract_first_png.py"
hub: "Claude agents and skills"
lines: 46
tags:
  - "code/python"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/run-local-research-notebook/scripts/extract_first_png.py"
---
# extract_first_png.py

`.claude/skills/run-local-research-notebook/scripts/extract_first_png.py` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/run-local-research-notebook/scripts/extract_first_png.py)

## Dependencies


**Imports (external):** [[Indexes/External packages#base64|base64]], [[Indexes/External packages#json|json]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#sys|sys]]

## Functions

### `_coerce_png()`

```python
def _coerce_png(data)
```
[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/run-local-research-notebook/scripts/extract_first_png.py#L8)

### `main()`

```python
def main() -> int
```
[line 14](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/run-local-research-notebook/scripts/extract_first_png.py#L14)

## Source

> [!example]- .claude/skills/run-local-research-notebook/scripts/extract_first_png.py (46 lines)
> ```python
> #!/usr/bin/env python3
> import base64
> import json
> import sys
> from pathlib import Path
>
>
> def _coerce_png(data):
>     if isinstance(data, list):
>         return "".join(data)
>     return data
>
>
> def main() -> int:
>     if len(sys.argv) != 3:
>         print("Usage: extract_first_png.py <executed-notebook.ipynb> <output.png>", file=sys.stderr)
>         return 2
>
>     notebook_path = Path(sys.argv[1])
>     output_path = Path(sys.argv[2])
>
>     if not notebook_path.is_file():
>         print(f"Notebook not found: {notebook_path}", file=sys.stderr)
>         return 1
>
>     notebook = json.loads(notebook_path.read_text())
>
>     for cell in notebook.get("cells", []):
>         if cell.get("cell_type") != "code":
>             continue
>         for output in cell.get("outputs", []):
>             image_data = output.get("data", {}).get("image/png")
>             if not image_data:
>                 continue
>             output_path.parent.mkdir(parents=True, exist_ok=True)
>             output_path.write_bytes(base64.b64decode(_coerce_png(image_data)))
>             print(output_path)
>             return 0
>
>     print("No image/png output found", file=sys.stderr)
>     return 1
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
