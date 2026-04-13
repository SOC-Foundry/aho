"""Tests for pipeline schemas — RoleAssignment, PipelineTrace, DeltaItem (0.2.14 W1)."""
import pytest
from pydantic import ValidationError


def test_role_assignment_valid():
    from aho.pipeline.schemas import RoleAssignment
    ra = RoleAssignment(
        indexer_in="qwen3.5:9b",
        producer="qwen3.5:9b",
        auditor="qwen3.5:9b",
        indexer_out="qwen3.5:9b",
        assessor="qwen3.5:9b",
    )
    assert ra.producer == "qwen3.5:9b"
    assert ra.all_model_ids() == {"qwen3.5:9b"}


def test_role_assignment_multiple_models():
    from aho.pipeline.schemas import RoleAssignment
    ra = RoleAssignment(
        indexer_in="nemotron-mini:4b",
        producer="qwen3.5:9b",
        auditor="haervwe/GLM-4.6V-Flash-9B",
        indexer_out="nemotron-mini:4b",
        assessor="qwen3.5:9b",
    )
    assert len(ra.all_model_ids()) == 3


def test_role_assignment_missing_field():
    from aho.pipeline.schemas import RoleAssignment
    with pytest.raises(ValidationError):
        RoleAssignment(
            indexer_in="qwen3.5:9b",
            producer="qwen3.5:9b",
            # auditor missing
            indexer_out="qwen3.5:9b",
            assessor="qwen3.5:9b",
        )


def test_delta_item_valid():
    from aho.pipeline.schemas import DeltaItem
    d = DeltaItem(
        proposer_role="indexer_in",
        confidence=0.8,
        evidence_citation="Section 3.2",
        proposed_text="Add G084",
        canonical_target_path="data/gotcha_registry.yaml",
        category="new_gotcha",
    )
    assert d.proposer_role == "indexer_in"
    assert d.confidence == 0.8


def test_delta_item_invalid_proposer():
    from aho.pipeline.schemas import DeltaItem
    with pytest.raises(ValidationError):
        DeltaItem(
            proposer_role="producer",  # invalid — must be indexer_in or indexer_out
            confidence=0.5,
        )


def test_delta_item_confidence_bounds():
    from aho.pipeline.schemas import DeltaItem
    with pytest.raises(ValidationError):
        DeltaItem(proposer_role="indexer_in", confidence=1.5)
    with pytest.raises(ValidationError):
        DeltaItem(proposer_role="indexer_in", confidence=-0.1)


def test_delta_proposal_item_count():
    from aho.pipeline.schemas import DeltaProposal, DeltaItem
    dp = DeltaProposal(
        new_gotchas=[DeltaItem(proposer_role="indexer_in", confidence=0.9)],
        adr_candidates=[
            DeltaItem(proposer_role="indexer_out", confidence=0.7),
            DeltaItem(proposer_role="indexer_out", confidence=0.6),
        ],
    )
    assert dp.item_count() == 3


def test_pipeline_trace_shape():
    from aho.pipeline.schemas import PipelineTrace, RoleAssignment, HandoffEvent
    ra = RoleAssignment(
        indexer_in="m", producer="m", auditor="m", indexer_out="m", assessor="m"
    )
    trace = PipelineTrace(
        pipeline_run_id="abc123",
        document_id="test.txt",
        role_assignment=ra,
    )
    assert trace.pipeline_run_id == "abc123"
    assert len(trace.handoffs) == 0
    trace.handoffs.append(HandoffEvent(
        stage="indexer_in", started_at="t0", completed_at="t1",
        wall_clock_seconds=1.5, output_size_chars=100,
    ))
    assert len(trace.handoffs) == 1


def test_delta_validation_shape():
    from aho.pipeline.schemas import DeltaValidation
    dv = DeltaValidation(
        validated_by_role="auditor",
        proposal_accepted=True,
        reasoning="Looks correct",
        items_accepted=3,
        items_rejected=1,
    )
    assert dv.proposal_accepted is True
