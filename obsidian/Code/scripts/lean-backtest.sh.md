---
path: "scripts/lean-backtest.sh"
hub: "Scripts"
tags:
  - "code/bash"
  - "areas/Scripts"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/scripts/lean-backtest.sh"
---
# lean-backtest.sh

`scripts/lean-backtest.sh` · hub [[Hubs/Areas/Scripts|Scripts]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/scripts/lean-backtest.sh)

## Source

> [!example] scripts/lean-backtest.sh
> ```bash
> #!/usr/bin/env bash
> #
> # scripts/lean-backtest.sh — workspace wrapper for `lean backtest`
> #
> # Always mounts MyProjects/shared/ into the LEAN container at /shared so that
> # the relative symlinks at <Project>/domain/signals/<name>.py → ../../../shared/
> # resolve inside the Docker bind mount.
> #
> # Without this, the algorithm fails to import shared signals during local
> # backtests (`No module named 'domain.signals.<name>'`). Cloud backtests are
> # unaffected — `lean cloud push` follows symlinks and inlines the content.
> #
> # Usage (from anywhere):
> #   bash scripts/lean-backtest.sh "<ProjectName>" [any other lean backtest flags]
> #
> # Forwards every argument to `lean backtest` verbatim after appending the
> # required --extra-docker-config volume mount.
>
> set -euo pipefail
>
> REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
> LEAN_BIN="$REPO_ROOT/venv/bin/lean"
> SHARED_DIR="$REPO_ROOT/MyProjects/shared"
>
> if [[ ! -x "$LEAN_BIN" ]]; then
>   echo "lean CLI not found at $LEAN_BIN — see docs/getting-started.md" >&2
>   exit 1
> fi
> if [[ ! -d "$SHARED_DIR" ]]; then
>   echo "MyProjects/shared/ not found at $SHARED_DIR — workspace layout is wrong" >&2
>   exit 1
> fi
>
> EXTRA_DOCKER_CONFIG=$(cat <<JSON
> {"volumes": {"$SHARED_DIR": {"bind": "/shared", "mode": "ro"}}}
> JSON
> )
>
> cd "$REPO_ROOT/MyProjects"
> exec "$LEAN_BIN" backtest "$@" --extra-docker-config "$EXTRA_DOCKER_CONFIG"
> ```
