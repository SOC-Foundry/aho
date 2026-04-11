"""Anti-hallucination evaluator for Qwen-generated artifacts.

Uses Nemotron for reference extraction and grep-validates every reference
against the actual codebase. Catches the 0.1.5 failure modes: hallucinated
file paths, hallucinated CLI commands, fabricated phase labels, revived
retired patterns.
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any

from aho.artifacts.nemotron_client import _call as nemotron_call
from aho.logger import log_event as _log_event
from aho.paths import find_project_root, get_scripts_dir, get_harness_dir, get_data_dir


FILE_PATH_RE = re.compile(r"(?:^|\s|`)((?:src|artifacts|app|pipeline|data)/[\w/\.\-]+\.\w+)")
CLI_COMMAND_RE = re.compile(r"`?(?:aho|\./bin/aho)\s+([\w\-]+)(?:\s+[\w\-]+)?`?")
# More robust script name regex to catch root-level .py files
SCRIPT_NAME_RE = re.compile(r"`?(\b\w+[\w\-]*\.py\b)`?")
ADR_ID_RE = re.compile(r"(ahomw-ADR-\d+)")
GOTCHA_ID_RE = re.compile(r"(aho-G\d+)")
# More robust phase label regex to catch **Phase:** 1 etc.
PHASE_LABEL_RE = re.compile(r"Phase\s*[:*]*\s*(\d+)(?:\s*\(([^)]+)\))?", re.IGNORECASE)


def get_allowed_cli_commands(project_root: Path = None) -> set[str]:
    """Dynamically discover allowed CLI commands from aho.cli."""
    try:
        from aho.cli import main_parser
        parser = main_parser()
        commands = set()
        for action in parser._actions:
            if isinstance(action, (argparse._SubParsersAction,)):
                for cmd_name in action.choices:
                    commands.add(cmd_name)
        return commands
    except Exception:
        return {"project", "init", "check", "push", "log", "doctor", "status", "eval", "registry", "rag", "telegram", "preflight", "postflight", "secret", "pipeline", "iteration"}

def get_allowed_scripts(project_root: Path) -> set[str]:
    """Dynamically discover allowed scripts from artifacts/scripts/ directory."""
    scripts = set()
    scripts_dir = get_scripts_dir()
    if scripts_dir.exists():
        for f in scripts_dir.glob("*.py"):
            scripts.add(f.name)
    return scripts

def extract_references(text: str) -> dict:
    """Extract references via regex."""
    return {
        "file_paths": sorted(set(FILE_PATH_RE.findall(text))),
        "cli_commands": sorted(set(CLI_COMMAND_RE.findall(text))),
        "script_names": sorted(set(SCRIPT_NAME_RE.findall(text))),
        "adr_ids": sorted(set(ADR_ID_RE.findall(text))),
        "gotcha_ids": sorted(set(GOTCHA_ID_RE.findall(text))),
        "phase_labels": [(p, lbl or "") for p, lbl in PHASE_LABEL_RE.findall(text)],
    }


def load_known_hallucinations() -> dict:
    p = get_data_dir() / "known_hallucinations.json"
    if not p.exists():
        return {"retired_patterns": [], "kjtcom_references_that_look_like_aho": [], "fabricated_history": []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"retired_patterns": [], "kjtcom_references_that_look_like_aho": [], "fabricated_history": []}


def validate_references(refs: dict, project_root: Path, seed: dict = None) -> dict:
    errors = []
    known = load_known_hallucinations()
    seed = seed or {}

    # File paths
    for fp in refs.get("file_paths", []):
        if not (project_root / fp).exists():
            errors.append(f"hallucinated file path: {fp}")

    # Script names (root-level or otherwise)
    allowed_scripts = get_allowed_scripts(project_root)
    for sn in refs.get("script_names", []):
        if sn not in allowed_scripts:
            # Deep search in src/ as fallback
            if not list(project_root.glob(f"src/**/{sn}")):
                errors.append(f"hallucinated script: {sn}")

    # CLI commands
    allowed_cmds = get_allowed_cli_commands(project_root)
    for cmd in refs.get("cli_commands", []):
        if cmd not in allowed_cmds:
            errors.append(f"hallucinated CLI command: aho {cmd}")

    # ADR ids
    base_md = get_harness_dir() / "base.md"
    if base_md.exists():
        base_content = base_md.read_text()
        for adr in refs.get("adr_ids", []):
            if adr not in base_content:
                errors.append(f"hallucinated ADR: {adr}")

    # Gotcha ids
    gotcha_path = get_data_dir() / "gotcha_archive.json"
    if gotcha_path.exists():
        try:
            gdata = json.loads(gotcha_path.read_text())
            gotchas = gdata.get("gotchas", []) if isinstance(gdata, dict) else gdata
            known_ids = {g.get("id") or g.get("code") for g in gotchas}
            for gid in refs.get("gotcha_ids", []):
                if gid not in known_ids:
                    errors.append(f"hallucinated gotcha: {gid}")
        except json.JSONDecodeError:
            pass

    # Phase labels: must match .aho.json phase
    aho_json = project_root / ".aho.json"
    if aho_json.exists():
        try:
            current_phase = json.loads(aho_json.read_text()).get("phase", 0)
            for phase_num, phase_label in refs.get("phase_labels", []):
                if int(phase_num) != current_phase:
                    errors.append(f"phase mismatch: text says Phase {phase_num}{' (' + phase_label + ')' if phase_label else ''}, .aho.json says Phase {current_phase}")
        except (json.JSONDecodeError, ValueError):
            pass

    # Severity
    if not errors:
        return {"severity": "clean", "errors": [], "message": "No hallucinations detected"}
    elif len(errors) <= 3:
        return {"severity": "warn", "errors": errors, "message": f"{len(errors)} minor hallucinations"}
    else:
        return {"severity": "reject", "errors": errors, "message": f"{len(errors)} hallucinations — artifact rejected"}


def evaluate_text(text: str, project_root: Path = None, seed: dict = None, artifact_type: str = None) -> dict:
    """Full evaluation: extract references, validate, return severity."""
    if project_root is None:
        try:
            project_root = find_project_root()
        except Exception:
            project_root = Path.cwd()
    refs = extract_references(text)

    # Also check anti_hallucination_list phrases directly against text
    anti_errors = []
    known = load_known_hallucinations()
    anti = (seed or {}).get("anti_hallucination_list", [])
    all_bad = anti + known.get("retired_patterns", []) + known.get("kjtcom_references_that_look_like_aho", [])
    for bad_phrase in all_bad:
        if bad_phrase.lower() in text.lower():
            anti_errors.append(f"retired/anti pattern present: '{bad_phrase}'")

    validation = validate_references(refs, project_root, seed)
    validation["errors"] = anti_errors + validation.get("errors", [])

    # Re-assess severity
    n = len(validation["errors"])
    is_synthesis = artifact_type and "synthesis" in artifact_type.lower()
    if n == 0:
        validation["severity"] = "clean"
    elif is_synthesis and anti_errors:
        validation["severity"] = "reject"
    elif n <= 3:
        validation["severity"] = "warn"
    else:
        validation["severity"] = "reject"
    validation["message"] = f"{n} issues found, severity: {validation['severity']}"
    validation["references"] = refs
    try:
        _log_event("evaluator_run", "evaluator", artifact_type or "unknown", "evaluate",
                   output_summary=f"severity={validation['severity']} errors={n}",
                   status=validation["severity"])
    except Exception:
        pass
    return validation
