"""Orchestrator configuration - reads ~/.config/aho/orchestrator.json.

0.2.7 W5. Engine field is reserved metadata only (no behavior change).

0.3.1 council-wiring: tier-aware council inference helpers. Base-tier hosts
(no discrete GPU) run produce/assess at a reduced context window so a
warm dispatch completes in bounded time on CPU; partial/full-tier hosts
keep the natural windows so 9B producers/evaluators run at full quality.
The carry-forward end-state is that heavy produce/assess routes to
partial-tier hosts (see CLAUDE.md "Council producer/evaluator seats are
partial-tier work" carry-forward, ADR-0007 W6 amendment target).
"""
import json
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path.home() / ".config" / "aho" / "orchestrator.json"
TIER_PATH = Path.home() / ".config" / "aho" / "tier.json"

_DEFAULTS = {
    "engine": "gemini",
    "search": {
        "provider": "brave",
        "token_secret_key": "brave_search_token",
    },
    "openclaw": {
        "default_model": "qwen3.5:9b",
    },
    "nemoclaw": {
        "classifier_model": "nemotron-mini:4b",
    },
}


def load_config() -> dict:
    """Load orchestrator config, falling back to defaults if missing."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            # Merge with defaults for missing keys
            merged = _DEFAULTS.copy()
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError):
            return _DEFAULTS.copy()
    return _DEFAULTS.copy()


def save_config(config: dict):
    """Write orchestrator config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    CONFIG_PATH.chmod(0o600)


def ensure_config():
    """Create default config if it doesn't exist."""
    if not CONFIG_PATH.exists():
        save_config(_DEFAULTS.copy())


def get_openclaw_model() -> str:
    """Get the default OpenClaw model from config."""
    config = load_config()
    return config.get("openclaw", {}).get("default_model", "qwen3.5:9b")


def get_nemoclaw_model() -> str:
    """Get the NemoClaw classifier model from config."""
    config = load_config()
    return config.get("nemoclaw", {}).get("classifier_model", "nemotron-mini:4b")


def get_search_token_key() -> str:
    """Get the fernet store key name for the search token."""
    config = load_config()
    return config.get("search", {}).get("token_secret_key", "brave_search_token")


# ---------------------------------------------------------------------------
# Tier-aware helpers (0.3.1 council-wiring)
# ---------------------------------------------------------------------------

def get_host_tier() -> str:
    """Read VRAM-tier from ~/.config/aho/tier.json (ADR-0007).

    Returns 'base', 'partial', or 'full'. Falls back to 'base' if the file
    is missing or malformed - the conservative default for context-window
    sizing on an unidentified host.
    """
    if not TIER_PATH.exists():
        return "base"
    try:
        return json.loads(TIER_PATH.read_text()).get("tier", "base")
    except (json.JSONDecodeError, OSError):
        return "base"


def get_tier_num_ctx(default: int = 16384, base_ctx: int = 4096) -> int:
    """Tier-appropriate context window for council inference (qwen workstream).

    Base-tier hosts (CPU/iGPU, no discrete GPU) get `base_ctx` so a warm
    dispatch completes in bounded time; partial/full-tier hosts keep
    `default` so producer/evaluator quality stays at the natural setting.
    Per-stage CPU latency measured on base tier (a8cos, vram_gb=0):
    route 3.5s, produce(qwen3.5:9b) 110s, assess(GLM-9B) 64.8s warm at
    4096ctx - smoke blew 900s at 16384ctx + GLM 65K + cold load.
    """
    return base_ctx if get_host_tier() == "base" else default


def get_tier_glm_ctx_override(base_ctx: int = 4096) -> Optional[int]:
    """Tier-appropriate num_ctx override for the GLM evaluator.

    Returns `base_ctx` on base tier (so GLM does not pull its 65K modelfile
    default into CPU memory) and None on partial/full tier (preserves the
    historical "no num_ctx override - use the modelfile default" behavior).
    """
    return base_ctx if get_host_tier() == "base" else None
