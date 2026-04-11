"""Tests for the component manifest system."""
import json
import pytest
from pathlib import Path
from aho.components.manifest import load_components, attribute_workload, render_section


def test_load_components_from_project():
    """Load components from the real components.yaml — should have ≥30 entries."""
    from aho.paths import get_harness_dir
    yaml_path = get_harness_dir() / "components.yaml"
    components = load_components(yaml_path)
    assert len(components) >= 30, f"Expected ≥30 components, got {len(components)}"


def test_named_stubs_present():
    """openclaw, nemoclaw, telegram must be present as stubs."""
    from aho.paths import get_harness_dir
    yaml_path = get_harness_dir() / "components.yaml"
    components = load_components(yaml_path)
    names = {c.name for c in components}
    assert "openclaw" in names
    assert "nemoclaw" in names
    assert "telegram" in names

    stubs = {c.name: c for c in components if c.status == "stub"}
    assert "openclaw" in stubs
    assert "nemoclaw" in stubs
    assert "telegram" in stubs


def test_attribute_workload_sums_to_one():
    """Workload attribution should sum to ~1.0."""
    events = [
        {"source_agent": "qwen", "event_type": "llm_call"},
        {"source_agent": "qwen", "event_type": "llm_call"},
        {"source_agent": "gemini", "event_type": "llm_call"},
        {"source_agent": "aho-cli", "event_type": "cli_invocation"},
    ]
    workload = attribute_workload(events)
    assert abs(sum(workload.values()) - 1.0) < 0.01


def test_attribute_workload_empty():
    assert attribute_workload([]) == {}


def test_render_section_produces_markdown():
    """render_section should produce a markdown table with stubs visible."""
    from aho.paths import get_harness_dir
    yaml_path = get_harness_dir() / "components.yaml"
    section = render_section(yaml_path)
    assert "openclaw" in section
    assert "nemoclaw" in section
    assert "telegram" in section
    assert "stub" in section
    assert "Total components:" in section


def test_load_components_missing_file(tmp_path):
    """Loading from a nonexistent file returns empty list."""
    result = load_components(tmp_path / "nonexistent.yaml")
    assert result == []
