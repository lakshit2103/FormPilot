"""
Form Filling Agent — fills form fields using only the approved ControlledActions tool set.
Handles text, dropdown, radio, checkbox, date, and file upload fields.
Confirms each action and prevents duplicates.
"""
import asyncio
from datetime import datetime
from typing import Optional

from app.agents.state import AgentState, FieldMapping
from app.browser.manager import BrowserManager
from app.browser.actions import ControlledActions


# Confidence thresholds (FR-38)
AUTO_FILL_THRESHOLD = 0.90
HIGHLIGHT_THRESHOLD = 0.70
ASK_THRESHOLD = 0.40


def _format_date_for_field(value: str, input_type: str) -> str:
    """Convert date string to appropriate format for the field."""
    if not value:
        return value
    try:
        # Try to parse common date formats
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y"):
            try:
                dt = datetime.strptime(value, fmt)
                if input_type == "date":
                    return dt.strftime("%Y-%m-%d")
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue
    except Exception:
        pass
    return value


async def run_filling_agent(state: AgentState) -> AgentState:
    """Fill all ready mappings using controlled Playwright actions."""
    session_id = state.get("browser_session_id") or state["session_id"]
    mappings = state.get("field_mappings", [])
    detected = {f["field_id"]: f for f in state.get("detected_fields", [])}

    try:
        page = await BrowserManager.get_page(session_id)
        actions = ControlledActions(page, session_id)
    except Exception as e:
        state["error_message"] = f"Could not get browser page: {e}"
        return state

    fill_results = []
    low_confidence_fields = []

    for mapping in mappings:
        status = mapping.get("status", "")
        confidence = mapping.get("confidence", 0.0)
        value = mapping.get("value")
        field_id = mapping.get("field_id", "")

        if status != "ready" or not value or not field_id:
            continue

        if confidence < ASK_THRESHOLD:
            state["messages"].append({
                "type": "agent_message",
                "node": "fill_form",
                "text": f"⏭️ Skipping '{mapping.get('field_label', field_id)}' (confidence {confidence:.0%} too low)",
            })
            continue

        if confidence < HIGHLIGHT_THRESHOLD:
            low_confidence_fields.append(field_id)

        field = detected.get(field_id, {})
        field_type = field.get("input_type", "text")

        try:
            result = None

            if field_type == "file":
                # Find the user's default resume path
                resume_path = state.get("_resume_path")
                if resume_path:
                    result = await actions.upload_file(field_id, resume_path)
            elif field_type == "select-one" or field.get("html_tag") == "select":
                result = await actions.select_option(field_id, value)
            elif field_type == "radio":
                result = await actions.select_radio(field_id, value)
            elif field_type == "checkbox":
                checked = value.lower() in ("true", "yes", "1", "on")
                result = await actions.set_checkbox(field_id, checked)
            elif field_type == "date":
                formatted = _format_date_for_field(value, field_type)
                result = await actions.fill_text(field_id, formatted)
            else:
                result = await actions.fill_text(field_id, value)

            if result:
                fill_results.append(result.model_dump())
                if result.success:
                    state["messages"].append({
                        "type": "form_filled",
                        "node": "fill_form",
                        "text": f"✅ Filled '{mapping.get('field_label', field_id)}': {str(value)[:40]}",
                        "field": mapping.get("field_label", field_id),
                        "value": str(value)[:40],
                    })
                else:
                    state["messages"].append({
                        "type": "error",
                        "node": "fill_form",
                        "text": f"⚠️ Could not fill '{mapping.get('field_label', field_id)}': {result.error}",
                        "recoverable": True,
                    })

        except Exception as e:
            state["messages"].append({
                "type": "error",
                "node": "fill_form",
                "text": f"❌ Error filling '{field_id}': {str(e)[:80]}",
                "recoverable": True,
            })

        await asyncio.sleep(0.3)  # human-like pacing

    successful = sum(1 for r in fill_results if r.get("success"))
    state["current_node"] = "fill_form"
    state["messages"].append({
        "type": "agent_message",
        "node": "fill_form",
        "text": f"📝 Filled {successful}/{len(fill_results)} fields successfully",
    })

    # Re-scan for dynamic fields after filling
    if fill_results:
        await asyncio.sleep(1.5)
        state["messages"].append({
            "type": "agent_message",
            "node": "rescan_form",
            "text": "🔄 Re-scanning form for dynamically revealed fields…",
        })
        from app.agents.extraction_agent import extract_form_fields
        current_page_num = 1  # Could be tracked in state
        new_fields = await extract_form_fields(page, page_number=current_page_num)
        new_field_ids = {f["field_id"] for f in new_fields}
        old_field_ids = {f["field_id"] for f in state.get("detected_fields", [])}
        added = new_field_ids - old_field_ids
        if added:
            state["detected_fields"] = new_fields
            state["messages"].append({
                "type": "fields_extracted",
                "node": "rescan_form",
                "text": f"🆕 Found {len(added)} new fields after filling — will process",
                "count": len(added),
            })

    return state
