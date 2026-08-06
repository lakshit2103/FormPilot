"""
Search Agent — orchestrates the form/job discovery pipeline using the search/ module.

Delegates to:
  app.search.query_builder  — generates DDG query variants
  app.search.duckduckgo     — executes searches with retry/rate-limit handling
  app.search.verifier       — classifies and validates each result
  app.search.ranking        — scores and ranks results by relevance

PRD §13 REQ-01 to REQ-06.
"""
from __future__ import annotations

import logging

from app.agents.state import AgentState
from app.search.query_builder import build_queries
from app.search.duckduckgo import ddg_multi_search
from app.search.verifier import verify_results_batch
from app.search.ranking import rank_results

logger = logging.getLogger(__name__)


async def run_search_agent(state: AgentState) -> AgentState:
    """
    Phase 1 of discovery: generate queries and retrieve raw results.
    Adds verified, normalised results to state['raw_results'].
    """
    intent: dict = state.get("intent") or {}
    if not isinstance(intent, dict):
        intent = {}

    # Build query variants
    queries = build_queries(intent)
    state["search_queries"] = queries

    state["messages"].append({
        "type": "agent_message",
        "node": "search_jobs",
        "text": f"🔍 Running {len(queries)} search queries…",
        "queries": queries,
    })

    if not queries:
        state["raw_results"] = []
        state["messages"].append({
            "type": "agent_message",
            "node": "search_jobs",
            "text": "⚠️ Could not build search queries — please provide a URL directly.",
        })
        return state

    # Execute multi-query search with deduplication
    raw_results = await ddg_multi_search(
        queries,
        max_results_per_query=8,
        inter_query_delay=1.5,
    )

    # Verify and classify each result
    company = intent.get("company")
    verified_results = verify_results_batch(raw_results, company=company)

    state["raw_results"] = verified_results
    state["current_node"] = "search_jobs"
    state["messages"].append({
        "type": "agent_message",
        "node": "search_jobs",
        "text": f"✅ Found {len(verified_results)} unique results across {len(queries)} queries.",
        "count": len(verified_results),
    })

    if not verified_results:
        state["messages"].append({
            "type": "agent_message",
            "node": "search_jobs",
            "text": "⚠️ No results found. You can provide the form URL directly.",
        })

    return state


async def run_ranking_agent(state: AgentState) -> AgentState:
    """
    Phase 2 of discovery: rank the verified raw results by intent relevance.
    Adds ranked results to state['ranked_results'].
    """
    intent: dict = state.get("intent") or {}
    raw_results: list[dict] = state.get("raw_results") or []

    if not raw_results:
        state["ranked_results"] = []
        state["current_node"] = "rank_results"
        return state

    ranked = rank_results(raw_results, intent)
    state["ranked_results"] = ranked
    state["current_node"] = "rank_results"

    top = ranked[0] if ranked else None
    state["messages"].append({
        "type": "agent_message",
        "node": "rank_results",
        "text": (
            f"📊 Ranked {len(ranked)} results. "
            f"Top match: {top['title'][:60] if top else 'None'} "
            f"(score: {top['relevance_score'] if top else 0})"
        ),
        "count": len(ranked),
        "top_score": top["relevance_score"] if top else 0,
    })

    return state
