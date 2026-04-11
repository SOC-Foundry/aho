"""Tests for new doctor checks (0.2.3 W4)."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_check_age_key_present(tmp_path):
    key = tmp_path / "age.key"
    key.write_text("AGE-SECRET-KEY-...")
    key.chmod(0o600)
    with patch("aho.doctor.Path.home", return_value=tmp_path):
        # Need to create the expected path structure
        config_dir = tmp_path / ".config" / "aho"
        config_dir.mkdir(parents=True)
        real_key = config_dir / "age.key"
        real_key.write_text("AGE-SECRET-KEY-...")
        real_key.chmod(0o600)
        from aho.doctor import _check_age_key
        status, msg = _check_age_key()
        assert status == "ok"


def test_check_dashboard_port():
    from aho.doctor import _check_dashboard_port
    status, msg = _check_dashboard_port()
    assert status in ("ok", "warn")


def test_check_role_agents():
    from aho.doctor import _check_role_agents
    status, msg = _check_role_agents()
    assert status == "ok"
    assert "all role agents importable" in msg


@patch("aho.doctor.subprocess.run")
def test_check_mcp_fleet_missing(mock_run):
    mock_run.return_value = MagicMock(stdout="npm global packages:\n")
    from aho.doctor import _check_mcp_fleet
    status, msg = _check_mcp_fleet()
    assert status == "warn"
    assert "missing" in msg


@patch("aho.doctor.subprocess.run")
def test_check_mcp_fleet_all_present(mock_run):
    packages = [
        "firebase-tools", "@upstash/context7-mcp", "firecrawl-mcp",
        "@playwright/mcp", "flutter-mcp",
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-github",
        "@modelcontextprotocol/server-google-drive",
        "@modelcontextprotocol/server-slack",
        "@modelcontextprotocol/server-fetch",
        "@modelcontextprotocol/server-memory",
        "@modelcontextprotocol/server-sequential-thinking",
    ]
    mock_run.return_value = MagicMock(stdout="\n".join(packages))
    from aho.doctor import _check_mcp_fleet
    status, msg = _check_mcp_fleet()
    assert status == "ok"
