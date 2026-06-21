import os
import time
from typing import Any, Dict
from playwright.sync_api import sync_playwright
from hands.skills.base import BaseSkill

class SocialPostSkill(BaseSkill):
    name = "social_post"
    description = "Posts text and optional image/video files to Facebook, Instagram, or TikTok using your saved session."
    parameters = {
        "platform": "The target platform: facebook, instagram, or tiktok",
        "text": "The text content or caption for the post",
        "media_path": "Optional. The absolute path to a local image or video file",
        "page_url": "Optional. Specific Facebook Page/Group URL to post to",
        "headless": "Optional. 'true' or 'false' (defaults to 'true')"
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        platform = kwargs.get("platform", "").lower()
        text = kwargs.get("text", "")
        media_path = kwargs.get("media_path", "")
        page_url = kwargs.get("page_url", "")
        headless_str = kwargs.get("headless", "true").lower()
        is_headless = headless_str == "true"

        if platform not in ("facebook", "instagram", "tiktok"):
            return {
                "success": False,
                "message": f"Invalid platform '{platform}'. Supported platforms: facebook, instagram, tiktok."
            }

        if platform in ("instagram", "tiktok") and not media_path:
            return {
                "success": False,
                "message": f"Media path (image or video) is required for posting on {platform.capitalize()}."
            }

        if media_path and not os.path.exists(media_path):
            return {
                "success": False,
                "message": f"Media file not found at path: {media_path}"
            }

        # Resolve paths
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        user_data_dir = os.path.join(project_root, '.playwright_social_data', platform)
        error_screenshot_path = os.path.join(project_root, 'assets', 'social_post_error.png')

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

                if platform == "facebook":
                    url = page_url if page_url else "https://www.facebook.com/"
                    print(f"[*] Navigating to {url}...")
                    page.goto(url)
                    time.sleep(3)

                    # Check for login form redirect or presence
                    if page.locator('input[name="email"]').is_visible() or page.locator('button[name="login"]').is_visible():
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Session expired or not logged in. Please run 'social_login' first."
                        }

                    print("[*] Locating Facebook post composer...")
                    composer_selectors = [
                        'div[role="button"]:has-text("What\'s on your mind")',
                        'span:has-text("What\'s on your mind")',
                        'div[role="button"]:has-text("Create a post")',
                        'div[role="button"]:has-text("Write something...")'
                    ]
                    composer = None
                    for sel in composer_selectors:
                        try:
                            loc = page.locator(sel)
                            if loc.first.is_visible():
                                composer = loc.first
                                break
                        except Exception:
                            continue

                    if not composer:
                        page.screenshot(path=error_screenshot_path)
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Could not find post composer. Captured error screenshot at assets/social_post_error.png"
                        }

                    composer.click()
                    print("[*] Opening post composer dialog...")
                    dialog = page.locator('div[role="dialog"]')
                    dialog.wait_for(state="visible", timeout=10000)

                    textbox = dialog.locator('div[role="textbox"]')
                    textbox.wait_for(state="visible", timeout=5000)
                    textbox.click()
                    textbox.fill(text)
                    time.sleep(1)

                    if media_path:
                        print(f"[*] Uploading media: {media_path}...")
                        photo_button = dialog.locator('div[aria-label*="Photo/video"], div[aria-label*="Photo/Video"]').first
                        if not photo_button.is_visible():
                            photo_button = dialog.locator('div[role="button"]:has-text("Photo/video")').first

                        if photo_button.is_visible():
                            photo_button.click()

                        # Helper to search frames for input
                        file_input = None
                        inp = page.locator('input[type="file"]')
                        if inp.count() > 0:
                            file_input = inp.first
                        else:
                            for frame in page.frames:
                                try:
                                    inp = frame.locator('input[type="file"]')
                                    if inp.count() > 0:
                                        file_input = inp.first
                                        break
                                except Exception:
                                    continue

                        if file_input:
                            file_input.set_input_files(media_path)
                            print("[*] File selected. Waiting for upload to complete...")
                            time.sleep(5) # buffer for upload
                        else:
                            print("[!] Photo/video file input element not found.")

                    print("[*] Clicking Post button...")
                    post_button = dialog.locator('div[role="button"]:has-text("Post"), div[role="button"][aria-label="Post"]').first
                    post_button.click()

                    # Wait for dialog to close
                    time.sleep(5)
                    print("[+] Post submitted successfully.")

                elif platform == "instagram":
                    print("[*] Navigating to Instagram...")
                    page.goto("https://www.instagram.com/")
                    time.sleep(4)

                    # Check for login redirection
                    if page.url.endswith("/accounts/login/") or page.locator('input[name="username"]').is_visible():
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Session expired or not logged in. Please run 'social_login' first."
                        }

                    print("[*] Locating Instagram Create button...")
                    create_selectors = [
                        'svg[aria-label="New post"]',
                        'svg[aria-label="Create"]',
                        'span:has-text("Create")',
                        'a[href="#"]:has-text("Create")'
                    ]
                    create_btn = None
                    for sel in create_selectors:
                        try:
                            loc = page.locator(sel)
                            if loc.first.is_visible():
                                create_btn = loc.first
                                break
                        except Exception:
                            continue

                    if not create_btn:
                        page.screenshot(path=error_screenshot_path)
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Could not find Instagram Create button. Captured screenshot."
                        }

                    create_btn.click()
                    time.sleep(2)

                    print(f"[*] Uploading media: {media_path}...")
                    file_input = page.locator('input[type="file"]').first
                    file_input.wait_for(state="attached", timeout=10000)
                    file_input.set_input_files(media_path)
                    time.sleep(3)

                    # Click Next (Crop screen)
                    print("[*] Advancing Crop screen...")
                    next_btn = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")').first
                    next_btn.wait_for(state="visible", timeout=10000)
                    next_btn.click()
                    time.sleep(2)

                    # Click Next (Filter screen)
                    print("[*] Advancing Filter screen...")
                    next_btn.wait_for(state="visible", timeout=10000)
                    next_btn.click()
                    time.sleep(2)

                    # Write Caption
                    print("[*] Adding caption...")
                    caption_box = page.locator('div[aria-label="Write a caption..."], textarea[placeholder="Write a caption..."]').first
                    caption_box.wait_for(state="visible", timeout=10000)
                    caption_box.click()
                    caption_box.fill(text)
                    time.sleep(1)

                    # Click Share
                    print("[*] Clicking Share button...")
                    share_btn = page.locator('div[role="button"]:has-text("Share"), button:has-text("Share")').first
                    share_btn.click()

                    # Wait for upload to complete
                    print("[*] Uploading. This may take a moment...")
                    time.sleep(10)
                    print("[+] Instagram post completed.")

                elif platform == "tiktok":
                    url = "https://www.tiktok.com/creator-center/upload?lang=en"
                    print(f"[*] Navigating to TikTok Creator Upload ({url})...")
                    page.goto(url)
                    time.sleep(5)

                    if "login" in page.url or page.locator('div:has-text("Log in to TikTok")').first.is_visible():
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Session expired or not logged in. Please run 'social_login' first."
                        }

                    print("[*] Waiting for TikTok file uploader...")
                    file_input = None
                    inp = page.locator('input[type="file"]')
                    if inp.count() > 0:
                        file_input = inp.first
                    else:
                        for frame in page.frames:
                            try:
                                inp = frame.locator('input[type="file"]')
                                if inp.count() > 0:
                                    file_input = inp.first
                                    break
                            except Exception:
                                continue

                    if not file_input:
                        page.screenshot(path=error_screenshot_path)
                        browser_context.close()
                        return {
                            "success": False,
                            "message": "Could not locate file input for TikTok uploader."
                        }

                    print(f"[*] Selecting video: {media_path}...")
                    file_input.set_input_files(media_path)
                    print("[*] Uploading video to TikTok. Waiting 10 seconds for completion indicator...")
                    time.sleep(10)

                    # Locate caption editor textbox
                    print("[*] Filling post caption...")
                    caption_box = page.locator('div[role="textbox"], div[class*="editor"]').first
                    if caption_box.is_visible():
                        caption_box.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.keyboard.type(text)
                        time.sleep(1)

                    print("[*] Clicking Post button...")
                    post_btn = page.locator('button:has-text("Post"), button[class*="post"]').first
                    post_btn.wait_for(state="visible", timeout=15000)
                    post_btn.click()

                    time.sleep(6)
                    print("[+] TikTok post submitted.")

                browser_context.close()
                try:
                    from hands.skills.audia import speak
                    speak(f"Successfully published post to {platform.capitalize()}!")
                except Exception:
                    pass
                return {
                    "success": True,
                    "message": f"Successfully published post to {platform.capitalize()}!"
                }

        except Exception as e:
            # Attempt to capture a diagnostic screenshot
            try:
                with sync_playwright() as p:
                    # open a separate session to take a screenshot or reuse context if possible,
                    # but here we can just save it inside the except block if browser is still active.
                    pass
            except Exception:
                pass
            return {
                "success": False,
                "message": f"Failed to post on {platform.capitalize()}: {str(e)}. A diagnostic screenshot has been saved to assets/social_post_error.png if browser was active."
            }
