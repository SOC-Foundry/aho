"""Migrate kjtcom harness artifacts (gotchas, ADRs, patterns) to aho.

Uses Nemotron-mini for classification.
"""
import json
import os
from pathlib import Path
from aho.artifacts.nemotron_client import classify

KJTCOM_GOTCHAS = Path.home() / "dev/projects/kjtcom/data/gotcha_archive.json"
IAO_GOTCHAS = Path("data/gotcha_archive.json")
AMBIGUOUS_FILE = Path("/tmp/iao-0.1.4-ambiguous-gotchas.md")


def migrate_gotchas():
    print("Starting Gotcha Migration...")
    if not KJTCOM_GOTCHAS.exists():
        print(f"Error: {KJTCOM_GOTCHAS} not found.")
        return

    with open(KJTCOM_GOTCHAS) as f:
        kjt_data = json.load(f)
    
    with open(IAO_GOTCHAS) as f:
        iao_data = json.load(f)
    
    existing_ids = {g["id"] for g in iao_data["gotchas"]}
    legacy_ids = {g.get("kjtcom_source_id") for g in iao_data["gotchas"] if g.get("kjtcom_source_id")}
    
    next_id_num = 108 # Start after ahomw-G107
    
    ambiguous = []
    universal = []
    skipped = 0

    # Kjtcom schema uses 'registry' key
    for g in kjt_data.get("registry", []):
        kjt_id = g.get("id")
        if kjt_id in legacy_ids:
            skipped += 1
            continue
            
        title = g.get("title") or g.get("description") or "Untitled"
        action = g.get("action") or g.get("resolution") or ""
        text = f"Title: {title}\nAction/Resolution: {action}"
        
        category = classify(text, ["UNIVERSAL", "KJTCOM-SPECIFIC", "AMBIGUOUS"])
        print(f"[{kjt_id}] {title[:40]}... -> {category}")
        
        if category == "UNIVERSAL":
            new_id = f"ahomw-G{next_id_num}"
            next_id_num += 1
            universal.append({
                "id": new_id,
                "title": title,
                "pattern": action,
                "symptoms": g.get("symptoms", ["Migrated from kjtcom"]),
                "mitigation": action,
                "context": f"Migrated from kjtcom {kjt_id} in iao 0.1.4 W3.",
                "kjtcom_source_id": kjt_id
            })
        elif category == "AMBIGUOUS":
            ambiguous.append({
                "id": kjt_id,
                "title": title,
                "text": text
            })
        else:
            skipped += 1

    # Write universal to registry
    if universal:
        iao_data["gotchas"].extend(universal)
        with open(IAO_GOTCHAS, "w") as f:
            json.dump(iao_data, f, indent=2)
        print(f"Added {len(universal)} universal gotchas.")

    # Write ambiguous to /tmp
    if ambiguous:
        lines = ["# Ambiguous Gotchas for Review\n", "Iteration: 0.1.4\n"]
        for g in ambiguous:
            lines.append(f"## {g['id']}: {g['title']}\n")
            lines.append(f"{g['text']}\n")
        AMBIGUOUS_FILE.write_text("\n".join(lines))
        print(f"Wrote {len(ambiguous)} ambiguous gotchas to {AMBIGUOUS_FILE}")
    
    return len(ambiguous) > 0


if __name__ == "__main__":
    has_ambiguous = migrate_gotchas()
    if has_ambiguous:
        print("PAUSE_REQUIRED")
