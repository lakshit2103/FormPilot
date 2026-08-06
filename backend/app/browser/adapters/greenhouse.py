"""
greenhouse.py — Greenhouse.io ATS platform adapter.

Greenhouse uses a standard form structure but with some quirks:
- File upload buttons are styled as <div> wrappers over hidden <input type="file">
- Education and employment sections can be repeated via "Add another" buttons
- Some demographic questions are in a separate section at the end
- Multi-select values use custom checkbox widgets

This adapter handles:
1. Detecting Greenhouse pages.
2. Clicking "Add another education/experience" to expand sections before extraction.
3. Handling custom file upload widgets.
4. Identifying and noting demographic/EEOC sections for human review.
"""
from __future__ import annotations

import asyncio
import logging
from playwright.async_api import Page

from .base import BaseAdapter

logger = logging.getLogger(__name__)


class GreenhouseAdapter(BaseAdapter):
    """Adapter for Greenhouse.io job application pages."""

    DOMAINS = [
        "greenhouse.io",
        "boards.greenhouse.io",
        "job-boards.greenhouse.io",
    ]

    # Selectors for Greenhouse-specific elements
    _ADD_EDUCATION_BTN = "button[data-source='education'], a[data-source='education'], .add_education"
    _ADD_EXPERIENCE_BTN = "button[data-source='employment'], a[data-source='employment'], .add_employment"
    _DEMOGRAPHIC_SECTION = "#demographic_questions, .demographic-questions, [id*='demographic']"
    _FILE_UPLOAD_WRAPPER = ".attach-or-paste input[type='file'], #resume_input, #cover_letter_input"
    _SUBMIT_BTN = "input[type='submit'][value*='Submit'], button[type='submit']"

    async def detect(self, page: Page) -> bool:
        """Return True if this is a Greenhouse application page."""
        try:
            # Greenhouse pages typically have a greenhouse-specific form or script
            has_gh_form = await page.query_selector("#application_form, form#new_application")
            has_gh_script = await page.query_selector("script[src*='greenhouse']")
            return bool(has_gh_form or has_gh_script)
        except Exception:
            return False

    async def prepare(self, page: Page) -> None:
        """
        Pre-extraction setup:
        - Ensure education and experience sections are visible.
        - Note demographic sections for HITL handling.
        """
        logger.info("Greenhouse adapter: preparing page")

        # Wait for the form to load
        try:
            await page.wait_for_selector("#application_form", timeout=5000)
        except Exception:
            pass

        # Click "Add education" if not already showing fields
        await self._expand_section(page, self._ADD_EDUCATION_BTN, "education")

        # Click "Add experience" if not already showing fields
        await self._expand_section(page, self._ADD_EXPERIENCE_BTN, "employment")

    async def _expand_section(self, page: Page, selector: str, section_name: str) -> None:
        """Click an 'Add another' button to expand a repeatable section."""
        try:
            btn = await page.query_selector(selector)
            if btn and await btn.is_visible():
                logger.info("Greenhouse: expanding %s section", section_name)
                await btn.click()
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.debug("Greenhouse: could not expand %s: %s", section_name, e)

    async def handle_file_upload(self, page: Page, field_selector: str, file_path: str) -> bool:
        """
        Handle Greenhouse's custom file upload widget.
        The visible button triggers a hidden <input type='file'>.
        """
        try:
            # Find the hidden file input within the upload wrapper
            file_input = await page.query_selector(self._FILE_UPLOAD_WRAPPER)
            if file_input:
                await file_input.set_input_files(file_path)
                logger.info("Greenhouse: uploaded file via hidden input")
                return True
            # Fallback to the provided selector
            el = await page.query_selector(field_selector)
            if el:
                await el.set_input_files(file_path)
                return True
            return False
        except Exception as e:
            logger.warning("Greenhouse file upload failed: %s", e)
            return False

    def is_demographic_field(self, field_id: str, label: str) -> bool:
        """Return True if a field is part of the demographic/EEOC section (HITL required)."""
        indicators = [
            "demographic", "eeoc", "race", "ethnicity", "veteran", "disability",
            "gender identity", "sexual orientation",
        ]
        combined = (field_id + " " + label).lower()
        return any(kw in combined for kw in indicators)

    async def after_fill(self, page: Page) -> None:
        """Post-fill hook — scroll to confirm no missed sections."""
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.3)
        except Exception:
            pass
