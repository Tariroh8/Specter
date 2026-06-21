import os
import time
from typing import Any, Dict
from playwright.sync_api import sync_playwright
from hands.skills.base import BaseSkill

class SocialCommentSkill(BaseSkill):
    name = "social_comment"
    description = "Posts a comment to a specific post or video URL on Facebook, Instagram, or TikTok using your saved session."
    parameters = {
        "platform": "The target platform: facebook, instagram, or tiktok",
        "url": "The full HTTP URL of the target post or video",
        "text": "The comment message text",
        "headless": "Optional. 'true' or 'false' (defaults to 'true')"
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        platform = kwargs.get("platform", "").lower()
        url = kwargs.get("url", "")
        text = kwargs.get("text", "")
        headless_str = kwargs.get("headless", "true").lower()
        is_headless = headless_str == "true"

        if platform not in ("facebook", "instagram", "tiktok"):
            return {
                "success": False,
                "message": f"Invalid platform '{platform}'. Supported platforms: facebook, instagram, tiktok."
            }

        if not url:
            return {
                "success": False,
                "message": "Missing required parameter 'url'."
            }

        if not text:
            return {
                "success": False,
                "message": "Missing required parameter 'text' (comment text)."
            }

        # Resolve paths
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        user_data_dir = os.path.join(project_root, '.playwright_social_data', platform)
        error_screenshot_path = os.path.join(project_root, 'assets', 'social_comment_error.png')

        # Make sure assets directory exists
        os.makedirs(os.path.dirname(error_screenshot_path), exist_ok=True)

        try:
            with sync_playwright() as p:
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=is_headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser_context.pages[0] if len(browser_context.pages) > 0 else browser_context.new_page()
                page.set_default_timeout(20000) # 20 second default timeout

                print(f"[*] Navigating to post URL: {url}...")
                page.goto(url)
                time.sleep(4)

                if platform == "facebook":
                    # Check for login redirection
                    if page.locator('input[name="email"]').is_visible() or page.locator('button[name="login"]').is_visible():
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Session expired or not logged in. Please run 'social_login' first."
                        }

                    print("[*] Locating Facebook comment input field...")
                    # Facebook uses contenteditable divs with role="textbox" inside comment areas
                    comment_selectors = [
                        'div[role="textbox"][aria-label*="comment"]',
                        'div[role="textbox"][aria-label*="Comment"]',
                        'div[role="textbox"][aria-label*="Write a comment"]',
                        'div[role="textbox"]' # Fallback to any textbox on the post page
                    ]
                    
                    comment_box = None
                    for sel in comment_selectors:
                        try:
                            loc = page.locator(sel)
                            # Get the first visible element matching selector
                            for i in range(loc.count()):
                                if loc.nth(i).is_visible():
                                    comment_box = loc.nth(i)
                                    break
                            if comment_box:
                                break
                        except Exception:
                            continue

                    if not comment_box:
                        # Sometimes we need to click a "Write a comment" span first to activate it
                        try:
                            placeholder = page.locator('span:has-text("Write a comment")').first
                            if placeholder.is_visible():
                                placeholder.click()
                                time.sleep(1)
                                comment_box = page.locator('div[role="textbox"]').first
                        except Exception:
                            pass

                    if not comment_box:
                        page.screenshot(path=error_screenshot_path)
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Could not locate comment textbox. Saved error screenshot to assets/social_comment_error.png"
                        }

                    print("[*] Typing comment...")
                    comment_box.click()
                    comment_box.fill(text)
                    time.sleep(1)

                    print("[*] Submitting comment...")
                    page.keyboard.press("Enter")
                    time.sleep(3)
                    print("[+] Facebook comment posted.")

                elif platform == "instagram":
                    # Check for login redirection
                    if page.url.endswith("/accounts/login/") or page.locator('input[name="username"]').is_visible():
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Session expired or not logged in. Please run 'social_login' first."
                        }

                    print("[*] Locating Instagram comment textarea...")
                    comment_selectors = [
                        'textarea[aria-label="Add a comment…"]',
                        'textarea[placeholder*="comment"]',
                        'textarea[aria-label*="comment"]',
                        'textarea'
                    ]
                    
                    comment_box = None
                    for sel in comment_selectors:
                        try:
                            loc = page.locator(sel)
                            if loc.first.is_visible():
                                comment_box = loc.first
                                break
                        except Exception:
                            continue

                    if not comment_box:
                        page.screenshot(path=error_screenshot_path)
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Could not find Instagram comment textarea. Saved screenshot."
                        }

                    print("[*] Typing comment...")
                    comment_box.click()
                    comment_box.fill(text)
                    time.sleep(1)

                    print("[*] Clicking Post button...")
                    post_btn = page.locator('button:has-text("Post"), div[role="button"]:has-text("Post")').first
                    if post_btn.is_visible():
                        post_btn.click()
                    else:
                        page.keyboard.press("Enter")

                    time.sleep(3)
                    print("[+] Instagram comment posted.")

                elif platform == "tiktok":
                    # Check for login redirection
                    if "login" in page.url or page.locator('div:has-text("Log in to TikTok")').first.is_visible():
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Session expired or not logged in. Please run 'social_login' first."
                        }

                    print("[*] Locating TikTok comment input...")
                    # TikTok comments are contenteditable elements or inputs
                    comment_selectors = [
                        'div[role="textbox"]',
                        'div[contenteditable="true"]',
                        'input[placeholder*="comment"]',
                        'div[class*="comment"]'
                    ]

                    comment_box = None
                    for sel in comment_selectors:
                        try:
                            loc = page.locator(sel)
                            if loc.first.is_visible():
                                comment_box = loc.first
                                break
                        except Exception:
                            continue

                    if not comment_box:
                        page.screenshot(path=error_screenshot_path)
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Could not locate comment input box for TikTok video."
                        }

                    print("[*] Typing comment...")
                    comment_box.click()
                    # Type human-like or use fill
                    comment_box.fill(text)
                    time.sleep(1)

                    print("[*] Submitting comment...")
                    post_btn = page.locator('button:has-text("Post"), div:has-text("Post"), button[class*="post"]').first
                    if post_btn.is_visible():
                        post_btn.click()
                    else:
                        page.keyboard.press("Enter")

                    time.sleep(3)
                    print("[+] TikTok comment posted.")

                browser_context.close()
                try:
                    from hands.skills.audia import speak
                    speak(f"Successfully commented on {platform.capitalize()} post!")
                except Exception:
                    pass
                return {
                    "success": True,
                    "message": f"Successfully commented on {platform.capitalize()} post!"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to comment on {platform.capitalize()}: {str(e)}. A diagnostic screenshot has been saved to assets/social_comment_error.png if browser was active."
            }
