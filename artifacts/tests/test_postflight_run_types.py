import json
import pathlib
import pytest
from aho.postflight.bundle_quality import check as check_bundle
from aho.postflight.run_complete import check as check_run

def setup_mock_project(tmp_path, iteration="0.1.99", run_type="mixed", components=4):
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "artifacts" / "iterations" / iteration).mkdir(parents=True, exist_ok=True)
    
    # .aho.json
    (tmp_path / ".aho.json").write_text(json.dumps({
        "current_iteration": iteration,
        "artifact_prefix": "aho"
    }))
    
    # .aho-checkpoint.json
    (tmp_path / ".aho-checkpoint.json").write_text(json.dumps({
        "iteration": iteration,
        "run_type": run_type,
        "workstreams": {"W0": {"status": "pass"}}
    }))
    
    # Event log (for run_complete check)
    event_log = tmp_path / "data" / "aho_event_log.jsonl"
    events = []
    for i in range(components):
        events.append({"iteration": iteration, "source_agent": f"agent-{i}", "event_type": "test"})
    with open(event_log, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
            
    # Bundle (for bundle_quality check)
    bundle_path = tmp_path / "artifacts" / "iterations" / iteration / f"aho-bundle-{iteration}.md"
    content = [
        f"# aho - Bundle {iteration}",
        "## §22. Agentic Components",
        f"**Unique components:** {components}",
        "",
        # Add other sections to satisfy validate_bundle size and headers
        "## §1. Design", "D" * 10000,
        "## §2. Plan", "P" * 10000,
        "## §3. Build Log", "B" * 5000,
        "## §4. Report", "R" * 5000,
        "## §5. Run Report", "RR" * 5000,
        "## §6. Harness", "H" * 5000,
        "## §7. README", "RE" * 5000,
        "## §8. CHANGELOG", "C" * 2000,
        "## §9. CLAUDE.md", "CL" * 2000,
        "## §10. GEMINI.md", "G" * 2000,
        "## §11. .aho.json", "J" * 1000,
        "## §12. Sidecars", "S" * 100,
        "## §13. Gotcha Registry", "GR" * 1000,
        "## §14. Script Registry", "SR" * 100,
        "## §15. ahomw MANIFEST", "M" * 500,
        "## §16. install.fish", "I" * 1000,
        "## §17. COMPATIBILITY", "CO" * 500,
        "## §18. projects.json", "PJ" * 500,
        "## §19. Event Log (tail 500)", "E" * 1000,
        "## §20. File Inventory (sha256_16)", "FI" * 1000,
        "## §21. Environment", "ENV" * 1000,
        "## §22. Component Checklist", "CC" * 1000,
        "## §23. Component Manifest", "CM" * 1000,
    ]
    bundle_path.write_text("\n".join(content))
    
    # Run report (for sign-off check in run_complete)
    run_path = tmp_path / "artifacts" / "iterations" / iteration / f"aho-run-{iteration}.md"
    run_path.write_text("## Sign-off\n- [x] 1\n- [x] 2\n- [x] 3\n- [x] 4\n- [x] 5\n## Agent Questions\n")

def test_run_type_mixed_pass(tmp_path, monkeypatch):
    setup_mock_project(tmp_path, run_type="mixed", components=3)
    monkeypatch.chdir(tmp_path)
    
    status, msg = check_bundle()
    if status != "ok":
        print(f"DEBUG: check_bundle failed with: {msg}")
    assert status == "ok"
    
    status, msg = check_run()
    assert status == "ok"

def test_run_type_mixed_fail(tmp_path, monkeypatch):
    setup_mock_project(tmp_path, run_type="mixed", components=2)
    monkeypatch.chdir(tmp_path)
    
    status, msg = check_bundle()
    assert status == "fail"
    assert "component count 2 < 3" in msg
    
    status, msg = check_run()
    assert status == "fail"
    assert "Component floor not met: 2 < 3" in msg

def test_run_type_agent_execution_fail(tmp_path, monkeypatch):
    setup_mock_project(tmp_path, run_type="agent_execution", components=5)
    monkeypatch.chdir(tmp_path)
    
    status, msg = check_bundle()
    assert status == "fail"
    assert "component count 5 < 6" in msg
