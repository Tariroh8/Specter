import os
import subprocess
from typing import Any, Dict
from hands.skills.base import BaseSkill

class RestartSpecterSkill(BaseSkill):
    name = "restart_specter"
    description = "Restarts the Specter OS background services and bot."
    parameters = {}

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            # We need to find the root directory of Specter
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            vbs_path = os.path.join(base_dir, "start_specter.vbs")
            
            # This powershell command will sleep for 2 seconds (giving the bot time to send the success message back),
            # kill all pythonw processes, and then launch the vbs script to bring it all back up.
            cmd = f'Start-Sleep -Seconds 2; Stop-Process -Name pythonw -Force; cscript.exe //nologo "{vbs_path}"'
            
            # We launch this as an independent background process so it survives the bot dying
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(["powershell", "-Command", cmd], creationflags=CREATE_NO_WINDOW)
            
            return {"success": True, "message": "Restarting Specter in 2 seconds..."}
        except Exception as e:
            return {"success": False, "message": f"Failed to initiate restart: {e}"}
