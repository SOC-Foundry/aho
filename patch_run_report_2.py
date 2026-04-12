import re

with open("artifacts/iterations/0.2.12/aho-run-0.2.12.md", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("**Status:**"):
        new_lines.append("**Status:** Closed pending Kyle sign-off\n")
    elif "| W8 |" in line:
        new_lines.append("| W8 | Iteration close | 2 | Close | pass | Executed strategic rescope boundary closing 0.2.12. Evaluated systemic G083 impact, generated retrospective, rewrote carry-forwards, constructed v10.66 context bundle, and prepared Kyle's sign-off sheet. |\n")
    elif "| W9 |" in line or "| W10 |" in line or "| W11 |" in line or "| W12 |" in line or "| W13 |" in line or "| W14 |" in line or "| W15 |" in line or "| W16 |" in line or "| W17 |" in line or "| W18 |" in line or "| W19 |" in line:
        continue
    elif "- [ ] W" in line:
        continue
    else:
        new_lines.append(line)

out = "".join(new_lines)
signoff_replacement = """## Sign-off

- [ ] Session 1 (W0-W7) Discovery & Visibility
- [ ] Session 2 (W8) Close
"""
out = re.sub(r'## Sign-off.*', signoff_replacement, out, flags=re.DOTALL)

with open("artifacts/iterations/0.2.12/aho-run-0.2.12.md", "w") as f:
    f.write(out)
