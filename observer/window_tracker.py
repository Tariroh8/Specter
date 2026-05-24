import time
import threading
from brain.db import log_event

try:
    import win32gui
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("[WARNING] pywin32 not installed. Window tracking is disabled.")

class WindowTracker:
    def __init__(self, interval=2.0, idle_threshold_sec=300):
        self.interval = interval
        self.idle_threshold_sec = idle_threshold_sec
        self.running = False
        self.last_title = ""
        self.is_idle = False
        self.thread = None

    def start(self):
        if not HAS_WIN32:
            return
            
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print(f"[*] Started watching Active Windows (interval: {self.interval}s)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _parse_title(self, full_title):
        # Splits the title by the last dash to guess the app name vs document title
        parts = full_title.rsplit(" - ", 1)
        if len(parts) == 2:
            return parts[1].strip(), parts[0].strip()
        return "Unknown App", full_title.strip()

    def _detect_browser_search(self, app_name, doc_title):
        browsers = ["Google Chrome", "Mozilla Firefox", "Microsoft Edge", "Brave", "Opera", "Safari", "Arc"]
        if not any(b in app_name for b in browsers):
            return None
            
        # Check for Google Search
        if doc_title.endswith("- Google Search"):
            return doc_title.rsplit("- Google Search", 1)[0].strip()
            
        # Check for Bing Search
        if doc_title.endswith("- Search"):
             return doc_title.rsplit("- Search", 1)[0].strip()
             
        # Check for Yahoo Search
        if doc_title.endswith("- Yahoo Search Results"):
             return doc_title.rsplit("- Yahoo Search Results", 1)[0].strip()
             
        # Check for DuckDuckGo
        if " at DuckDuckGo" in doc_title:
             return doc_title.rsplit(" at DuckDuckGo", 1)[0].strip()
             
        return None

    def _detect_ai_chat(self, app_name, doc_title):
        browsers = ["Google Chrome", "Mozilla Firefox", "Microsoft Edge", "Brave", "Opera", "Safari", "Arc"]
        if not any(b in app_name for b in browsers):
            return None
            
        # Check for ChatGPT
        if doc_title.endswith("- ChatGPT"):
            return doc_title.rsplit("- ChatGPT", 1)[0].strip()
        elif doc_title == "ChatGPT":
            return "New Chat"
            
        # Check for Claude
        if doc_title.endswith("- Claude"):
            return doc_title.rsplit("- Claude", 1)[0].strip()
        elif doc_title == "Claude":
            return "New Chat"
            
        # Check for Gemini
        if doc_title.endswith("- Google Gemini") or doc_title.endswith("- Gemini"):
             return doc_title.rsplit("-", 1)[0].strip()
        elif doc_title == "Gemini" or doc_title == "Google Gemini":
             return "New Chat"

        # Check for Google AI Studio
        if doc_title.endswith("| Google AI Studio") or doc_title.endswith("- Google AI Studio"):
             return doc_title.rsplit("|", 1)[0].rsplit("-", 1)[0].strip()
        elif doc_title == "Google AI Studio":
             return "New Chat"
             
        # Check for Copilot
        if doc_title.endswith("- Microsoft Copilot") or doc_title.endswith("- Copilot"):
            return doc_title.rsplit("-", 1)[0].strip()
            
        return None

    def _run_loop(self):
        while self.running:
            try:
                # Check idle status
                last_input = win32api.GetLastInputInfo()
                current_tick = win32api.GetTickCount()
                idle_sec = (current_tick - last_input) / 1000.0
                
                if idle_sec > self.idle_threshold_sec:
                    if not self.is_idle:
                        self.is_idle = True
                        log_event(event_type="IDLE_START", source="os_system", content=f"User idle > {self.idle_threshold_sec}s")
                else:
                    if self.is_idle:
                        self.is_idle = False
                        log_event(event_type="IDLE_END", source="os_system", content=f"User returned.")
                        # Force re-log of window when returning from idle
                        self.last_title = "" 
                
                # Track window only if not idle
                if not self.is_idle:
                    window_handle = win32gui.GetForegroundWindow()
                    if window_handle:
                        active_title = win32gui.GetWindowText(window_handle)
                        
                        # Only log if the title has changed and is not empty
                        if active_title and active_title != self.last_title:
                            app_name, doc_title = self._parse_title(active_title)
                            
                            ai_chat_topic = self._detect_ai_chat(app_name, doc_title)
                            search_query = self._detect_browser_search(app_name, doc_title) if not ai_chat_topic else None
                            
                            if ai_chat_topic:
                                log_event(
                                    event_type="AI_CHAT",
                                    source=app_name,
                                    content=f"Chatting about: {ai_chat_topic}",
                                    project_dir=""
                                )
                            elif search_query:
                                log_event(
                                    event_type="BROWSER_SEARCH",
                                    source=app_name,
                                    content=f"Searched for: {search_query}",
                                    project_dir=""
                                )
                            else:
                                log_event(
                                    event_type="WINDOW_ACTIVE",
                                    source=app_name,
                                    content=doc_title,
                                    project_dir=""
                                )
                            
                            self.last_title = active_title
            except Exception as e:
                # Catch occasional access denied or handle invalidation errors
                pass
            
            time.sleep(self.interval)
