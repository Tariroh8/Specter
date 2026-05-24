import os
import time
from typing import Any, Dict
from playwright.sync_api import sync_playwright
from hands.skills.base import BaseSkill

class ChatGPTBrowserSkill(BaseSkill):
    name = "chatgpt_browser"
    description = "Opens ChatGPT in a browser, submits a prompt, and returns the response. Supports persistent sessions."
    parameters = {
        "prompt": "The prompt to send to ChatGPT.",
        "headless": "Optional. 'true' or 'false'. Defaults to 'true'. Set to 'false' for the first run to log in."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        prompt = kwargs.get("prompt")
        if not prompt:
            return {"success": False, "message": "Missing required parameter 'prompt'."}

        headless_str = kwargs.get("headless", "true").lower()
        is_headless = headless_str == "true"

        # Create a persistent data directory in the project root to store login state
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        user_data_dir = os.path.join(project_root, '.playwright_data')

        try:
            with sync_playwright() as p:
                # Launch a persistent context so cookies and logins are saved
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=is_headless,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                page = browser_context.pages[0] if len(browser_context.pages) > 0 else browser_context.new_page()
                
                # Navigate to ChatGPT
                page.goto("https://chatgpt.com/")

                # Wait for the prompt textarea to be visible
                try:
                    prompt_selector = "#prompt-textarea"
                    page.wait_for_selector(prompt_selector, timeout=15000)
                except Exception:
                    browser_context.close()
                    return {
                        "success": False, 
                        "message": "Could not find the prompt input box. You likely need to run this with `headless=false` first and manually log in or solve a Captcha."
                    }

                # Fill the prompt and press enter
                page.fill(prompt_selector, prompt)
                page.press(prompt_selector, "Enter")

                # Wait for response to generate
                # Wait briefly for generation to begin, then wait for the stop button to disappear
                time.sleep(2)
                try:
                    # Wait up to 60 seconds for the 'Stop generating' button to hide
                    page.wait_for_selector("button[aria-label='Stop generating']", state='hidden', timeout=60000)
                except Exception:
                    pass
                
                # Add an extra small buffer to ensure the DOM has fully settled
                time.sleep(2)
                
                # Scrape the response
                # ChatGPT responses are usually wrapped in elements with the "markdown" class
                response_elements = page.locator(".markdown").all()
                if not response_elements:
                    browser_context.close()
                    return {"success": False, "message": "Could not extract the AI response from the page."}

                # The last markdown block is the latest response
                latest_response = response_elements[-1].inner_text()
                
                browser_context.close()
                return {"success": True, "message": latest_response}

        except Exception as e:
            return {"success": False, "message": f"Browser automation error: {str(e)}"}
