import json
import subprocess
import re

checks = [
    ("renderer_module_importable", "python -c \"from aho.dashboard.lego.renderer import render_council_svg; from aho.council.status import collect_status; svg = render_council_svg(collect_status()); assert svg.startswith('<svg'); assert 'qwen' in svg.lower() or 'Qwen' in svg; print('ok')\"", 0, "^ok$"),
    ("svg_artifact_written", "test -f artifacts/visualizations/lego-office-0.2.12.svg; and wc -c < artifacts/visualizations/lego-office-0.2.12.svg", 0, "^[1-9][0-9]{2,}"),
    ("svg_contains_all_members", "python -c \"svg = open('artifacts/visualizations/lego-office-0.2.12.svg').read(); members = ['Qwen', 'Nemotron', 'GLM', 'NemoClaw', 'context7']; missing = [m for m in members if m not in svg]; print('missing:', missing if missing else 'none')\"", 0, "missing: none"),
    ("color_encoding_present", "python -c \"svg = open('artifacts/visualizations/lego-office-0.2.12.svg').read(); has_green = '#' in svg and ('4ade80' in svg.lower() or '22c55e' in svg.lower() or 'green' in svg.lower()); has_red = 'ef4444' in svg.lower() or 'dc2626' in svg.lower() or 'red' in svg.lower(); print('green=' + str(has_green) + ' red=' + str(has_red))\"", 0, "green=True red=True"),
    ("dashboard_lego_route_responds", "curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:7800/lego/", 0, "^200$"),
    ("api_lego_returns_data", "curl -s http://127.0.0.1:7800/api/lego | jq -r '.figures | length'", 0, "^[1-9][0-9]?$"),
    ("tests_pass", "pytest tests/test_lego_renderer.py -v 2>&1 | tail -1", 0, "([5-9]|[1-9][0-9]+) passed"),
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

with open("artifacts/iterations/0.2.12/acceptance/W7.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
