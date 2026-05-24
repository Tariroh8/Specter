from typing import Any, Dict, List

class BaseSkill:
    """
    The base class for all Specter Skills (Actions).
    Every skill must inherit from this class and implement the execute() method.
    """
    name: str = "BaseSkill"
    description: str = "A basic skill template"
    parameters: Dict[str, str] = {} # e.g. {"project_name": "Name of the project"}

    def __init__(self):
        pass

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the skill's logic.
        Must return a dictionary containing at least a 'success' boolean and a 'message'.
        """
        raise NotImplementedError("Skills must implement the execute() method.")

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Returns metadata about the skill for the registry and future LLM context."""
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.parameters
        }
