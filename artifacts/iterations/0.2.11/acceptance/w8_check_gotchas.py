"""W8 acceptance: G074-G076 registered."""
import json
data = json.loads(open("/home/kthompson/.local/share/aho/registries/gotcha_archive.json").read())
ids = sorted([g["id"] for g in data["gotchas"] if any(x in g["id"] for x in ["G074", "G075", "G076"])])
print(" ".join(ids))
assert ids == ["aho-G074", "aho-G075", "aho-G076"], f"Expected 3, got {ids}"
