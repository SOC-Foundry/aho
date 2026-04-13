import json
import subprocess
import re

checks = [
    ("cli_subcommand_registered", "aho council status --help 2>&1 | head -5", 0, "council|status"),
    ("status_human_output", "aho council status 2>&1 | head -20", 0, "qwen|nemoclaw|glm|nemotron|operational|gap"),
    ("status_json_output", "aho council status --json | jq '.members | length'", 0, "^[1-9][0-9]?$"),
    ("member_filter_works", "aho council status --member qwen --json | jq -r '.name'", 0, "qwen|Qwen"),
    ("verbose_includes_g083", "aho council status --verbose 2>&1 | grep -cE \"G083|anti.?pattern|silent\"", 0, "^[1-9]"),
    ("dashboard_api_responds", "curl -s http://127.0.0.1:7800/api/council | jq -r '.members | length'", 0, "^[1-9][0-9]?$"),
    ("tests_pass", "pytest tests/test_council_status.py -v 2>&1 | tail -1", 0, "([6-9]|[1-9][0-9]+) passed"),
    ("no_new_baseline_regressions", "python -c \"from aho.acceptance import baseline_regression_check, run_check; r = run_check(baseline_regression_check()); print('baseline-stable' if r.passed else r.actual_output)\"", 0, "^baseline-stable$")
]

results = []
for name, cmd, exp_exit, exp_pat in checks:
    res = subprocess.run(cmd, shell=True, executable="/usr/bin/fish", capture_output=True, text=True)
    passed_exit = res.returncode == exp_exit
    actual_output = res.stdout.strip()
    matched = bool(re.search(exp_pat, actual_output, re.IGNORECASE)) if exp_pat else True
    results.append({
        "name": name,
        "command": cmd,
        "passed": passed_exit and matched,
        "actual_exit": res.returncode,
        "actual_output": actual_output,
        "matched": matched
    })

with open("artifacts/iterations/0.2.12/acceptance/W6.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
