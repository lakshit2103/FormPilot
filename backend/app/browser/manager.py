"""
Playwright Browser Manager — launches and manages Chromium browser sessions.
Each user session gets an isolated browser context.
"""
import asyncio
import uuid
from typing import Optional
from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, Playwright
)


class BrowserManager:
    """Manages Playwright browser instances per session."""
    
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _contexts: dict[str, BrowserContext] = {}

    @classmethod
    async def _ensure_started(cls):
        if cls._playwright is None:
            cls._playwright = await async_playwright().start()
        if cls._browser is None:
            cls._browser = await cls._playwright.chromium.launch(
                headless=False,  # Headed mode for MVP (user can see)
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ],
            )

    @classmethod
    async def create_context(cls, session_id: str) -> BrowserContext:
        """Create an isolated browser context for a session."""
        await cls._ensure_started()
        if session_id in cls._contexts:
            return cls._contexts[session_id]
        
        context = await cls._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=False,
            accept_downloads=True,
        )
        cls._contexts[session_id] = context
        return context

    @classmethod
    async def get_page(cls, session_id: str) -> Page:
        """Get or create the active page for a session context."""
        context = await cls.create_context(session_id)
        pages = context.pages
        if pages:
            return pages[-1]
        return await context.new_page()

    @classmethod
    async def close_context(cls, session_id: str):
        """Close and clean up a session's browser context."""
        if session_id in cls._contexts:
            try:
                await cls._contexts[session_id].close()
            except Exception:
                pass
            del cls._contexts[session_id]

    @classmethod
    async def shutdown(cls):
        """Close all contexts and the browser."""
        for sid in list(cls._contexts.keys()):
            await cls.close_context(sid)
        if cls._browser:
            await cls._browser.close()
            cls._browser = None
        if cls._playwright:
            await cls._playwright.stop()
            cls._playwright = None


class LoginDetector:
    """Detects login, OTP, and CAPTCHA requirements on a page."""

    LOGIN_INDICATORS = [
        "input[type='password']",
        "[name='password']",
        "[id*='password']",
        "[placeholder*='password']",
        "button:has-text('Login')",
        "button:has-text('Sign in')",
        "button:has-text('Log in')",
    ]

    CAPTCHA_INDICATORS = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        "[class*='captcha']",
        "[id*='captcha']",
        ".g-recaptcha",
    ]

    OTP_INDICATORS = [
        "[placeholder*='OTP']",
        "[placeholder*='verification code']",
        "[placeholder*='one-time']",
        "[name*='otp']",
        "[id*='otp']",
    ]

    @staticmethod
    async def detect(page: Page) -> dict:
        """Check for login, captcha, and OTP elements."""
        result = {
            "requires_login": False,
            "requires_otp": False,
            "requires_captcha": False,
            "reason": None,
        }

        for selector in LoginDetector.LOGIN_INDICATORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    result["requires_login"] = True
                    result["reason"] = "Login form detected"
                    break
            except Exception:
                pass

        for selector in LoginDetector.CAPTCHA_INDICATORS:
            try:
                el = await page.query_selector(selector)
                if el:
                    result["requires_captcha"] = True
                    result["reason"] = "CAPTCHA detected — please complete manually"
                    break
            except Exception:
                pass

        for selector in LoginDetector.OTP_INDICATORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    result["requires_otp"] = True
                    result["reason"] = "OTP required — please enter manually"
                    break
            except Exception:
                pass

        return result
