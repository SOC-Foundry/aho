"""tier_manifest - write the per-host tier manifest (~/.config/aho/tier.json).

F-0.2.18-W2-003 closure (0.3.1 W2 D6): the minimal inline tier-detect-and-write
that lived in install.fish becomes a first-class, testable subcommand. Builds
on aho.tier_detect for VRAM probing + classification so the threshold logic is
not duplicated.

The manifest shape (consumed by bin/aho-models, aho.council.dispatch, etc.):
    {
      "host_id":         short hostname,
      "tier":            "base" | "partial" | "full",
      "deployment_mode": "production",
      "families":        model families for the tier,
      "bundle":          ollama models to pull for the tier,
      "rationale":       human-readable note,
      "vram_gb":         detected GPU VRAM in GiB (0 if no NVIDIA GPU),
      "detected_at":     ISO-8601 UTC
    }
"""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from aho.tier_detect import classify, probe_vram_mb


# Per-tier model bundles. base runs small models on CPU/iGPU; partial/full add
# the larger auditor + multimodal seats.
TIER_BUNDLES: Dict[str, list] = {
    "base": ["llama3.2:3b", "nomic-embed-text"],
    "partial": ["qwen3.5:9b", "nomic-embed-text"],
    "full": ["qwen3.5:9b", "glm-4.6v:flash", "nomic-embed-text"],
}

TIER_FAMILIES: Dict[str, list] = {
    "base": ["llama3", "nomic"],
    "partial": ["qwen3", "nomic"],
    "full": ["qwen3", "glm", "nomic"],
}


def manifest_path() -> Path:
    return Path(os.environ.get(
        "AHO_TIER_MANIFEST", str(Path.home() / ".config" / "aho" / "tier.json")
    ))


def build_manifest(host_id: Optional[str] = None) -> Dict[str, Any]:
    """Detect VRAM, classify tier, and assemble the manifest dict."""
    vram_mb = probe_vram_mb()
    tier = classify(vram_mb)
    vram_gb = (vram_mb // 1024) if vram_mb else 0
    host = host_id or socket.gethostname().split(".")[0]
    return {
        "host_id": host,
        "tier": tier,
        "deployment_mode": "production",
        "families": TIER_FAMILIES.get(tier, ["llama3", "nomic"]),
        "bundle": TIER_BUNDLES.get(tier, TIER_BUNDLES["base"]),
        "rationale": f"auto-detected by aho install tier-manifest (vram_gb={vram_gb})",
        "vram_gb": vram_gb,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(path: Optional[Path] = None, host_id: Optional[str] = None) -> Path:
    """Build + write the manifest. Idempotent in shape (re-running reclassifies
    and rewrites; the only volatile field is detected_at).
    """
    target = path or manifest_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(host_id=host_id)
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return target


def main(argv: Optional[list] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Detect VRAM, classify tier, write ~/.config/aho/tier.json. F-0.2.18-W2-003."
    )
    ap.add_argument("--print", action="store_true",
                    help="Print the manifest that would be written; do not write.")
    args = ap.parse_args(argv)

    if args.print:
        print(json.dumps(build_manifest(), indent=2))
        return 0

    p = write_manifest()
    data = json.loads(p.read_text())
    print(f"wrote {p}: tier={data['tier']} vram_gb={data['vram_gb']} bundle={data['bundle']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
