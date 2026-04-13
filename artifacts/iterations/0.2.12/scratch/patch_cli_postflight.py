import re

with open("src/aho/cli.py", "r") as f:
    content = f.read()

# Replace unpacking
old_loop = """            for name, (status, msg) in results.items():
                tag = {"ok": "[ok]", "pass": "[ok]", "warn": "[WARN]", "fail": "[FAIL]", "deferred": "[DEFR]"}.get(status, f"[{status}]")
                print(f"{tag:8} {name:20}: {msg}")
                if status == "fail":"""

new_loop = """            for name, res_tuple in results.items():
                status, msg = res_tuple[0], res_tuple[1]
                tag = {"ok": "[ok]", "pass": "[ok]", "warn": "[WARN]", "fail": "[FAIL]", "deferred": "[DEFR]"}.get(status, f"[{status}]")
                print(f"{tag:8} {name:20}: {msg}")
                if status == "fail":"""

content = content.replace(old_loop, new_loop)

with open("src/aho/cli.py", "w") as f:
    f.write(content)
