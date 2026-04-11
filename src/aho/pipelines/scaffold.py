"""Pipeline scaffolding — `aho pipeline init <name>`."""
import json
from datetime import datetime, timezone
from pathlib import Path

from aho.pipelines.pattern import PHASE_DESCRIPTIONS


def scaffold_pipeline(name: str, target_dir: Path = None) -> Path:
    """Create a new pipeline directory from the skeleton template."""
    if target_dir is None:
        target_dir = Path.cwd()

    pipeline_dir = target_dir / "pipelines" / name
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    # Create phase files
    for phase_name, description in PHASE_DESCRIPTIONS.items():
        phase_file = pipeline_dir / f"{phase_name}.py"
        phase_file.write_text(
            f'"""{name} — {phase_name.replace("_", " ").title()}.\n\n'
            f"{description}. Project-specific implementation\n"
            f'replaces the TODO block.\n"""\n'
            f"import json\n"
            f"from pathlib import Path\n\n"
            f'PIPELINE = "{name}"\n'
            f'PHASE = "{phase_name}"\n'
            f"CHECKPOINT_PATH = Path(__file__).parent / \"checkpoint.json\"\n\n\n"
            f"def read_checkpoint() -> dict:\n"
            f"    if CHECKPOINT_PATH.exists():\n"
            f"        return json.loads(CHECKPOINT_PATH.read_text())\n"
            f"    return {{}}\n\n\n"
            f"def write_checkpoint(state: dict) -> None:\n"
            f"    CHECKPOINT_PATH.write_text(json.dumps(state, indent=2))\n\n\n"
            f"def main() -> int:\n"
            f"    checkpoint = read_checkpoint()\n"
            f'    if checkpoint.get(PHASE, {{}}).get("status") == "complete":\n'
            f'        print(f"{{PIPELINE}}/{{PHASE}} already complete, skipping")\n'
            f"        return 0\n\n"
            f"    # TODO: project-specific logic goes here\n"
            f'    raise NotImplementedError(f"{{PHASE}} TODO")\n\n\n'
            f'if __name__ == "__main__":\n'
            f"    raise SystemExit(main())\n"
        )

    # Create checkpoint.json
    checkpoint = {
        "pipeline": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phases": {},
    }
    (pipeline_dir / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2))

    # Create README
    (pipeline_dir / "README.md").write_text(
        f"# {name} Pipeline\n\n"
        f"10-phase pipeline scaffolded by `aho pipeline init`.\n\n"
        f"## Phases\n\n"
        + "\n".join(f"- **{k}**: {v}" for k, v in PHASE_DESCRIPTIONS.items())
        + "\n\n## Usage\n\n"
        f"Fill in each phase's `main()` function with project-specific logic.\n"
        f"The checkpoint tracks which phases have completed.\n"
    )

    return pipeline_dir
