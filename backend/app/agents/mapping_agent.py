"""
Profile Mapping Agent — semantically maps detected form fields to user profile data.
Uses OpenAI structured outputs with confidence scoring (FR-34 to FR-38).
"""
import json
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.state import AgentState, DetectedField, FieldMapping


class SingleMapping(BaseModel):
    field_id: str = Field(description="The field's CSS selector / field_id from extraction")
    field_label: str = Field(description="The human-readable label of the field")
    profile_key: Optional[str] = Field(None, description="Dot-notation key in the user profile, e.g. 'personal.full_name'")
    value: Optional[str] = Field(None, description="The value to fill, as a string")
    confidence: float = Field(description="0.0–1.0 confidence score")
    status: str = Field(description="ready | missing | ambiguous | unsupported | sensitive | requires_user_action | not_applicable")
    reason: str = Field(description="Brief explanation of the mapping decision")


class MappingResponse(BaseModel):
    mappings: list[SingleMapping]


MAPPING_SYSTEM_PROMPT = """You are FormPilot AI's form mapping engine.

Given:
1. A list of detected form fields (with labels, types, options, required status)
2. The user's profile data (structured JSON)

For each field:
- Find the best matching profile key
- Determine confidence (0.0–1.0)
- Set status: 
  * "ready" — clear match, fill automatically (confidence ≥ 0.7)
  * "missing" — no profile data available for this field
  * "ambiguous" — multiple possible values (e.g., two phone numbers)
  * "unsupported" — field type/format not supported (e.g., complex CAPTCHA)
  * "sensitive" — field asks for Aadhaar, PAN, bank details, OTP (do NOT fill)
  * "requires_user_action" — user must manually handle this
  * "not_applicable" — field is optional and not needed

Common mappings:
- "Candidate Name", "Full Name", "Applicant Name" → personal.full_name
- "First Name" → personal.first_name
- "Last Name" → personal.last_name
- "Email" → contact.email
- "Phone", "Mobile" → contact.phone
- "Current Address" → addresses[current].address_line_1
- "City" → addresses[current].city
- "State" → addresses[current].state
- "Country" → addresses[current].country
- "Pincode", "ZIP" → addresses[current].postal_code
- "Date of Birth" → personal.date_of_birth
- "Gender" → personal.gender
- "LinkedIn" → professional_links[linkedin].url
- "GitHub" → professional_links[github].url
- "Resume", "CV" → documents.default_resume (type: file upload)
- "Notice Period" → preferences.notice_period
- "Expected Salary" → preferences.minimum_salary
- "Willing to Relocate" → preferences.willing_to_relocate

NEVER fill: Aadhaar, PAN, passport number, bank account, OTP, password, payment info.
Mark those as "sensitive".

For address disambiguation:
- "Current Address" vs "Permanent Address" vs "Correspondence Address" — use the correct type from addresses array.
"""


def _build_profile_context(profile_data: dict) -> str:
    """Build a concise profile JSON string for the LLM."""
    # Only send relevant, non-sensitive fields
    safe_fields = {
        "personal": profile_data.get("personal", {}),
        "contact": profile_data.get("contact", {}),
        "addresses": profile_data.get("addresses", []),
        "education": profile_data.get("education", [])[:3],  # limit
        "experience": profile_data.get("experience", [])[:3],
        "skills": [s.get("skill_name") for s in profile_data.get("skills", [])][:20],
        "preferences": profile_data.get("preferences", {}),
        "professional_links": profile_data.get("professional_links", []),
        "documents": {"has_resume": bool(profile_data.get("documents", {}).get("default_resume"))},
    }
    return json.dumps(safe_fields, default=str, indent=2)


async def run_mapping_agent(state: AgentState, profile_data: dict) -> AgentState:
    """Map detected fields to user profile data using AI semantic matching."""
    fields = state.get("detected_fields", [])
    if not fields:
        state["messages"].append({
            "type": "agent_message",
            "node": "map_profile_fields",
            "text": "⚠️ No fields to map",
        })
        return state

    profile_context = _build_profile_context(profile_data)
    fields_summary = json.dumps([
        {"field_id": f["field_id"], "label": f["label"], "type": f["input_type"],
         "required": f["is_required"], "options": f["available_options"][:10]}
        for f in fields
    ], indent=2)

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from app.core.config import settings

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(MappingResponse)

        result: MappingResponse = await llm.ainvoke([
            SystemMessage(content=MAPPING_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"USER PROFILE:\n{profile_context}\n\n"
                f"FORM FIELDS:\n{fields_summary}"
            )),
        ])

        state["field_mappings"] = [m.model_dump() for m in result.mappings]

    except Exception as e:
        # Fallback: rule-based mapping for common fields
        state["field_mappings"] = _rule_based_mapping(fields, profile_data)
        state["messages"].append({
            "type": "agent_message",
            "node": "map_profile_fields",
            "text": f"⚠️ AI mapping unavailable — using rule-based mapping ({str(e)[:60]})",
        })

    ready = sum(1 for m in state["field_mappings"] if m["status"] == "ready")
    missing = sum(1 for m in state["field_mappings"] if m["status"] == "missing")
    ambiguous = sum(1 for m in state["field_mappings"] if m["status"] == "ambiguous")

    state["current_node"] = "map_profile_fields"
    state["messages"].append({
        "type": "mapping_complete",
        "node": "map_profile_fields",
        "text": f"🗺️ Mapped {len(state['field_mappings'])} fields: {ready} ready, {missing} missing, {ambiguous} ambiguous",
        "ready": ready, "missing": missing, "ambiguous": ambiguous,
    })
    return state


def _rule_based_mapping(fields: list[DetectedField], profile: dict) -> list[dict]:
    """Simple keyword-based fallback mapping."""
    personal = profile.get("personal", {})
    contact = profile.get("contact", {})
    addresses = profile.get("addresses", [])
    current_addr = next((a for a in addresses if a.get("address_type") == "current"), {})
    prefs = profile.get("preferences", {})

    RULES = {
        "full name": ("personal.full_name", personal.get("full_name", "")),
        "first name": ("personal.first_name", personal.get("first_name", "")),
        "last name": ("personal.last_name", personal.get("last_name", "")),
        "email": ("contact.email", contact.get("email", "")),
        "phone": ("contact.phone", contact.get("phone", "")),
        "mobile": ("contact.phone", contact.get("phone", "")),
        "city": ("addresses.current.city", current_addr.get("city", "")),
        "state": ("addresses.current.state", current_addr.get("state", "")),
        "country": ("addresses.current.country", current_addr.get("country", "India")),
        "pincode": ("addresses.current.postal_code", current_addr.get("postal_code", "")),
        "date of birth": ("personal.date_of_birth", str(personal.get("date_of_birth", ""))),
        "gender": ("personal.gender", personal.get("gender", "")),
        "notice period": ("preferences.notice_period", prefs.get("notice_period", "")),
    }

    results = []
    for field in fields:
        label_lower = field["label"].lower()
        matched = False
        for keyword, (profile_key, value) in RULES.items():
            if keyword in label_lower:
                status = "ready" if value else "missing"
                results.append({
                    "field_id": field["field_id"],
                    "field_label": field["label"],
                    "profile_key": profile_key,
                    "value": value if value else None,
                    "confidence": 0.85 if value else 0.0,
                    "status": status,
                    "reason": f"Matched by keyword '{keyword}'",
                })
                matched = True
                break
        if not matched:
            results.append({
                "field_id": field["field_id"],
                "field_label": field["label"],
                "profile_key": None,
                "value": None,
                "confidence": 0.0,
                "status": "missing",
                "reason": "No rule-based match found",
            })
    return results
