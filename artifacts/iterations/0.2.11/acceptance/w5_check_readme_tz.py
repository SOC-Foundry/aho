"""W5 acceptance: readme_current timezone normalization."""
from aho.postflight.readme_current import check
s, m = check()
assert s == "ok", f"{s}: {m}"
assert "+00:00" in m or "UTC" in m, f"No UTC indicator in: {m}"
print("ok")
