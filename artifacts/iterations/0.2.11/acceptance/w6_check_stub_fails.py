"""W6 acceptance: pillars_present fails on design doc without §3 Trident."""
from aho.postflight.pillars_present import _check_trident

stub = "## §1 Context\n\nSome content.\n\n## §2 Goals\n\n1. Goal\n"
checks = _check_trident(stub)
heading = next(c for c in checks if c.name == "trident_heading")
assert heading.status == "fail", f"Expected fail, got {heading.status}"
assert "trident" in heading.message.lower() or "missing" in heading.message.lower()
print("Trident missing detected correctly")
