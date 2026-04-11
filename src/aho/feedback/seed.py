"""Seed extraction — reads Kyle's notes and debts to seed the next iteration.

aho 0.1.13: updated to use new artifact paths.
"""
import json
import re
from pathlib import Path
from typing import List, Dict

from aho.paths import find_project_root, get_iterations_dir


def extract_carryover_debts(report_path: Path) -> List[Dict]:
    """Parse workstream summary table and extract debts."""
    if not report_path.exists():
        return []
    
    content = report_path.read_text()
    # Look for table rows like: | W1 | ... | ... | status |
    debts = []
    lines = content.splitlines()
    in_table = False
    for line in lines:
        if "| Workstream |" in line:
            in_table = True
            continue
        if in_table and "|" in line and "---" not in line:
            # Match | W1 | Description | Score | Status |
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                wid, desc, _, status = parts[:4]
                if status.lower() not in ("complete", "status"):
                    debts.append({"source": wid, "description": desc, "status": status})
        elif in_table and line.strip() == "":
            in_table = False
            
    return debts


def build_seed(source_iteration: str, target_iteration: str) -> dict:
    """Assemble the full structured seed."""
    root = find_project_root()
    config = json.loads((root / ".aho.json").read_text())
    prefix = config.get("artifact_prefix") or config.get("name") or "aho"
    phase = config.get("phase", 0)

    # Check for both old and new filename patterns
    iter_dir = get_iterations_dir() / source_iteration
    report_path = iter_dir / f"{prefix}-run-{source_iteration}.md"
    if not report_path.exists():
        report_path = iter_dir / f"{prefix}-run-report-{source_iteration}.md"
    
    notes = ""
    questions = []
    debts = []

    if report_path.exists():
        content = report_path.read_text()
        # Extract Kyle's Notes
        notes_match = re.search(r"## Kyle's Notes for Next Iteration\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL)
        notes = notes_match.group(1).strip() if notes_match else ""
        
        # Extract Agent Questions
        q_match = re.search(r"## Agent Questions for Kyle\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL)
        if q_match:
            questions = [q.strip("- ").strip() for q in q_match.group(1).strip().splitlines() if q.strip()]
        
        debts = extract_carryover_debts(report_path)

    return {
        "source_iteration": source_iteration,
        "target_iteration": target_iteration,
        "phase": phase,
        "iteration_theme": "",
        "kyles_notes": notes,
        "agent_questions": questions,
        "carryover_debts": debts,
        "scope_hints": "",
        "anti_hallucination_list": [],
        "retired_patterns": [],
        "known_file_paths": [],
        "known_cli_commands": [],
    }


def write_seed(target_iteration: str, seed: dict) -> Path:
    """Write seed to artifacts/iterations/{target}/seed.json."""
    iter_dir = get_iterations_dir() / target_iteration
    iter_dir.mkdir(parents=True, exist_ok=True)
    
    seed_path = iter_dir / "seed.json"
    seed_path.write_text(json.dumps(seed, indent=2))
    return seed_path
