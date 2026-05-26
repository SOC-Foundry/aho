"""Source-side guard against accidental real-checkpoint mutation.

0.2.17 W0 Bucket 1 - F-W0-004 closure. The conftest allowlist
(_CHECKPOINT_MUTATING_MODULES) keeps known emit-using test modules
isolated. This test exercises the source-code guard in
workstream_events._resolve_checkpoint_root() that catches anything the
allowlist misses: any test module not in the allowlist that calls
emit_workstream_start without setting AHO_TEST_CHECKPOINT_DIR raises
TestIsolationError instead of silently corrupting the real checkpoint.

Belt-and-suspenders defense: allowlist provides positive isolation;
guard catches drift.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aho.workstream_events import (
    TestIsolationError,
    _resolve_checkpoint_root,
    emit_workstream_start,
)


def test_guard_raises_when_emitting_outside_allowlist(monkeypatch, tmp_path):
    """Test module not in allowlist + no AHO_TEST_CHECKPOINT_DIR + real
    project root resolved → TestIsolationError. This module is intentionally
    NOT in _CHECKPOINT_MUTATING_MODULES so the guard fires by default.

    Simulate the failure mode by pointing find_project_root at a non-tmp
    path and confirming the guard catches it.
    """
    fake_real_root = Path("/home/kthompson/dev/projects/aho")
    monkeypatch.setattr("aho.paths.find_project_root", lambda *a, **k: fake_real_root)
    monkeypatch.delenv("AHO_TEST_CHECKPOINT_DIR", raising=False)

    with pytest.raises(TestIsolationError) as exc:
        _resolve_checkpoint_root()
    msg = str(exc.value)
    assert "PYTEST_CURRENT_TEST" in msg
    assert "AHO_TEST_CHECKPOINT_DIR" in msg
    assert "_CHECKPOINT_MUTATING_MODULES" in msg


def test_guard_accepts_explicit_test_checkpoint_dir(monkeypatch, tmp_path):
    """AHO_TEST_CHECKPOINT_DIR override bypasses the guard cleanly."""
    monkeypatch.setenv("AHO_TEST_CHECKPOINT_DIR", str(tmp_path))
    resolved = _resolve_checkpoint_root()
    assert resolved == tmp_path


def test_guard_accepts_tmpdir_resolved_root(monkeypatch, tmp_path):
    """find_project_root resolving under the system tempdir is acceptable
    inside pytest - that is the conftest happy path.
    """
    monkeypatch.delenv("AHO_TEST_CHECKPOINT_DIR", raising=False)
    monkeypatch.setattr("aho.paths.find_project_root", lambda *a, **k: tmp_path)
    resolved = _resolve_checkpoint_root()
    assert resolved == tmp_path


def test_real_checkpoint_untouched_when_guard_fires(monkeypatch, tmp_path):
    """End-to-end: emit_workstream_start raises before touching the real
    checkpoint when isolation is missing. The real .aho-checkpoint.json
    mtime stays unchanged.
    """
    fake_real_root = Path("/home/kthompson/dev/projects/aho")
    real_ckpt = fake_real_root / ".aho-checkpoint.json"
    if not real_ckpt.exists():
        pytest.skip("No real checkpoint present to assert against")

    mtime_before = real_ckpt.stat().st_mtime
    content_before = real_ckpt.read_text()

    monkeypatch.setattr("aho.paths.find_project_root", lambda *a, **k: fake_real_root)
    monkeypatch.delenv("AHO_TEST_CHECKPOINT_DIR", raising=False)
    # Avoid the log-event idempotency short-circuit by using a unique id
    with pytest.raises(TestIsolationError):
        emit_workstream_start("W_GUARD_TEST_DO_NOT_USE", summary="guard test")

    assert real_ckpt.stat().st_mtime == mtime_before
    assert real_ckpt.read_text() == content_before
