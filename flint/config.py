import os
import json
from pathlib import Path
from platformdirs import user_config_dir, user_cache_dir

APP_NAME = "textual-md-viewer"

def get_config_dir() -> Path:
    path = Path(user_config_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_cache_dir() -> Path:
    path = Path(user_cache_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_themes_dir() -> Path:
    path = get_config_dir() / "themes"
    path.mkdir(parents=True, exist_ok=True)
    return path

# Ensure directories exist on import
CONFIG_DIR = get_config_dir()
CACHE_DIR = get_cache_dir()
THEMES_DIR = get_themes_dir()
SETTINGS_FILE = CONFIG_DIR / "settings.json"

_settings_cache = None

def load_settings() -> dict:
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
        
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                _settings_cache = json.load(f)
                return _settings_cache
        except Exception:
            pass
    _settings_cache = {}
    return _settings_cache

def save_settings(settings: dict) -> None:
    global _settings_cache
    _settings_cache = settings
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass
