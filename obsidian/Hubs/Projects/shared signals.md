---
hub: "shared signals"
tags:
  - "hub"
  - "projects/shared-signals"
---
# shared signals

`MyProjects/shared/` · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/shared)

> [!abstract] Summary
> Reusable, pure-Python atoms that any QuantConnect project in this workspace can consume — without copy-pasting code between projects.
>
> This directory is **outside** every project's tree and is **never pushed to QuantConnect Cloud directly**. Projects consume its contents via relative symlinks inside their own `domain/signals/` directory. When `lean cloud push` walks the project, it follows the symlink and uploads the *content* — so QC Cloud sees a normal file, the local workspace sees a single source of truth.
>
> — from `MyProjects/shared/README.md`

## Files

**`MyProjects/shared/signals/`**

- [[Code/MyProjects/shared/signals/__init__.py|__init__.py]] · *Atom (shared signal)*
- [[Code/MyProjects/shared/signals/cross_sectional_rank.py|cross_sectional_rank.py]] · *Atom (shared signal)*
- [[Code/MyProjects/shared/signals/election_beta.py|election_beta.py]] · *Atom (shared signal)*
- [[Code/MyProjects/shared/signals/news_tone.py|news_tone.py]] · *Atom (shared signal)*

## Other tracked files (on GitHub)

- [MyProjects/shared/README.md](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/shared/README.md)
