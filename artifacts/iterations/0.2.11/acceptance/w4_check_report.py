"""W4 acceptance: verify report builder renders nested checks."""
from aho.feedback.report_builder import _section_postflight

postflight = {
    "run_quality": ("ok", "all good", [
        {"name": "min_size", "status": "ok", "message": "2000 bytes"},
    ]),
    "simple_gate": ("ok", "no detail"),
}
rendered = _section_postflight(postflight)
assert "min_size" in rendered, "Nested check not rendered"
lines = [l for l in rendered.splitlines() if "- min_size" in l]
assert len(lines) >= 1, "Sub-check row not found"
print(f"REPORT NESTED OK ({len(lines)} sub-check rows)")
