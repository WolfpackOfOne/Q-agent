---
path: "scripts/check-prereqs.sh"
hub: "Scripts"
tags:
  - "code/bash"
  - "areas/Scripts"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/scripts/check-prereqs.sh"
---
# check-prereqs.sh

`scripts/check-prereqs.sh` · hub [[Hubs/Areas/Scripts|Scripts]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/scripts/check-prereqs.sh)

## Source

> [!example]- scripts/check-prereqs.sh
> ```bash
> #!/usr/bin/env bash
> #
> # scripts/check-prereqs.sh
> #
> # Verifies the Q-agent workspace is ready for LEAN CLI work. Run after
> # `git clone` and any time `lean: command not found` shows up unexpectedly.
> #
> # Exits non-zero if any required resource is missing — friendly for CI gates
> # or `&& lean ...` chains.
>
> set -uo pipefail
>
> REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
> RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; RESET=$'\033[0m'
> PASS_COUNT=0
> FAIL_COUNT=0
> WARN_COUNT=0
>
> pass() { printf "  %sPASS%s %s\n" "$GREEN" "$RESET" "$1"; PASS_COUNT=$((PASS_COUNT+1)); }
> fail() { printf "  %sFAIL%s %s\n    %s\n" "$RED" "$RESET" "$1" "$2"; FAIL_COUNT=$((FAIL_COUNT+1)); }
> warn() { printf "  %sWARN%s %s\n    %s\n" "$YELLOW" "$RESET" "$1" "$2"; WARN_COUNT=$((WARN_COUNT+1)); }
>
> printf "Q-agent prereqs check — %s\n\n" "$REPO_ROOT"
>
> # 1. Workspace venv
> if [[ -x "$REPO_ROOT/venv/bin/python" ]]; then
>   pass "workspace venv at $REPO_ROOT/venv/"
> else
>   fail "workspace venv missing" \
>        "Create it: cd $REPO_ROOT && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install lean"
> fi
>
> # 2. lean CLI inside that venv
> if [[ -x "$REPO_ROOT/venv/bin/lean" ]]; then
>   LEAN_VERSION="$("$REPO_ROOT/venv/bin/lean" --version 2>/dev/null | head -1 || true)"
>   pass "lean CLI at $REPO_ROOT/venv/bin/lean ($LEAN_VERSION)"
> else
>   fail "lean CLI not in workspace venv" \
>        "source $REPO_ROOT/venv/bin/activate && pip install lean"
> fi
>
> # 3. QC credentials
> if [[ -s "$HOME/.lean/credentials" ]]; then
>   pass "QuantConnect credentials at ~/.lean/credentials"
> else
>   warn "no ~/.lean/credentials (cloud commands will fail)" \
>        "Run 'lean login' interactively. See CREDENTIALS.md § 'QuantConnect (lean CLI)'."
> fi
>
> # 4. MyProjects/lean.json
> if [[ -f "$REPO_ROOT/MyProjects/lean.json" ]]; then
>   pass "MyProjects/lean.json exists"
> else
>   warn "MyProjects/lean.json missing (created on demand by 'lean init')" \
>        "cd $REPO_ROOT/MyProjects && lean init"
> fi
>
> # 5. Docker daemon (only required for local backtests, not for cloud)
> if command -v docker >/dev/null 2>&1; then
>   if docker info >/dev/null 2>&1; then
>     pass "Docker daemon reachable (required for 'lean backtest' local runs)"
>   else
>     warn "docker CLI present but daemon not responding" \
>          "open -a 'Docker' on macOS; cloud backtests don't need this"
>   fi
> else
>   warn "docker not installed (required for local backtests only)" \
>        "Install Docker Desktop if you want 'lean backtest' to work locally"
> fi
>
> # 6. Shared signals library
> if [[ -d "$REPO_ROOT/MyProjects/shared/signals" ]]; then
>   pass "MyProjects/shared/signals/ present"
> else
>   warn "MyProjects/shared/signals/ missing" \
>        "Tracked in this repo — try 'git status' and 'git pull'"
> fi
>
> printf "\nSummary: %d pass, %d warn, %d fail\n" "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
> if (( FAIL_COUNT > 0 )); then
>   printf "\n%sFix the FAIL items above before running lean commands.%s\n" "$RED" "$RESET"
>   printf "Full first-time setup: docs/getting-started.md\n"
>   exit 1
> fi
> exit 0
> ```
