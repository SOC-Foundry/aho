"""aho artifact loop subpackage (W6).

Produces the five canonical aho artifacts (design, plan, build-log, report,
bundle) for an iteration via a Qwen-managed Ollama loop.

This subpackage is the scaffolding for the architecture introduced in aho
0.1.2: from aho 0.1.3 onward, all canonical iteration artifacts are produced
by Qwen via this loop, not by Claude or Gemini directly.
"""
from aho.artifacts.loop import run_artifact_loop, ARTIFACT_KINDS

__all__ = ["run_artifact_loop", "ARTIFACT_KINDS"]
