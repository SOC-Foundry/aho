"""Pipeline validation — `aho pipeline validate <name>`."""
from pathlib import Path

from aho.pipelines.pattern import PHASE_DESCRIPTIONS


def validate_pipeline(name: str, target_dir: Path = None) -> list[str]:
    """Return list of validation errors. Empty = valid."""
    if target_dir is None:
        target_dir = Path.cwd()

    pipeline_dir = target_dir / "pipelines" / name
    errors = []

    if not pipeline_dir.exists():
        return [f"Pipeline directory not found: {pipeline_dir}"]

    for phase_name in PHASE_DESCRIPTIONS:
        phase_file = pipeline_dir / f"{phase_name}.py"
        if not phase_file.exists():
            errors.append(f"Missing phase file: {phase_name}.py")
            continue
        content = phase_file.read_text()
        if "def main()" not in content:
            errors.append(f"{phase_name}.py missing main() function")

    checkpoint = pipeline_dir / "checkpoint.json"
    if not checkpoint.exists():
        errors.append("Missing checkpoint.json")

    return errors
