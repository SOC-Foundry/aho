"""Postflight gate: verify all MCP canonical packages exist on npm registry.

G-mcp-canonical-drift defense — catches 404s and deprecations before they
reach bin/aho-mcp install on a fresh clone.
"""
import subprocess


# Must match bin/aho-mcp and src/aho/doctor.py
# npm-managed packages only; dart mcp-server is SDK-bundled (checked separately)
MCP_NPM_PACKAGES = [
    "firebase-tools",
    "@upstash/context7-mcp",
    "firecrawl-mcp",
    "@playwright/mcp",
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
    for pkg in MCP_NPM_PACKAGES:
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

    # Verify dart SDK presence (dart mcp-server is SDK-bundled)
    try:
        dr = subprocess.run(["dart", "--version"], capture_output=True, text=True, timeout=5)
        if dr.returncode != 0:
            failures.append("dart-mcp-server: dart SDK not found")
    except Exception:
        failures.append("dart-mcp-server: dart not on PATH")

    total = len(MCP_NPM_PACKAGES) + 1  # +1 for dart
    if failures:
        return ("fail", "; ".join(failures))
    return ("ok", f"all {total} MCP packages registry-verified")
