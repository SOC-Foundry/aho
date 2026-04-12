"""W5 acceptance: bundle_quality §22 regex format stable."""
import re
pattern = r"\*\*(?:Unique|Total)\s+components:\*\*\s+(\d+)"
assert re.search(pattern, "**Unique components:** 6")
assert re.search(pattern, "**Total components:** 85")
print("ok")
