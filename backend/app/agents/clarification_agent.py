"""
Clarification Agent — identifies missing/ambiguous fields and generates grouped questions.
Validates answers and manages save-to-profile consent flow.
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.agents.state import AgentState, MissingQuestion


class QuestionGroup(BaseModel):
    group_title: str
    questions: list[dict]


VALIDATION_RULES: dict[str, dict] = {
    "email": {"format": "email", "pattern": r"[^@]+@[^@]+\.[^@]+"},
    "phone": {"format": "phone", "min_length": 7, "max_length": 15},
    "date": {"format": "date", "hint": "YYYY-MM-DD"},
    "number": {"format": "number"},
    "salary": {"format": "number", "hint": "Annual salary in INR"},
}


def _get_field_hint(field_type: str, constraints: dict) -> str:
    """Generate a helpful hint for the user based on field type."""
    if field_type in ("email",):
        return "Format: user@example.com"
    if field_type in ("tel", "phone"):
        return "Format: +91 99999 99999"
    if field_type == "date":
        return "Format: YYYY-MM-DD"
    if field_type == "number":
        if constraints.get("min") and constraints.get("max"):
            return f"Range: {constraints['min']} – {constraints['max']}"
    if constraints.get("maxLength"):
        return f"Max {constraints['maxLength']} characters"
    return ""


async def run_clarification_agent(state: AgentState) -> AgentState:
    """Generate grouped questions for missing and ambiguous fields."""
    mappings = state.get("field_mappings", [])
    detected = {f["field_id"]: f for f in state.get("detected_fields", [])}

    questions: list[MissingQuestion] = []

    for mapping in mappings:
        if mapping["status"] not in ("missing", "ambiguous"):
            continue
        if not mapping.get("field_id"):
            continue

        field = detected.get(mapping["field_id"], {})
        label = mapping.get("field_label") or field.get("label", "Unknown field")
        field_type = field.get("input_type", "text")
        constraints = field.get("validation_constraints", {})
        options = field.get("available_options", [])
        is_required = field.get("is_required", False)

        question_text = f"Please provide your **{label}**"
        if mapping["status"] == "ambiguous":
            question_text = f"Multiple values found for **{label}** — which should be used?"

        hint = _get_field_hint(field_type, constraints)
        if options:
            hint = f"Choose from: {', '.join(options[:8])}"

        questions.append({
            "question_id": mapping["field_id"],
            "field_id": mapping["field_id"],
            "question": question_text,
            "field_requirements": {
                "type": field_type,
                "hint": hint,
                "required": is_required,
                "options": options,
                "constraints": constraints,
            },
            "answer": None,
            "save_to_profile": "use_once",
        })

    state["missing_questions"] = questions
    state["current_node"] = "detect_missing_fields"

    if questions:
        required_count = sum(
            1 for q in questions if q["field_requirements"].get("required", False)
        )
        state["messages"].append({
            "type": "questions_ready",
            "node": "detect_missing_fields",
            "text": f"❓ {len(questions)} questions ({required_count} required) — waiting for your answers",
            "count": len(questions),
        })
    else:
        state["messages"].append({
            "type": "agent_message",
            "node": "detect_missing_fields",
            "text": "✅ All required fields have profile data — proceeding to fill",
        })

    return state


def validate_answer(value: str, field_requirements: dict) -> Optional[str]:
    """Validate a user-provided answer. Returns error message or None."""
    field_type = field_requirements.get("type", "text")
    constraints = field_requirements.get("constraints", {})

    if not value and field_requirements.get("required"):
        return "This field is required"

    if not value:
        return None

    if field_type == "email":
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return "Please enter a valid email address"

    if field_type in ("tel", "phone"):
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) < 7:
            return "Phone number appears too short"

    if field_type == "number":
        try:
            num = float(value.replace(",", ""))
            if "min" in constraints and num < float(constraints["min"]):
                return f"Value must be at least {constraints['min']}"
            if "max" in constraints and num > float(constraints["max"]):
                return f"Value must be at most {constraints['max']}"
        except ValueError:
            return "Please enter a valid number"

    if "maxLength" in constraints and len(value) > int(constraints["maxLength"]):
        return f"Maximum {constraints['maxLength']} characters allowed"

    options = field_requirements.get("options", [])
    if options and value not in options:
        # Try case-insensitive match
        if not any(o.lower() == value.lower() for o in options):
            return f"Please choose one of: {', '.join(options[:5])}"

    return None


async def process_answers(state: AgentState, answers: list[dict]) -> AgentState:
    """Apply user answers to field mappings and update state."""
    answer_map = {a["question_id"]: a for a in answers}

    for q in state.get("missing_questions", []):
        qid = q["question_id"]
        if qid in answer_map:
            answer = answer_map[qid]
            q["answer"] = answer.get("answer_value", "")
            q["save_to_profile"] = answer.get("save_to_profile", "use_once")

    # Apply answers to field mappings
    for mapping in state.get("field_mappings", []):
        if mapping["status"] in ("missing", "ambiguous"):
            fid = mapping["field_id"]
            if fid in answer_map:
                mapping["value"] = answer_map[fid].get("answer_value", "")
                mapping["status"] = "ready"
                mapping["confidence"] = 1.0  # user-provided = highest confidence

    state["user_answers"] = answers
    state["current_node"] = "validate_answers"
    state["messages"].append({
        "type": "agent_message",
        "node": "validate_answers",
        "text": f"✅ {len(answers)} answers received — proceeding to form fill",
    })
    return state
