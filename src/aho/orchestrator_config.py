"""Orchestrator configuration — reads ~/.config/aho/orchestrator.json.

0.2.7 W5. Engine field is reserved metadata only (no behavior change).
"""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "aho" / "orchestrator.json"

_DEFAULTS = {
    "engine": "gemini",
    "search": {
        "provider": "brave",
        "token_secret_key": "brave_search_token",
    },
    "openclaw": {
        "default_model": "qwen3.5:9b",
    },
    "nemoclaw": {
        "classifier_model": "nemotron-mini:4b",
    },
}


def load_config() -> dict:
    """Load orchestrator config, falling back to defaults if missing."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            # Merge with defaults for missing keys
            merged = _DEFAULTS.copy()
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError):
            return _DEFAULTS.copy()
    return _DEFAULTS.copy()


def save_config(config: dict):
    """Write orchestrator config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    CONFIG_PATH.chmod(0o600)


def ensure_config():
    """Create default config if it doesn't exist."""
    if not CONFIG_PATH.exists():
        save_config(_DEFAULTS.copy())


def get_openclaw_model() -> str:
    """Get the default OpenClaw model from config."""
    config = load_config()
    return config.get("openclaw", {}).get("default_model", "qwen3.5:9b")


def get_nemoclaw_model() -> str:
    """Get the NemoClaw classifier model from config."""
    config = load_config()
    return config.get("nemoclaw", {}).get("classifier_model", "nemotron-mini:4b")


def get_search_token_key() -> str:
    """Get the fernet store key name for the search token."""
    config = load_config()
    return config.get("search", {}).get("token_secret_key", "brave_search_token")
