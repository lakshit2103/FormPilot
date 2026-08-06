"""
query_builder.py — generate diverse DuckDuckGo search queries from structured intent.

Given an intent dict (extracted by the Intent Agent), produces up to 5 distinct
queries designed to maximise the chance of finding the official job/form page.

PRD §13 REQ-03.
"""
from __future__ import annotations

from typing import Optional


def build_queries(intent: dict) -> list[str]:
    """
    Generate up to 5 search query variants from a parsed intent.

    Args:
        intent: dict with keys: company, role, location, employment_type,
                skills, job_url, form_category (optional)

    Returns:
        List of non-empty, deduplicated query strings.
    """
    company: str = (intent.get("company") or "").strip()
    role: str = (intent.get("role") or "").strip()
    location: str = (intent.get("location") or "").strip()
    skills: list[str] = intent.get("skills") or []
    emp_type: str = (intent.get("employment_type") or "job").strip().lower()
    form_category: str = (intent.get("form_category") or "job").strip().lower()

    # Normalise employment type label for queries
    type_label = {
        "internship": "internship",
        "full-time": "job",
        "part-time": "part-time job",
        "contract": "contract job",
        "freelance": "freelance",
    }.get(emp_type, "job")

    queries: list[str] = []

    # ── Query 1: Most specific — company + role + type ──────────────────────
    if company and role:
        q = f'"{company}" "{role}" {type_label}'
        if location:
            q += f" {location}"
        queries.append(q)
    elif role:
        q = f'"{role}" {type_label}'
        if location:
            q += f" {location}"
        queries.append(q)

    # ── Query 2: Official career page ────────────────────────────────────────
    if company:
        slug = company.lower().replace(" ", "").replace(",", "").replace(".", "")
        if role:
            queries.append(f'site:{slug}.com careers "{role}"')
        else:
            queries.append(f'site:{slug}.com careers apply')

    # ── Query 3: Company + apply intent ─────────────────────────────────────
    if company and role:
        queries.append(f'"{company}" "{role}" apply online {location}'.strip())
    elif company:
        queries.append(f'"{company}" {type_label} apply {location}'.strip())

    # ── Query 4: Role + top skill ────────────────────────────────────────────
    if role and skills:
        queries.append(f'"{role}" "{skills[0]}" {type_label} apply {location}'.strip())

    # ── Query 5: Broad fallback ──────────────────────────────────────────────
    if role:
        queries.append(f'{role} {type_label} application form {location}'.strip())
    elif company:
        queries.append(f'{company} {type_label} application {location}'.strip())

    # Deduplicate and strip empty
    seen: set[str] = set()
    result: list[str] = []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            result.append(q)

    return result[:5]
