"""Run report generation — the iteration's feedback artifact."""
import json
import os
import re as _re
from datetime import datetime, timezone
from pathlib import Path

from aho.paths import find_project_root, get_harness_dir, get_iterations_dir
from aho.feedback.questions import collect_all_questions

_PILLARS_CACHE: list[str] | None = None


def _load_pillars_from_base(base_md_path: Path | None = None) -> list[str]:
    """Read the eleven pillars from the base harness doc."""
    if base_md_path is None:
        base_md_path = get_harness_dir() / "base.md"
    if not base_md_path.exists():
        raise RuntimeError(f"base harness not found at {base_md_path}")
    text = base_md_path.read_text()
    section_match = _re.search(
        r"^## [^\n]*[Pp]illar[^\n]*\n(.*?)(?=^## |\Z)",
        text,
        _re.MULTILINE | _re.DOTALL,
    )
    if not section_match:
        raise RuntimeError("pillar section not found in base.md")
    section = section_match.group(1)
    entries = _re.findall(
        r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(.+?)(?=^\d+\.|\Z)",
        section,
        _re.MULTILINE | _re.DOTALL,
    )
    if len(entries) < 11:
        raise RuntimeError(f"expected 11 pillars in base.md, found {len(entries)}")
    return [
        f"{num}. **{title}** {body.strip()}"
        for num, title, body in entries[:11]
    ]


def get_pillars() -> list[str]:
    """Return the eleven aho pillars, cached after first load."""
    global _PILLARS_CACHE
    if _PILLARS_CACHE is None:
        _PILLARS_CACHE = _load_pillars_from_base()
    return _PILLARS_CACHE


def build_workstream_summary(checkpoint: dict) -> list[dict]:
    """Build workstream summary rows from a checkpoint dict."""
    # Resolve agent: checkpoint executor field > env var > "unknown"
    executor_fallback = checkpoint.get("executor") or os.environ.get("AHO_EXECUTOR", os.environ.get("IAO_EXECUTOR", "unknown"))
    rows = []
    for ws_id, ws_data in sorted(checkpoint.get("workstreams", {}).items()):
        if isinstance(ws_data, str):
            rows.append({
                "id": ws_id, "name": ws_id,
                "status": ws_data, "agent": executor_fallback, "wall_clock": "-",
            })
        else:
            agent = ws_data.get("agent") or ws_data.get("executor") or executor_fallback
            rows.append({
                "id": ws_id, "name": ws_id,
                "status": ws_data.get("status", "pending"),
                "agent": agent,
                "wall_clock": ws_data.get("wall_clock") or ws_data.get("duration") or "-",
            })
    return rows


def generate_run(iteration: str, workstreams: list[dict] = None, agent_questions: list[str] = None) -> Path:
    """Generate the run file for an iteration."""
    root = find_project_root()
    config = json.loads((root / ".aho.json").read_text())
    prefix = config.get("artifact_prefix") or config.get("name") or "aho"

    parts = iteration.split(".")
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration

    iter_dir = get_iterations_dir() / version
    iter_dir.mkdir(parents=True, exist_ok=True)

    if workstreams is None:
        ckpt_path = root / ".aho-checkpoint.json"
        if ckpt_path.exists():
            ckpt = json.loads(ckpt_path.read_text())
            workstreams = build_workstream_summary(ckpt)
        else:
            workstreams = []

    if agent_questions is None:
        build_log_path = iter_dir / f"{prefix}-build-log-{iteration}.md"
        from aho.paths import get_data_dir
        event_log_path = get_data_dir() / "aho_event_log.jsonl"
        agent_questions = collect_all_questions(iteration, build_log_path, event_log_path)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# Run File — {prefix} {iteration}",
        "",
        f"**Generated:** {now}",
        f"**Iteration:** {iteration}",
        f"**Phase:** {config.get('phase', 0)}",
        "",
        "## About this Report",
        "",
        "This run file is a canonical iteration artifact produced during the `iteration close` sequence. "
        "It serves as the primary feedback interface between the autonomous agent and the human supervisor. "
        "Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the "
        "iteration's ground truth: the execution checkpoint and the extracted agent questions.",
        "",
        "The report includes a workstream summary, a collection of technical or procedural questions "
        "surfaced by the agent during execution, and a sign-off section for the reviewer.",
        "",
        "---",
        "",
        "## Workstream Summary",
        "",
        "| Workstream | Status | Agent | Wall Clock |",
        "|---|---|---|---|",
    ]

    for ws in workstreams:
        lines.append(f"| {ws['id']} | {ws['status']} | {ws['agent']} | {ws['wall_clock']} |")

    # Component Activity section
    try:
        from aho.components.manifest import render_section
        component_md = render_section()
    except Exception:
        component_md = "*(component manifest not available)*"

    lines += [
        "",
        "---",
        "",
        "## Component Activity",
        "",
        component_md,
        "",
        "---",
        "",
        "## Agent Questions for Kyle",
        "",
    ]
    if agent_questions:
        for q in agent_questions:
            lines.append(f"- {q}")
    else:
        lines.append("(none — no questions surfaced during execution)")

    lines += [
        "",
        "---",
        "",
        "## Kyle's Notes for Next Iteration",
        "",
        "<!-- Fill in after reviewing the bundle -->",
        "",
        "",
        "---",
        "",
        "## Reference: The Eleven Pillars",
        "",
        *get_pillars(),
        "",
        "---",
        "",
        "## Sign-off",
        "",
        "- [ ] I have reviewed the bundle",
        "- [ ] I have reviewed the build log",
        "- [ ] I have reviewed the report",
        "- [ ] I have answered all agent questions above",
        "- [ ] I am satisfied with this iteration's output",
        "",
        "---",
        "",
        f"*Run report generated {now}*",
        "",
    ]

    output = iter_dir / f"{prefix}-run-{iteration}.md"
    output.write_text("\n".join(lines))
    return output
