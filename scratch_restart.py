import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
vbs_path = os.path.join(BASE_DIR, "start_specter.vbs")

cmd = f'Start-Sleep -Seconds 2; Stop-Process -Name pythonw -Force; cscript.exe //nologo "{vbs_path}"'
subprocess.Popen(["powershell", "-Command", cmd], creationflags=subprocess.CREATE_NO_WINDOW)
print("Restart initiated")
