"""W9 acceptance: G077 registered."""
import json
data = json.loads(open("/home/kthompson/.local/share/aho/registries/gotcha_archive.json").read())
g077 = [g for g in data["gotchas"] if g["id"] == "aho-G077"]
assert len(g077) == 1, f"Expected 1, found {len(g077)}"
print("aho-G077")
