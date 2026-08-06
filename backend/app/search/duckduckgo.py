"""
duckduckgo.py — DuckDuckGo search wrapper with retry and rate-limit handling.

Uses the `duckduckgo_search` library (DDGS). Implements:
- Exponential backoff on rate-limit (429) errors
- Timeout handling
- Result normalisation to a consistent dict schema

PRD §13 REQ-03, §27 (Search error handling).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

# Fields returned per result
_RESULT_SCHEMA = ("title", "url", "snippet")


def _normalize_url(url: str) -> str:
    """Lowercase domain, strip path trailing slash and tracking fragments."""
    try:
        p = urlparse(url)
        clean = urlunparse((
            p.scheme.lower(),
            p.netloc.lower(),
            p.path.rstrip("/"),
            "",
            "",
            "",
        ))
        return clean
    except Exception:
        return url.lower()


def _extract_url(raw: dict) -> str:
    """Handle both 'href' and 'link' field names from different DDGS versions."""
    return raw.get("href") or raw.get("link") or raw.get("url") or ""


def _normalize_result(raw: dict, query: str, position: int) -> Optional[dict]:
    """Convert a raw DDGS result to the normalised FormPilot schema."""
    url = _extract_url(raw)
    if not url:
        return None
    return {
        "title": (raw.get("title") or "").strip(),
        "url": url,
        "normalized_url": _normalize_url(url),
        "snippet": (raw.get("body") or raw.get("snippet") or "").strip(),
        "search_query": query,
        "search_position": position,
    }


async def ddg_search(
    query: str,
    max_results: int = 10,
    max_retries: int = 3,
    base_delay: float = 3.0,
) -> list[dict]:
    """
    Search DuckDuckGo for `query`, returning up to `max_results` normalised results.

    Retries up to `max_retries` times on rate-limit errors with exponential backoff.
    Returns an empty list on unrecoverable errors (logged at WARNING level).

    Args:
        query: The search query string.
        max_results: Maximum number of results to return per query.
        max_retries: How many times to retry on rate-limit.
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        List of normalised result dicts.
    """
    for attempt in range(max_retries):
        try:
            from duckduckgo_search import DDGS

            # DDGS is synchronous — run in thread pool to avoid blocking the event loop
            def _sync_search() -> list[dict]:
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))

            raw_results = await asyncio.get_event_loop().run_in_executor(
                None, _sync_search
            )

            normalised = []
            for i, raw in enumerate(raw_results):
                r = _normalize_result(raw, query, i + 1)
                if r:
                    normalised.append(r)

            logger.debug("DDG query=%r returned %d results", query, len(normalised))
            return normalised

        except Exception as exc:
            err_lower = str(exc).lower()
            is_rate_limit = any(
                kw in err_lower for kw in ("ratelimit", "429", "too many requests", "rate limit")
            )

            if is_rate_limit and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "DDG rate-limited on attempt %d/%d — waiting %.1fs before retry",
                    attempt + 1, max_retries, delay,
                )
                await asyncio.sleep(delay)
                continue

            logger.warning("DDG search failed for query=%r: %s", query, exc)
            return []

    return []


async def ddg_multi_search(
    queries: list[str],
    max_results_per_query: int = 8,
    inter_query_delay: float = 1.5,
) -> list[dict]:
    """
    Run multiple DDG queries sequentially (to avoid rate-limiting),
    deduplicate by normalized URL, and return all unique results.

    Args:
        queries: List of query strings.
        max_results_per_query: Max results to fetch per query.
        inter_query_delay: Seconds to wait between queries.

    Returns:
        Deduplicated list of normalised result dicts.
    """
    seen_urls: set[str] = set()
    all_results: list[dict] = []

    for query in queries:
        results = await ddg_search(query, max_results=max_results_per_query)
        for r in results:
            norm_url = r.get("normalized_url", "")
            if norm_url and norm_url not in seen_urls:
                seen_urls.add(norm_url)
                all_results.append(r)

        if inter_query_delay > 0:
            await asyncio.sleep(inter_query_delay)

    logger.info("DDG multi-search: %d queries → %d unique results", len(queries), len(all_results))
    return all_results
