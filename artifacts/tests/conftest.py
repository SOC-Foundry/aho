"""Test-suite conftest - autouse checkpoint isolation.

Allowlisted test modules that call emit_workstream_start / emit_workstream_complete
get a per-test tmp_path scoped via AHO_TEST_CHECKPOINT_DIR. The source-code
guard in workstream_events._resolve_checkpoint_root() raises TestIsolationError
on any other test module that emits without isolation - making the failure mode
loud rather than silently corrupting the real .aho-checkpoint.json. Third-
recurrence fix for test_workstream_events.py - prior occurrences in 0.2.13,
0.2.14, 0.2.15 W0/W3, plus a fourth recurrence in 0.2.16 W0. The 0.2.17 W0
fix (F-W0-004 closure) hardens the source side so allowlist drift cannot
re-introduce the failure mode.

test_paths.py tests find_project_root itself, so the autouse is disabled
for that module.
"""
import json
import pytest


# Allowlisted test modules that legitimately call emit_workstream_*. The
# fixture below pre-creates the .aho.json + .aho-checkpoint.json files in
# tmp_path, monkey-patches find_project_root, AND sets AHO_TEST_CHECKPOINT_DIR
# so the source-code guard accepts the call. Adding a new module here is the
# explicit opt-in path; the source-code guard catches anything missed.
_CHECKPOINT_MUTATING_MODULES = {
    "test_workstream_events",
    "test_workstream_events_v2",
    "test_schema_v3",
    "test_ws_fixes",
}


@pytest.fixture(autouse=True)
def _isolate_project_root(request, tmp_path, monkeypatch):
    if request.module.__name__ not in _CHECKPOINT_MUTATING_MODULES:
        return

    # Create a minimal project structure so emit_workstream_start/complete
    # find a valid tmp checkpoint file instead of mutating the real one.
    (tmp_path / ".aho.json").write_text(json.dumps({
        "name": "test",
        "artifact_prefix": "test",
        "current_iteration": "test",
        "phase": 0,
    }))
    (tmp_path / ".aho-checkpoint.json").write_text(json.dumps({
        "iteration": "test",
        "phase": 0,
        "current_workstream": None,
        "workstreams": {},
    }))

    monkeypatch.setattr("aho.paths.find_project_root", lambda *a, **k: tmp_path)
    monkeypatch.setenv("AHO_TEST_CHECKPOINT_DIR", str(tmp_path))
