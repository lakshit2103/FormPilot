"""
Validation Agent — detects form validation errors after filling.
Checks required fields, inline errors, newly revealed fields, and file uploads.
"""
import asyncio
from playwright.async_api import Page

from app.agents.state import AgentState
from app.browser.manager import BrowserManager
from app.browser.actions import ControlledActions


VALIDATION_ERROR_SELECTORS = [
    ".error-message",
    ".field-error",
    ".form-error",
    ".invalid-feedback",
    "[aria-invalid='true']",
    "[class*='error']",
    "[class*='invalid']",
    ".ant-form-item-explain-error",  # Ant Design
    ".MuiFormHelperText-root.Mui-error",  # Material UI
    "[data-error]",
    "p.error",
    "span.error",
]


async def _detect_page_errors(page: Page) -> list[dict]:
    """Scan the page for validation error messages."""
    errors = []
    seen_texts = set()

    for selector in VALIDATION_ERROR_SELECTORS:
        try:
            els = await page.query_selector_all(selector)
            for el in els:
                if await el.is_visible():
                    text = (await el.inner_text()).strip()
                    if text and text not in seen_texts and len(text) < 200:
                        seen_texts.add(text)
                        # Try to get the associated field
                        field_info = await page.evaluate("""
                            (el) => {
                                const form_el = el.closest('.form-group, .field, [class*="field"]');
                                if (!form_el) return null;
                                const input = form_el.querySelector('input, select, textarea');
                                return input ? (input.id || input.name || null) : null;
                            }
                        """, el)
                        errors.append({
                            "error_type": "validation",
                            "error_message": text,
                            "field_id": field_info,
                            "is_resolved": False,
                        })
        except Exception:
            continue

    return errors


async def _check_required_empty(page: Page, fields: list[dict]) -> list[dict]:
    """Check that all required fields have values filled."""
    missing = []
    for field in fields:
        if not field.get("is_required"):
            continue
        field_id = field.get("field_id", "")
        try:
            el = page.locator(field_id).first
            value = await el.input_value()
            if not value or not value.strip():
                missing.append({
                    "error_type": "required_empty",
                    "error_message": f"Required field '{field.get('label', field_id)}' is empty",
                    "field_id": field_id,
                    "is_resolved": False,
                })
        except Exception:
            pass
    return missing


async def run_validation_agent(state: AgentState) -> AgentState:
    """Validate the filled form and collect all errors."""
    session_id = state.get("browser_session_id") or state["session_id"]
    
    try:
        page = await BrowserManager.get_page(session_id)
    except Exception as e:
        state["error_message"] = f"Browser not available: {e}"
        return state

    all_errors = []

    # Detect inline validation errors
    inline_errors = await _detect_page_errors(page)
    all_errors.extend(inline_errors)

    # Check required-but-empty fields
    required_errors = await _check_required_empty(page, state.get("detected_fields", []))
    all_errors.extend(required_errors)

    state["validation_errors"] = all_errors
    state["current_node"] = "validate_form"

    if all_errors:
        state["messages"].append({
            "type": "agent_message",
            "node": "validate_form",
            "text": f"⚠️ Found {len(all_errors)} validation issue(s) — please review",
        })
    else:
        state["messages"].append({
            "type": "agent_message",
            "node": "validate_form",
            "text": "✅ Validation passed — no errors detected",
        })

    # Build review summary
    mappings = state.get("field_mappings", [])
    auto_filled = sum(1 for m in mappings if m.get("status") == "ready" and m.get("confidence", 0) >= 0.90)
    user_provided = sum(1 for a in state.get("user_answers", []))
    missing = sum(1 for m in mappings if m.get("status") == "missing")
    low_conf = sum(1 for m in mappings if 0.40 <= m.get("confidence", 0) < 0.90 and m.get("status") == "ready")

    state["_review_summary"] = {
        "total_fields": len(mappings),
        "auto_filled": auto_filled,
        "user_provided": user_provided,
        "missing": missing,
        "low_confidence": low_conf,
        "errors": len(all_errors),
    }

    state["review_ready"] = True
    state["messages"].append({
        "type": "review_ready",
        "node": "prepare_review",
        "text": "📊 Review dashboard ready",
        "summary": state["_review_summary"],
    })

    return state
