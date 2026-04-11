"""aho harness alignment tool - enforces two-harness model (10.68.1 W4)."""
import re
import json
import pathlib
from typing import List

BASE_ID_PATTERN = re.compile(r'ahomw-(ADR|Pattern|Pillar|G)-?(\d+)')
PROJECT_ID_PATTERN = re.compile(r'([a-z0-9]{5})-(ADR|Pattern|G)-?(\d+)')


class HarnessViolation:
    def __init__(self, rule, severity, message):
        self.rule = rule
        self.severity = severity  # "fail" | "warn"
        self.message = message

    def __repr__(self):
        return f"[{self.severity.upper()}] Rule {self.rule}: {self.message}"


def parse_base_harness(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"ids": set(), "error": f"base.md not found at {path}"}
    text = path.read_text()
    ids = set()
    for m in BASE_ID_PATTERN.finditer(text):
        ids.add(f"ahomw-{m.group(1)}-{m.group(2)}")
    return {"ids": ids, "error": None}


def parse_project_harness(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"code": None, "acknowledged": set(), "local_ids": set(),
                "ahomw_definitions": set(), "error": f"project.md not found at {path}"}
    text = path.read_text()

    code_match = re.search(r'\*\*Project code:\*\*\s*([a-z0-9]{5})', text)
    code = code_match.group(1) if code_match else None

    acknowledged = set()
    ack_match = re.search(r'\*\*Base imports \(acknowledged\):\*\*(.*?)(?=\n\n|\n\*Acknowledg)', text, re.DOTALL)
    if ack_match:
        ack_text = ack_match.group(1)
        # Expand range patterns like ahomw-ADR-001..014
        for rm in re.finditer(r'ahomw-(ADR|Pattern|Pillar|G)-?(\d+)\.\.(\d+)', ack_text):
            kind = rm.group(1)
            start_n = int(rm.group(2))
            end_n = int(rm.group(3))
            for n in range(start_n, end_n + 1):
                # Pad to width of original
                width = len(rm.group(2))
                acknowledged.add(f"ahomw-{kind}-{str(n).zfill(width)}")
        for m in BASE_ID_PATTERN.finditer(ack_text):
            acknowledged.add(f"ahomw-{m.group(1)}-{m.group(2)}")

    local_ids = set()
    for m in PROJECT_ID_PATTERN.finditer(text):
        if m.group(1) != "ahomw":
            local_ids.add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    ahomw_definitions = set()
    for m in re.finditer(r'^### (ahomw-[A-Za-z]+-?\d+)', text, re.MULTILINE):
        ahomw_definitions.add(m.group(1))

    return {
        "code": code,
        "acknowledged": acknowledged,
        "local_ids": local_ids,
        "ahomw_definitions": ahomw_definitions,
        "error": None,
    }


def check_alignment(base_path: pathlib.Path, project_path: pathlib.Path) -> List[HarnessViolation]:
    violations = []
    base = parse_base_harness(base_path)
    proj = parse_project_harness(project_path)

    if base.get("error"):
        violations.append(HarnessViolation("setup", "fail", base["error"]))
        return violations
    if proj.get("error"):
        violations.append(HarnessViolation("setup", "fail", proj["error"]))
        return violations

    code = proj["code"]
    if not code:
        violations.append(HarnessViolation("A", "fail", "project harness missing **Project code:** header"))
        return violations

    # Rule A: ID collision
    for lid in proj["local_ids"]:
        prefix = lid.split("-")[0]
        if prefix != code:
            violations.append(HarnessViolation("A", "fail", f"local ID {lid} does not match project code {code}"))

    # Rule B: base inviolability
    for bad_id in proj["ahomw_definitions"]:
        violations.append(HarnessViolation("B", "fail", f"project defines {bad_id} - only base may define ahomw-* IDs"))

    # Rule C: acknowledgment currency
    unacknowledged = base["ids"] - proj["acknowledged"]
    for uid in sorted(unacknowledged):
        violations.append(HarnessViolation("C", "warn", f"base ID {uid} not in project acknowledgment list"))

    return violations


def cli_main():
    import sys
    from aho.paths import find_project_root
    try:
        project_root = find_project_root()
    except Exception as e:
        print(f"[FAIL] cannot find project root: {e}", file=sys.stderr)
        return 1

    base_path = project_root / "aho" / "docs" / "harness" / "base.md"
    iao_json = project_root / ".aho.json"
    if not iao_json.exists():
        print("[FAIL] .aho.json not found", file=sys.stderr)
        return 1
    iao_data = json.loads(iao_json.read_text())
    proj_code = iao_data.get("project_code")
    if not proj_code:
        print("[FAIL] .aho.json missing project_code", file=sys.stderr)
        return 1

    project_path = project_root / proj_code / "docs" / "harness" / "project.md"
    violations = check_alignment(base_path, project_path)

    fails = [v for v in violations if v.severity == "fail"]
    warns = [v for v in violations if v.severity == "warn"]

    if not violations:
        print("[ok] harness alignment: clean")
        return 0

    for v in violations:
        print(v)
    print(f"\nSummary: {len(fails)} FAIL, {len(warns)} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    sys.exit(cli_main())
