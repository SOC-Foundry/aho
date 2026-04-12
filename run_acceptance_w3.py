import json
import subprocess
import re

checks = [
    ("glm_audit_sections_complete", "test -f artifacts/iterations/0.2.12/glm-evaluator-audit.md && grep -cE \"^## §[1-7]\" artifacts/iterations/0.2.12/glm-evaluator-audit.md", 0, "^7$"),
    ("inventory_glm_updated", "python -c \"from aho.council.inventory import inventory; m = inventory(); glm = next((x for x in m if 'glm' in x.name.lower() or 'evaluator' in x.name.lower()), None); print(f'glm={glm.status if glm else None}')\"", 0, "glm=(operational|gap:.+)"),
    ("w14_readiness_documented", "grep -cE \"^## §7\" artifacts/iterations/0.2.12/glm-evaluator-audit.md; grep -cE \"W14|ready|not ready|feasible|deferred|gap\" artifacts/iterations/0.2.12/glm-evaluator-audit.md", 0, "[1-9]"),
    ("no_new_baseline_regressions", "python -c \"from aho.acceptance import baseline_regression_check, run_check; r = run_check(baseline_regression_check()); print('baseline-stable' if r.passed else r.actual_output)\"", 0, "^baseline-stable$")
]

results = []
for name, cmd, exp_exit, exp_pat in checks:
    res = subprocess.run(cmd, shell=True, executable="/bin/bash", capture_output=True, text=True)
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

with open("artifacts/iterations/0.2.12/acceptance/W3.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
