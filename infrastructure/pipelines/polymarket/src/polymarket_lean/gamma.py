"""Polymarket Gamma API client — market metadata + tag filtering.

Endpoints used:
    GET  https://gamma-api.polymarket.com/markets?limit=...&offset=...
    GET  https://gamma-api.polymarket.com/events?...

No auth required for read.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterator

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

GAMMA_BASE = "https://gamma-api.polymarket.com"

# Tag slugs we keep when running with --filter default.
# Polymarket exposes tag slugs on each market under `events[].tags[].slug`.
DEFAULT_TAG_FILTER: tuple[str, ...] = (
    "crypto",
    "bitcoin",
    "ethereum",
    "solana",
    "macro",
    "economics",
    "fed",
    "inflation",
    "elections",
    "politics",
    "us-elections",
    "trump",
    "biden",
)


@dataclass
class GammaClient:
    base_url: str = GAMMA_BASE
    pacing_s: float = 0.20
    timeout_s: float = 30.0

    def __post_init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "polymarket-lean/0.1"})

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        time.sleep(self.pacing_s)
        r = self._session.get(f"{self.base_url}{path}", params=params,
                              timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def iter_markets(
        self,
        limit_per_page: int = 500,
        max_pages: int | None = None,
        active: bool | None = None,
        closed: bool | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield raw market dicts. Paginates until exhausted.

        Pagination notes for the Gamma API:
        - The server silently caps each response at ~100 markets even when
          `limit` is higher, so we advance `offset` by the actual batch length
          rather than the requested limit.
        - Stop on an empty batch, or HTTP 422 (the API uses 422 to signal an
          offset past the available range), or when `max_pages` is reached.
        """
        offset = 0
        page = 0
        while True:
            params: dict[str, Any] = {"limit": limit_per_page, "offset": offset}
            if active is not None:
                params["active"] = str(active).lower()
            if closed is not None:
                params["closed"] = str(closed).lower()
            try:
                batch = self._get("/markets", params=params)
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 422:
                    return
                raise
            if not batch:
                return
            for m in batch:
                yield m
            page += 1
            if max_pages and page >= max_pages:
                return
            offset += len(batch)

    def iter_events(
        self,
        limit_per_page: int = 500,
        max_pages: int | None = None,
        closed: bool | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield raw event dicts. Same pagination quirks as iter_markets."""
        offset = 0
        page = 0
        while True:
            params: dict[str, Any] = {"limit": limit_per_page, "offset": offset}
            if closed is not None:
                params["closed"] = str(closed).lower()
            try:
                batch = self._get("/events", params=params)
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 422:
                    return
                raise
            if not batch:
                return
            for e in batch:
                yield e
            page += 1
            if max_pages and page >= max_pages:
                return
            offset += len(batch)

    def build_event_tag_index(
        self,
        max_pages: int | None = None,
        closed: bool | None = None,
    ) -> dict[str, set[str]]:
        """Return `{event_id: {tag_slug, ...}}` by iterating /events.

        The Gamma /markets endpoint no longer embeds event tags, so callers
        that want to filter markets by tag must pre-fetch this index and
        pass it to `market_tags` / `market_matches_filter`.
        """
        index: dict[str, set[str]] = {}
        for ev in self.iter_events(max_pages=max_pages, closed=closed):
            eid = str(ev.get("id") or "")
            if not eid:
                continue
            slugs = {
                (t.get("slug") or "").lower()
                for t in (ev.get("tags") or [])
                if t.get("slug")
            }
            if slugs:
                index[eid] = slugs
        return index

    @staticmethod
    def market_tags(
        market: dict[str, Any],
        event_tag_index: dict[str, set[str]] | None = None,
    ) -> set[str]:
        """Pull the union of tag slugs from a market's events.

        If `event_tag_index` is provided, tags are looked up by event id —
        required because the /markets endpoint no longer embeds tags. If
        omitted, falls back to whatever tags are inline on the market dict
        (will be empty against the current Gamma API).
        """
        tags: set[str] = set()
        for ev in market.get("events", []) or []:
            if event_tag_index is not None:
                eid = str(ev.get("id") or "")
                tags |= event_tag_index.get(eid, set())
            else:
                for t in ev.get("tags", []) or []:
                    slug = t.get("slug")
                    if slug:
                        tags.add(slug.lower())
        return tags

    @classmethod
    def market_matches_filter(
        cls,
        market: dict[str, Any],
        filter_slugs: tuple[str, ...],
        event_tag_index: dict[str, set[str]] | None = None,
    ) -> bool:
        if not filter_slugs:
            return True
        return bool(
            cls.market_tags(market, event_tag_index)
            & set(s.lower() for s in filter_slugs)
        )
