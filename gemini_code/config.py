"""
Configuration manager for Gemini Code.
Stores persistent settings in ~/.gemini-code/config.json
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".gemini-code"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "api_key": "",
    "model": "gemini-2.5-flash",
    "language": "ru",
    "theme": "auto",
    "proxy_mode": "auto",
    "custom_proxy_url": "",
    "confirm_danger_actions": True,
    "active_subagent": "coder",
}

class Config:
    def __init__(self):
        self._data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Load settings from JSON file if exists."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data.update(loaded)
            except Exception:
                pass

    def save(self):
        """Save settings to ~/.gemini-code/config.json."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def is_first_run(self) -> bool:
        return not CONFIG_FILE.exists() or not self._data.get("api_key")

    def get(self, key: str, default=None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @property
    def model(self) -> str:
        return self._data.get("model", "gemini-2.5-flash")

    @property
    def language(self) -> str:
        return self._data.get("language", "ru")

    @property
    def theme(self) -> str:
        return self._data.get("theme", "auto")

    @property
    def proxy_mode(self) -> str:
        return self._data.get("proxy_mode", "auto")

    @property
    def custom_proxy_url(self) -> str:
        return self._data.get("custom_proxy_url", "")

    @property
    def confirm_danger_actions(self) -> bool:
        return self._data.get("confirm_danger_actions", True)

    @property
    def active_subagent(self) -> str:
        return self._data.get("active_subagent", "coder")

# Global singleton
config = Config()
