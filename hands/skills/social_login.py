import os
import sys
import time
import threading
from typing import Any, Dict
from playwright.sync_api import sync_playwright
from hands.skills.base import BaseSkill

class SocialLoginSkill(BaseSkill):
    name = "social_login"
    description = (
        "Launches a visible browser window for you to log in manually to Facebook, "
        "Instagram, or TikTok. Saves the session cookies for future automated posts and comments."
    )
    parameters = {
        "platform": "The target platform: facebook, instagram, or tiktok"
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        platform = kwargs.get("platform", "").lower()
        if platform not in ("facebook", "instagram", "tiktok"):
            return {
                "success": False,
                "message": f"Invalid platform '{platform}'. Supported platforms: facebook, instagram, tiktok."
            }

        # Resolve paths
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        user_data_dir = os.path.join(project_root, '.playwright_social_data', platform)

        login_urls = {
            "facebook": "https://www.facebook.com/",
            "instagram": "https://www.instagram.com/accounts/login/",
            "tiktok": "https://www.tiktok.com/login"
        }

        try:
            print(f"[*] Starting browser for {platform.capitalize()}...")
            with sync_playwright() as p:
                # Launch persistent context so cookies are saved
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser_context.pages[0] if len(browser_context.pages) > 0 else browser_context.new_page()
                page.goto(login_urls[platform])

                browser_closed = [False]

                def on_close(p_obj):
                    browser_closed[0] = True

                page.on("close", on_close)

                # Wait for user to log in and close browser OR press Enter (if in a TTY)
                if sys.stdin.isatty():
                    print("\n" + "="*60)
                    print(f"🔑 MANUAL LOGIN REQUIRED FOR {platform.upper()}")
                    print("="*60)
                    print("1. A browser window has opened.")
                    print("2. Log in manually, complete any 2FA/CAPTCHA challenges.")
                    print("3. When finished, press [ENTER] in this terminal or close the browser window.")
                    print("="*60 + "\n")

                    def wait_for_input():
                        try:
                            input()
                        except (EOFError, Exception):
                            pass
                        browser_closed[0] = True

                    input_thread = threading.Thread(target=wait_for_input, daemon=True)
                    input_thread.start()
                else:
                    print("\n" + "="*60)
                    print(f"🔑 MANUAL LOGIN REQUIRED FOR {platform.upper()}")
                    print("="*60)
                    print("1. A browser window has opened.")
                    print("2. Log in manually, complete any 2FA/CAPTCHA challenges.")
                    print("3. When finished, CLOSE the browser window.")
                    print("="*60 + "\n")

                # Poll until browser_closed flag is set to True
                while not browser_closed[0]:
                    try:
                        if page.is_closed():
                            break
                    except Exception:
                        break
                    time.sleep(0.5)

                # Close browser context to save state properly
                browser_context.close()
                return {
                    "success": True,
                    "message": f"Session cookies and storage state saved successfully for {platform}!"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred during social media login: {str(e)}"
            }
