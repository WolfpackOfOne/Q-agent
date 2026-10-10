---
path: "MyProjects/FundamentalsPortfolio/.claude/hooks/stop-memory-nudge.sh"
hub: "FundamentalsPortfolio"
tags:
  - "code/bash"
  - "projects/FundamentalsPortfolio"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/.claude/hooks/stop-memory-nudge.sh"
---
# stop-memory-nudge.sh

`MyProjects/FundamentalsPortfolio/.claude/hooks/stop-memory-nudge.sh` · hub [[Hubs/Projects/FundamentalsPortfolio|FundamentalsPortfolio]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/FundamentalsPortfolio/.claude/hooks/stop-memory-nudge.sh)

## Source

> [!example] MyProjects/FundamentalsPortfolio/.claude/hooks/stop-memory-nudge.sh
> ```bash
> #!/usr/bin/env bash
> set -euo pipefail
>
> CONTEXT="$(cat)"
>
> STRONG_PATTERNS="fixed|workaround|gotcha|that's wrong|check again|we already|should have|discovered|realized|turns out"
> WEAK_PATTERNS="error|bug|issue|problem|fail"
>
> if printf '%s' "$CONTEXT" | grep -qiE "$STRONG_PATTERNS"; then
>   cat <<'EOF'
> {
>   "decision": "approve",
>   "systemMessage": "This session involved fixes or discoveries. Consider running /reflect to capture learnings in project docs."
> }
> EOF
> elif printf '%s' "$CONTEXT" | grep -qiE "$WEAK_PATTERNS"; then
>   echo '{"decision":"approve","systemMessage":"If you learned something non-obvious this session, run /reflect to update docs."}'
> else
>   echo '{"decision":"approve"}'
> fi
> ```
