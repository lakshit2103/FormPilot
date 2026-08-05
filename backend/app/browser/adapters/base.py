"""
Base adapter interface for platform-specific form handling.
"""
from abc import ABC, abstractmethod
from playwright.async_api import Page, Locator
from typing import Optional
from app.agents.state import DetectedField
from app.browser.actions import ActionResult


class BaseAdapter(ABC):
    """
    Platform adapter interface. Each ATS (Greenhouse, Lever, Workday, etc.)
    may have a specific implementation to improve field extraction and filling.
    """

    @classmethod
    @abstractmethod
    def detect(cls, url: str) -> bool:
        """Return True if this adapter should handle the given URL."""
        ...

    @classmethod
    async def locate_apply_button(cls, page: Page) -> Optional[Locator]:
        """Find the Apply button on the job listing page."""
        return None

    @classmethod
    async def extract_fields(cls, page: Page) -> list[DetectedField]:
        """Extract form fields specific to this platform."""
        from app.agents.extraction_agent import extract_form_fields
        return await extract_form_fields(page)

    @classmethod
    async def fill_field(cls, page: Page, field: DetectedField, value: str) -> ActionResult:
        """Fill a single field using platform-specific logic."""
        from app.browser.actions import ControlledActions
        actions = ControlledActions(page, "adapter")
        if field["input_type"] == "select-one":
            return await actions.select_option(field["field_id"], value)
        return await actions.fill_text(field["field_id"], value)
