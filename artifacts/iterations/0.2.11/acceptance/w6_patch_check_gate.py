"""W6-patch acceptance: gate requires exactly 11, passes on corrected design."""
from aho.postflight.pillars_present import check
result = check()
s = result["status"]
m = result["message"]
assert s == "ok", f"Gate failed: {m}"
# Verify 11-pillar check is in the checks array
pillars_check = [c for c in result.get("checks", []) if c["name"] == "design_pillars"]
assert len(pillars_check) == 1, "design_pillars check missing"
assert pillars_check[0]["status"] == "ok", f"design_pillars failed: {pillars_check[0]['message']}"
assert "11" in pillars_check[0]["message"], f"Expected 11 in: {pillars_check[0]['message']}"
print("ok")
