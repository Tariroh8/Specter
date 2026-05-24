import subprocess
import time
from typing import Any, Dict
from hands.skills.base import BaseSkill

# Global reference to keep track of tunnel processes by port
_TUNNEL_PROCESSES = {}

class LocalServerTunnelerSkill(BaseSkill):
    name = "local_server_tunneler"
    description = "Starts or stops a public localtunnel to expose a local port to the internet. Useful for sharing a local server."
    parameters = {
        "action": "The action to perform: 'start' or 'stop'.",
        "port": "The local port to expose (e.g., 5000). Only required when action is 'start', or when stopping a specific tunnel.",
        "subdomain": "Optional permanent custom subdomain (e.g., 'my-specter-app'). If provided, the link will always be https://<subdomain>.loca.lt"
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        global _TUNNEL_PROCESSES
        
        action = kwargs.get("action", "").lower()
        port = str(kwargs.get("port", "5000"))
        subdomain = kwargs.get("subdomain", "").strip()
        
        if action == "stop":
            if port in _TUNNEL_PROCESSES:
                proc = _TUNNEL_PROCESSES[port]
                if proc.poll() is None:
                    proc.terminate()
                del _TUNNEL_PROCESSES[port]
                return {"success": True, "message": f"Successfully stopped the local tunnel on port {port}."}
            elif not kwargs.get("port"):
                # If no port provided, stop all
                stopped = 0
                for p, proc in list(_TUNNEL_PROCESSES.items()):
                    if proc.poll() is None:
                        proc.terminate()
                    del _TUNNEL_PROCESSES[p]
                    stopped += 1
                return {"success": True, "message": f"Successfully stopped {stopped} active tunnels."}
            else:
                return {"success": True, "message": f"No active tunnel was running on port {port}."}
                
        elif action == "start":
            # Stop existing tunnel on this port if there is one
            if port in _TUNNEL_PROCESSES:
                proc = _TUNNEL_PROCESSES[port]
                if proc.poll() is None:
                    proc.terminate()
                del _TUNNEL_PROCESSES[port]
                
            try:
                # Spawn localtunnel using npx
                CREATE_NO_WINDOW = 0x08000000
                cmd = ["npx.cmd", "-y", "localtunnel", "--port", port]
                if subdomain:
                    cmd.extend(["--subdomain", subdomain])
                    
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )
                
                # Save it to our tracking dictionary
                _TUNNEL_PROCESSES[port] = proc
                
                # Give it a moment to connect and output the URL
                time.sleep(2)
                
                # Check if it exited early
                if proc.poll() is not None:
                    error_out = proc.stdout.read()
                    del _TUNNEL_PROCESSES[port]
                    return {"success": False, "message": f"Tunnel process failed to start. Error: {error_out}"}
                    
                # Read output lines
                # localtunnel usually prints "your url is: https://..." on the first line
                url = None
                line = proc.stdout.readline()
                if "your url is:" in line:
                    url = line.split("your url is:")[1].strip()
                    # Return formatted discord hyperlink
                    return {"success": True, "message": f"Successfully started tunnel on port {port}. **[🔗 Click here to open]({url})**"}
                else:
                    return {"success": True, "message": f"Started tunnel on port {port}, but could not parse the URL. Output was: {line}"}
                    
            except Exception as e:
                return {"success": False, "message": f"Failed to start localtunnel: {e}"}
                
        else:
            return {"success": False, "message": f"Invalid action '{action}'. Must be 'start' or 'stop'."}
