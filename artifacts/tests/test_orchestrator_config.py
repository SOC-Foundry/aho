"""Tests for aho.orchestrator_config — W5 0.2.7."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_load_defaults(tmp_path):
    """Config returns defaults when file doesn't exist."""
    with patch("aho.orchestrator_config.CONFIG_PATH", tmp_path / "missing.json"):
        from aho.orchestrator_config import load_config
        config = load_config()
        assert config["engine"] == "gemini"
        assert config["openclaw"]["default_model"] == "qwen3.5:9b"
        assert config["nemoclaw"]["classifier_model"] == "nemotron-mini:4b"
        assert config["search"]["provider"] == "brave"


def test_save_and_load(tmp_path):
    """Config round-trips through save/load."""
    config_path = tmp_path / "orchestrator.json"
    with patch("aho.orchestrator_config.CONFIG_PATH", config_path):
        from aho.orchestrator_config import save_config, load_config
        custom = {
            "engine": "gemini",
            "search": {"provider": "brave", "token_secret_key": "my_key"},
            "openclaw": {"default_model": "qwen3.5:14b"},
            "nemoclaw": {"classifier_model": "nemotron-mini:4b"},
        }
        save_config(custom)
        assert config_path.exists()
        loaded = load_config()
        assert loaded["openclaw"]["default_model"] == "qwen3.5:14b"


def test_ensure_config_creates_file(tmp_path):
    """ensure_config creates default file if missing."""
    config_path = tmp_path / "orchestrator.json"
    with patch("aho.orchestrator_config.CONFIG_PATH", config_path):
        from aho.orchestrator_config import ensure_config
        ensure_config()
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert data["engine"] == "gemini"


def test_get_openclaw_model_default(tmp_path):
    """get_openclaw_model returns default when no config."""
    with patch("aho.orchestrator_config.CONFIG_PATH", tmp_path / "missing.json"):
        from aho.orchestrator_config import get_openclaw_model
        assert get_openclaw_model() == "qwen3.5:9b"


def test_get_nemoclaw_model_default(tmp_path):
    """get_nemoclaw_model returns default when no config."""
    with patch("aho.orchestrator_config.CONFIG_PATH", tmp_path / "missing.json"):
        from aho.orchestrator_config import get_nemoclaw_model
        assert get_nemoclaw_model() == "nemotron-mini:4b"
