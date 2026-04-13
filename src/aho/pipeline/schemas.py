"""Pipeline schemas — Role assignment, trace, and delta (0.2.14 W1).

Triple schema for the 5-stage cascade pipeline:
- RoleAssignment: binds each pipeline role to a model_id
- PipelineTrace: full execution trace with per-stage handoff timestamps
- DeltaItem / DeltaProposal: indexer-proposed changes for auditor/assessor validation
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RoleAssignment(BaseModel):
    """Binds each pipeline role to a model_id."""
    indexer_in: str
    producer: str
    auditor: str
    indexer_out: str
    assessor: str

    def all_model_ids(self) -> set[str]:
        return {self.indexer_in, self.producer, self.auditor,
                self.indexer_out, self.assessor}


class HandoffEvent(BaseModel):
    """Single stage completion record."""
    stage: str
    started_at: str
    completed_at: str
    wall_clock_seconds: float
    partial_completion: bool = False
    error: Optional[str] = None
    output_size_chars: int = 0


class PipelineTrace(BaseModel):
    """Full execution trace for one pipeline run."""
    pipeline_run_id: str
    document_id: str
    role_assignment: RoleAssignment
    dispatch_layer: str = "ollama-direct"
    handoffs: list[HandoffEvent] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    total_wall_clock_seconds: float = 0.0
    started_at: str = ""
    completed_at: str = ""


class DeltaItem(BaseModel):
    """Single proposed change from an indexer role."""
    proposer_role: str  # "indexer_in" or "indexer_out"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_citation: str = ""
    proposed_text: str = ""
    canonical_target_path: str = ""
    category: str = ""  # "new_gotcha", "gotcha_update", "adr_candidate", "harness_patch", "pattern_candidate"

    @field_validator("proposer_role")
    @classmethod
    def validate_proposer(cls, v: str) -> str:
        if v not in ("indexer_in", "indexer_out"):
            raise ValueError(f"proposer_role must be indexer_in or indexer_out, got {v}")
        return v


class DeltaProposal(BaseModel):
    """Collection of proposed deltas from one indexer pass."""
    new_gotchas: list[DeltaItem] = Field(default_factory=list)
    gotcha_updates: list[DeltaItem] = Field(default_factory=list)
    adr_candidates: list[DeltaItem] = Field(default_factory=list)
    harness_patches: list[DeltaItem] = Field(default_factory=list)
    pattern_candidates: list[DeltaItem] = Field(default_factory=list)

    def all_items(self) -> list[DeltaItem]:
        return (self.new_gotchas + self.gotcha_updates + self.adr_candidates
                + self.harness_patches + self.pattern_candidates)

    def item_count(self) -> int:
        return len(self.all_items())


class DeltaValidation(BaseModel):
    """Auditor or assessor validation of a delta proposal."""
    validated_by_role: str  # "auditor" or "assessor"
    proposal_accepted: bool
    reasoning: str = ""
    items_accepted: int = 0
    items_rejected: int = 0
