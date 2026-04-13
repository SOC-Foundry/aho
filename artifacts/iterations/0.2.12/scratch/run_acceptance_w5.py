import json
import subprocess
import re

checks = [
    ("mcp_audit_sections_complete", "test -f artifacts/iterations/0.2.12/mcp-workflow-audit.md; and grep -cE \"^## §[1-7]\" artifacts/iterations/0.2.12/mcp-workflow-audit.md", 0, "^7$"),
    ("mcp_workflow_invocations_attempted", "grep -cE \"context7|sequential.?thinking|playwright|filesystem\" artifacts/iterations/0.2.12/mcp-workflow-audit.md", 0, "^[4-9]|^[1-9][0-9]"),
    ("g083_scan_produced", "test -f artifacts/iterations/0.2.12/g083-scan-report.md; and grep -cE \"Safe|G083-class|Ambiguous\" artifacts/iterations/0.2.12/g083-scan-report.md", 0, "^[3-9]|^[1-9][0-9]"),
    ("g083_hits_characterized", "grep -cE \"src/aho/.+\\.py:[0-9]+\" artifacts/iterations/0.2.12/g083-scan-report.md", 0, "^[3-9]|^[1-9][0-9]"),
    ("inventory_mcps_updated", "python -c \"from aho.council.inventory import inventory; m = inventory(); mcps = [x for x in m if 'mcp' in x.kind.lower() or 'mcp' in x.name.lower()]; not_unknown = [x for x in mcps if x.status != 'unknown']; print(len(not_unknown))\"", 0, "^[4-9]|^[1-9][0-9]"),
    ("no_new_baseline_regressions", "python -c \"from aho.acceptance import baseline_regression_check, run_check; r = run_check(baseline_regression_check()); print('baseline-stable' if r.passed else r.actual_output)\"", 0, "^baseline-stable$")
]

results = []
for name, cmd, exp_exit, exp_pat in checks:
    res = subprocess.run(cmd, shell=True, executable="/usr/bin/fish", capture_output=True, text=True)
    passed_exit = res.returncode == exp_exit
    actual_output = res.stdout.strip()
    matched = bool(re.search(exp_pat, actual_output)) if exp_pat else True
    results.append({
        "name": name,
        "command": cmd,
        "passed": passed_exit and matched,
        "actual_exit": res.returncode,
        "actual_output": actual_output,
        "matched": matched
    })

with open("artifacts/iterations/0.2.12/acceptance/W5.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
