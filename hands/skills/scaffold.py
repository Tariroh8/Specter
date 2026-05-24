import os
import subprocess
from typing import Any, Dict
from hands.skills.base import BaseSkill

class ProjectScaffoldSkill(BaseSkill):
    name = "scaffold_project"
    description = "Scaffolds a new project (e.g. Python, Node) and opens it in VS Code."
    parameters = {
        "project_type": "The type of project (e.g. 'python', 'node', 'react')",
        "project_name": "The name of the new directory/project",
        "path": "Optional. The absolute path where the project should be created. Defaults to current directory."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        project_type = kwargs.get("project_type", "python").lower()
        project_name = kwargs.get("project_name")
        target_path = kwargs.get("path", os.getcwd())
        
        if not project_name:
            return {"success": False, "message": "Missing required parameter: project_name"}

        full_path = os.path.join(target_path, project_name)
        
        if os.path.exists(full_path):
            return {"success": False, "message": f"Directory already exists: {full_path}"}
            
        try:
            # 1. Create directory
            os.makedirs(full_path)
            
            # 2. Run specific setup based on type
            commands = [f"cd {full_path}"]
            
            if project_type == "python":
                commands.extend([
                    "python -m venv venv",
                    "git init",
                    # create basic files
                    "echo print('Hello from Specter!') > main.py",
                    "echo venv/ > .gitignore"
                ])
            elif project_type == "node":
                commands.extend([
                    "npm init -y",
                    "git init",
                    "echo console.log('Hello from Specter!'); > index.js",
                    "echo node_modules/ > .gitignore"
                ])
            else:
                commands.extend(["git init"]) # Generic fallback
                
            # 3. Always open in VS Code
            commands.append("code .")
            
            # Execute the chained commands in a single shell
            full_command = " && ".join(commands)
            print(f"[*] Executing scaffold commands: {full_command}")
            
            subprocess.run(full_command, shell=True, check=True)
            
            return {
                "success": True, 
                "message": f"Successfully scaffolded {project_type} project '{project_name}' at {full_path}"
            }
            
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Command execution failed: {e}"}
        except Exception as e:
            return {"success": False, "message": f"Error during scaffolding: {e}"}
