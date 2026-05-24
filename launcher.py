import os
import sys
import time
import socket
import subprocess
import threading
import webbrowser
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item

# Paths to the scripts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_TO_RUN = [
    os.path.join(BASE_DIR, "ui", "server.py"),
    os.path.join(BASE_DIR, "brain", "remote.py"),
    os.path.join(BASE_DIR, "observer", "monitor.py"),
    os.path.join(BASE_DIR, "observer", "auto_clicker.py")
]

# Keep track of running processes
processes = []
lock_socket = None

def get_lock():
    """Check if another instance of the launcher is already running."""
    global lock_socket
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        lock_socket.bind(('127.0.0.1', 50019)) # Custom lock port for Specter launcher
        return True
    except socket.error:
        return False

def create_image():
    """Create a placeholder icon image."""
    icon_path = os.path.join(BASE_DIR, "icon.png")
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    
    # Generate a simple placeholder icon
    width = 64
    height = 64
    color1 = (45, 45, 45)
    color2 = (100, 150, 255)
    
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill=color2)
    
    image.save(icon_path)
    return image

def start_services():
    """Start all background services."""
    CREATE_NO_WINDOW = 0x08000000
    for script in SCRIPTS_TO_RUN:
        if os.path.exists(script):
            print(f"Starting {script}...")
            # Using sys.executable to use the exact same python/pythonw that started the launcher
            p = subprocess.Popen(
                [sys.executable, script],
                creationflags=CREATE_NO_WINDOW,
                cwd=BASE_DIR
            )
            processes.append(p)
        else:
            print(f"Warning: Script not found - {script}")

def stop_services():
    """Terminate all background services."""
    for p in processes:
        try:
            p.terminate()
        except Exception as e:
            print(f"Error terminating process: {e}")

def open_dashboard(icon=None, item=None):
    """Open the local dashboard in the default web browser."""
    webbrowser.open("http://127.0.0.1:5000")

def quit_app(icon, item):
    """Stop services and exit the launcher."""
    icon.stop()
    stop_services()
    sys.exit(0)

def delayed_open_dashboard():
    """Wait for services to initialize and open dashboard."""
    time.sleep(2)
    open_dashboard()

def main():
    # Only allow one instance to run
    if not get_lock():
        print("Launcher is already running. Opening dashboard.")
        open_dashboard()
        sys.exit(0)

    start_services()
    
    # Auto-open dashboard after a short delay so user knows it started
    threading.Thread(target=delayed_open_dashboard, daemon=True).start()
    
    # Setup System Tray
    image = create_image()
    menu = (
        item('Open Dashboard', open_dashboard),
        item('Quit', quit_app)
    )
    
    icon = pystray.Icon("Specter", image, "Specter OS", menu)
    icon.run()

if __name__ == "__main__":
    main()
