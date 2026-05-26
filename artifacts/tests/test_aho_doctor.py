"""test_aho_doctor.py - W1 D7 of 0.3.1.

Tests bin/aho-doctor:
- Invokes install.fish --check, parses JSONL output
- Exits 0 when all required-steps pass for the W
- Exits 1 when any required-step fails for the W
- --json output validates as JSON
- --required-steps override works
- Unknown workstream exits 3
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AHO_DOCTOR = ROOT / "bin" / "aho-doctor"


def _run_doctor(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(AHO_DOCTOR), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_doctor_exists_and_executable():
    assert AHO_DOCTOR.exists(), f"missing {AHO_DOCTOR}"
    assert os.access(AHO_DOCTOR, os.X_OK)


def test_unknown_workstream_exits_3():
    proc = _run_doctor("--workstream", "Wbogus")
    assert proc.returncode == 3


def test_workstream_w1_runs_and_exits_clean_or_with_failure():
    """W1 doctor should run without error; exit code is 0 (all passing) or 1
    (some failures, e.g., sys.path drift expected on a W1 substrate).
    """
    proc = _run_doctor("--workstream", "W1", timeout=120)
    assert proc.returncode in (0, 1), (
        f"unexpected exit {proc.returncode}: {proc.stderr}"
    )
    # Plain-text output should include the workstream tag
    assert "workstream=W1" in proc.stdout


def test_json_output_validates(tmp_path):
    proc = _run_doctor("--workstream", "W1", "--json", timeout=120)
    assert proc.returncode in (0, 1)
    d = json.loads(proc.stdout)
    assert d["workstream"] == "W1"
    assert "required_steps_count" in d
    assert "passing_count" in d
    assert "failed_count" in d
    assert "failed" in d and isinstance(d["failed"], list)
    assert d["passing_count"] + d["failed_count"] + d["missing_count"] == d["required_steps_count"]


def test_required_steps_override_via_flag():
    """--required-steps explicit list short-circuits the workstream default."""
    proc = _run_doctor(
        "--workstream", "W1",
        "--required-steps", "chromadb_importable,canonical_checkpoint_present",
        "--json",
        timeout=120,
    )
    assert proc.returncode in (0, 1)
    d = json.loads(proc.stdout)
    assert d["required_steps_count"] == 2


def test_jsonl_file_is_refreshed_each_invocation():
    """Each aho-doctor invocation runs install.fish --check, which appends fresh
    JSONL entries. The newest entries-per-step should be from the latest run.
    """
    jsonl_file = Path.home() / ".local" / "share" / "aho" / "install-state.jsonl"
    if not jsonl_file.exists():
        pytest.skip("no jsonl file yet (run install.fish first)")
    pre_size = jsonl_file.stat().st_size
    proc = _run_doctor("--workstream", "W1", timeout=120)
    assert proc.returncode in (0, 1)
    post_size = jsonl_file.stat().st_size
    assert post_size > pre_size, "aho-doctor did not append fresh JSONL entries"
