"""Write Polymarket data as CSVs under lean-data/alternative/polymarket/."""
from __future__ import annotations

import pathlib
from typing import Any, Iterable

import pandas as pd


MARKET_COLUMNS = [
    "MarketId",
    "Slug",
    "Question",
    "EventSlug",
    "EventTitle",
    "Active",
    "Closed",
    "Archived",
    "StartDate",
    "EndDate",
    "ResolvedOutcome",
    "OutcomePrices",
    "Volume",
    "Liquidity",
    "YesTokenId",
    "NoTokenId",
    "Tags",
]


def _first_event(market: dict[str, Any]) -> dict[str, Any]:
    events = market.get("events") or []
    return events[0] if events else {}


def _outcome_token_ids(market: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (YES_token_id, NO_token_id) if parseable."""
    raw = market.get("clobTokenIds")
    if not raw:
        return None, None
    # Field is sometimes a JSON-encoded string, sometimes a list.
    if isinstance(raw, str):
        import json
        try:
            ids = json.loads(raw)
        except json.JSONDecodeError:
            return None, None
    else:
        ids = raw
    if not isinstance(ids, list) or len(ids) < 2:
        return None, None
    return str(ids[0]), str(ids[1])


def _market_row(
    market: dict[str, Any],
    event_tag_index: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    yes_id, no_id = _outcome_token_ids(market)
    ev = _first_event(market)
    if event_tag_index is not None:
        tags = sorted({
            slug
            for ev2 in (market.get("events") or [])
            for slug in event_tag_index.get(str(ev2.get("id") or ""), set())
        })
    else:
        tags = sorted({
            t.get("slug") for ev2 in (market.get("events") or [])
            for t in (ev2.get("tags") or [])
            if t.get("slug")
        })
    return {
        "MarketId": market.get("id"),
        "Slug": market.get("slug"),
        "Question": market.get("question"),
        "EventSlug": ev.get("slug"),
        "EventTitle": ev.get("title"),
        "Active": market.get("active"),
        "Closed": market.get("closed"),
        "Archived": market.get("archived"),
        "StartDate": market.get("startDate"),
        "EndDate": market.get("endDate"),
        "ResolvedOutcome": market.get("resolvedOutcome"),
        "OutcomePrices": market.get("outcomePrices"),
        "Volume": market.get("volume"),
        "Liquidity": market.get("liquidity"),
        "YesTokenId": yes_id,
        "NoTokenId": no_id,
        "Tags": "|".join(tags),
    }


def write_markets_csv(
    markets: Iterable[dict[str, Any]],
    out_path: pathlib.Path,
    event_tag_index: dict[str, set[str]] | None = None,
) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_market_row(m, event_tag_index) for m in markets]
    df = pd.DataFrame(rows, columns=MARKET_COLUMNS)
    df.to_csv(out_path, index=False)
    return len(df)


def write_market_prices_csv(
    df_prices: pd.DataFrame, market_slug: str, prices_dir: pathlib.Path
) -> pathlib.Path:
    prices_dir.mkdir(parents=True, exist_ok=True)
    out = prices_dir / f"{market_slug}.csv"
    if df_prices.empty:
        out.write_text("datetime,price\n")
        return out
    df_prices.to_csv(out, index_label="datetime", header=True,
                     date_format="%Y-%m-%dT%H:%M:%SZ")
    return out
