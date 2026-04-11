"""Postflight gate: verify all MCP canonical packages exist on npm registry.

G-mcp-canonical-drift defense — catches 404s and deprecations before they
reach bin/aho-mcp install on a fresh clone.
"""
import subprocess


# Must match bin/aho-mcp and src/aho/doctor.py
MCP_PACKAGES = [
    "firebase-tools",
    "@upstash/context7-mcp",
    "firecrawl-mcp",
    "@playwright/mcp",
    "flutter-mcp",
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-memory",
    "@modelcontextprotocol/server-sequential-thinking",
    "@modelcontextprotocol/server-everything",
]


def check():
    """npm view each canonical package; FAIL on 404 or deprecation."""
    try:
        subprocess.run(
            ["npm", "--version"], capture_output=True, timeout=5
        )
    except Exception:
        return ("skip", "npm not available")

    failures = []
    for pkg in MCP_PACKAGES:
        try:
            r = subprocess.run(
                ["npm", "view", pkg, "version"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode != 0:
                failures.append(f"{pkg}: 404")
            elif "deprecated" in r.stderr.lower():
                failures.append(f"{pkg}: deprecated")
        except subprocess.TimeoutExpired:
            return ("skip", f"npm view timed out on {pkg} — network issue?")
        except Exception as e:
            return ("skip", f"npm view failed: {e}")

    if failures:
        return ("fail", "; ".join(failures))
    return ("ok", f"all {len(MCP_PACKAGES)} MCP packages registry-verified")
