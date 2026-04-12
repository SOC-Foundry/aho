import json
import subprocess
import re

checks = [
    ("nemotron_audit_sections_complete", "test -f artifacts/iterations/0.2.12/nemotron-audit.md; and grep -cE \"^## §[1-7]\" artifacts/iterations/0.2.12/nemotron-audit.md", 0, "^7$"),
    ("inventory_nemotron_updated", "python -c \"from aho.council.inventory import inventory; m = inventory(); n = next((x for x in m if 'nemotron' in x.name.lower()), None); print(f'nemotron={n.status if n else None}')\"", 0, "nemotron=(operational|gap:.+)"),
    ("g083_registered", "jq -r '.gotchas[] | select(.id == \"aho-G083\") | .id' ~/.local/share/aho/registries/gotcha_archive.json", 0, "aho-G083"),
    ("baseline_updated_to_10", "python -c \"import json; b = json.load(open('artifacts/harness/test-baseline.json')); print(len(b['baseline_failures']))\"", 0, "^10$"),
    ("removed_test_not_in_baseline", "python -c \"import json; b = json.load(open('artifacts/harness/test-baseline.json')); ids = [f['test_id'] for f in b['baseline_failures']]; assert 'test_trace_state_returns_last_20' not in ' '.join(ids); print('ok')\"", 0, "^ok$"),
    ("no_new_baseline_regressions", "python -c \"from aho.acceptance import baseline_regression_check, run_check; r = run_check(baseline_regression_check()); print('baseline-stable' if r.passed else r.actual_output)\"", 0, "^baseline-stable$"),
    ("silent_fallback_audit_documented", "grep -cE \"silent.?fallback|hardcode|rubber.?stamp|G083\" artifacts/iterations/0.2.12/nemotron-audit.md", 0, "^[1-9]")
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

with open("artifacts/iterations/0.2.12/acceptance/W4.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
