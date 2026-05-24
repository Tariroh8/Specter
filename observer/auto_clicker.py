import os
import time
import pyautogui

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUTTONS_DIR = os.path.join(BASE_DIR, "assets", "buttons")

def monitor_screen():
    print("Starting auto-clicker for Antigravity permissions...")
    while True:
        # Define the buttons we are looking for
        buttons = ["accept.png", "run.png", "retry.png"]
        
        for button in buttons:
            button_path = os.path.join(BUTTONS_DIR, button)
            if os.path.exists(button_path):
                try:
                    # Look for the button with 80% confidence
                    location = pyautogui.locateCenterOnScreen(button_path, confidence=0.8)
                    if location:
                        print(f"Found {button}! Clicking at {location}")
                        pyautogui.click(location)
                        # Small sleep to let the UI update after clicking
                        time.sleep(1)
                except pyautogui.ImageNotFoundException:
                    # PyAutoGUI raises this if the image is not found on screen
                    pass
                except Exception as e:
                    print(f"Error checking {button}: {e}")
                    
        # Sleep to avoid high CPU usage
        time.sleep(2)

if __name__ == "__main__":
    monitor_screen()
