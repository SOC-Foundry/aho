"""aho postflight check modules (10.69 W2 dynamic loader).

Gate result dataclasses added 0.2.11 W4 for per-check verbosity.
"""
from dataclasses import dataclass, field, asdict


@dataclass
class CheckResult:
    """Single sub-check within a gate."""
    name: str
    status: str  # ok|fail|skip|deferred
    message: str
    evidence_path: str | None = None


@dataclass
class GateResult:
    """Top-level gate result with optional per-check detail."""
    status: str  # ok|fail|skip|deferred — rollup of checks
    message: str
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for backward-compat consumption."""
        d = {"status": self.status, "message": self.message}
        if self.checks:
            d["checks"] = [asdict(c) for c in self.checks]
        return d


_STATUS_SEVERITY = {"ok": 0, "skip": 1, "deferred": 2, "fail": 3}


def worst_status(statuses: list[str]) -> str:
    """Return the worst status from a list, by severity order."""
    if not statuses:
        return "ok"
    return max(statuses, key=lambda s: _STATUS_SEVERITY.get(s.lower(), 3))
