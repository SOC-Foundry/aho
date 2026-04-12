import json
import os
import re
import subprocess
from pathlib import Path
from aho.paths import find_project_root
from pydantic import BaseModel
from aho.council.inventory import inventory, CouncilMember

class CouncilMemberStatus(BaseModel):
    name: str
    kind: str
    declared_capability: str
    config_source: str
    status: str

class CouncilStatus(BaseModel):
    members: list[CouncilMemberStatus]
    ollama_models: list[str]
    nemoclaw_socket: str | None
    recent_dispatches: list[dict]
    g083_density: dict
    health_score: float

def ollama_models_pulled() -> list[str]:
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return []
        lines = r.stdout.splitlines()[1:] # skip header
        return [line.split()[0] for line in lines if line.strip()]
    except Exception:
        return []

def nemoclaw_socket_status() -> str | None:
    path = Path.home() / ".local" / "share" / "aho" / "nemoclaw.sock"
    if path.exists() and path.is_socket():
        return str(path)
    return None

def recent_dispatches(n=10) -> list[dict]:
    log_path = Path.home() / ".local" / "share" / "aho" / "events" / "aho_event_log.jsonl"
    if not log_path.exists():
        return []
    
    try:
        lines = log_path.read_text().splitlines()
    except Exception:
        return []
        
    dispatches = []
    for line in reversed(lines):
        try:
            ev = json.loads(line)
            if ev.get("action") in ("dispatch", "route", "classify", "review"):
                dispatches.append(ev)
                if len(dispatches) >= n:
                    break
        except Exception:
            continue
    return dispatches

def g083_anti_pattern_density() -> dict:
    report_path = find_project_root() / "artifacts" / "iterations" / "0.2.12" / "g083-scan-report.md"
    density = {"Safe": 0, "G083-class": 0, "Ambiguous": 0, "Total": 0}
    if report_path.exists():
        try:
            content = report_path.read_text()
            for key in density.keys():
                m = re.search(fr"\*\*?{key}.*?:\*\*?\s*(\d+)", content)
                if m:
                    density[key] = int(m.group(1))
        except Exception:
            pass
    return density

def calculate_health(members: list[CouncilMemberStatus], g083: dict) -> float:
    total_members = len(members)
    if total_members == 0:
        return 0.0
    operational = sum(1 for m in members if "operational" in m.status)
    base_score = (operational / total_members) * 100.0
    
    penalty = g083.get("G083-class", 0) * 1.0
    return max(0.0, min(100.0, base_score - penalty))

def collect_status() -> CouncilStatus:
    base_members = inventory()
    member_statuses = [
        CouncilMemberStatus(
            name=m.name,
            kind=m.kind,
            declared_capability=m.declared_capability,
            config_source=m.config_source,
            status=m.status
        ) for m in base_members
    ]
    g083 = g083_anti_pattern_density()
    
    return CouncilStatus(
        members=member_statuses,
        ollama_models=ollama_models_pulled(),
        nemoclaw_socket=nemoclaw_socket_status(),
        recent_dispatches=recent_dispatches(),
        g083_density=g083,
        health_score=calculate_health(member_statuses, g083)
    )

def format_human(status: CouncilStatus, verbose: bool = False) -> str:
    lines = []
    lines.append(f"Council Health Score: {status.health_score:.1f}/100")
    lines.append(f"Nemoclaw Socket: {status.nemoclaw_socket or 'MISSING'}")
    lines.append(f"Ollama Models: {', '.join(status.ollama_models) or 'NONE'}")
    lines.append("")
    lines.append("--- Members ---")
    
    fmt = "{:<35} | {:<12} | {:<40}"
    lines.append(fmt.format("Name", "Kind", "Status"))
    lines.append("-" * 90)
    for m in status.members:
        lines.append(fmt.format(m.name[:35], m.kind[:12], m.status[:40]))
        
    if verbose:
        lines.append("")
        lines.append("--- G083 Anti-Pattern Density ---")
        for k, v in status.g083_density.items():
            lines.append(f"{k}: {v}")
            
        lines.append("")
        lines.append("--- Recent Routing Activity ---")
        for d in status.recent_dispatches:
            action = d.get("action", "unknown")
            target = d.get("target", "unknown")
            lines.append(f"[{d.get('timestamp', '')}] {action} -> {target}")
            
    return "\n".join(lines)

def format_json(status: CouncilStatus, member: str = None) -> str:
    if member:
        for m in status.members:
            if member.lower() in m.name.lower():
                return m.model_dump_json(indent=2)
        return "{}"
    return status.model_dump_json(indent=2)
