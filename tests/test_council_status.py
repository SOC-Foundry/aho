import pytest
import json
import subprocess
from aho.council.status import collect_status, format_human, format_json, CouncilStatus
from aho.council.inventory import inventory

def test_collect_status_returns_valid_object():
    status = collect_status()
    assert isinstance(status, CouncilStatus)
    assert len(status.members) >= 7

def test_format_human_basic():
    status = collect_status()
    out = format_human(status, verbose=False)
    assert "Council Health Score:" in out
    assert "Nemoclaw Socket:" in out
    assert "Ollama Models:" in out

def test_format_human_verbose_includes_g083():
    status = collect_status()
    out = format_human(status, verbose=True)
    assert "G083 Anti-Pattern Density" in out

def test_format_json_returns_valid_json():
    status = collect_status()
    out = format_json(status)
    parsed = json.loads(out)
    assert "members" in parsed
    assert isinstance(parsed["members"], list)

def test_format_json_member_filter():
    status = collect_status()
    out = format_json(status, member="qwen")
    parsed = json.loads(out)
    assert "name" in parsed
    assert "qwen" in parsed["name"].lower()

def test_degrades_gracefully_when_components_unreachable(monkeypatch):
    # Test that collect_status doesn't crash if ollama is missing
    monkeypatch.setenv("PATH", "")
    status = collect_status()
    assert isinstance(status, CouncilStatus)
    assert status.ollama_models == []

def test_backward_compat_with_inventory():
    # Test that inventory still returns the base list
    base_members = inventory()
    assert len(base_members) >= 7
    assert hasattr(base_members[0], "name")
