"""W6-patch acceptance: verify G073 registered."""
import json
data = json.loads(open("/home/kthompson/.local/share/aho/registries/gotcha_archive.json").read())
g073 = [g for g in data["gotchas"] if g["id"] == "aho-G073"]
assert len(g073) == 1, f"Expected 1, found {len(g073)}"
print("aho-G073")
