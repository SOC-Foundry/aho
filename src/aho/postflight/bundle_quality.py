"""Post-flight check: bundle quality gate (ahomw-ADR-029)."""
import json
import re
from pathlib import Path


def check():
    """Returns (status, message) tuple."""
    from aho.paths import find_project_root

    try:
        root = find_project_root()
        aho_json = root / ".aho.json"
        if not aho_json.exists():
            return ("fail", ".aho.json not found")

        config = json.loads(aho_json.read_text())
        iteration = config.get("current_iteration", "")
        prefix = config.get("artifact_prefix") or config.get("name") or "aho"

        parts = iteration.split(".")
        version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration

        bundle_path = root / "artifacts" / "iterations" / version / f"{prefix}-bundle-{iteration}.md"
        if not bundle_path.exists():
            return ("warn", f"Bundle not yet generated: {bundle_path.name}")

        content = bundle_path.read_text()
        
        from aho.bundle import validate_bundle
        errors = validate_bundle(bundle_path)
        
        # §22 component count floor check
        checkpoint_path = root / ".aho-checkpoint.json"
        run_type = "mixed"
        if checkpoint_path.exists():
            try:
                ckpt = json.loads(checkpoint_path.read_text())
                run_type = ckpt.get("run_type", "mixed")
            except Exception:
                pass
                
        FLOORS = {"agent_execution": 6, "reorg_docs": 2, "hygiene": 1, "mixed": 3}
        floor = FLOORS.get(run_type, 3)
        
        # Extract component count from §22 section in bundle
        # Match: **Unique components:** (\d+)
        match = re.search(r"\*\*Unique components:\*\*\s+(\d+)", content)
        if match:
            unique_components = int(match.group(1))
            if unique_components < floor:
                errors.append(f"§22 component count {unique_components} < {floor} (run_type: {run_type})")
        else:
             # Only error if it's not a dry-run or something? 
             # Actually, if the bundle is generated, it SHOULD have §22.
             errors.append("§22 Unique components count not found in bundle")

        if errors:
            return ("fail", f"{len(errors)} errors: {'; '.join(errors[:3])}")

        size_kb = bundle_path.stat().st_size // 1024
        return ("ok", f"Bundle valid ({size_kb} KB, run_type: {run_type})")
    except Exception as e:
        return ("fail", f"error: {e}")
