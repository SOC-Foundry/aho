"""Test-suite conftest — autouse checkpoint isolation (0.2.16 W0).

Patches `aho.paths.find_project_root` to return a per-test `tmp_path` so no
test mutates the real `.aho-checkpoint.json` or `.aho.json`. Third-recurrence
fix for test_workstream_events.py and test_workstream_events_v2.py — prior
occurrences in 0.2.13, 0.2.14, 0.2.15 W0/W3. Those test files call
emit_workstream_start/complete which read the checkpoint path from
find_project_root() internally (inline import), so patching LOG_PATH alone
did not stop the leak.

test_paths.py tests find_project_root itself, so the autouse is disabled
for that module.
"""
import json
import pytest


# Scope the autouse to ONLY the modules that corrupt checkpoint. Previous
# attempt with unconditional autouse broke 15+ tests that legitimately read
# real project files. The bug is specific to emit_workstream_start/complete
# in workstream_events.py reading the real checkpoint path via inline
# find_project_root(); only test files that exercise those functions hit it.
_CHECKPOINT_MUTATING_MODULES = {
    "test_workstream_events",
    "test_workstream_events_v2",
    # test_schema_v3 mutates real checkpoint via emit_workstream_complete on
    # W_V3_TEST / W_V3_COMBO / W_V2_COMPAT / W_V1_COMPAT — confirmed in the
    # 0.2.16 W0 fourth-recurrence run. test_ws_fixes uses emit_workstream_start
    # on "W_TEST_IP". test_emit_sibling_preservation is safe: it already patches
    # find_project_root inline.
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
