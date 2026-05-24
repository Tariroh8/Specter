import os
import json
from pathlib import Path

# Define the user-specific data directory for Specter
APP_DATA_DIR = Path(os.path.expandvars(r"%APPDATA%\Specter"))
CONFIG_PATH = APP_DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "model_provider": "gemini", # Options: 'gemini', 'ollama', 'openai'
    "model_name": "gemini-2.5-pro",
    "discord_bot_token": ""
}

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONFIG ERROR] Failed to load config: {e}")
        return DEFAULT_CONFIG

def save_config(config_data: dict):
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"[CONFIG ERROR] Failed to save config: {e}")

def get_setting(key: str, default=None):
    config = load_config()
    return config.get(key, default)

def set_setting(key: str, value):
    config = load_config()
    config[key] = value
    save_config(config)
