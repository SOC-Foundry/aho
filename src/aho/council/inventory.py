from dataclasses import dataclass
import re
from pathlib import Path
from aho.paths import find_project_root

@dataclass
class CouncilMember:
    name: str
    kind: str
    declared_capability: str
    config_source: str
    status: str

def inventory() -> list[CouncilMember]:
    members = []

    # Read Model Fleet
    model_fleet_path = find_project_root() / "artifacts" / "harness" / "model-fleet.md"
    if model_fleet_path.exists():
        content = model_fleet_path.read_text()
        for line in content.splitlines():
            m = re.match(r"-\s*\*\*(.*?)\*\*:\s*(.*)", line)
            if m:
                members.append(CouncilMember(
                    name=m.group(1).strip(),
                    kind="llm" if "Embed" not in m.group(1) and "Chroma" not in m.group(1) else "daemon",
                    declared_capability=m.group(2).strip(),
                    config_source=str(model_fleet_path),
                    status="unknown"
                ))

    # Read Agents Architecture
    agents_path = find_project_root() / "artifacts" / "harness" / "agents-architecture.md"
    if agents_path.exists():
        content = agents_path.read_text()
        for line in content.splitlines():
            m = re.match(r"### \d+\.\s+([^\s]+)\s+\(`(.*)`\)", line)
            if m:
                name = m.group(1).strip()
                if "OpenClaw" in name or "NemoClaw" in name:
                    members.append(CouncilMember(
                        name=name,
                        kind="daemon",
                        declared_capability=f"Agent daemon running {name}",
                        config_source=str(agents_path),
                        status="unknown"
                    ))

    # Read MCP Fleet
    mcp_path = find_project_root() / "artifacts" / "harness" / "mcp-fleet.md"
    if mcp_path.exists():
        content = mcp_path.read_text()
        in_table = False
        for line in content.splitlines():
            if line.startswith("| # |"):
                in_table = True
                continue
            if in_table and line.startswith("|---"):
                continue
            if in_table and line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    members.append(CouncilMember(
                        name=parts[3], # Component Name
                        kind="mcp_server",
                        declared_capability=parts[4], # Role
                        config_source=str(mcp_path),
                        status="unknown"
                    ))
            elif in_table and not line.strip():
                in_table = False
    
    # We also need evaluator-agent. The plan says "evaluator-agent". Let's just add it if found in agents logic.
    roles_path = find_project_root() / "src" / "aho" / "agents" / "roles" / "evaluator_agent.py"
    if roles_path.exists():
        members.append(CouncilMember(
            name="evaluator-agent",
            kind="evaluator",
            declared_capability="Evaluator agent role",
            config_source=str(roles_path),
            status="unknown"
        ))
        
    for member in members:
        if "qwen" in member.name.lower() or "nemoclaw" in member.name.lower():
            member.status = "operational"
        elif "evaluator" in member.name.lower() or "glm" in member.name.lower():
            member.status = "gap: parsing logic converts real reviews to rubber stamps"
        elif "nemotron" in member.name.lower():
            member.status = "gap: classification logic silences errors and defaults to reviewer"
        elif any(s in member.name.lower() for s in ["context7", "sequential-thinking", "playwright", "filesystem"]):
            member.status = "operational"

    return members
