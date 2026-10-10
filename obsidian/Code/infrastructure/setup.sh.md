---
path: "infrastructure/setup.sh"
hub: "Workspace root"
tags:
  - "code/bash"
  - "areas/Workspace-root"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/setup.sh"
---
# setup.sh

`infrastructure/setup.sh` · hub [[Hubs/Areas/Workspace root|Workspace root]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/setup.sh)

## Source

> [!example] infrastructure/setup.sh
> ```bash
> #!/usr/bin/env bash
> # Sets up the shared infrastructure venv used by the crypto and polymarket pipelines.
> # Run once after cloning. Idempotent — safe to re-run for dependency updates.
> set -euo pipefail
>
> HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
> VENV="$HERE/.venv"
>
> if [ ! -d "$VENV" ]; then
>   python3.11 -m venv "$VENV"
> fi
>
> # shellcheck disable=SC1091
> source "$VENV/bin/activate"
> pip install --upgrade pip
> pip install -r "$HERE/requirements.txt"
>
> # Editable installs so scripts can `from crypto_lean...` / `from polymarket_lean...` / `from yfinance_lean...`
> pip install -e "$HERE/pipelines/crypto"
> pip install -e "$HERE/pipelines/polymarket"
> pip install -e "$HERE/pipelines/yfinance"
>
> echo
> echo "Shared infrastructure venv ready at $VENV"
> echo "Activate with:  source $VENV/bin/activate"
> ```
