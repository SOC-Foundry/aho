"""W5 acceptance: manifest idempotency check."""
from aho.manifest import regenerate_manifest
from aho.postflight.manifest_current import check

regenerate_manifest()
s1, _ = check()
assert s1 == "ok", f"Pass 1 failed: {s1}"
regenerate_manifest()
s2, _ = check()
assert s2 == "ok", f"Pass 2 failed: {s2}"
print("ok")
