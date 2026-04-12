"""W7 acceptance: daemons restarted and healthy."""
from aho.acceptance import daemon_healthy, run_check
t = run_check(daemon_healthy("aho-telegram"))
o = run_check(daemon_healthy("aho-openclaw"))
assert t.passed, f"telegram: {t.actual_output}"
assert o.passed, f"openclaw: {o.actual_output}"
print("ok")
