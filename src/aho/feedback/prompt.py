"""Sign-off validation for iteration close --confirm."""
import re
from pathlib import Path


def validate_signoff(run_path: Path) -> tuple[bool, list[str]]:
    """Check all sign-off boxes are ticked. Returns (all_ticked, missing)."""
    if not run_path.exists():
        return False, ["Run report does not exist"]

    content = run_path.read_text()

    # Find the Sign-off section
    signoff_match = re.search(
        r"## Sign-off\s*\n(.*?)(?=\n## |\n---|\Z)",
        content,
        re.DOTALL,
    )
    if not signoff_match:
        return False, ["No Sign-off section found in run report"]

    signoff_text = signoff_match.group(1)

    # Check for unchecked boxes
    unchecked = re.findall(r"- \[ \] (.+)", signoff_text)
    checked = re.findall(r"- \[x\] (.+)", signoff_text, re.IGNORECASE)

    if not checked and not unchecked:
        return False, ["No sign-off checkboxes found"]

    if unchecked:
        return False, unchecked

    return True, []
