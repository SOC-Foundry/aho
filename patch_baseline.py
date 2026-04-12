with open("src/aho/acceptance.py", "r") as f:
    content = f.read()

old_cmd = '''    cmd = (
        "python -c \\\""
        "import json, subprocess, re, sys, os; "
        "baseline_path = 'artifacts/harness/test-baseline.json'; "
        "baseline = set(); "
        "if os.path.exists(baseline_path): "
        "    b_data = json.load(open(baseline_path)); "
        "    baseline = {f.get('test_id') for f in b_data.get('baseline_failures', []) if f.get('test_id')}; "
        f"r = subprocess.run('{pytest_cmd}', shell=True, capture_output=True, text=True); "
        "out = r.stdout + r.stderr; "
        "failed_matches = re.findall(r'^FAILED\\\\s+([^ ]+)', out, re.MULTILINE); "
        "current_failures = set(failed_matches); "
        "new_failures = current_failures - baseline; "
        "fixed_failures = baseline - current_failures; "
        "if fixed_failures: "
        "    print(f'Fixed baseline failures (consider removing from baseline): {fixed_failures}'); "
        "if new_failures: "
        "    print(f'NEW regressions found: {new_failures}'); "
        "    sys.exit(1); "
        "print('baseline-stable'); "
        "sys.exit(0);\\\""
    )'''

new_cmd = '''    script = f\"\"\"
import json, subprocess, re, sys, os
baseline_path = 'artifacts/harness/test-baseline.json'
baseline = set()
if os.path.exists(baseline_path):
    b_data = json.load(open(baseline_path))
    baseline = {{f.get('test_id') for f in b_data.get('baseline_failures', []) if f.get('test_id')}}
r = subprocess.run('{pytest_cmd}', shell=True, capture_output=True, text=True)
out = r.stdout + r.stderr
failed_matches = re.findall(r'^FAILED\\\\s+([^ ]+)', out, re.MULTILINE)
current_failures = set(failed_matches)
new_failures = current_failures - baseline
fixed_failures = baseline - current_failures
if fixed_failures:
    print(f'Fixed baseline failures (consider removing from baseline): {{fixed_failures}}')
if new_failures:
    print(f'NEW regressions found: {{new_failures}}')
    sys.exit(1)
print('baseline-stable')
sys.exit(0)
\"\"\"
    cmd = ["python", "-c", script]'''

content = content.replace(old_cmd, new_cmd)

with open("src/aho/acceptance.py", "w") as f:
    f.write(content)
