"""Tests for the mechanical report builder."""
import json
import pytest
from pathlib import Path
from aho.feedback.report_builder import build_report


@pytest.fixture
def mock_project(tmp_path):
    """Set up a minimal project structure for report builder tests."""
    (tmp_path / "data").mkdir()
    (tmp_path / "artifacts" / "iterations" / "0.1.14").mkdir(parents=True)
    (tmp_path / "artifacts" / "harness").mkdir(parents=True)

    # .aho.json
    (tmp_path / ".aho.json").write_text(json.dumps({
        "aho_version": "0.1",
        "name": "aho",
        "artifact_prefix": "aho",
        "current_iteration": "0.1.14",
        "last_completed_iteration": "0.1.13",
        "phase": 0,
    }))

    # checkpoint
    (tmp_path / ".aho-checkpoint.json").write_text(json.dumps({
        "iteration": "0.1.14",
        "phase": 0,
        "run_type": "mixed",
        "status": "closed",
        "workstreams": {
            "W0": "pass",
            "W1": "pass",
            "W2": "pass",
            "W3": "fail",
        },
        "executor": "gemini-cli",
    }))

    # event log
    events = [
        {"iteration": "0.1.14", "workstream_id": "W0", "event_type": "cli_invocation",
         "timestamp": "2026-04-11T01:00:00Z", "source_agent": "aho-cli",
         "status": "success", "action": "doctor"},
        {"iteration": "0.1.14", "workstream_id": "W1", "event_type": "llm_call",
         "timestamp": "2026-04-11T01:05:00Z", "source_agent": "qwen",
         "status": "success", "action": "generate"},
        {"iteration": "0.1.14", "workstream_id": "W2", "event_type": "tool_call",
         "timestamp": "2026-04-11T01:10:00Z", "source_agent": "gemini",
         "status": "warn", "action": "build", "error": "timeout on first attempt"},
        {"iteration": "0.1.13", "workstream_id": "W0", "event_type": "other",
         "timestamp": "2026-04-10T01:00:00Z", "source_agent": "test"},
    ]
    with open(tmp_path / "data" / "aho_event_log.jsonl", "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    return tmp_path


def test_report_produces_all_sections(mock_project):
    output = build_report("0.1.14", project_root=mock_project)
    assert output.exists()
    content = output.read_text()

    expected_sections = [
        "# Report",
        "## Executive Summary",
        "## Workstream Detail",
        "## Component Activity",
        "## Postflight Results",
        "## Risk Register",
        "## Carryovers",
        "## Next Iteration Recommendation",
    ]
    for section in expected_sections:
        assert section in content, f"Missing section: {section}"


def test_report_workstream_counts(mock_project):
    output = build_report("0.1.14", project_root=mock_project)
    content = output.read_text()
    assert "4 workstreams" in content
    assert "3 passed" in content
    assert "1 failed" in content


def test_report_filters_events_by_iteration(mock_project):
    output = build_report("0.1.14", project_root=mock_project)
    content = output.read_text()
    assert "3 events" in content


def test_report_risk_register_captures_warnings(mock_project):
    output = build_report("0.1.14", project_root=mock_project)
    content = output.read_text()
    assert "timeout on first attempt" in content


def test_report_output_path(mock_project):
    output = build_report("0.1.14", project_root=mock_project)
    assert output.name == "aho-report-0.1.14.md"
    assert "iterations" in str(output)


def test_report_no_qwen_required(mock_project):
    """Report builder must produce output without any LLM call."""
    output = build_report("0.1.14", project_root=mock_project)
    assert output.exists()
    assert output.stat().st_size > 500
