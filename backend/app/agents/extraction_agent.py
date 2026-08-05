"""
Form Extraction Agent — extracts all form fields from the current Playwright page.
Implements label priority from PRD FR-27. Triggers re-scan after dynamic changes.
"""
import asyncio
import json
from typing import Optional
from playwright.async_api import Page

from app.agents.state import DetectedField, AgentState
from app.browser.manager import BrowserManager


LABEL_EXTRACTION_JS = """
() => {
  const fields = [];
  const inputs = document.querySelectorAll(
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select, [role="combobox"], [role="listbox"]'
  );
  
  function getLabel(el) {
    // Priority: label > aria-label > aria-labelledby > placeholder > name > id > nearby text
    if (el.id) {
      const lbl = document.querySelector(`label[for="${el.id}"]`);
      if (lbl) return lbl.innerText.trim();
    }
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').trim();
    if (el.getAttribute('aria-labelledby')) {
      const lblEl = document.getElementById(el.getAttribute('aria-labelledby'));
      if (lblEl) return lblEl.innerText.trim();
    }
    if (el.placeholder) return el.placeholder;
    if (el.name) return el.name;
    if (el.id) return el.id;
    // Nearby text: check parent container
    const parent = el.closest('.field, .form-group, .form-control, [class*="field"], [class*="input"]');
    if (parent) {
      const label = parent.querySelector('label, .label, [class*="label"]');
      if (label) return label.innerText.trim();
    }
    return '';
  }

  function getSectionHeading(el) {
    let current = el.parentElement;
    for (let i = 0; i < 5 && current; i++) {
      const h = current.querySelector('h1, h2, h3, h4, legend, [class*="section-title"]');
      if (h) return h.innerText.trim();
      current = current.parentElement;
    }
    return '';
  }

  function getOptions(el) {
    if (el.tagName === 'SELECT') {
      return Array.from(el.options).map(o => o.text.trim()).filter(Boolean);
    }
    return [];
  }

  inputs.forEach((el, idx) => {
    const rect = el.getBoundingClientRect();
    const isVisible = rect.width > 0 && rect.height > 0 && el.offsetParent !== null;
    const isEnabled = !el.disabled && !el.readOnly;
    
    const fieldId = el.id || el.name || `field_${idx}`;
    const fieldSelector = el.id ? `#${CSS.escape(el.id)}` : 
                          el.name ? `[name="${CSS.escape(el.name)}"]` : 
                          `[data-field-index="${idx}"]`;
    if (el.id === undefined || el.name === undefined) el.dataset.fieldIndex = idx;
    
    const validationConstraints = {};
    if (el.required) validationConstraints.required = true;
    if (el.minLength > 0) validationConstraints.minLength = el.minLength;
    if (el.maxLength > 0 && el.maxLength < 524288) validationConstraints.maxLength = el.maxLength;
    if (el.pattern) validationConstraints.pattern = el.pattern;
    if (el.min) validationConstraints.min = el.min;
    if (el.max) validationConstraints.max = el.max;
    if (el.type === 'email') validationConstraints.format = 'email';
    if (el.type === 'tel') validationConstraints.format = 'phone';
    if (el.type === 'number') validationConstraints.format = 'number';
    
    fields.push({
      field_id: fieldSelector,
      html_tag: el.tagName.toLowerCase(),
      input_type: el.type || el.tagName.toLowerCase(),
      label: getLabel(el),
      placeholder: el.placeholder || '',
      is_required: el.required || el.getAttribute('aria-required') === 'true',
      is_visible: isVisible,
      is_enabled: isEnabled,
      available_options: getOptions(el),
      current_value: el.value || '',
      section_name: getSectionHeading(el),
      validation_constraints: validationConstraints,
    });
  });
  
  return fields;
}
"""


async def extract_form_fields(page: Page, page_number: int = 1) -> list[DetectedField]:
    """Extract all form fields from the current page using JavaScript injection."""
    try:
        raw_fields = await page.evaluate(LABEL_EXTRACTION_JS)
        fields: list[DetectedField] = []
        for i, f in enumerate(raw_fields):
            fields.append({
                "field_id": f.get("field_id", f"field_{i}"),
                "html_tag": f.get("html_tag", "input"),
                "input_type": f.get("input_type", "text"),
                "label": f.get("label", ""),
                "placeholder": f.get("placeholder", ""),
                "is_required": f.get("is_required", False),
                "is_visible": f.get("is_visible", True),
                "is_enabled": f.get("is_enabled", True),
                "available_options": f.get("available_options", []),
                "current_value": f.get("current_value", ""),
                "page_number": page_number,
                "section_name": f.get("section_name", ""),
                "validation_constraints": f.get("validation_constraints", {}),
            })
        return [f for f in fields if f["is_visible"] and f["is_enabled"]]
    except Exception as e:
        return []


async def run_extraction_agent(state: AgentState) -> AgentState:
    """Extract form fields from the active Playwright page."""
    session_id = state["browser_session_id"] or state["session_id"]
    
    try:
        page = await BrowserManager.get_page(session_id)
        current_url = page.url
        state["current_url"] = current_url
        
        fields = await extract_form_fields(page, page_number=1)
        state["detected_fields"] = fields
        state["current_node"] = "extract_form"
        state["messages"].append({
            "type": "fields_extracted",
            "node": "extract_form",
            "text": f"📋 Extracted {len(fields)} form fields",
            "count": len(fields),
        })
    except Exception as e:
        state["error_message"] = f"Field extraction failed: {str(e)}"
        state["messages"].append({
            "type": "error",
            "node": "extract_form",
            "text": f"❌ Could not extract form fields: {str(e)}",
        })
    
    return state
