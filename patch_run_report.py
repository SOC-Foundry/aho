with open("artifacts/iterations/0.2.12/aho-run-0.2.12.md", "r") as f:
    content = f.read()

# Replace In Progress with closed
content = content.replace("**Status:** In Progress", "**Status:** closed pending Kyle sign-off")

# Add W8 close
w8_row = "| W8 | Iteration close | 2 | Close | pass | Executed strategic rescope boundary closing 0.2.12. Evaluated systemic G083 impact, generated retrospective, rewrote carry-forwards, constructed v10.66 context bundle, and prepared Kyle's sign-off sheet. |"

import re
# Truncate unused workstreams
content = re.sub(r'\| W8 \| OTEL trace instrumentation per agent .*', w8_row, content)
content = re.sub(r'\| W9 \| Council visibility dashboard integration .*', '', content)
content = re.sub(r'\| W10 \| Workstream-level delegation pattern design .*', '', content)
content = re.sub(r'\| W11 \| Dispatch contract specification .*', '', content)
content = re.sub(r'\| W12 \| Pattern framework bootstrap .*', '', content)
content = re.sub(r'\| W13 \| Qwen dispatch: one real workstream task .*', '', content)
content = re.sub(r'\| W14 \| GLM review dispatch: one real evaluation .*', '', content)
content = re.sub(r'\| W15 \| MCP workflow-participant invocation .*', '', content)
content = re.sub(r'\| W16 \| Delegation path of least resistance .*', '', content)
content = re.sub(r'\| W17 \| Schema v3 baseline measurement .*', '', content)
content = re.sub(r'\| W18 \| Tech-legacy-debt audit \+ README review .*', '', content)
content = re.sub(r'\| W19 \| Close .*', '', content)
content = re.sub(r'\n+', '\n', content) # compress newlines a bit

sign_off_replacement = """## Sign-off

- [ ] Session 1 (W0-W7) Discovery & Visibility
- [ ] Session 2 (W8) Close
"""

content = re.sub(r'## Sign-off\n.*', sign_off_replacement, content, flags=re.DOTALL)

with open("artifacts/iterations/0.2.12/aho-run-0.2.12.md", "w") as f:
    f.write(content)
