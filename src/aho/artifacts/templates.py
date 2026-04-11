"""Jinja2 template loading for the artifact loop.

Templates live in the `artifacts/prompts/` directory as
`{artifact}.md.j2`. Each is rendered with the iteration context
(version, prefix, project, workstreams, prior_artifacts) and the result
becomes the user prompt sent to Qwen via Ollama.

W6 addition (0.1.3): trident_block and ten_pillars_block loaded from base.md.
W1 update (0.1.8): pillars_block reads the eleven pillars; ten_pillars_block
kept as alias for template backward compatibility.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from aho.paths import get_prompts_dir, get_harness_dir


def _load_harness_blocks() -> Dict[str, str]:
    """Extract the eleven pillars from base.md.

    The Trident mermaid block was retired in 0.1.8 (absorbed into Pillar 1 and 8).
    """
    base_path = get_harness_dir() / "base.md"
    if not base_path.exists():
        return {"trident_block": "(retired in 0.1.8)", "pillars_block": "(base.md not found)", "ten_pillars_block": "(retired in 0.1.8)"}

    content = base_path.read_text()

    # Extract the eleven pillars section
    pillars_match = re.search(
        r"^## [^\n]*[Pp]illar[^\n]*\n(.*?)(?=^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    pillars = pillars_match.group(0).strip() if pillars_match else "(pillars not found in base.md)"

    return {
        "trident_block": "(retired in 0.1.8 — see Pillar 1 and 8)",
        "pillars_block": pillars,
        "ten_pillars_block": pillars,  # backward compat alias
    }


def get_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(get_prompts_dir())),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )


def render_prompt(artifact: str, context: Dict[str, Any]) -> str:
    env = get_environment()
    template = env.get_template(f"{artifact}.md.j2")

    # Inject harness blocks if not already in context
    if "pillars_block" not in context or "ten_pillars_block" not in context:
        blocks = _load_harness_blocks()
        context = {**blocks, **context}

    return template.render(**context)
