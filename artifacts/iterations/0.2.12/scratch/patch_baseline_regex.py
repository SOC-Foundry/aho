import re

with open("src/aho/acceptance.py", "r") as f:
    code = f.read()

import base64

# Extract the old base64
m = re.search(r"import base64; exec\(base64\.b64decode\('([^']+)'\)", code)
if m:
    b64_str = m.group(1)
    decoded = base64.b64decode(b64_str).decode('utf-8')
    # Fix the regex
    decoded = decoded.replace(r"^FAILED\\s+([^ ]+)", r"^FAILED\\s+([^\\s]+)")
    new_b64 = base64.b64encode(decoded.encode('utf-8')).decode('utf-8')
    code = code.replace(b64_str, new_b64)
    with open("src/aho/acceptance.py", "w") as f:
        f.write(code)
    print("Fixed.")
else:
    print("Not found.")
