"""BE2-03 A1.2 contracts: A1-C01, A1-C02, A1-N12, A1-N18 (contract level)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from sketch2life.application.services.assistance import device_view, teacher_view
from sketch2life.contracts.schemas.ai_contract_candidates import SHAPE_SPECS
from sketch2life.contracts.schemas.assistance_requests import (
    AssistanceCancelCommandV1,
    AssistanceEventV1,
    AssistanceRequestCommandV1,
    AssistanceRequestDeviceViewV1,
    AssistanceRequestRecordV1,
)
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    build_assistance_harness,
)


def command(**changes: object) -> dict[str, object]:
    body: dict[str, object] = {
        "canvas_id": "canvas_fx_001",
        "checkpoint_ref": {"checkpoint_id": "checkpoint_fx", "document_epoch": 1,
                           "server_sequence": 40, "hash": "a" * 64},
        "target_scope": {"kind": "individual", "participant_id": CHILD_A},
        "target_region_id": None,
        "requested_level": "level_fx_1",
        "child_intent": "a cat with stripes",
        "request_reason": "child_request",
        "context_revision": 3,
        "client_request_id": "client_fx_001",
    }
    body.update(changes)
    return body


def test_command_round_trip_and_group_union() -> None:
    parsed = AssistanceRequestCommandV1.model_validate_json(json.dumps(command()))
    assert parsed.target_scope.kind == "individual"
    group = AssistanceRequestCommandV1.model_validate_json(json.dumps(command(
        target_scope={"kind": "group", "group_id": "group_fx_1"}, child_intent=None,
        request_reason="teacher_request")))
    assert group.target_scope.kind == "group"


@pytest.mark.parametrize("extra", [
    {"role": "teacher"}, {"organization_id": "org"}, {"status": "scheduled"},
    {"audience": ["p"]}, {"age_months": 60},
])
def test_command_refuses_unknown_authority_fields(extra: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AssistanceRequestCommandV1.model_validate_json(json.dumps(command(**extra)))


@pytest.mark.parametrize("reason", ["inactivity", "idle", "auto", None])
def test_no_idle_or_inferred_request_reason_exists(reason: object) -> None:
    """A1-N12: the closed DATA-21 enum has no inactivity value."""

    with pytest.raises(ValidationError):
        AssistanceRequestCommandV1.model_validate_json(json.dumps(command(
            request_reason=reason)))


def test_child_intent_and_ids_are_bounded() -> None:
    """A1-N18 contract level (service-level control-char check is in the service tests)."""

    with pytest.raises(ValidationError):
        AssistanceRequestCommandV1.model_validate_json(json.dumps(command(
            child_intent="x" * 4001)))
    with pytest.raises(ValidationError):
        AssistanceRequestCommandV1.model_validate_json(json.dumps(command(
            canvas_id="bad id\n")))
    with pytest.raises(ValidationError):
        AssistanceCancelCommandV1.model_validate_json('{"reason": "x", "role": "teacher"}')


def test_command_examples_still_satisfy_the_unchanged_data21_shape_spec() -> None:
    """A1-C02: the foundation's shallow DATA-21 ShapeSpec accepts the strict command."""

    spec = SHAPE_SPECS["DATA-21"]
    assert spec.contract_version == "0.1-candidate" and spec.owner_card == "BE2-03"
    for body in (command(), command(request_reason="teacher_request", child_intent=None)):
        assert all(name in body for name in spec.required)
        for name, allowed in spec.enums.items():
            assert body[name] in allowed


def test_projections_validate_and_device_view_is_minimal() -> None:
    """A1-C01: Teacher record and device view validate strictly; device view leaks nothing."""

    h = build_assistance_harness()
    result = h.submit(h.command(intent="a cat"))
    request = h.request(result.request.assistance_id)
    record = AssistanceRequestRecordV1.model_validate_json(json.dumps(teacher_view(request)))
    assert record.validated_target_scope.kind == "individual"
    assert [ref.participant_id for ref in record.audience_age_context_refs] == [CHILD_A]
    view = AssistanceRequestDeviceViewV1.model_validate_json(json.dumps(
        device_view(request, 2000)))
    dumped = view.model_dump(mode="json")
    assert set(dumped) == {"contract_name", "contract_version", "assistance_id",
                           "request_revision", "status", "job_id", "poll_after_ms"}
    text = json.dumps(dumped)
    for secret in ("age", "consent", "audience", "cat", "budget", "digest", "analysis"):
        assert secret not in text.replace("contract_name", "")


def test_event_contract_validates_recorded_events() -> None:
    h = build_assistance_harness()
    h.submit()
    for event in h.store.snapshot().events:
        AssistanceEventV1.model_validate_json(json.dumps({
            "event_id": event.event_id, "event_type": event.event_type,
            "organization_id": event.organization_id, "assistance_id": event.assistance_id,
            "request_revision": event.request_revision, "reason": event.reason,
            "occurred_at": event.occurred_at.isoformat(),
        }))


def test_handoff_examples_are_pinned_and_valid() -> None:
    """A1.5: the published H-AI-REVIEW / H-OPERATIONS examples match the harness exactly."""

    from pathlib import Path

    from sketch2life.infrastructure.assistance.harness import build_handoff_examples

    path = (Path(__file__).resolve().parents[3] / "features"
            / "FEAT-049-be2-assistance-orchestration" / "fixtures" / "h_ai_review"
            / "assistance_handoff_examples.json")
    examples = build_handoff_examples()
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(json.dumps(examples))
    for name in ("teacher_record_analysis_ready", "teacher_record_cache_hit",
                 "teacher_record_cancelled_group"):
        AssistanceRequestRecordV1.model_validate_json(json.dumps(examples[name]))
    AssistanceRequestDeviceViewV1.model_validate_json(
        json.dumps(examples["device_view_analysis_ready"]))
    for event in examples["events"]:  # type: ignore[attr-defined]
        AssistanceEventV1.model_validate_json(json.dumps(event))
    assert examples["sketch_intent"]["status"] == "SIMULATED_NO_PRODUCER"  # type: ignore[index]
