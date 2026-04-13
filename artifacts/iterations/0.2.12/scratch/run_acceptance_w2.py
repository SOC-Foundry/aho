import json
import subprocess
import re

checks = [
    ("qwen_audit_sections_complete", "test -f artifacts/iterations/0.2.12/qwen-dispatch-audit.md && grep -cE \"^## §[1-7]\" artifacts/iterations/0.2.12/qwen-dispatch-audit.md", 0, "^7$"),
    ("inventory_qwen_and_nemoclaw_updated", "python -c \"from aho.council.inventory import inventory; m = inventory(); qwen = next((x for x in m if 'qwen' in x.name.lower()), None); nemo = next((x for x in m if 'nemoclaw' in x.name.lower()), None); print(f'qwen={qwen.status if qwen else None}; nemo={nemo.status if nemo else None}')\"", 0, "qwen=(operational|gap:.+); nemo=(operational|gap:.+)"),
    ("registry_sync_complete", "diff <(jq -r '.gotchas[].id' ~/.local/share/aho/registries/gotcha_archive.json | sort) <(jq -r '.gotchas[].id' data/gotcha_archive.json | sort); echo \"exit=$?\"", 0, "exit=0"),
    ("g082_or_next_registered", "jq -r '.gotchas[] | select(.title | test(\"dual-path|registry.*stale\")) | .id' ~/.local/share/aho/registries/gotcha_archive.json", 0, "aho-G0[89][0-9]|aho-G1[0-9]{2}"),
    ("no_new_baseline_regressions", "python -c \"from aho.acceptance import baseline_regression_check, run_check; r = run_check(baseline_regression_check()); print('baseline-stable' if r.passed else r.actual_output)\"", 0, "^baseline-stable$"),
    ("registry_write_path_uses_canonical", "grep -rE \"gotcha_archive\\\\.json\" src/aho/ --include=\"*.py\" | grep -v \"test\" | grep -vE \"registries/gotcha_archive\\\\.json\" | wc -l", 0, "^0$")
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

with open("artifacts/iterations/0.2.12/acceptance/W2.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
