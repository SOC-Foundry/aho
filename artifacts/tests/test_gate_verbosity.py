"""Tests for gate verbosity — per-check CheckResult detail.

Minimum 5 cases per W4 plan:
1. run_quality emits per-check results
2. structural_gates emits per-check results
3. rollup status = worst(checks)
4. gate without checks still renders (backward compat)
5. report builder renders nested checks under gate
"""
from aho.postflight import CheckResult, GateResult, worst_status


def test_run_quality_emits_checks():
    """run_quality returns dict with checks list."""
    from aho.postflight.run_quality import check
    result = check()
    assert isinstance(result, dict)
    assert "checks" in result
    assert len(result["checks"]) >= 4
    for c in result["checks"]:
        assert "name" in c
        assert "status" in c
        assert "message" in c


def test_structural_gates_emits_checks():
    """structural_gates returns dict with checks list."""
    from aho.postflight.structural_gates import check
    result = check()
    assert isinstance(result, dict)
    assert "checks" in result
    assert len(result["checks"]) >= 2
    for c in result["checks"]:
        assert "name" in c
        assert "status" in c
        assert "message" in c


def test_rollup_status_worst_of_children():
    """worst_status returns the most severe status."""
    assert worst_status(["ok", "ok", "ok"]) == "ok"
    assert worst_status(["ok", "skip", "ok"]) == "skip"
    assert worst_status(["ok", "deferred", "ok"]) == "deferred"
    assert worst_status(["ok", "ok", "fail"]) == "fail"
    assert worst_status(["fail", "deferred", "skip"]) == "fail"
    assert worst_status([]) == "ok"


def test_gate_result_without_checks_backward_compat():
    """GateResult with no checks renders to dict without checks key."""
    gr = GateResult(status="ok", message="all good")
    d = gr.to_dict()
    assert d["status"] == "ok"
    assert d["message"] == "all good"
    assert "checks" not in d


def test_gate_result_with_checks_to_dict():
    """GateResult with checks serializes checks to dict."""
    checks = [
        CheckResult(name="c1", status="ok", message="good"),
        CheckResult(name="c2", status="fail", message="bad", evidence_path="/tmp/x"),
    ]
    gr = GateResult(status="fail", message="1 failure", checks=checks)
    d = gr.to_dict()
    assert d["status"] == "fail"
    assert len(d["checks"]) == 2
    assert d["checks"][0]["name"] == "c1"
    assert d["checks"][1]["evidence_path"] == "/tmp/x"


def test_report_builder_renders_nested_checks():
    """Report builder postflight section renders sub-check rows."""
    from aho.feedback.report_builder import _section_postflight

    postflight = {
        "run_quality": ("ok", "all good", [
            {"name": "min_size", "status": "ok", "message": "2000 bytes"},
            {"name": "ws_table", "status": "ok", "message": "W0 present"},
        ]),
        "structural": ("fail", "1 fail", [
            {"name": "design", "status": "ok", "message": "sections present"},
            {"name": "report", "status": "fail", "message": "missing"},
        ]),
        "legacy_gate": ("ok", "simple gate"),
    }
    rendered = _section_postflight(postflight)
    assert "| Gate | Status | Message |" in rendered
    assert "run_quality" in rendered
    assert "min_size" in rendered
    assert "ws_table" in rendered
    assert "legacy_gate" in rendered
    # legacy_gate should NOT have sub-checks
    lines = rendered.splitlines()
    legacy_idx = next(i for i, l in enumerate(lines) if "legacy_gate" in l)
    # Next line should be another gate or empty, not a sub-check
    if legacy_idx + 1 < len(lines) and lines[legacy_idx + 1].strip():
        assert "- " not in lines[legacy_idx + 1] or "legacy" not in lines[legacy_idx + 1]
