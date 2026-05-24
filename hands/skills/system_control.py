import os
from typing import Any, Dict
from hands.skills.base import BaseSkill

class SystemControlSkill(BaseSkill):
    name = "system_control"
    description = "Controls the system power state (shutdown, sleep, restart)."
    parameters = {
        "action": "The power action to perform. Valid options: 'shutdown', 'restart', 'sleep'."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "").lower()
        
        if action == "shutdown":
            # For Windows
            os.system("shutdown /s /t 0")
            return {"success": True, "message": "Initiating system shutdown."}
            
        elif action == "restart":
            # For Windows
            os.system("shutdown /r /t 0")
            return {"success": True, "message": "Initiating system restart."}
            
        elif action == "sleep":
            # For Windows: Note that hibernation must be off for this to sleep rather than hibernate.
            # Usually users who want sleep have hibernation off or use powercfg /h off.
            # A more robust way to sleep is via powershell or just using SetSuspendState.
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return {"success": True, "message": "Initiating system sleep."}
            
        else:
            return {
                "success": False, 
                "message": f"Invalid action: '{action}'. Valid actions are 'shutdown', 'restart', 'sleep'."
            }
