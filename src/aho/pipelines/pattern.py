"""The 10-phase universal pipeline pattern."""
from dataclasses import dataclass
from typing import Literal

PhaseName = Literal[
    "phase1_extract",
    "phase2_transform",
    "phase3_normalize",
    "phase4_enrich",
    "phase5_production_run",
    "phase6_frontend",
    "phase7_production_load",
    "phase8_hardening",
    "phase9_optimization",
    "phase10_retrospective",
]

PHASE_DESCRIPTIONS = {
    "phase1_extract": "Acquire raw data from source",
    "phase2_transform": "Convert raw data to intermediate format (transcribe, OCR, parse)",
    "phase3_normalize": "Apply schema and normalize fields",
    "phase4_enrich": "Add derived data from external sources",
    "phase5_production_run": "Execute the full pipeline at production scale",
    "phase6_frontend": "Build or update consumer-facing interface",
    "phase7_production_load": "Load processed data into production storage",
    "phase8_hardening": "Re-enrichment, gap filling, schema upgrades",
    "phase9_optimization": "Performance, cost, monitoring",
    "phase10_retrospective": "Document lessons, write ADRs, plan next phase",
}


@dataclass
class PipelinePattern:
    name: str
    phases: list
    checkpoint_path: str

    @classmethod
    def standard(cls, name: str) -> "PipelinePattern":
        return cls(
            name=name,
            phases=list(PHASE_DESCRIPTIONS.keys()),
            checkpoint_path=f"pipelines/{name}/checkpoint.json",
        )
