import time
import requests
from typing import Any, Dict
from hands.skills.base import BaseSkill

class DeployDjangoPythonAnywhereSkill(BaseSkill):
    name = "deploy_django_pythonanywhere"
    description = "Deploys a Django application to PythonAnywhere autonomously using the PythonAnywhere REST API."
    parameters = {
        "username": "Your PythonAnywhere username.",
        "api_token": "Your PythonAnywhere API Token (generated in Account -> API Token).",
        "github_url": "The HTTPS Git clone URL of the Django repository (e.g., https://github.com/user/repo.git).",
        "domain": "Optional. The domain or subdomain to host on. Defaults to <username>.pythonanywhere.com.",
        "python_version": "Optional. The Python version to use (e.g., '3.10', '3.9'). Defaults to '3.10'."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        username = kwargs.get("username")
        api_token = kwargs.get("api_token")
        github_url = kwargs.get("github_url")
        
        if not username or not api_token or not github_url:
            return {
                "success": False,
                "message": "Missing required parameters. 'username', 'api_token', and 'github_url' are all required."
            }

        domain = kwargs.get("domain", f"{username}.pythonanywhere.com").strip()
        python_version = kwargs.get("python_version", "3.10").strip()

        # Setup API Session
        base_url = f"https://www.pythonanywhere.com/api/v0/user/{username}"
        headers = {"Authorization": f"Token {api_token}"}
        session = requests.Session()
        session.headers.update(headers)

        # 1. Test connection and authorization
        print(f"[*] Validating PythonAnywhere API token for user '{username}'...")
        try:
            resp = session.get(f"{base_url}/cpu/")
            if resp.status_code == 401 or resp.status_code == 403:
                return {
                    "success": False,
                    "message": "Invalid PythonAnywhere credentials or API Token. Please verify username and token."
                }
            resp.raise_for_status()
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect to PythonAnywhere API: {e}"
            }

        # 2. Check if a console is available or create a new bash console
        print("[*] Creating a new remote Bash console on PythonAnywhere...")
        console_id = None
        try:
            resp = session.post(f"{base_url}/consoles/", json={"executable": "bash"})
            resp.raise_for_status()
            console_data = resp.json()
            console_id = console_data.get("id")
            print(f"[+] Console successfully created. ID: {console_id}")
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create a remote bash console: {e}"
            }

        # 3. Send setup command
        # pa_autoconfigure_django.py is PythonAnywhere's official automation script
        # We append a unique terminal token/exit check so we know exactly when execution finishes.
        print(f"[*] Dispatching deployment for: '{github_url}' to domain '{domain}'...")
        setup_cmd = (
            f"pa_autoconfigure_django.py --git-clone {github_url} --domain {domain} --python {python_version}\n"
            f"echo \"===EXIT_CODE: $?===\"\n"
            f"echo \"___SPECTER_DEPLOY_DONE___\"\n"
        )

        try:
            resp = session.post(
                f"{base_url}/consoles/{console_id}/input/",
                json={"input": setup_cmd}
            )
            resp.raise_for_status()
        except Exception as e:
            # Clean up console before failing
            session.delete(f"{base_url}/consoles/{console_id}/")
            return {
                "success": False,
                "message": f"Failed to send deploy commands to the console: {e}"
            }

        # 4. Poll console output until completion or timeout
        print("[*] Deployment in progress. Polling console output (this may take a few minutes)...")
        timeout_seconds = 600  # 10 minutes max
        start_time = time.time()
        output_buffer = ""
        success = False
        exit_code = None

        try:
            while time.time() - start_time < timeout_seconds:
                time.sleep(10)
                
                resp = session.get(f"{base_url}/consoles/{console_id}/get_latest_output/")
                resp.raise_for_status()
                new_output = resp.json().get("output", "")
                
                # Append only new output parts if possible, or print latest
                if len(new_output) > len(output_buffer):
                    added_text = new_output[len(output_buffer):]
                    output_buffer = new_output
                    print(added_text, end="", flush=True)

                if "___SPECTER_DEPLOY_DONE___" in output_buffer:
                    success = True
                    # Check for exit code
                    if "===EXIT_CODE:" in output_buffer:
                        parts = output_buffer.split("===EXIT_CODE:")
                        if len(parts) > 1:
                            exit_code_str = parts[1].split("===")[0].strip()
                            try:
                                exit_code = int(exit_code_str)
                            except ValueError:
                                pass
                    break
            
            if not success:
                raise TimeoutError("Deployment timed out on PythonAnywhere.")

        except Exception as e:
            # Clean up console
            session.delete(f"{base_url}/consoles/{console_id}/")
            return {
                "success": False,
                "message": f"Deployment interrupted: {e}"
            }

        # 5. Clean up: terminate/delete the console
        print("\n[*] Cleaning up remote console resources...")
        try:
            session.delete(f"{base_url}/consoles/{console_id}/")
            print("[+] Console deleted successfully.")
        except Exception as e:
            print(f"[-] Warning: Failed to delete console {console_id}: {e}")

        # 6. Verify result
        site_url = f"https://{domain}"
        if exit_code == 0:
            return {
                "success": True,
                "message": (
                    f"Django App deployed successfully to PythonAnywhere!\n\n"
                    f"🌐 **Website URL:** [🔗 Click here to open]({site_url})\n\n"
                    f"**Deployment Log Summary:**\n"
                    f"- Configured domain: {domain}\n"
                    f"- Python version: {python_version}\n"
                    f"- Autoconfigure status: Success (Exit Code 0)\n"
                    f"- Virtualenv & requirements: Created and installed successfully"
                )
            }
        else:
            return {
                "success": False,
                "message": (
                    f"Deployment command executed but returned a non-zero exit code ({exit_code}).\n"
                    f"Please check console output or review logs on PythonAnywhere."
                )
            }
