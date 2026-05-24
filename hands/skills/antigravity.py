import time
import win32gui
import win32con
import pyautogui
from typing import Any, Dict
from hands.skills.base import BaseSkill

class AntigravityDelegateSkill(BaseSkill):
    name = "delegate_to_antigravity"
    description = "Focuses Visual Studio Code and types a prompt directly into the Antigravity AI chat box. Use this to assign coding tasks to the Antigravity AI."
    parameters = {
        "prompt": "The prompt or instruction to type out to Antigravity."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        prompt = kwargs.get("prompt")
        if not prompt:
            return {"success": False, "message": "Missing required parameter 'prompt'."}

        def window_enum_handler(hwnd, resultList):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Visual Studio Code" in title:
                    resultList.append((hwnd, title))

        try:
            windows = []
            win32gui.EnumWindows(window_enum_handler, windows)
            
            if not windows:
                return {"success": False, "message": "Could not find a running instance of Visual Studio Code."}

            # Take the first matched VS Code window
            hwnd, title = windows[0]
            
            # Restore if minimized and bring to front
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            
            # Give the window a moment to become fully focused
            time.sleep(0.5)
            
            # Type out the prompt
            pyautogui.write(prompt, interval=0.01)
            
            # Hit enter to submit
            pyautogui.press('enter')
            
            return {"success": True, "message": f"Successfully delegated to Antigravity: '{prompt}'"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to delegate to Antigravity: {e}"}
