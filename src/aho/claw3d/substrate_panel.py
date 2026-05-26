"""aho.claw3d.substrate_panel — substrate-freshness panel for the claw3d
dashboard. W1 D5 of 0.3.1.

Reads `aho.observability.snapshot_all_facts()`, renders a 13-fact brick grid
with color cascade (green / yellow / red) and a summary tile (count of
stale facts).

Two surfaces:
- get_substrate_state() — JSON dict for /api/substrate consumers (Flutter
  app or future tooling)
- render_substrate_html() — self-contained HTML page for /substrate route
"""
from __future__ import annotations

import html
import json
from typing import Any, Dict, List

from aho.observability import (
    FACT_WARNING_AGE_SECONDS,
    snapshot_all_facts,
    stale_count,
)


def _format_age(seconds):
    if seconds is None:
        return "—"
    s = float(seconds)
    if s < 60:
        return f"{int(s)}s"
    if s < 3600:
        return f"{int(s/60)}m"
    if s < 86400:
        return f"{int(s/3600)}h"
    return f"{int(s/86400)}d"


def _format_warn(seconds: int) -> str:
    s = seconds
    if s < 3600:
        return f"{int(s/60)}m"
    if s < 86400:
        return f"{int(s/3600)}h"
    return f"{int(s/86400)}d"


def get_substrate_state(host: str = None, project: str = None) -> Dict[str, Any]:
    """Return JSON-serializable substrate state for /api/substrate."""
    snapshot = snapshot_all_facts(host=host, project=project)
    rows: List[Dict[str, Any]] = []
    for s in snapshot:
        rows.append({
            "fact_id": s["fact_id"],
            "last_age_seconds": s["last_age_seconds"],
            "warning_age_seconds": s["warning_age_seconds"],
            "color": s["color"],
            "last_age_human": _format_age(s["last_age_seconds"]),
            "warning_age_human": _format_warn(s["warning_age_seconds"]),
        })
    return {
        "facts": rows,
        "summary": {
            "total": len(rows),
            "stale_count": stale_count(snapshot),
            "green_count": sum(1 for r in rows if r["color"] == "green"),
            "yellow_count": sum(1 for r in rows if r["color"] == "yellow"),
            "red_count": sum(1 for r in rows if r["color"] == "red"),
        },
    }


_COLOR_BG = {
    "green":  "#1e7d3a",
    "yellow": "#b88914",
    "red":    "#b8332a",
}


def render_substrate_html() -> str:
    """Self-contained HTML page for the /substrate route. No JS — server-side
    render with a meta-refresh for live updates.
    """
    state = get_substrate_state()
    summary = state["summary"]
    bricks_html_parts: List[str] = []
    for row in state["facts"]:
        color = row["color"]
        bg = _COLOR_BG.get(color, "#444")
        bricks_html_parts.append(
            "<div class=\"brick\" style=\"background-color:" + bg + ";\">"
            + "<div class=\"fact\">" + html.escape(row["fact_id"]) + "</div>"
            + "<div class=\"age\">" + html.escape(row["last_age_human"]) + "</div>"
            + "<div class=\"warn\">warn ≥ " + html.escape(row["warning_age_human"]) + "</div>"
            + "</div>"
        )
    bricks_html = "".join(bricks_html_parts)
    stale = summary["stale_count"]
    stale_color = "#1e7d3a" if stale == 0 else "#b8332a"
    return (
        "<!DOCTYPE html><html><head><title>aho substrate freshness</title>"
        + "<meta http-equiv=\"refresh\" content=\"10\">"
        + "<style>"
        + "body{background:#111;color:#eee;font-family:monospace;margin:24px;}"
        + "h1{font-size:18px;margin-bottom:8px;}"
        + ".summary{padding:8px 12px;background:" + stale_color + ";color:#fff;display:inline-block;border-radius:4px;margin-bottom:16px;}"
        + ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;}"
        + ".brick{padding:10px;border-radius:4px;color:#fff;}"
        + ".fact{font-size:11px;opacity:.9;}"
        + ".age{font-size:22px;font-weight:600;margin-top:4px;}"
        + ".warn{font-size:10px;opacity:.7;margin-top:4px;}"
        + ".footer{margin-top:16px;font-size:11px;color:#888;}"
        + "</style></head><body>"
        + "<h1>aho substrate freshness — 13 facts</h1>"
        + "<div class=\"summary\">stale: " + str(stale) + " / " + str(summary["total"])
        + "  ·  green " + str(summary["green_count"])
        + "  ·  yellow " + str(summary["yellow_count"])
        + "  ·  red " + str(summary["red_count"])
        + "</div>"
        + "<div class=\"grid\">" + bricks_html + "</div>"
        + "<div class=\"footer\">auto-refresh every 10s; data from "
        + "~/.local/share/aho/observables.jsonl via aho.observability.snapshot_all_facts()."
        + "  W1 D5 of 0.3.1.</div>"
        + "</body></html>"
    )
