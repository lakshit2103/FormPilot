"""
lever.py — Lever.co ATS platform adapter.

Lever uses a React-based form structure with some specific patterns:
- Application forms are embedded in /apply pages
- File upload uses a drag-and-drop zone with a hidden input
- Card-style sections for personal, links, work samples
- Some fields use custom React select components
- Referral and source fields appear at the top

This adapter handles:
1. Detecting Lever application pages.
2. Handling the drag-and-drop file upload widget.
3. Dealing with Lever's custom link fields (LinkedIn, Github, portfolio).
4. Noting the referral/source section for special treatment.
"""
from __future__ import annotations

import asyncio
import logging
from playwright.async_api import Page

from .base import BaseAdapter

logger = logging.getLogger(__name__)


class LeverAdapter(BaseAdapter):
    """Adapter for Lever.co job application pages."""

    DOMAINS = [
        "lever.co",
        "jobs.lever.co",
    ]

    # Lever-specific selectors
    _APPLY_FORM = "form.application-form, #application-form, [data-qa='application-form']"
    _FILE_UPLOAD_ZONE = ".upload-input-container input[type='file'], input[name='resume']"
    _LINK_FIELDS = ".application-form-field input[name*='url'], .application-form-field input[name*='link']"
    _SUBMIT_BTN = "button[type='submit'], button[data-qa='btn-submit']"
    _REFERRAL_FIELD = "select[name='source'], input[name='referredBy']"

    async def detect(self, page: Page) -> bool:
        """Return True if this is a Lever application page."""
        try:
            has_apply = await page.query_selector(self._APPLY_FORM)
            is_lever_url = "lever.co" in page.url
            return bool(has_apply or is_lever_url)
        except Exception:
            return False

    async def prepare(self, page: Page) -> None:
        """
        Pre-extraction setup for Lever pages:
        - Wait for the React form to mount.
        - Ensure all link fields are visible (some collapse by default).
        """
        logger.info("Lever adapter: preparing page at %s", page.url)
        try:
            # Wait for Lever's form to fully render
            await page.wait_for_selector(self._APPLY_FORM, timeout=8000)
            await asyncio.sleep(0.5)
        except Exception:
            logger.debug("Lever: form selector not found — proceeding anyway")

        # Scroll through to trigger any lazy-rendered fields
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(0.3)
            await page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

    async def handle_file_upload(self, page: Page, field_selector: str, file_path: str) -> bool:
        """
        Handle Lever's drag-and-drop file upload zone.
        The visible zone contains a hidden <input type='file'>.
        """
        try:
            # Try the generic resume upload input first
            file_input = await page.query_selector(self._FILE_UPLOAD_ZONE)
            if file_input:
                await file_input.set_input_files(file_path)
                logger.info("Lever: uploaded file via upload zone input")
                await asyncio.sleep(0.5)
                return True
            # Fallback to provided selector
            el = await page.query_selector(field_selector)
            if el:
                await el.set_input_files(file_path)
                return True
            return False
        except Exception as e:
            logger.warning("Lever file upload failed: %s", e)
            return False

    def get_link_field_mapping(self) -> dict[str, str]:
        """
        Return the mapping of profile link types to Lever's expected field names.
        """
        return {
            "linkedin": "linkedin",
            "github": "github",
            "portfolio": "portfolio",
            "twitter": "twitter",
            "website": "other",
        }

    def is_referral_field(self, field_id: str, label: str) -> bool:
        """Return True if this field asks about how the user heard about the role."""
        indicators = ["referr", "source", "heard about", "how did you", "referred by"]
        combined = (field_id + " " + label).lower()
        return any(kw in combined for kw in indicators)

    async def after_fill(self, page: Page) -> None:
        """Post-fill: scroll back to top so the user can review the form."""
        try:
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.3)
        except Exception:
            pass
