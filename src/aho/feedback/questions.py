"""Extract agent questions from build log and event log for run report."""
import re
import json
from pathlib import Path


QUESTION_MARKER_RE = re.compile(
    r"(?:Agent Question for Kyle|Agent Question|Question for Kyle)[:\-]\s*(.+?)(?=\n\n|\n#|\n---|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def extract_questions_from_build_log(build_log_path: Path) -> list[str]:
    """Extract questions from build log markers.

    Looks for lines starting with 'Agent Question for Kyle:' or similar
    and collects the text until the next blank line, section, or EOF.
    """
    if not build_log_path.exists():
        return []
    content = build_log_path.read_text()
    matches = QUESTION_MARKER_RE.findall(content)
    return [m.strip() for m in matches if m.strip()]


def extract_questions_from_event_log(event_log_path: Path, iteration: str) -> list[str]:
    """Extract questions from JSONL event log tagged with the current iteration."""
    if not event_log_path.exists():
        return []
    questions = []
    for line in event_log_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "agent_question" and event.get("iteration") == iteration:
            text = event.get("text") or event.get("question") or ""
            if text:
                questions.append(text)
    return questions


def collect_all_questions(iteration: str, build_log_path: Path, event_log_path: Path) -> list[str]:
    """Collect questions from both sources, deduplicated."""
    build_log_questions = extract_questions_from_build_log(build_log_path)
    event_log_questions = extract_questions_from_event_log(event_log_path, iteration)
    seen = set()
    combined = []
    for q in build_log_questions + event_log_questions:
        if q not in seen:
            seen.add(q)
            combined.append(q)
    return combined
