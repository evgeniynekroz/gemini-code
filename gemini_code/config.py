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
    "model": "gemini-2.0-flash",
    "language": "ru",
    "theme": "auto",
    "proxy_mode": "auto",
    "custom_proxy_url": "",
    "custom_base_url": "",
    "confirm_danger_actions": True,
    "active_subagent": "coder",
}

class Config:
    def __init__(self):
        self._data = DEFAULT_CONFIG.copy()
        self._model_override = None
        self._subagent_override = None
        self._confirm_danger_override = None
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
        return not self.api_key

    def get(self, key: str, default=None) -> Any:
        return self._data.get(key, default)

    def reset_overrides(self):
        """Reset session CLI flag overrides back to defaults / stored config."""
        self._model_override = None
        self._subagent_override = None
        self._confirm_danger_override = None

    def set(self, key: str, value: Any):
        self._data[key] = value
        if key == "model":
            self._model_override = value
        elif key == "active_subagent":
            self._subagent_override = value
        elif key == "confirm_danger_actions":
            self._confirm_danger_override = value
        self.save()

    @property
    def api_key(self) -> str:
        # Check environment variable first
        env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if env_key:
            return env_key.strip()
        return self._data.get("api_key", "").strip()

    @property
    def model(self) -> str:
        if getattr(self, "_model_override", None):
            return self._model_override
        env_model = os.environ.get("GEMINI_MODEL")
        if env_model:
            return env_model.strip()
        stored = self._data.get("model", "gemini-2.0-flash")
        if "2.5" in stored:
            stored = "gemini-2.0-flash"
            self._data["model"] = stored
        return stored

    @model.setter
    def model(self, val: str):
        self._model_override = val

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
        env_proxy = os.environ.get("GEMINI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if env_proxy and not self._data.get("custom_proxy_url"):
            return env_proxy.strip()
        return self._data.get("custom_proxy_url", "").strip()

    @property
    def custom_base_url(self) -> str:
        env_base = os.environ.get("GEMINI_BASE_URL")
        if env_base:
            return env_base.strip()
        return self._data.get("custom_base_url", "").strip()

    @property
    def confirm_danger_actions(self) -> bool:
        if getattr(self, "_confirm_danger_override", None) is not None:
            return self._confirm_danger_override
        return self._data.get("confirm_danger_actions", True)

    @confirm_danger_actions.setter
    def confirm_danger_actions(self, val: bool):
        self._confirm_danger_override = val

    @property
    def active_subagent(self) -> str:
        if getattr(self, "_subagent_override", None):
            return self._subagent_override
        return self._data.get("active_subagent", "coder")

    @active_subagent.setter
    def active_subagent(self, val: str):
        self._subagent_override = val

# Global singleton
config = Config()
