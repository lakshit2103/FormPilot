"""
verifier.py — domain trust, safety, and URL verification for search results.

For each candidate result, computes:
  - domain_trust_score  (0-40) — is this an official or trusted ATS domain?
  - content_safety      — checks for suspicious/spam patterns
  - status              — available | expired | suspicious | unverified
  - source_type         — official | trusted_third_party | aggregator | unverified | suspicious

PRD §13 REQ-04, REQ-05.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


# ── Trusted ATS / job-platform domains ───────────────────────────────────────

TRUSTED_ATS_DOMAINS: frozenset[str] = frozenset({
    "greenhouse.io",
    "lever.co",
    "workday.com",
    "myworkdayjobs.com",
    "taleo.net",
    "icims.com",
    "smartrecruiters.com",
    "bamboohr.com",
    "jobvite.com",
    "ashbyhq.com",
    "recruitee.com",
})

TRUSTED_AGGREGATORS: frozenset[str] = frozenset({
    "linkedin.com",
    "naukri.com",
    "instahyre.com",
    "wellfound.com",
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "shine.com",
    "freshersworld.com",
    "internshala.com",
})

# Patterns that strongly suggest spam / scam listings
SUSPICIOUS_SNIPPET_PATTERNS: tuple[str, ...] = (
    "earn per day",
    "no experience required unlimited",
    "work from home scam",
    "guaranteed income",
    "click here to earn",
    "data entry typing work",
    "earn ₹",
    "earn rs.",
    "mlm",
    "pyramid scheme",
)

# Patterns suggesting the position is closed / expired
EXPIRED_SNIPPET_PATTERNS: tuple[str, ...] = (
    "no longer accepting",
    "position has been filled",
    "position filled",
    "application closed",
    "this job is no longer available",
    "listing has expired",
    "this posting has expired",
)

# Title patterns that indicate non-job pages
NON_JOB_TITLE_PATTERNS: tuple[str, ...] = (
    "blog", "news", "article", "review", "salary guide", "interview tips",
    "how to", "what is", "best companies", "top 10",
)


@dataclass
class VerificationResult:
    """Result of verifying a single search result."""
    domain: str
    source_type: str          # official | trusted_third_party | aggregator | unverified | suspicious
    is_official: bool
    domain_trust_score: float  # 0–40
    job_status: str            # available | expired | suspicious | unverified
    is_suspicious: bool
    confidence_modifier: float  # multiplier applied to relevance score (0.0–1.2)
    flags: list[str] = field(default_factory=list)


def verify_result(
    url: str,
    title: str,
    snippet: str,
    company: Optional[str] = None,
) -> VerificationResult:
    """
    Verify a single search result and return a VerificationResult.

    Args:
        url: The result URL.
        title: The page title from search results.
        snippet: The search snippet/description.
        company: The target company name (from user intent), if known.

    Returns:
        VerificationResult with domain trust, status and scoring modifiers.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
    except Exception:
        domain = ""

    title_lower = title.lower()
    snippet_lower = snippet.lower()

    flags: list[str] = []
    is_official = False
    domain_trust_score = 0.0
    source_type = "unverified"
    is_suspicious = False
    job_status = "available"
    confidence_modifier = 1.0

    # ── Official company career page detection ────────────────────────────────
    if company:
        company_slug = (
            company.lower()
            .replace(" ", "")
            .replace(",", "")
            .replace(".", "")
            .replace("-", "")
        )
        # Check if company name appears in domain
        if len(company_slug) >= 4 and (
            company_slug in domain or domain.startswith(company_slug[:6])
        ):
            is_official = True
            source_type = "official"
            domain_trust_score += 40
            flags.append("official_career_page")

    # ── Trusted ATS detection ─────────────────────────────────────────────────
    for ats in TRUSTED_ATS_DOMAINS:
        if ats in domain:
            source_type = "trusted_third_party" if not is_official else source_type
            domain_trust_score += 20
            flags.append(f"trusted_ats:{ats}")
            break

    # ── Job aggregator detection ──────────────────────────────────────────────
    for agg in TRUSTED_AGGREGATORS:
        if agg in domain:
            if source_type == "unverified":
                source_type = "aggregator"
            domain_trust_score += 8
            flags.append(f"aggregator:{agg}")
            break

    # ── Suspicious content check ──────────────────────────────────────────────
    if any(p in snippet_lower for p in SUSPICIOUS_SNIPPET_PATTERNS):
        is_suspicious = True
        job_status = "suspicious"
        source_type = "suspicious"
        confidence_modifier = 0.0
        domain_trust_score = 0.0
        flags.append("suspicious_content")

    # ── Expired / closed check ────────────────────────────────────────────────
    elif any(p in snippet_lower or p in title_lower for p in EXPIRED_SNIPPET_PATTERNS):
        job_status = "expired"
        confidence_modifier = 0.3
        flags.append("expired_listing")

    # ── Non-job page penalty ──────────────────────────────────────────────────
    if any(p in title_lower for p in NON_JOB_TITLE_PATTERNS):
        confidence_modifier *= 0.5
        flags.append("non_job_page")

    return VerificationResult(
        domain=domain,
        source_type=source_type,
        is_official=is_official,
        domain_trust_score=min(40.0, domain_trust_score),
        job_status=job_status,
        is_suspicious=is_suspicious,
        confidence_modifier=confidence_modifier,
        flags=flags,
    )


def verify_results_batch(
    results: list[dict],
    company: Optional[str] = None,
) -> list[dict]:
    """
    Verify a list of normalised search results in-place.
    Adds verification fields to each result dict and returns the list.
    """
    for r in results:
        vr = verify_result(
            url=r.get("url", ""),
            title=r.get("title", ""),
            snippet=r.get("snippet", ""),
            company=company,
        )
        r["domain"] = vr.domain
        r["source_type"] = vr.source_type
        r["is_official"] = vr.is_official
        r["domain_trust_score"] = vr.domain_trust_score
        r["job_status"] = vr.job_status
        r["is_suspicious"] = vr.is_suspicious
        r["confidence_modifier"] = vr.confidence_modifier
        r["verification_flags"] = vr.flags

    return results
