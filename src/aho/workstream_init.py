"""workstream_init.py - write literal env values into .claude/settings.json.

F-W1-001 closure (0.2.17 W0 Bucket 1). Claude Code does not shell-expand
${AHO_ITERATION} / ${AHO_WORKSTREAM} in .claude/settings.json env values:
the literal string "${AHO_ITERATION}" lands in OTEL resource attributes,
not the runtime value. This module updates the settings.json env block
in place with literal iteration + workstream values, so a workstream
boundary can be a one-command operation instead of a manual JSON edit.

Used by:
    aho iteration workstream init W{N} [--iteration 0.2.17]

Returns True if the file changed, False if it was already at the target
state (idempotent).
"""
from __future__ import annotations

import json
from pathlib import Path

from aho.paths import AhoProjectNotFound, find_project_root


_OTEL_ATTRS_KEY = "OTEL_RESOURCE_ATTRIBUTES"


def _resolve_settings_path(settings_path: str | None) -> Path:
    if settings_path:
        return Path(settings_path)
    try:
        root = find_project_root()
    except AhoProjectNotFound as exc:
        raise FileNotFoundError(
            "Could not resolve project root for .claude/settings.json. "
            "Pass --settings-path or set AHO_PROJECT_ROOT."
        ) from exc
    return root / ".claude" / "settings.json"


def _rewrite_resource_attrs(attrs: str, iteration: str, workstream_id: str) -> str:
    """Replace aho.iteration and aho.workstream in the OTEL_RESOURCE_ATTRIBUTES
    csv string with literal values. Other keys (service.name, aho.role, etc.)
    are preserved in their original order. Missing aho.* keys are appended.
    """
    pairs = [p for p in (s.strip() for s in attrs.split(",")) if p]
    seen_iter = False
    seen_ws = False
    out: list[str] = []
    for pair in pairs:
        if "=" not in pair:
            out.append(pair)
            continue
        k, _v = pair.split("=", 1)
        k = k.strip()
        if k == "aho.iteration":
            out.append(f"aho.iteration={iteration}")
            seen_iter = True
        elif k == "aho.workstream":
            out.append(f"aho.workstream={workstream_id}")
            seen_ws = True
        else:
            out.append(pair)
    if not seen_iter:
        out.append(f"aho.iteration={iteration}")
    if not seen_ws:
        out.append(f"aho.workstream={workstream_id}")
    return ",".join(out)


def init_settings_for_workstream(
    *,
    iteration: str,
    workstream_id: str,
    settings_path: str | None = None,
) -> bool:
    """Update .claude/settings.json env block with literal iteration + ws values.

    Raises FileNotFoundError if settings.json does not exist.
    Raises json.JSONDecodeError / ValueError if it is malformed.
    Returns True iff the file's bytes changed.
    """
    path = _resolve_settings_path(settings_path)
    if not path.exists():
        raise FileNotFoundError(f"settings.json not found at {path}")

    original = path.read_text()
    data = json.loads(original)
    env = data.setdefault("env", {})
    if not isinstance(env, dict):
        raise ValueError(f"settings.json env block is {type(env).__name__}, expected dict")

    current_attrs = env.get(_OTEL_ATTRS_KEY, "")
    if not isinstance(current_attrs, str):
        raise ValueError(
            f"settings.json env.{_OTEL_ATTRS_KEY} is {type(current_attrs).__name__}, expected str"
        )

    new_attrs = _rewrite_resource_attrs(current_attrs, iteration, workstream_id)
    env[_OTEL_ATTRS_KEY] = new_attrs

    serialized = json.dumps(data, indent=2) + "\n"
    if serialized == original:
        return False
    path.write_text(serialized)
    return True
