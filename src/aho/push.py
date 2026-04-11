"""aho push - continuous improvement feedback loop skeleton (10.68.1 W8).

v10.68: skeleton only, does not push to github. Emits PR draft to stdout.
"""
import pathlib
import re
import json
from typing import List


def scan_candidates(project_harness_path: pathlib.Path) -> List[dict]:
    if not project_harness_path.exists():
        return []
    text = project_harness_path.read_text()
    candidates = []
    pattern = re.compile(
        r'^### ([a-z0-9]{5}-(?:ADR|Pattern)-\d+)[:\s]+(.+?)$(.+?)(?=^###\s|\Z)',
        re.MULTILINE | re.DOTALL
    )
    for m in pattern.finditer(text):
        body = m.group(3)
        if "scope: universal-candidate" in body.lower():
            candidates.append({
                "id": m.group(1),
                "title": m.group(2).strip(),
                "body": body.strip(),
            })
    return candidates


def generate_pr_draft(candidates, project_code, iteration):
    if not candidates:
        return ""
    lines = [
        f"# aho push from {project_code} {iteration}",
        "",
        f"**Project:** {project_code}",
        f"**Iteration:** {iteration}",
        f"**Candidates:** {len(candidates)}",
        "",
        "## Proposed promotions to ahomw",
        "",
    ]
    for c in candidates:
        lines.append(f"### Promote {c['id']} -> ahomw-*")
        lines.append(f"**Original title:** {c['title']}")
        lines.append("")
        lines.append(c["body"])
        lines.append("")
        lines.append(f"**Origin:** `origin: {project_code} {iteration}, promoted to ahomw v<TBD>`")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def cli_main():
    import sys
    from aho.paths import find_project_root

    try:
        project_root = find_project_root()
    except Exception as e:
        print(f"[FAIL] cannot find project root: {e}", file=sys.stderr)
        return 1

    iao_json = project_root / ".aho.json"
    if not iao_json.exists():
        print("[FAIL] .aho.json not found", file=sys.stderr)
        return 1

    data = json.loads(iao_json.read_text())
    project_code = data.get("project_code")
    iteration = data.get("current_iteration", "unknown")
    if not project_code:
        print("[FAIL] .aho.json missing project_code", file=sys.stderr)
        return 1

    project_harness = project_root / project_code / "docs" / "harness" / "project.md"
    candidates = scan_candidates(project_harness)

    if not candidates:
        print("no universal candidates found, nothing to push")
        return 0

    draft = generate_pr_draft(candidates, project_code, iteration)
    print("=" * 60)
    print("10.68: github push deferred, draft only")
    print("=" * 60)
    print(draft)
    print("=" * 60)
    print(f"\n{len(candidates)} candidate(s) found. Draft above.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(cli_main())
