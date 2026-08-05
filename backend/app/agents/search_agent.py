"""
Search Agent — generates DuckDuckGo queries and collects job results.
Handles rate limits with exponential backoff and deduplicates by URL.
"""
import re
import asyncio
import hashlib
from urllib.parse import urlparse, urlunparse
from typing import Optional

from app.agents.state import AgentState


def _normalize_url(url: str) -> str:
    """Normalize a URL for deduplication (strip tracking params, lowercase domain)."""
    try:
        parsed = urlparse(url)
        # Strip common tracking params
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            '', '', ''
        ))
    except Exception:
        return url.lower()


def _generate_queries(intent: dict) -> list[str]:
    """Generate multiple search queries from intent."""
    company = intent.get("company") or ""
    role = intent.get("role") or ""
    location = intent.get("location") or ""
    skills = intent.get("skills") or []
    emp_type = intent.get("employment_type") or "jobs"

    queries = []

    # Primary: exact match
    if company and role:
        queries.append(f'"{company}" "{role}" {emp_type} {location}'.strip())
    elif role:
        queries.append(f'"{role}" {emp_type} {location}'.strip())

    # Official career page
    if company:
        domain = company.lower().replace(" ", "").replace(",", "")
        queries.append(f'site:{domain}.com careers "{role}"' if role else f'site:{domain}.com careers')
        queries.append(f'"{company}" careers "{role}" apply {location}'.strip())

    # With top skill
    if skills and role:
        queries.append(f'"{role}" "{skills[0]}" {emp_type} {location}'.strip())

    # Broad fallback
    if role:
        queries.append(f'{role} {emp_type} {location} apply'.strip())

    return [q for q in queries if q.strip()][:5]


async def _ddgs_search(query: str, max_results: int = 10) -> list[dict]:
    """Call DuckDuckGo search with retry on rate limit."""
    for attempt in range(3):
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return results
        except Exception as e:
            err_msg = str(e).lower()
            if "ratelimit" in err_msg or "429" in err_msg:
                wait = 2 ** attempt * 3
                await asyncio.sleep(wait)
            else:
                break
    return []


TRUSTED_ATS = {"greenhouse.io", "lever.co", "workday.com", "myworkdayjobs.com",
               "taleo.net", "icims.com", "smartrecruiters.com", "bamboohr.com",
               "linkedin.com", "naukri.com", "instahyre.com", "wellfound.com"}

SUSPICIOUS_PATTERNS = ["work from home scam", "no experience required unlimited", "earn per day"]


def _classify_result(url: str, snippet: str, company: Optional[str]) -> dict:
    """Classify a result and compute initial relevance score."""
    domain = urlparse(url).netloc.lower().replace("www.", "")
    
    is_official = False
    source_type = "unverified"
    score = 0.0
    status = "available"

    # Official company career page
    if company:
        company_slug = company.lower().replace(" ", "").replace(",", "").replace(".", "")
        if company_slug in domain or domain.startswith(company_slug[:6]):
            is_official = True
            source_type = "official"
            score += 40

    # Trusted ATS
    for ats in TRUSTED_ATS:
        if ats in domain:
            source_type = "trusted_third_party" if not is_official else source_type
            score += 15
            break

    # Suspicious check
    snip_lower = snippet.lower()
    if any(p in snip_lower for p in SUSPICIOUS_PATTERNS):
        source_type = "suspicious"
        score -= 50
        status = "suspicious"

    # Expiry indicators
    expiry_words = ["no longer accepting", "position filled", "expired", "closed"]
    if any(w in snip_lower for w in expiry_words):
        status = "expired"
        score -= 30

    return {
        "domain": domain,
        "source_type": source_type,
        "is_official": is_official,
        "relevance_score": max(0.0, score),
        "job_status": status,
    }


async def run_search_agent(state: AgentState) -> AgentState:
    """Generate queries, search DuckDuckGo, deduplicate, and classify results."""
    intent = state.get("intent") or {}
    queries = _generate_queries(intent)
    state["search_queries"] = queries
    state["messages"].append({
        "type": "agent_message",
        "node": "search_jobs",
        "text": f"🔍 Searching with {len(queries)} queries…",
    })

    seen_urls: set[str] = set()
    all_results: list[dict] = []

    for i, query in enumerate(queries):
        raw = await _ddgs_search(query, max_results=8)
        for r in raw:
            url = r.get("href") or r.get("link") or ""
            if not url:
                continue
            norm = _normalize_url(url)
            if norm in seen_urls:
                continue
            seen_urls.add(norm)

            classification = _classify_result(
                url, r.get("body", ""), intent.get("company")
            )
            all_results.append({
                "title": r.get("title", ""),
                "url": url,
                "snippet": r.get("body", ""),
                "search_query": query,
                "search_position": len(all_results) + 1,
                **classification,
            })

        await asyncio.sleep(1)  # gentle rate limit

    state["raw_results"] = all_results
    state["current_node"] = "search_jobs"
    state["messages"].append({
        "type": "agent_message",
        "node": "search_jobs",
        "text": f"✅ Found {len(all_results)} unique results",
    })

    if not all_results:
        state["messages"].append({
            "type": "agent_message",
            "node": "search_jobs",
            "text": "⚠️ No results found. Please provide the job URL directly.",
        })

    return state


async def run_ranking_agent(state: AgentState) -> AgentState:
    """Score and rank job results. Apply intent-based boosting."""
    intent = state.get("intent") or {}
    results = state.get("raw_results") or []

    company = (intent.get("company") or "").lower()
    role = (intent.get("role") or "").lower()
    location = (intent.get("location") or "").lower()
    emp_type = (intent.get("employment_type") or "").lower()

    scored = []
    for r in results:
        score = r.get("relevance_score", 0.0)
        title = r.get("title", "").lower()
        snip = r.get("snippet", "").lower()

        # Role match
        if role and (role in title or role in snip):
            score += 25
        # Company match
        if company and (company in title or company in r.get("domain", "")):
            score += 20
        # Location match
        if location and location in snip:
            score += 10
        # Employment type
        if emp_type and emp_type in snip:
            score += 5
        # Penalize non-job pages
        if any(w in title for w in ["blog", "news", "article", "review"]):
            score -= 15

        scored.append({**r, "relevance_score": round(min(100.0, score), 2)})

    ranked = sorted(scored, key=lambda x: x["relevance_score"], reverse=True)
    state["ranked_results"] = ranked[:10]
    state["current_node"] = "rank_results"
    state["messages"].append({
        "type": "agent_message",
        "node": "rank_results",
        "text": f"📊 Ranked {len(ranked)} results. Top match: {ranked[0]['title'][:60] if ranked else 'None'}",
    })
    return state
