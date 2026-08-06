"""
FormPilot AI — Complete LangGraph Workflow Graph.
Implements all nodes from PRD §16.1 with conditional routing.

Nodes:
  parse_request → (search_jobs | open_job_page)
  search_jobs → (show_results | request_job_url)
  open_job_page → (wait_for_login | extract_form | request_job_url)
  extract_form → load_user_profile → map_profile_fields → detect_missing
  detect_missing → (ask_user | fill_form)
  fill_form → validate_form → prepare_review → complete_session
"""
from __future__ import annotations

import asyncio
from typing import Literal
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.intent_agent import run_intent_agent
from app.agents.search_agent import run_search_agent, run_ranking_agent
from app.agents.navigation_agent import run_navigation_agent
from app.agents.extraction_agent import run_extraction_agent
from app.agents.profile_retrieval_agent import run_profile_retrieval_agent
from app.agents.clarification_agent import run_clarification_agent
from app.agents.filling_agent import run_filling_agent
from app.agents.validation_agent import run_validation_agent
from app.agents.review_agent import run_review_agent


# ── Node wrappers ─────────────────────────────────────────────────────────────

async def node_parse_request(state: AgentState) -> AgentState:
    return await run_intent_agent(state)


async def node_search_jobs(state: AgentState) -> AgentState:
    state = await run_search_agent(state)
    return await run_ranking_agent(state)


async def node_show_results(state: AgentState) -> AgentState:
    state["current_node"] = "show_results"
    state["messages"].append({
        "type": "jobs_found",
        "node": "show_results",
        "text": f"🏢 Found {len(state['ranked_results'])} results — please select one to proceed.",
        "count": len(state["ranked_results"]),
    })
    return state


async def node_request_job_url(state: AgentState) -> AgentState:
    state["current_node"] = "request_job_url"
    state["manual_action_required"] = True
    state["manual_action_reason"] = "no_results"
    state["messages"].append({
        "type": "manual_action_required",
        "node": "request_job_url",
        "text": "🔗 No matching results found — please paste the application URL directly.",
        "reason": "no_results",
        "instructions": "Paste the job application or form URL in the field below.",
    })
    return state


async def node_open_job_page(state: AgentState) -> AgentState:
    return await run_navigation_agent(state)


async def node_wait_for_login(state: AgentState) -> AgentState:
    """Pause — user must complete login/CAPTCHA manually, then click Continue."""
    state["current_node"] = "wait_for_login"
    return state


async def node_extract_form(state: AgentState) -> AgentState:
    return await run_extraction_agent(state)


async def node_load_user_profile(state: AgentState) -> AgentState:
    """
    Retrieve only the profile sections relevant to the detected form fields.
    Uses the profile_retrieval_agent for data minimisation (PRD §12).
    """
    return await run_profile_retrieval_agent(state)


async def node_map_profile_fields(state: AgentState) -> AgentState:
    """Map form fields to profile values using the mapping agent."""
    profile_data = state.get("_profile_data") or {}
    from app.agents.mapping_agent import run_mapping_agent
    return await run_mapping_agent(state, profile_data)


async def node_detect_missing(state: AgentState) -> AgentState:
    """Identify fields with missing, ambiguous or low-confidence mappings."""
    return await run_clarification_agent(state)


async def node_ask_user(state: AgentState) -> AgentState:
    """Pause — user must answer clarification questions via API."""
    state["current_node"] = "ask_user"
    state["manual_action_required"] = True
    state["manual_action_reason"] = "missing_information"
    return state


async def node_fill_form(state: AgentState) -> AgentState:
    return await run_filling_agent(state)


async def node_validate_form(state: AgentState) -> AgentState:
    return await run_validation_agent(state)


async def node_prepare_review(state: AgentState) -> AgentState:
    """Build the structured review summary using the review agent."""
    return await run_review_agent(state)


async def node_complete_session(state: AgentState) -> AgentState:
    state["current_node"] = "complete"
    state["messages"].append({
        "type": "session_complete",
        "node": "complete_session",
        "text": (
            "🎉 Review complete — application is ready for your approval. "
            "FormPilot AI has stopped before final submission as required."
        ),
    })
    return state


# ── Conditional routing ───────────────────────────────────────────────────────

def route_intent(
    state: AgentState,
) -> Literal["search_jobs", "open_job_page", "complete_session"]:
    intent = state.get("intent") or {}
    if not isinstance(intent, dict):
        return "search_jobs"
    intent_type = intent.get("intent", "search_and_apply")
    # If a URL was supplied directly, skip search
    if intent_type in ("open_and_apply", "fill_only") or intent.get("job_url"):
        return "open_job_page"
    if intent_type == "continue_application":
        return "complete_session"
    return "search_jobs"


def route_after_search(
    state: AgentState,
) -> Literal["show_results", "request_job_url"]:
    ranked = state.get("ranked_results") or []
    return "show_results" if ranked else "request_job_url"


def route_after_nav(
    state: AgentState,
) -> Literal["wait_for_login", "extract_form", "request_job_url"]:
    if state.get("manual_action_required"):
        reason = state.get("manual_action_reason", "")
        if "login" in reason or "captcha" in reason or "otp" in reason:
            return "wait_for_login"
    if state.get("error_message"):
        return "request_job_url"
    return "extract_form"


def route_after_mapping(
    state: AgentState,
) -> Literal["ask_user", "fill_form"]:
    missing = [
        m for m in state.get("field_mappings", [])
        if m.get("status") in ("missing", "ambiguous")
    ]
    return "ask_user" if missing else "fill_form"


def route_after_validation(
    state: AgentState,
) -> Literal["prepare_review"]:
    # Always go to review — user decides what to do with errors
    return "prepare_review"


# ── Build the graph ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    # Register nodes
    g.add_node("parse_request", node_parse_request)
    g.add_node("search_jobs", node_search_jobs)
    g.add_node("show_results", node_show_results)
    g.add_node("request_job_url", node_request_job_url)
    g.add_node("open_job_page", node_open_job_page)
    g.add_node("wait_for_login", node_wait_for_login)
    g.add_node("extract_form", node_extract_form)
    g.add_node("load_user_profile", node_load_user_profile)
    g.add_node("map_profile_fields", node_map_profile_fields)
    g.add_node("detect_missing", node_detect_missing)
    g.add_node("ask_user", node_ask_user)
    g.add_node("fill_form", node_fill_form)
    g.add_node("validate_form", node_validate_form)
    g.add_node("prepare_review", node_prepare_review)
    g.add_node("complete_session", node_complete_session)

    # Entry point
    g.set_entry_point("parse_request")

    # parse_request → search | open | complete
    g.add_conditional_edges("parse_request", route_intent, {
        "search_jobs": "search_jobs",
        "open_job_page": "open_job_page",
        "complete_session": "complete_session",
    })

    # search_jobs → show_results | request_job_url
    g.add_conditional_edges("search_jobs", route_after_search, {
        "show_results": "show_results",
        "request_job_url": "request_job_url",
    })

    # Both pause states end — user selects via REST API
    g.add_edge("show_results", END)
    g.add_edge("request_job_url", END)

    # Navigation
    g.add_conditional_edges("open_job_page", route_after_nav, {
        "wait_for_login": "wait_for_login",
        "extract_form": "extract_form",
        "request_job_url": "request_job_url",
    })
    g.add_edge("wait_for_login", END)  # Pause — user logs in

    # Form processing pipeline
    g.add_edge("extract_form", "load_user_profile")
    g.add_edge("load_user_profile", "map_profile_fields")
    g.add_edge("map_profile_fields", "detect_missing")
    g.add_conditional_edges("detect_missing", route_after_mapping, {
        "ask_user": "ask_user",
        "fill_form": "fill_form",
    })
    g.add_edge("ask_user", END)  # Pause — user answers

    # Fill → validate → review → complete
    g.add_edge("fill_form", "validate_form")
    g.add_conditional_edges("validate_form", route_after_validation, {
        "prepare_review": "prepare_review",
    })
    g.add_edge("prepare_review", "complete_session")
    g.add_edge("complete_session", END)

    return g


# Compiled graph singleton
_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
    return _compiled_graph
