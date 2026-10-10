---
path: ".github/workflows/codeql.yml"
hub: "CI workflows"
tags:
  - "code/yaml"
  - "areas/CI-workflows"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.github/workflows/codeql.yml"
---
# codeql.yml

`.github/workflows/codeql.yml` · hub [[Hubs/Areas/CI workflows|CI workflows]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.github/workflows/codeql.yml)

**Triggers:**

```yaml
pull_request:
  push:
    branches: [main]
  schedule:
    - cron: "23 7 * * 1"
```

**Jobs:** `analyze`

## Source

> [!example] .github/workflows/codeql.yml
> ```yaml
> name: CodeQL
>
> on:
>   pull_request:
>   push:
>     branches: [main]
>   schedule:
>     - cron: "23 7 * * 1"
>
> permissions:
>   contents: read
>   security-events: write
>
> concurrency:
>   group: codeql-${{ github.ref }}
>   cancel-in-progress: true
>
> jobs:
>   analyze:
>     name: CodeQL
>     runs-on: ubuntu-latest
>     timeout-minutes: 20
>     steps:
>       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
>
>       - name: Initialize CodeQL
>         uses: github/codeql-action/init@b96794f015dfd88f77b49b1c93e0fa7110f94c63 # v4
>         with:
>           languages: python
>           build-mode: none
>
>       - name: Analyze
>         uses: github/codeql-action/analyze@b96794f015dfd88f77b49b1c93e0fa7110f94c63 # v4
> ```
