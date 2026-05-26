"""gap_carry_forward_writer - append carry-forward entries to the canonical
carry-forwards-{iteration}.md file in the existing structural shape.

Entry shape (per carry-forwards-0.2.16.md):

    - **{id} - {title}**
      - Severity: {info|important|cosmetic|critical}
      - {body line(s) - what surfaced / mechanism / location}
      - Disposition: {disposition text}
      - Target: {target iteration or workstream}
      - Source: {source reference}
      - Audit traceability: {finding id and audit archive path}

Inserted under the matching `## Target: {target}` heading. New target
sections are appended in target-order. Pillar 11: writes only to
artifacts/iterations/. Never invokes git.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.gap_carry_forward_writer")
except ImportError:  # pragma: no cover
    _otel_trace = None
    _tracer = None

try:
    from opentelemetry import metrics as _otel_metrics
    _meter = _otel_metrics.get_meter("aho.gap_carry_forward_writer")
    _reindex_failure_counter = _meter.create_counter(
        "aho.gap_carry_forward_writer.reindex_failures",
        description=(
            "Re-index failures during gap-carry-forward append. Append "
            "succeeds regardless; this counter signals staleness risk for "
            "the iteration-context ChromaDB collection."
        ),
        unit="1",
    )
except ImportError:  # pragma: no cover
    _otel_metrics = None
    _meter = None
    _reindex_failure_counter = None


VALID_SEVERITIES = ("info", "cosmetic", "important", "critical")

ENTRY_HEADER_RE = re.compile(r"^- \*\*([A-Za-z0-9.\-_/]+)\s+-\s+")
TARGET_HEADER_RE = re.compile(r"^## Target:\s+(.+?)\s*$")
CARRY_FWD_FILENAME_RE = re.compile(r"^carry-forwards-(\d+\.\d+\.\d+)\.md$")


class GapCarryForwardError(RuntimeError):
    pass


class GapCarryForwardInputError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Entry rendering
# ---------------------------------------------------------------------------

def _normalize_body_lines(body: str) -> List[str]:
    """Return the body as a list of indented bullet sub-lines (4-space indent
    for sub-bullet wraps that match existing file shape).
    """
    lines = [ln.rstrip() for ln in body.strip().splitlines() if ln.strip()]
    return lines


def render_entry(entry: Dict[str, Any]) -> str:
    """Render a structured entry into markdown matching the existing file
    shape. Caller-provided fields:

    - id (required) - e.g. "F-0.2.17-W2-001"
    - title (required) - short headline
    - severity (required) - one of VALID_SEVERITIES
    - what_surfaced (required) - short prose; rendered as the first body line
    - mechanism (optional) - second body bullet line
    - location (optional) - file/line pointer
    - disposition (required) - short prose
    - target (required) - e.g. "0.2.17 W3" or "0.2.18"
    - source (required) - reference to the surfacing artifact
    - audit_traceability (optional) - link to the audit finding that
      surfaced this carry-forward
    """
    for required in ("id", "title", "severity", "what_surfaced",
                     "disposition", "target", "source"):
        if required not in entry or not str(entry[required]).strip():
            raise GapCarryForwardInputError(
                f"entry missing required field: {required!r}"
            )
    severity = entry["severity"]
    if severity not in VALID_SEVERITIES:
        raise GapCarryForwardInputError(
            f"severity {severity!r} not one of {VALID_SEVERITIES}"
        )

    lines: List[str] = []
    lines.append(f"- **{entry['id']} - {str(entry['title']).strip()}**")
    lines.append(f"  - Severity: {severity}")

    what = str(entry["what_surfaced"]).strip()
    for sub in _normalize_body_lines(what):
        lines.append(f"  - {sub}" if not sub.startswith("- ") else f"  {sub}")

    if entry.get("mechanism"):
        lines.append(f"  - Mechanism: {str(entry['mechanism']).strip()}")
    if entry.get("location"):
        lines.append(f"  - Location: {str(entry['location']).strip()}")

    lines.append(f"  - Disposition: {str(entry['disposition']).strip()}")
    lines.append(f"  - Target: {str(entry['target']).strip()}")
    lines.append(f"  - Source: {str(entry['source']).strip()}")
    if entry.get("audit_traceability"):
        lines.append(
            f"  - Audit traceability: {str(entry['audit_traceability']).strip()}"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# File mutation
# ---------------------------------------------------------------------------

def _find_target_section(
    lines: List[str], target: str
) -> Tuple[Optional[int], Optional[int]]:
    """Return (section_start_line_index, section_end_line_index) for the
    `## Target: {target}` section, or (None, None) if not present.
    section_end is the index of the next `## ` heading or end of file.
    """
    start = None
    for i, line in enumerate(lines):
        m = TARGET_HEADER_RE.match(line)
        if m and m.group(1).strip() == target.strip():
            start = i
            break
    if start is None:
        return None, None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ") and not lines[j].startswith("## Target:"):
            end = j
            break
        if lines[j].startswith("## Target:") and j != start:
            end = j
            break
    return start, end


def _entry_count_in_section(lines: List[str], start: int, end: int) -> int:
    return sum(
        1 for ln in lines[start:end] if ENTRY_HEADER_RE.match(ln)
    )


def total_entry_count(text: str) -> int:
    return sum(1 for ln in text.splitlines() if ENTRY_HEADER_RE.match(ln))


def _emit_span(*, file_path: Path, target: str, entry_id: str) -> None:
    if _tracer is None:
        return
    with _tracer.start_as_current_span("aho.gap_carry_forward_writer") as span:
        try:
            span.set_attribute("aho.cf.file_path", str(file_path))
            span.set_attribute("aho.cf.target", target)
            span.set_attribute("aho.cf.entry_id", entry_id)
            span.set_attribute("aho.materiality.bucket", "carry_forward_added")
        except Exception:
            pass


def _trigger_reindex(file_path: Path) -> Dict[str, Any]:
    """Re-index the carry-forwards file in ChromaDB after a successful append.

    Best-effort by design (F-0.2.17-W4-001 closure). Failures emit a warning
    to stderr + increment `aho.gap_carry_forward_writer.reindex_failures`
    counter, but never block the append.

    Returns dict with `reindex_status` ('ok'|'failed'|'skipped'), and on
    success `doc_id` + `iteration` + `project`. On failure, `error` carries
    the exception type and message.
    """
    iteration: Optional[str] = None
    m = CARRY_FWD_FILENAME_RE.match(file_path.name)
    if m:
        iteration = m.group(1)
    else:
        iteration = os.environ.get("AHO_ITERATION") or None
    if not iteration:
        return {
            "reindex_status": "skipped",
            "reason": (
                "iteration label undeterminable: filename does not match "
                "carry-forwards-{X.Y.Z}.md and AHO_ITERATION env not set"
            ),
        }
    project = os.environ.get("AHO_PROJECT", "ahomw")
    try:
        from . import rag as _rag
    except ImportError as exc:
        _record_reindex_failure(
            file_path=file_path,
            iteration=iteration,
            error_type="ImportError",
            error_message=str(exc),
        )
        return {
            "reindex_status": "failed",
            "iteration": iteration,
            "project": project,
            "error": f"ImportError: {exc}",
        }
    try:
        doc_id = _rag.index_artifact(
            file_path,
            project=project,
            iteration=iteration,
            workstream="carry-forwards",
        )
    except (_rag.RagError, _rag.RagInputError, OSError) as exc:
        _record_reindex_failure(
            file_path=file_path,
            iteration=iteration,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        return {
            "reindex_status": "failed",
            "iteration": iteration,
            "project": project,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "reindex_status": "ok",
        "iteration": iteration,
        "project": project,
        "doc_id": doc_id,
    }


def _record_reindex_failure(
    *,
    file_path: Path,
    iteration: str,
    error_type: str,
    error_message: str,
) -> None:
    """Emit OTEL counter increment + stderr warning for a re-index failure."""
    import sys
    print(
        f"WARNING: aho.gap_carry_forward_writer reindex failed for "
        f"{file_path}: {error_type}: {error_message}",
        file=sys.stderr,
    )
    if _reindex_failure_counter is None:
        return
    try:
        _reindex_failure_counter.add(
            1,
            attributes={
                "aho.cf.file_path": str(file_path),
                "aho.cf.iteration": iteration,
                "aho.cf.error_type": error_type,
            },
        )
    except (ValueError, RuntimeError, AttributeError):
        # OTEL is observability - never block the append return.
        pass


def append_to_file(
    *,
    file_path: str | Path,
    entry: Dict[str, Any],
) -> Dict[str, Any]:
    """Append a rendered entry to the right section of the carry-forwards
    file. Creates the section if missing. Returns dict with `file_path`,
    `entry_id`, `target_section`, `entry_count_before`, `entry_count_after`,
    `lines_added`.
    """
    rendered = render_entry(entry)
    target = str(entry["target"]).strip()
    p = Path(file_path)
    if not p.exists():
        raise GapCarryForwardError(f"carry-forwards file does not exist: {p}")
    original = p.read_text(encoding="utf-8")
    lines = original.splitlines()
    entries_before = total_entry_count(original)
    line_count_before = len(lines)

    section_start, section_end = _find_target_section(lines, target)
    if section_start is None:
        # Append a new section at end of file.
        new_lines = lines[:]
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(f"## Target: {target}")
        new_lines.append("")
        new_lines.extend(rendered.rstrip("\n").splitlines())
        new_lines.append("")
        target_section = "appended_new_section"
    else:
        # Insert before the next `##` heading. If the section ends with
        # blank lines, preserve them as a tail.
        insertion_idx = section_end
        # Walk backwards over trailing blanks so we insert before them.
        while insertion_idx > section_start + 1 and lines[insertion_idx - 1].strip() == "":
            insertion_idx -= 1
        new_lines = lines[:insertion_idx] + rendered.rstrip("\n").splitlines() + [""] + lines[insertion_idx:]
        target_section = f"appended_to_existing_section[{section_start}:{section_end}]"

    new_text = "\n".join(new_lines)
    if not new_text.endswith("\n"):
        new_text += "\n"
    p.write_text(new_text, encoding="utf-8")

    entries_after = total_entry_count(new_text)
    line_count_after = len(new_text.splitlines())
    _emit_span(file_path=p, target=target, entry_id=str(entry["id"]))
    # Materiality - drafter-flagged carry-forward addition is the
    # caught_by_drafter signal; W3 will add resolution-rate signal when
    # an executor closes a carry-forward in their workstream output.
    try:
        from . import materiality as _materiality
        _materiality.record_caught_by_drafter(
            severity=str(entry.get("severity", "info")),
            extra={"aho.cf.entry_id": str(entry["id"])},
        )
    except Exception:
        pass

    reindex = _trigger_reindex(p)

    return {
        "file_path": str(p),
        "entry_id": str(entry["id"]),
        "target_section": target_section,
        "entry_count_before": entries_before,
        "entry_count_after": entries_after,
        "entries_added": entries_after - entries_before,
        "lines_added": line_count_after - line_count_before,
        "reindex": reindex,
    }


def carry_forward_file_path(
    iteration: str, *, iteration_root: Optional[Path] = None
) -> Path:
    """Return the canonical carry-forwards file path for an iteration."""
    if iteration_root is None:
        from aho.paths import get_iterations_dir
        iteration_root = get_iterations_dir()
    return iteration_root / iteration / f"carry-forwards-{iteration}.md"


def write_carry_forward(
    *,
    entry: Dict[str, Any],
    iteration: Optional[str] = None,
    iteration_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Convenience: resolve file path from entry's iteration context (defaults
    to AHO_ITERATION env) and append.
    """
    iteration = iteration or os.environ.get("AHO_ITERATION")
    if not iteration:
        raise GapCarryForwardInputError(
            "iteration required (set AHO_ITERATION or pass iteration=)"
        )
    fp = carry_forward_file_path(iteration, iteration_root=iteration_root)
    return append_to_file(file_path=fp, entry=entry)
