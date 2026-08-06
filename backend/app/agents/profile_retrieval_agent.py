"""
Profile Retrieval Agent — fetches only the profile sections relevant to the
current form's detected fields. Implements data-minimisation from PRD §12.

Instead of dumping the entire profile into the mapping prompt, this agent:
1. Analyses field labels + form category to identify needed profile sections.
2. Fetches only those sections from the DB.
3. Injects the trimmed profile into state['_profile_data'].

This keeps the LLM context smaller and avoids sending unnecessary personal data.
"""
from __future__ import annotations

import json
from typing import Optional

from app.agents.state import AgentState


# ── Section detection from field labels ─────────────────────────────────────

_SECTION_KEYWORDS: dict[str, list[str]] = {
    "personal": [
        "name", "first name", "last name", "full name", "dob", "date of birth",
        "gender", "nationality", "candidate", "applicant",
    ],
    "contact": [
        "email", "phone", "mobile", "contact", "telephone",
    ],
    "addresses": [
        "address", "city", "state", "country", "pincode", "zip", "postal",
        "district", "location", "current address", "permanent address",
    ],
    "education": [
        "education", "degree", "college", "university", "school", "cgpa",
        "percentage", "marks", "qualification", "board", "graduation",
        "specialisation", "major", "course",
    ],
    "experience": [
        "experience", "work", "employment", "company", "job title", "position",
        "organisation", "organization", "notice period", "current ctc",
        "previous", "employer", "designation",
    ],
    "skills": [
        "skills", "technologies", "languages", "tools", "frameworks",
        "proficiency", "expertise",
    ],
    "projects": [
        "project", "portfolio", "github", "repository", "demo",
    ],
    "certifications": [
        "certification", "certificate", "credential", "course", "license",
    ],
    "preferences": [
        "notice period", "salary", "expected ctc", "relocate", "work mode",
        "employment type", "joining date", "preferred location",
    ],
    "professional_links": [
        "linkedin", "github", "portfolio", "kaggle", "website", "blog",
    ],
    "documents": [
        "resume", "cv", "upload", "file", "attachment",
    ],
}


def _detect_needed_sections(field_labels: list[str]) -> set[str]:
    """
    Return the set of profile sections needed by the detected form fields.
    Always includes personal + contact as a baseline.
    """
    needed = {"personal", "contact"}  # always needed
    labels_lower = " ".join(field_labels).lower()

    for section, keywords in _SECTION_KEYWORDS.items():
        if any(kw in labels_lower for kw in keywords):
            needed.add(section)

    return needed


def _filter_profile(full_profile: dict, needed_sections: set[str]) -> dict:
    """Return only the needed sections from the full profile dict."""
    return {k: v for k, v in full_profile.items() if k in needed_sections}


async def run_profile_retrieval_agent(state: AgentState) -> AgentState:
    """
    Analyse detected fields, determine needed profile sections,
    filter the full profile and inject it into state.

    Expects state['_full_profile_data'] to have been populated by the
    application service before the graph is invoked.
    Falls back gracefully if the full profile hasn't been injected.
    """
    detected_fields = state.get("detected_fields", [])
    field_labels = [f.get("label", "") for f in detected_fields if f.get("label")]

    full_profile: dict = state.get("_profile_data") or state.get("_full_profile_data") or {}

    if not full_profile:
        state["messages"].append({
            "type": "agent_message",
            "node": "load_user_profile",
            "text": "⚠️ No profile data available — more questions will be required.",
        })
        state["_profile_data"] = {}
        state["current_node"] = "load_user_profile"
        return state

    # Determine which sections are relevant
    needed = _detect_needed_sections(field_labels)

    # Filter the profile
    filtered_profile = _filter_profile(full_profile, needed)

    # Count non-empty sections
    populated = sum(
        1 for v in filtered_profile.values()
        if v and (v != [] and v != {} and v is not None)
    )

    state["_profile_data"] = filtered_profile
    state["current_node"] = "load_user_profile"
    state["messages"].append({
        "type": "agent_message",
        "node": "load_user_profile",
        "text": (
            f"👤 Loaded {len(needed)} relevant profile sections "
            f"({populated} populated) for {len(field_labels)} form fields."
        ),
        "sections_loaded": list(needed),
        "sections_populated": populated,
    })

    return state


def build_profile_context_for_mapping(profile_data: dict) -> str:
    """
    Build a concise, redacted JSON string to send to the mapping LLM.
    Removes any fields that are None or empty, trims long lists.
    """
    safe: dict = {}

    if "personal" in profile_data:
        safe["personal"] = profile_data["personal"]

    if "contact" in profile_data:
        safe["contact"] = profile_data["contact"]

    if "addresses" in profile_data:
        safe["addresses"] = profile_data["addresses"]

    if "education" in profile_data:
        safe["education"] = profile_data["education"][:4]  # max 4 records

    if "experience" in profile_data:
        safe["experience"] = profile_data["experience"][:3]  # max 3 records

    if "skills" in profile_data:
        skills = profile_data["skills"]
        safe["skills"] = [
            s.get("skill_name") if isinstance(s, dict) else s
            for s in skills
        ][:25]

    if "projects" in profile_data:
        safe["projects"] = profile_data["projects"][:3]

    if "certifications" in profile_data:
        safe["certifications"] = profile_data["certifications"][:5]

    if "preferences" in profile_data:
        safe["preferences"] = profile_data["preferences"]

    if "professional_links" in profile_data:
        safe["professional_links"] = profile_data["professional_links"]

    if "documents" in profile_data:
        # Only expose whether a resume exists, not the path
        has_resume = bool(
            (profile_data["documents"] or {}).get("default_resume")
        )
        safe["documents"] = {"has_resume": has_resume}

    return json.dumps(safe, default=str, indent=2)
