"""W4 acceptance: verify gates emit per-check detail."""
import json

from aho.postflight.run_quality import check as rq_check
from aho.postflight.structural_gates import check as sg_check

rq = rq_check()
assert "checks" in rq, "run_quality missing checks"
print(f"run_quality: {len(rq['checks'])} checks")

sg = sg_check()
assert "checks" in sg, "structural_gates missing checks"
print(f"structural_gates: {len(sg['checks'])} checks")

# Verify rollup
from aho.postflight import worst_status
statuses = ["ok", "ok", "fail"]
assert worst_status(statuses) == "fail"
print("rollup: worst([ok,ok,fail]) == fail")

print("VERBOSE GATES OK")
