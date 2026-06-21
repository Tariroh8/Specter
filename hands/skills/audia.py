import pyttsx3
import threading
from typing import Any, Dict
from hands.skills.base import BaseSkill

def speak(text: str):
    """
    Synthesizes text to speech in a background thread to prevent blocking 
    the caller (such as Flask routes, CLI scripts, or Discord commands).
    """
    if not text:
        return

    def run():
        try:
            # Initialize engine in this thread context
            engine = pyttsx3.init()
            engine.setProperty('rate', 145) # Natural reading pace
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[!] Audia TTS Error: {e}")

    threading.Thread(target=run, daemon=True).start()

class AudiaSpeakSkill(BaseSkill):
    name = "speak"
    description = "Speaks the provided text aloud using Audia, our offline voice assistant."
    parameters = {
        "text": "The text message to speak aloud."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        text = kwargs.get("text", "")
        if not text:
            return {
                "success": False,
                "message": "Missing required parameter 'text'."
            }

        print(f"[*] Audia speaking: '{text}'")
        speak(text)
        
        return {
            "success": True,
            "message": f"Audia spoke: '{text}'"
        }
