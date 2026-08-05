"""
Generic fallback adapter — handles any website not matched by a specific adapter.
"""
from playwright.async_api import Page, Locator
from typing import Optional

from app.browser.adapters.base import BaseAdapter
from app.agents.state import DetectedField


class GreenhouseAdapter(BaseAdapter):
    """Adapter for Greenhouse ATS (boards.greenhouse.io)"""

    @classmethod
    def detect(cls, url: str) -> bool:
        return "greenhouse.io" in url or "boards.greenhouse" in url

    @classmethod
    async def locate_apply_button(cls, page: Page) -> Optional[Locator]:
        for selector in ["#apply_button", "a:has-text('Apply for this Job')", "button:has-text('Apply')"]:
            try:
                el = page.locator(selector).first
                if await el.is_visible(timeout=2000):
                    return el
            except Exception:
                pass
        return None


class LeverAdapter(BaseAdapter):
    """Adapter for Lever ATS (jobs.lever.co)"""

    @classmethod
    def detect(cls, url: str) -> bool:
        return "lever.co" in url

    @classmethod
    async def locate_apply_button(cls, page: Page) -> Optional[Locator]:
        for selector in [".postings-btn", "a:has-text('Apply for this job')", "a[class*='btn-apply']"]:
            try:
                el = page.locator(selector).first
                if await el.is_visible(timeout=2000):
                    return el
            except Exception:
                pass
        return None


class WorkdayAdapter(BaseAdapter):
    """Adapter for Workday ATS (myworkdayjobs.com)"""

    @classmethod
    def detect(cls, url: str) -> bool:
        return "myworkdayjobs.com" in url or "workday.com" in url

    @classmethod
    async def locate_apply_button(cls, page: Page) -> Optional[Locator]:
        for selector in ["[data-automation-id='applyBtn']", "button:has-text('Apply')"]:
            try:
                el = page.locator(selector).first
                if await el.is_visible(timeout=2000):
                    return el
            except Exception:
                pass
        return None


class GenericAdapter(BaseAdapter):
    """Generic fallback adapter for unrecognized platforms."""

    @classmethod
    def detect(cls, url: str) -> bool:
        return True  # Always matches as fallback


# Registry of adapters in priority order
ADAPTER_REGISTRY: list[type[BaseAdapter]] = [
    GreenhouseAdapter,
    LeverAdapter,
    WorkdayAdapter,
    GenericAdapter,  # Must be last
]


def get_adapter(url: str) -> type[BaseAdapter]:
    """Return the most specific adapter for the given URL."""
    for adapter_cls in ADAPTER_REGISTRY:
        if adapter_cls.detect(url) and adapter_cls is not GenericAdapter:
            return adapter_cls
    return GenericAdapter
