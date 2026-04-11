import json
import pathlib
import pytest
from aho.feedback.build_log_stub import generate_stub

def test_generate_stub(tmp_path):
    # Setup mock project structure
    project_root = tmp_path
    (project_root / "data").mkdir()
    (project_root / "artifacts" / "iterations" / "0.1.99").mkdir(parents=True)
    
    # Mock checkpoint
    checkpoint = {
        "iteration": "0.1.99",
        "run_type": "hygiene",
        "executor": "test-agent",
        "workstreams": {
            "W0": "pass",
            "W1": "pending"
        }
    }
    (project_root / ".aho-checkpoint.json").write_text(json.dumps(checkpoint))
    
    # Mock event log
    events = [
        {"iteration": "0.1.99", "workstream": "W0", "event_type": "test_event", "timestamp": "2026-04-10T10:00:00Z", "source_agent": "test-agent"},
        {"iteration": "0.1.99", "workstream": "W0", "event_type": "cli_invocation", "timestamp": "2026-04-10T10:01:00Z", "source_agent": "aho-cli"},
        {"iteration": "0.1.13", "workstream": "W5", "event_type": "other_it", "timestamp": "2026-04-10T09:00:00Z"} # Should be filtered out
    ]
    with open(project_root / "data" / "aho_event_log.jsonl", "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
            
    # Generate stub
    output_path = generate_stub("0.1.99", project_root=project_root)
    
    # Assertions
    assert output_path.exists()
    content = output_path.read_text()
    assert "# aho 0.1.99 — Build Log (Stub)" in content
    assert "**Run Type:** hygiene" in content
    assert "Auto-generated from checkpoint + event log" in content
    assert "| W0 | test-agent | pass | 2 |" in content
    assert "| W1 | test-agent | pending | 0 |" in content
    assert "- **test_event:** 1" in content
    assert "- **cli_invocation:** 1" in content
    assert "other_it" not in content # Filtered out
