"""check_compatibility.py - reads COMPATIBILITY.md and runs each check."""
import re, subprocess, sys
from pathlib import Path


def parse_checklist(md_path):
    lines = md_path.read_text().splitlines()
    rows = []
    in_table = False
    for line in lines:
        if line.startswith("| ID |"):
            in_table = True
            continue
        if line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            # Use regex to find parts, avoiding split on escaped pipes \|
            # This is a simple approximation: split on | NOT preceded by \
            parts = re.split(r"(?<!\\)\|", line)
            parts = [p.strip() for p in parts[1:-1]]
            if len(parts) >= 4 and parts[0].startswith("C"):
                # Clean up escaped pipes in the check command
                check_cmd = parts[2].strip("`").replace("\\|", "|")
                rows.append({
                    "id": parts[0],
                    "requirement": parts[1],
                    "check": check_cmd,
                    "required": parts[3].lower() == "yes",
                    "notes": parts[4] if len(parts) > 4 else "",
                })
    return rows


def run_check(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def main():
    md = Path(__file__).resolve().parent.parent / "COMPATIBILITY.md"
    if not md.exists():
        print(f"ERROR: {md} not found")
        sys.exit(2)
    rows = parse_checklist(md)
    failed_required = 0
    for row in rows:
        ok = run_check(row["check"])
        status = "PASS" if ok else ("FAIL" if row["required"] else "SKIP")
        print(f"  {status}: {row['id']} {row['requirement']}")
        if not ok and row["required"]:
            failed_required += 1
    print(f"Total: {len(rows)} checks, {failed_required} required failures")
    sys.exit(1 if failed_required > 0 else 0)


if __name__ == "__main__":
    main()
