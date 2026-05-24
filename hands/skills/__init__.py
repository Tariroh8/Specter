import os
import importlib
import inspect
from typing import Dict, Type
from hands.skills.base import BaseSkill

# A registry to hold loaded skills mapping their name to the class
SKILL_REGISTRY: Dict[str, Type[BaseSkill]] = {}

def load_skills():
    """Dynamically loads all skill classes from the skills directory."""
    global SKILL_REGISTRY
    SKILL_REGISTRY.clear()
    
    skills_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(skills_dir):
        if filename.endswith('.py') and filename not in ('__init__.py', 'base.py'):
            module_name = filename[:-3]
            
            try:
                # Import the module
                module = importlib.import_module(f'hands.skills.{module_name}')
                
                # Find all classes that inherit from BaseSkill
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                        SKILL_REGISTRY[obj.name] = obj
                        print(f"[+] Loaded skill: {obj.name}")
                        
            except Exception as e:
                print(f"[-] Failed to load skill from {filename}: {e}")

def get_skill(name: str) -> Type[BaseSkill]:
    """Retrieves a skill class by its name."""
    return SKILL_REGISTRY.get(name)

def get_all_skills_metadata() -> Dict[str, dict]:
    """Returns metadata for all loaded skills. Useful for LLM context."""
    return {name: cls.get_metadata() for name, cls in SKILL_REGISTRY.items()}

# Load skills when the package is imported
load_skills()
