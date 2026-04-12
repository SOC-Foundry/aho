"""Tests for aho.dashboard.aggregator — W1 0.2.7."""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def project_root(tmp_path):
    """Create minimal project structure for aggregator tests."""
    # .aho.json
    (tmp_path / ".aho.json").write_text(json.dumps({
        "current_iteration": "0.2.7",
        "phase": 0,
        "dashboard_port": 7800,
    }))

    # .aho-checkpoint.json
    (tmp_path / ".aho-checkpoint.json").write_text(json.dumps({
        "iteration": "0.2.7",
        "run_type": "single-agent",
        "status": "active",
        "current_workstream": "W1",
    }))

    # components.yaml (minimal)
    harness = tmp_path / "artifacts" / "harness"
    harness.mkdir(parents=True)
    (harness / "components.yaml").write_text(
        "schema_version: 1\n"
        "components:\n"
        "  - name: cli\n"
        "    kind: python_module\n"
        "    path: src/aho/cli.py\n"
        "    status: active\n"
        "    owner: soc-foundry\n"
    )

    # model-fleet.txt
    (harness / "model-fleet.txt").write_text("qwen3.5:9b\nnemotron-mini:4b\n")

    # event log
    data = tmp_path / "data"
    data.mkdir()
    events = []
    for i in range(25):
        events.append(json.dumps({
            "timestamp": f"2026-04-11T{i:02d}:00:00+00:00",
            "event_type": "test",
            "source_agent": "test",
            "target": "test",
            "action": "test",
        }))
    (data / "aho_event_log.jsonl").write_text("\n".join(events) + "\n")

    # web/claw3d placeholder
    web = tmp_path / "web" / "claw3d"
    web.mkdir(parents=True)
    (web / "index.html").write_text("<html><body>placeholder</body></html>")

    os.environ["AHO_PROJECT_ROOT"] = str(tmp_path)
    yield tmp_path
    os.environ.pop("AHO_PROJECT_ROOT", None)


def test_system_state(project_root):
    from aho.dashboard.aggregator import _system_state, _cache
    _cache["data"] = None  # clear cache
    state = _system_state()
    assert state["iteration"] == "0.2.7"
    assert state["phase"] == 0
    assert state["run_type"] == "single-agent"


def test_component_state(project_root):
    from aho.dashboard.aggregator import _component_state, _cache
    _cache["data"] = None
    comps = _component_state()
    assert len(comps) == 1
    assert comps[0]["name"] == "cli"
    assert comps[0]["kind"] == "python_module"


def test_trace_state_returns_last_20(project_root, monkeypatch):
    import aho.logger
    def mock_event_log_path():
        return project_root / "data" / "aho_event_log.jsonl"
    monkeypatch.setattr(aho.logger, "event_log_path", mock_event_log_path)
    
    from aho.dashboard.aggregator import _trace_state, _cache
    _cache["data"] = None
    traces = _trace_state()
    assert len(traces) == 20
    assert "24" in traces[0]["timestamp"]


def test_daemon_state_returns_7(project_root):
    from aho.dashboard.aggregator import _daemon_state, _cache
    _cache["data"] = None
    daemons = _daemon_state()
    assert len(daemons) == 7
    names = [d["name"] for d in daemons]
    assert "openclaw" in names
    assert "nemoclaw" in names
    assert "telegram" in names
    assert "harness-watcher" in names
    assert "otel-collector" in names
    assert "jaeger" in names
    assert "dashboard" in names


def test_get_state_returns_all_sections(project_root):
    from aho.dashboard.aggregator import get_state, _cache
    _cache["data"] = None
    state = get_state(force=True)
    assert "system" in state
    assert "components" in state
    assert "daemons" in state
    assert "traces" in state
    assert "mcp" in state
    assert "models" in state


def test_get_state_caching(project_root):
    from aho.dashboard.aggregator import get_state, _cache
    _cache["data"] = None
    s1 = get_state(force=True)
    s2 = get_state()  # should be cached
    assert s1 is s2


def test_mcp_state_returns_list(project_root):
    from aho.dashboard.aggregator import _mcp_state, _cache
    _cache["data"] = None
    mcp = _mcp_state()
    assert isinstance(mcp, list)
    assert len(mcp) > 0
    assert "name" in mcp[0]
    assert "status" in mcp[0]


def test_model_state_returns_list(project_root):
    from aho.dashboard.aggregator import _model_state, _cache
    _cache["data"] = None
    models = _model_state()
    assert isinstance(models, list)
    assert len(models) == 2
    assert models[0]["name"] == "qwen3.5:9b"
