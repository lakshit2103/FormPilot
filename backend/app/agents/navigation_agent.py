"""
Navigation Agent — opens job pages, locates Apply buttons, detects auth requirements.
Manages the browser session lifecycle.
"""
import asyncio
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.agents.state import AgentState
from app.browser.manager import BrowserManager, LoginDetector


APPLY_BUTTON_SELECTORS = [
    "a:has-text('Apply Now')",
    "a:has-text('Apply for this job')",
    "button:has-text('Apply Now')",
    "button:has-text('Apply for this job')",
    "button:has-text('Apply')",
    "a:has-text('Apply')",
    "[data-test*='apply']",
    "[id*='apply']",
    "[class*='apply-btn']",
    "a[href*='/apply']",
]


async def _find_apply_button(page: Page) -> Optional[str]:
    """Locate the Apply button on a job listing page."""
    for selector in APPLY_BUTTON_SELECTORS:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=2000):
                text = await el.inner_text()
                return selector
        except Exception:
            continue
    return None


async def run_navigation_agent(state: AgentState) -> AgentState:
    """Open the selected job URL and navigate to the application form."""
    selected_job = state.get("selected_job")
    if not selected_job:
        state["error_message"] = "No job selected"
        return state

    url = selected_job.get("url", "")
    session_id = state["session_id"]
    
    state["messages"].append({
        "type": "browser_opened",
        "node": "open_job_page",
        "text": f"🌐 Opening: {url[:80]}…",
        "url": url,
    })

    try:
        page = await BrowserManager.get_page(session_id)
        state["browser_session_id"] = session_id

        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # allow JS to render
        
        state["current_url"] = page.url

        # Detect auth requirements
        auth_state = await LoginDetector.detect(page)
        
        if auth_state["requires_captcha"]:
            state["manual_action_required"] = True
            state["manual_action_reason"] = "CAPTCHA detected — please complete it in the browser window"
            state["current_node"] = "wait_for_user"
            state["messages"].append({
                "type": "manual_action_required",
                "node": "open_job_page",
                "text": "🔐 CAPTCHA detected — please complete it manually, then click Continue",
                "reason": "captcha",
                "instructions": "Complete the CAPTCHA in the browser window, then click 'Continue' in FormPilot AI.",
            })
            return state

        if auth_state["requires_login"]:
            state["manual_action_required"] = True
            state["manual_action_reason"] = "Login required — please sign in manually"
            state["current_node"] = "wait_for_login"
            state["messages"].append({
                "type": "manual_action_required",
                "node": "open_job_page",
                "text": "🔑 Login required — please sign in in the browser window, then click Continue",
                "reason": "login",
                "instructions": "Sign in using your credentials in the opened browser window. Once logged in, click 'Continue' here.",
            })
            return state

        # Look for Apply button
        apply_selector = await _find_apply_button(page)
        if apply_selector:
            try:
                await page.locator(apply_selector).first.click()
                await asyncio.sleep(2)
                state["messages"].append({
                    "type": "agent_message",
                    "node": "locate_apply_action",
                    "text": "✅ Clicked Apply button — loading application form…",
                })
            except Exception:
                pass

        state["current_node"] = "extract_form"
        state["messages"].append({
            "type": "agent_message",
            "node": "locate_apply_action",
            "text": f"📄 Application page ready: {page.url[:80]}",
        })

    except PlaywrightTimeoutError:
        state["error_message"] = f"Page load timeout for: {url}"
        state["messages"].append({
            "type": "error",
            "node": "open_job_page",
            "text": f"⏱️ Page load timed out. Please provide a different URL or try again.",
            "recoverable": True,
        })
    except Exception as e:
        state["error_message"] = str(e)
        state["messages"].append({
            "type": "error",
            "node": "open_job_page",
            "text": f"❌ Could not open page: {str(e)[:100]}",
            "recoverable": True,
        })

    return state
