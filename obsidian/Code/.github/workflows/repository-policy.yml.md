---
path: ".github/workflows/repository-policy.yml"
hub: "CI workflows"
tags:
  - "code/yaml"
  - "areas/CI-workflows"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.github/workflows/repository-policy.yml"
---
# repository-policy.yml

`.github/workflows/repository-policy.yml` · hub [[Hubs/Areas/CI workflows|CI workflows]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.github/workflows/repository-policy.yml)

**Triggers:**

```yaml
pull_request:
  push:
    branches: [main]
```

**Jobs:** `policy`

## Source

> [!example] .github/workflows/repository-policy.yml
> ```yaml
> name: Repository Policy
>
> on:
>   pull_request:
>   push:
>     branches: [main]
>
> permissions:
>   contents: read
>
> concurrency:
>   group: repository-policy-${{ github.ref }}
>   cancel-in-progress: true
>
> jobs:
>   policy:
>     name: Repository policy
>     runs-on: ubuntu-latest
>     timeout-minutes: 10
>     steps:
>       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
>         with:
>           fetch-depth: 0
>
>       - name: Check repository policy
>         shell: bash
>         env:
>           EVENT_NAME: ${{ github.event_name }}
>           BASE_SHA: ${{ github.event.pull_request.base.sha }}
>         run: |
>           set -euo pipefail
>           if [ "$EVENT_NAME" = "pull_request" ]; then
>             python scripts/check_repository_policy.py --base "$BASE_SHA"
>           else
>             python scripts/check_repository_policy.py --all
>           fi
> ```
