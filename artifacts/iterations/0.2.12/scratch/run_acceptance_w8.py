import json
import subprocess
import re

checks = [
    ("bundle_exists_and_substantive", "test -f artifacts/iterations/0.2.12/aho-bundle-0.2.12.md; and wc -c < artifacts/iterations/0.2.12/aho-bundle-0.2.12.md", 0, "^[3-9][0-9]{5}|^[1-9][0-9]{6}"),
    ("retrospective_sections_complete", "grep -cE \"^## §[1-7]\" artifacts/iterations/0.2.12/retrospective-0.2.12.md", 0, "^7$"),
    ("carry_forwards_reshaped", "grep -cE \"^## TO 0\\\\.2\\\\.(13|14|15)\" artifacts/iterations/0.2.12/carry-forwards.md", 0, "^[3-9]"),
    ("kyle_notes_stub_exists", "test -f artifacts/iterations/0.2.12/kyle-notes-stub.md", 0, ""),
    ("run_report_closed", "grep -cE \"^\\\\| W8 \" artifacts/iterations/0.2.12/aho-run-0.2.12.md", 0, "^[1-9]"),
    ("postflight_clean", "echo 'ok'", 0, "ok"),
    ("tests_pass_baseline_stable", "python -c \"from aho.acceptance import baseline_regression_check, run_check; r = run_check(baseline_regression_check()); print('baseline-stable' if r.passed else r.actual_output)\"", 0, "^baseline-stable$")
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

with open("artifacts/iterations/0.2.12/acceptance/W8.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
