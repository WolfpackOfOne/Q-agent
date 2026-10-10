---
path: "scripts/start-remote.sh"
hub: "Scripts"
tags:
  - "code/bash"
  - "areas/Scripts"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/scripts/start-remote.sh"
---
# start-remote.sh

`scripts/start-remote.sh` · hub [[Hubs/Areas/Scripts|Scripts]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/scripts/start-remote.sh)

## Source

> [!example]- scripts/start-remote.sh
> ```bash
> #!/usr/bin/env bash
> # Start a Claude Code Remote Control session for this workspace.
> #
> # Usage:
> #   scripts/start-remote.sh                  # server mode, default name
> #   scripts/start-remote.sh -i               # interactive + remote (chat locally too)
> #   scripts/start-remote.sh -n "My Session"  # custom session name
> #   scripts/start-remote.sh -w               # server mode, each session in its own git worktree
> #
> # Press spacebar inside server mode to toggle the QR code for the Claude mobile app.
>
> set -euo pipefail
>
> REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
> cd "$REPO_ROOT"
>
> NAME="QuantConnect"
> MODE="server"
> SPAWN="same-dir"
>
> while getopts ":in:w" opt; do
>   case "$opt" in
>     i) MODE="interactive" ;;
>     n) NAME="$OPTARG" ;;
>     w) SPAWN="worktree" ;;
>     \?) echo "Unknown flag: -$OPTARG" >&2; exit 2 ;;
>     :)  echo "Flag -$OPTARG needs a value" >&2; exit 2 ;;
>   esac
> done
>
> if ! command -v claude >/dev/null 2>&1; then
>   echo "claude CLI not found. Activate the venv or install: npm i -g @anthropic-ai/claude-code@latest" >&2
>   exit 1
> fi
>
> if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
>   echo "warning: ANTHROPIC_API_KEY is set — Remote Control needs claude.ai OAuth, not API key auth." >&2
>   echo "         unset ANTHROPIC_API_KEY in this shell, then re-run." >&2
>   exit 1
> fi
>
> echo "Workspace: $REPO_ROOT"
> echo "Session name: $NAME"
> echo "Mode: $MODE"
> [[ "$MODE" == "server" ]] && echo "Spawn: $SPAWN"
> echo
>
> if [[ "$MODE" == "interactive" ]]; then
>   exec claude --remote-control "$NAME"
> else
>   exec claude remote-control --name "$NAME" --spawn "$SPAWN"
> fi
> ```
