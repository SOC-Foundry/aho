"""Tests for config.py port and role functions (0.2.3 W4)."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_get_dashboard_port_from_json(tmp_path):
    aho_json = tmp_path / ".aho.json"
    aho_json.write_text(json.dumps({"dashboard_port": 7850}))
    from aho.config import get_dashboard_port
    assert get_dashboard_port(aho_json) == 7850


def test_get_dashboard_port_default(tmp_path):
    aho_json = tmp_path / ".aho.json"
    aho_json.write_text(json.dumps({}))
    from aho.config import get_dashboard_port
    port = get_dashboard_port(aho_json)
    assert isinstance(port, int)
    assert 7000 <= port <= 8000


def test_get_aho_role_from_json(tmp_path):
    aho_json = tmp_path / ".aho.json"
    aho_json.write_text(json.dumps({"aho_role": "public_host"}))
    from aho.config import get_aho_role
    assert get_aho_role(aho_json) == "public_host"


def test_get_aho_role_default(tmp_path):
    aho_json = tmp_path / ".aho.json"
    aho_json.write_text(json.dumps({}))
    from aho.config import get_aho_role
    assert get_aho_role(aho_json) == "localhost"


def test_check_port_available():
    from aho.config import check_port_available
    # Port 0 should always be available (OS picks random port)
    # Just test the function returns a bool
    result = check_port_available(0)
    assert isinstance(result, bool)
