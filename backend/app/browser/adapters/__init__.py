"""
browser/adapters/__init__.py — Platform adapter registry.

Adapters handle ATS-specific behaviour: custom dropdowns, repeated sections,
multi-step navigation, file upload widgets.

Each adapter exposes:
  DOMAINS  — list of domain fragments that identify this platform
  detect(page) → bool  — returns True if this adapter handles the current page
  prepare(page)        — optional setup before extraction
  after_fill(page)     — optional hook after all fills complete

Usage:
    from app.browser.adapters import get_adapter
    adapter = await get_adapter(page)
    if adapter:
        await adapter.prepare(page)
"""
from __future__ import annotations

from typing import Optional, Type
from playwright.async_api import Page

from .base import BaseAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter


# Registry — ordered by specificity (more specific first)
_ADAPTERS: list[Type[BaseAdapter]] = [
    GreenhouseAdapter,
    LeverAdapter,
]


async def get_adapter(page: Page) -> Optional[BaseAdapter]:
    """
    Return the first matching adapter for the current page URL,
    or None if the page should use the generic extraction engine.
    """
    current_url = page.url.lower()
    for adapter_cls in _ADAPTERS:
        if any(domain in current_url for domain in adapter_cls.DOMAINS):
            adapter = adapter_cls()
            if await adapter.detect(page):
                return adapter
    return None


__all__ = ["get_adapter", "BaseAdapter", "GreenhouseAdapter", "LeverAdapter"]
