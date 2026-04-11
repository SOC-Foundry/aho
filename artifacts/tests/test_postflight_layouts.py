import pathlib
import pytest
from aho.postflight.layout import detect_layout, LayoutVariant
from aho.postflight.structural_gates import check_artifact

def test_detect_layout_w_based(tmp_path):
    p = tmp_path / "design.md"
    p.write_text("## Workstreams\n### W0 — Foo\n### W1 — Bar\n### W2 — Baz\n")
    assert detect_layout(p) == LayoutVariant.W_BASED

def test_detect_layout_section_based(tmp_path):
    p = tmp_path / "design.md"
    content = "\n".join([f"## §{i} Section" for i in range(1, 15)])
    p.write_text(content)
    assert detect_layout(p) == LayoutVariant.SECTION_BASED

def test_check_artifact_w_based_design(tmp_path):
    p = tmp_path / "aho-design-0.1.99.md"
    p.write_text("## Workstreams\n### W0 — Foo\n### W1 — Bar\n## Success criteria\n")
    # This should pass the W-based design requirements in structural_gates.py
    res = check_artifact(p, "design")
    assert res["status"] == "PASS"

def test_check_artifact_w_based_plan(tmp_path):
    p = tmp_path / "aho-plan-0.1.99.md"
    p.write_text("## W0 — Foo\n## W1 — Bar\n## Gate:\n")
    res = check_artifact(p, "plan")
    assert res["status"] == "PASS"

def test_check_artifact_legacy_design(tmp_path):
    p = tmp_path / "aho-design-0.1.99.md"
    content = "Phase 0\n" + "\n".join([f"## §{i} Section" for i in range(1, 10)])
    p.write_text(content)
    res = check_artifact(p, "design")
    assert res["status"] == "PASS"
