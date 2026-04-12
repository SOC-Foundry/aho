import re

with open("src/aho/council/inventory.py", "r") as f:
    content = f.read()

content = content.replace("from pathlib import Path", "from pathlib import Path\nfrom aho.paths import find_project_root")
content = content.replace('Path("artifacts/harness/model-fleet.md")', 'find_project_root() / "artifacts" / "harness" / "model-fleet.md"')
content = content.replace('Path("artifacts/harness/agents-architecture.md")', 'find_project_root() / "artifacts" / "harness" / "agents-architecture.md"')
content = content.replace('Path("artifacts/harness/mcp-fleet.md")', 'find_project_root() / "artifacts" / "harness" / "mcp-fleet.md"')
content = content.replace('Path("src/aho/agents/roles/evaluator_agent.py")', 'find_project_root() / "src" / "aho" / "agents" / "roles" / "evaluator_agent.py"')

with open("src/aho/council/inventory.py", "w") as f:
    f.write(content)

with open("src/aho/council/status.py", "r") as f:
    content2 = f.read()

content2 = content2.replace("from pathlib import Path", "from pathlib import Path\nfrom aho.paths import find_project_root")
content2 = content2.replace('Path("artifacts/iterations/0.2.12/g083-scan-report.md")', 'find_project_root() / "artifacts" / "iterations" / "0.2.12" / "g083-scan-report.md"')

with open("src/aho/council/status.py", "w") as f:
    f.write(content2)
