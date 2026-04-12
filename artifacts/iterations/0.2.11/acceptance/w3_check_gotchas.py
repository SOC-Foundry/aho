"""W3 acceptance helper: verify G070-G072 registered."""
import json
import sys

path = "/home/kthompson/.local/share/aho/registries/gotcha_archive.json"
data = json.loads(open(path).read())
ids = [g["id"] for g in data["gotchas"] if any(x in g["id"] for x in ["G070", "G071", "G072"])]
print(" ".join(ids))
assert len(ids) == 3, f"Expected 3 gotchas, found {len(ids)}: {ids}"
print("ALL GOTCHAS OK")
