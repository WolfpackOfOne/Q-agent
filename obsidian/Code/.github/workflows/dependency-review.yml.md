---
path: ".github/workflows/dependency-review.yml"
hub: "CI workflows"
tags:
  - "code/yaml"
  - "areas/CI-workflows"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.github/workflows/dependency-review.yml"
---
# dependency-review.yml

`.github/workflows/dependency-review.yml` · hub [[Hubs/Areas/CI workflows|CI workflows]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.github/workflows/dependency-review.yml)

**Triggers:**

```yaml
pull_request:
```

**Jobs:** `dependency-review`

## Source

> [!example] .github/workflows/dependency-review.yml
> ```yaml
> name: Dependency Review
>
> on:
>   pull_request:
>
> permissions:
>   contents: read
>
> concurrency:
>   group: dependency-review-${{ github.ref }}
>   cancel-in-progress: true
>
> jobs:
>   dependency-review:
>     name: Dependency review
>     runs-on: ubuntu-latest
>     timeout-minutes: 10
>     steps:
>       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
>       - name: Review dependency changes
>         uses: actions/dependency-review-action@2031cfc080254a8a887f58cffee85186f0e49e48 # v4
>         with:
>           fail-on-severity: high
> ```
