---
path: "infrastructure/pipelines/crypto/scripts/list_symbols.py"
hub: "crypto"
lines: 33
tags:
  - "code/python"
  - "pipelines/crypto"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/list_symbols.py"
---
# list_symbols.py

`infrastructure/pipelines/crypto/scripts/list_symbols.py` · hub [[Hubs/Pipelines/crypto|crypto]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/list_symbols.py)

## Purpose

Print which pairs a given exchange lists, optionally filtered by quote currency.

python scripts/list_symbols.py --exchange kraken --quote USD

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/crypto/src/crypto_lean/client.py|client.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#argparse|argparse]]

## Functions

### `main()`

```python
def main() -> int
```
[line 12](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/list_symbols.py#L12)

## Source

> [!example]- infrastructure/pipelines/crypto/scripts/list_symbols.py (33 lines)
> ```python
> """Print which pairs a given exchange lists, optionally filtered by quote currency.
>
>     python scripts/list_symbols.py --exchange kraken --quote USD
> """
> from __future__ import annotations
>
> import argparse
>
> from crypto_lean.client import ExchangeClient
>
>
> def main() -> int:
>     p = argparse.ArgumentParser(description=__doc__)
>     p.add_argument("--exchange", required=True,
>                    choices=["coinbase", "kraken"])
>     p.add_argument("--quote", default=None, help="Filter by quote currency (USD/USDT/USDC).")
>     p.add_argument("--base", default=None, help="Filter by base currency (BTC/ETH/...).")
>     args = p.parse_args()
>
>     client = ExchangeClient(exchange=args.exchange)
>     symbols = client._client.symbols or []
>     if args.quote:
>         symbols = [s for s in symbols if s.endswith(f"/{args.quote.upper()}")]
>     if args.base:
>         symbols = [s for s in symbols if s.startswith(f"{args.base.upper()}/")]
>     for s in sorted(symbols):
>         print(s)
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
