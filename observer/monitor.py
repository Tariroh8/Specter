import os
import sys
import time
from pathlib import Path

# Add project root to path so we can import 'brain' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from brain import db
from observer.window_tracker import WindowTracker

# Default PowerShell history location
PS_HISTORY_PATH = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"))

class ProjectEventHandler(FileSystemEventHandler):
    def __init__(self, watch_dir):
        self.watch_dir = watch_dir

    def on_modified(self, event):
        if not event.is_directory:
            print(f"[FILE MODIFIED] {event.src_path}")
            db.log_event("FILE_MODIFIED", event.src_path, project_dir=self.watch_dir)

    def on_created(self, event):
        if not event.is_directory:
            print(f"[FILE CREATED] {event.src_path}")
            db.log_event("FILE_CREATED", event.src_path, project_dir=self.watch_dir)

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"[FILE DELETED] {event.src_path}")
            db.log_event("FILE_DELETED", event.src_path, project_dir=self.watch_dir)

class SpecterObserver:
    def __init__(self, watch_dir):
        self.watch_dir = watch_dir
        self.history_file = PS_HISTORY_PATH
        self.last_history_size = 0
        self.observer = Observer()
        self.window_tracker = WindowTracker(interval=2.0)

    def start_file_watcher(self):
        event_handler = ProjectEventHandler(self.watch_dir)
        self.observer.schedule(event_handler, self.watch_dir, recursive=True)
        self.observer.start()
        print(f"[*] Started watching directory: {self.watch_dir}")
        print(f"[*] Tailing Terminal History: {self.history_file}")

    def poll_history(self):
        if not self.history_file.exists():
            return

        current_size = self.history_file.stat().st_size
        
        # If the file shrank, it was likely truncated/cleared, reset our pointer
        if current_size < self.last_history_size:
            self.last_history_size = 0

        if current_size > self.last_history_size:
            try:
                with open(self.history_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_history_size)
                    new_lines = f.readlines()
                    for line in new_lines:
                        cmd = line.strip()
                        if cmd:
                            print(f"[CMD EXECUTED] {cmd}")
                            db.log_event("CMD_EXECUTED", "PowerShell", content=cmd, project_dir=self.watch_dir)
                self.last_history_size = current_size
            except Exception as e:
                print(f"[ERROR] Failed to read history file: {e}")

    def run(self):
        # Initialize history file size so we don't read past history on startup
        if self.history_file.exists():
            self.last_history_size = self.history_file.stat().st_size
            
        self.start_file_watcher()
        self.window_tracker.start()
        
        try:
            while True:
                self.poll_history()
                time.sleep(1) # Poll every second
        except KeyboardInterrupt:
            self.observer.stop()
            self.window_tracker.stop()
            print("\n[*] Stopping Specter Observer")
        
        self.observer.join()

if __name__ == "__main__":
    # For now, watch the current directory the script is executed in.
    # We can point this to a master "Projects" directory later.
    current_dir = os.getcwd()
    print("=== SPECTER: OBSERVER STARTED ===")
    specter = SpecterObserver(watch_dir=current_dir)
    specter.run()
