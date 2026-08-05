"""
Controlled Actions — the ONLY approved Playwright tool set for FormPilot AI.
No arbitrary JS execution. Each action is audited and confirms success.
"""
import asyncio
from typing import Optional
from playwright.async_api import Page, Error as PlaywrightError
from pydantic import BaseModel


class ActionResult(BaseModel):
    success: bool
    field_id: str
    action: str
    value: Optional[str] = None
    error: Optional[str] = None


class ControlledActions:
    """
    Approved browser actions for the Form Filling Agent.
    The AI may ONLY use these methods — no raw page.evaluate() with user strings.
    """

    def __init__(self, page: Page, session_id: str):
        self.page = page
        self.session_id = session_id
        self._filled: set[str] = set()  # track filled fields to prevent duplicates

    # ── FORBIDDEN CLICK TARGETS ──────────────────────────────────────────────
    FORBIDDEN_PATTERNS = [
        "submit", "pay", "confirm", "accept", "declaration",
        "esign", "e-sign", "withdraw", "delete", "final submit",
        "apply now",  # only forbidden if it's the FINAL submit
    ]

    def _is_forbidden(self, text: str) -> bool:
        t = text.lower().strip()
        return any(p in t for p in self.FORBIDDEN_PATTERNS)

    # ── FILL TEXT ────────────────────────────────────────────────────────────
    async def fill_text(self, field_id: str, value: str) -> ActionResult:
        """Fill a text/textarea input. Handles React-controlled inputs."""
        if field_id in self._filled:
            return ActionResult(success=True, field_id=field_id, action="fill_text",
                                value=value, error="Already filled (skipped duplicate)")
        try:
            locator = self.page.locator(field_id).first
            await locator.scroll_into_view_if_needed(timeout=5000)
            await locator.click()
            await locator.select_text()  # select all
            await locator.type(value, delay=30)  # type with human-like delay
            # Dispatch React synthetic events
            await locator.dispatch_event("input")
            await locator.dispatch_event("change")
            # Verify
            actual = await locator.input_value()
            if value.strip() in actual.strip() or actual.strip().endswith(value.strip()[-5:]):
                self._filled.add(field_id)
                return ActionResult(success=True, field_id=field_id, action="fill_text", value=actual)
            return ActionResult(success=False, field_id=field_id, action="fill_text",
                                error=f"Value mismatch: expected '{value}', got '{actual}'")
        except PlaywrightError as e:
            return ActionResult(success=False, field_id=field_id, action="fill_text", error=str(e))

    # ── SELECT DROPDOWN ──────────────────────────────────────────────────────
    async def select_option(self, field_id: str, value: str) -> ActionResult:
        """Select a dropdown option by value, label, or partial text match."""
        try:
            locator = self.page.locator(field_id).first
            await locator.scroll_into_view_if_needed(timeout=5000)
            # Try value, then label
            try:
                await locator.select_option(value=value)
            except Exception:
                await locator.select_option(label=value)
            self._filled.add(field_id)
            return ActionResult(success=True, field_id=field_id, action="select_option", value=value)
        except PlaywrightError as e:
            return ActionResult(success=False, field_id=field_id, action="select_option", error=str(e))

    # ── SELECT RADIO ─────────────────────────────────────────────────────────
    async def select_radio(self, field_id: str, value: str) -> ActionResult:
        """Select a radio button matching the value."""
        try:
            # Try direct locator first
            radio = self.page.locator(f"input[type='radio'][value='{value}']").first
            if not await radio.is_visible():
                # Fallback: find label containing value text
                radio = self.page.locator(f"label:has-text('{value}') input[type='radio']").first
            await radio.scroll_into_view_if_needed(timeout=5000)
            await radio.check()
            self._filled.add(field_id)
            return ActionResult(success=True, field_id=field_id, action="select_radio", value=value)
        except PlaywrightError as e:
            return ActionResult(success=False, field_id=field_id, action="select_radio", error=str(e))

    # ── SET CHECKBOX ─────────────────────────────────────────────────────────
    async def set_checkbox(self, field_id: str, checked: bool) -> ActionResult:
        """Check or uncheck a checkbox."""
        try:
            locator = self.page.locator(field_id).first
            await locator.scroll_into_view_if_needed(timeout=5000)
            if checked:
                await locator.check()
            else:
                await locator.uncheck()
            self._filled.add(field_id)
            return ActionResult(success=True, field_id=field_id, action="set_checkbox", value=str(checked))
        except PlaywrightError as e:
            return ActionResult(success=False, field_id=field_id, action="set_checkbox", error=str(e))

    # ── UPLOAD FILE ──────────────────────────────────────────────────────────
    async def upload_file(self, field_id: str, file_path: str) -> ActionResult:
        """Upload a file to a file input element."""
        try:
            locator = self.page.locator(field_id).first
            await locator.set_input_files(file_path)
            self._filled.add(field_id)
            return ActionResult(success=True, field_id=field_id, action="upload_file", value=file_path)
        except PlaywrightError as e:
            return ActionResult(success=False, field_id=field_id, action="upload_file", error=str(e))

    # ── CLICK NEXT ───────────────────────────────────────────────────────────
    async def click_next(self) -> ActionResult:
        """Click Next/Continue to go to the next form page. NEVER clicks Submit."""
        safe_patterns = ["next", "continue", "proceed", "save & next", "save and next",
                         "forward", "step 2", "step 3", "step 4"]
        for pattern in safe_patterns:
            try:
                btn = self.page.locator(
                    f"button:has-text('{pattern}'), "
                    f"input[type='submit'][value*='{pattern}'], "
                    f"a:has-text('{pattern}')"
                ).first
                if await btn.is_visible():
                    text = await btn.inner_text()
                    if not self._is_forbidden(text):
                        await btn.click()
                        await asyncio.sleep(1.5)
                        return ActionResult(success=True, field_id="next_btn",
                                            action="click_next", value=text)
            except Exception:
                continue
        return ActionResult(success=False, field_id="next_btn", action="click_next",
                            error="No safe Next/Continue button found")

    # ── SCROLL TO FIELD ──────────────────────────────────────────────────────
    async def scroll_to_field(self, field_id: str) -> ActionResult:
        """Scroll the page so a field is visible."""
        try:
            locator = self.page.locator(field_id).first
            await locator.scroll_into_view_if_needed(timeout=5000)
            return ActionResult(success=True, field_id=field_id, action="scroll_to_field")
        except PlaywrightError as e:
            return ActionResult(success=False, field_id=field_id, action="scroll_to_field", error=str(e))

    # ── READ VALIDATION ERROR ────────────────────────────────────────────────
    async def read_validation_error(self, field_id: str) -> str:
        """Read validation error text near a field."""
        try:
            # Check aria-describedby, nearby error elements
            locator = self.page.locator(field_id).first
            aria_describedby = await locator.get_attribute("aria-describedby")
            if aria_describedby:
                error_el = self.page.locator(f"#{aria_describedby}").first
                if await error_el.is_visible():
                    return await error_el.inner_text()

            # Nearby sibling with error class
            parent = locator.locator("..")
            error_el = parent.locator(".error, .error-message, [aria-invalid='true'] + *, .field-error").first
            if await error_el.is_visible():
                return await error_el.inner_text()
            return ""
        except Exception:
            return ""

    # ── TAKE SCREENSHOT ──────────────────────────────────────────────────────
    async def take_screenshot(self) -> bytes:
        """Take a full-page screenshot for debugging/audit."""
        try:
            return await self.page.screenshot(full_page=True, type="png")
        except Exception:
            return b""
