"""
ranking.py — score and rank search results using intent-based boosting.

Combines the domain trust score (from verifier) with intent-based content
matching to produce a final relevance_score (0–100) for each result.

PRD §13 REQ-04.
"""
from __future__ import annotations

from typing import Optional


def _score_result(result: dict, intent: dict) -> float:
    """Compute a relevance score (0–100) for a single result."""
    company: str = (intent.get("company") or "").lower()
    role: str = (intent.get("role") or "").lower()
    location: str = (intent.get("location") or "").lower()
    emp_type: str = (intent.get("employment_type") or "").lower()
    skills: list[str] = [s.lower() for s in (intent.get("skills") or [])]

    title_lower = result.get("title", "").lower()
    snippet_lower = result.get("snippet", "").lower()
    combined = title_lower + " " + snippet_lower

    # Start from domain trust base score (0–40 from verifier)
    score = float(result.get("domain_trust_score", 0.0))

    # Apply verification confidence modifier (e.g. 0 for suspicious, 0.3 for expired)
    confidence_modifier = float(result.get("confidence_modifier", 1.0))

    # ── Content-based boosts ──────────────────────────────────────────────────

    # Role match in title is strongest signal
    if role:
        if role in title_lower:
            score += 30
        elif role in snippet_lower:
            score += 15

    # Company match
    if company:
        if company in title_lower or company in result.get("domain", ""):
            score += 20
        elif company in snippet_lower:
            score += 10

    # Location match
    if location and location in combined:
        score += 8

    # Employment type
    if emp_type and emp_type in combined:
        score += 5

    # Skills match (up to 3)
    matched_skills = sum(1 for s in skills[:3] if s in combined)
    score += matched_skills * 4

    # Apply confidence modifier (suspicious = 0, expired = 0.3)
    score *= confidence_modifier

    return round(min(100.0, max(0.0, score)), 2)


def rank_results(results: list[dict], intent: dict) -> list[dict]:
    """
    Score every result and return them sorted by relevance_score descending.

    Args:
        results: List of verified, normalised result dicts.
        intent: Parsed intent dict from the Intent Agent.

    Returns:
        Sorted list (highest first), with relevance_score added/updated.
    """
    scored = []
    for r in results:
        r["relevance_score"] = _score_result(r, intent)
        scored.append(r)

    ranked = sorted(scored, key=lambda x: x["relevance_score"], reverse=True)
    return ranked[:15]  # cap at 15 results for the UI
