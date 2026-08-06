"""
search/ — FormPilot AI form/job discovery service.

Modules:
  query_builder  — generate multi-query variants from intent
  duckduckgo     — DDG search with retry/rate-limit handling
  ranking        — score and rank results
  verifier       — domain trust and safety checks
"""
from .query_builder import build_queries
from .duckduckgo import ddg_search
from .ranking import rank_results
from .verifier import verify_result, VerificationResult

__all__ = [
    "build_queries",
    "ddg_search",
    "rank_results",
    "verify_result",
    "VerificationResult",
]
