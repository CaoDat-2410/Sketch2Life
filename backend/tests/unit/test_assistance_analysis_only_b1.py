from __future__ import annotations

from sketch2life.infrastructure.assistance.harness import build_assistance_harness
from sketch2life.infrastructure.vision_analysis.analysis_only import (
    A2AnalysisSourceAdmissionPort,
    build_analysis_only_assistance,
)


def test_analysis_only_keeps_handoff_but_blocks_sketch_cache_and_second_event() -> None:
    harness = build_assistance_harness()
    harness.service = build_analysis_only_assistance(harness.service._d)

    submitted = harness.submit()
    result = harness.run_vision(submitted.request.assistance_id)

    state = harness.store.snapshot()
    event_types = [event.event_type for event in state.events]
    assert result.status.value == "analysis_ready"
    assert result.handoff is not None
    assert event_types.count("assistance.analysis_ready") == 1
    assert "assistance.sketch_intent_simulated" not in event_types
    assert state.cache == {}
    assert state.intents == []
    assert harness.sketch.intents == []


def test_a2_source_and_receipt_are_bound_to_the_exact_organization_and_snapshot() -> None:
    harness = build_assistance_harness()
    resolved = harness.source_p
    adapter = A2AnalysisSourceAdmissionPort(
        lambda organization_id, snapshot_ref: (
            resolved
            if organization_id == resolved.snapshot.organization_id
            and snapshot_ref == resolved.snapshot.snapshot_ref
            else None
        )
    )

    snapshot = adapter.resolve(
        resolved.snapshot.snapshot_ref,
        organization_id=resolved.snapshot.organization_id,
    )
    assert snapshot == resolved.snapshot
    assert resolved.admission is not None
    assert (
        adapter.receipt_for(
            snapshot.render.render_ref,
            snapshot.render.render_sha256,
            organization_id=snapshot.organization_id,
        )
        == resolved.admission
    )
    assert (
        adapter.receipt_for(
            snapshot.render.render_ref,
            snapshot.render.render_sha256,
            organization_id=snapshot.organization_id,
        )
        is None
    )


def test_a2_source_adapter_refuses_a_foreign_organization() -> None:
    harness = build_assistance_harness()
    resolved = harness.source_p
    adapter = A2AnalysisSourceAdmissionPort(lambda _organization_id, _snapshot_ref: resolved)

    assert (
        adapter.resolve(
            resolved.snapshot.snapshot_ref,
            organization_id="synthetic-foreign-organization",
        )
        is None
    )
