"""
Review Agent — builds a structured user-facing review summary from field mappings,
validation errors and session state. Implements PRD §21 review requirements.

Groups fields by status:
  auto_filled   — confidence >= 0.90, ready
  highlighted   — confidence 0.70-0.89, ready (shown for review)
  user_provided — answered via clarification flow
  low_confidence — confidence 0.40-0.69
  missing       — no value found, required fields block completion
  sensitive     — marked sensitive, not filled
  not_applicable — optional, skipped

Blocks final review if required fields are missing or unresolved.
"""
from __future__ import annotations

from typing import Optional

from app.agents.state import AgentState, FieldMapping


# ── Confidence tiers (PRD §18) ─────────────────────────────────────────────

def _tier(confidence: float, status: str) -> str:
    """Return display tier based on confidence and status."""
    if status in ("sensitive", "requires_user_action"):
        return "sensitive"
    if status == "not_applicable":
        return "not_applicable"
    if status == "missing":
        return "missing"
    if status == "unsupported":
        return "unsupported"
    if status == "ambiguous":
        return "ambiguous"
    # ready / user_provided
    if confidence >= 0.90:
        return "auto_filled"
    if confidence >= 0.70:
        return "highlighted"
    if confidence >= 0.40:
        return "low_confidence"
    return "missing"


def build_review_summary(
    field_mappings: list[FieldMapping],
    validation_errors: list[dict],
    user_answers: list[dict],
) -> dict:
    """
    Build the full review payload for the frontend ReviewPage.

    Returns:
        {
            "can_proceed": bool,
            "blocking_issues": list[str],
            "totals": { auto_filled, highlighted, user_provided, low_confidence,
                        missing, sensitive, unsupported, not_applicable, errors },
            "groups": {
                "auto_filled": [...],
                "highlighted": [...],
                "user_provided": [...],
                "low_confidence": [...],
                "missing": [...],
                "sensitive": [...],
                "unsupported": [...],
                "not_applicable": [...],
            },
            "validation_errors": [...],
        }
    """
    # Build a lookup of user-answered field IDs for cross-reference
    answered_field_ids: set[str] = {
        a.get("field_id", "") for a in user_answers if a.get("field_id")
    }

    groups: dict[str, list[dict]] = {
        "auto_filled": [],
        "highlighted": [],
        "user_provided": [],
        "low_confidence": [],
        "missing": [],
        "sensitive": [],
        "unsupported": [],
        "not_applicable": [],
        "ambiguous": [],
    }

    for m in field_mappings:
        field_id = m.get("field_id", "")
        confidence = float(m.get("confidence", 0.0))
        status = m.get("status", "missing")

        # Promote to user_provided if the user answered this field
        if field_id in answered_field_ids and status != "sensitive":
            tier = "user_provided"
        else:
            tier = _tier(confidence, status)

        entry = {
            "field_id": field_id,
            "field_label": m.get("field_label", ""),
            "profile_key": m.get("profile_key"),
            "value": m.get("value"),
            "confidence": round(confidence, 3),
            "status": status,
            "tier": tier,
            "reason": m.get("reason", ""),
        }
        groups[tier].append(entry)

    # Validation errors keyed by field_id for display
    error_list = [
        {
            "field_id": e.get("field_id", ""),
            "error_type": e.get("error_type", "validation"),
            "message": e.get("error_message", e.get("message", "")),
        }
        for e in validation_errors
    ]

    # Blocking issues: unresolved required fields
    blocking: list[str] = []
    for m in field_mappings:
        constraints = m.get("validation_constraints", {}) or {}
        is_required = constraints.get("required", False) or m.get("is_required", False)
        if is_required and m.get("status") in ("missing", "ambiguous"):
            label = m.get("field_label") or m.get("field_id") or "Unknown field"
            blocking.append(f"Required field not filled: {label}")

    # Unresolved validation errors also block
    if error_list:
        blocking.append(f"{len(error_list)} validation error(s) detected on the form")

    totals = {tier: len(items) for tier, items in groups.items()}
    totals["errors"] = len(error_list)

    return {
        "can_proceed": len(blocking) == 0,
        "blocking_issues": blocking,
        "totals": totals,
        "groups": groups,
        "validation_errors": error_list,
    }


async def run_review_agent(state: AgentState) -> AgentState:
    """Build the review summary and store it in state."""
    field_mappings = state.get("field_mappings", [])
    validation_errors = state.get("validation_errors", [])
    user_answers = state.get("user_answers", [])

    summary = build_review_summary(field_mappings, validation_errors, user_answers)

    state["_review_summary"] = summary  # stored for the router to return
    state["review_ready"] = True
    state["current_node"] = "prepare_review"

    can_proceed = summary["can_proceed"]
    blocking = summary["blocking_issues"]

    state["messages"].append({
        "type": "review_ready",
        "node": "prepare_review",
        "text": (
            "✅ Review ready — application prepared for your approval."
            if can_proceed
            else f"⚠️ Review ready with {len(blocking)} blocking issue(s). Please resolve before proceeding."
        ),
        "can_proceed": can_proceed,
        "blocking_issues": blocking,
        "totals": summary["totals"],
    })

    return state
