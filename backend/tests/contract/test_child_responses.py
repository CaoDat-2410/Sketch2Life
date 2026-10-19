"""Strict command boundaries, truthful choice attribution and safe exact read shapes."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.child_responses import (
    AuthorizedChildReadV1,
    ChildResponseCommandV1,
    ChildResponseOutcomeV1,
    ChildResponseProjectionV1,
    ChildResponseReadV1,
    ReviewAccessSnapshotV1,
    TeacherResponseEventV1,
    command_fingerprint,
)
from sketch2life.contracts.schemas.sketch_proposals import ChildResponseV1
from sketch2life.contracts.schemas.sketch_reviews import SketchChildPayloadV0

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
DIGEST = "a" * 64
ETAG = '"child-response:fixture:1"'


def _access() -> ReviewAccessSnapshotV1:
    return ReviewAccessSnapshotV1(
        organization_id="org_fx", class_id="class_fx", session_id="session_fx",
        canvas_id="canvas_fx", proposal_id="proposal_fx", proposal_version=1,
        content_sha256=DIGEST, participant_id="child_a", review_ref="review_fx",
    )


def _command() -> ChildResponseCommandV1:
    return ChildResponseCommandV1(
        action="viewed", expected_proposal_version=1, review_ref="review_fx", turn_id="turn_fx",
    )


def _choice(action: str = "viewed", participant: str = "child_a") -> ChildResponseV1:
    return ChildResponseV1.model_validate({
        "action": action, "participant_id": participant, "turn_id": "turn_fx", "responded_at": NOW,
    })


def _projection(action: str | None = None) -> ChildResponseProjectionV1:
    return ChildResponseProjectionV1.model_validate({
        "access": _access(), "visibility": "available" if action is None else action,
        "response_revision": 1 if action is None else 2, "etag": ETAG,
        "turn_id": "turn_fx", "child_response": None if action is None else _choice(action),
    })


def _payload() -> SketchChildPayloadV0:
    return SketchChildPayloadV0(
        proposal_id="proposal_fx", status="available", display_mode="side_reference",
        text_or_question="Fixture reference question?", review_ref="review_fx",
    )


@pytest.mark.parametrize("field", [
    "participant_id", "organization_id", "content_sha256", "audience", "approve", "if_match",
])
def test_command_rejects_identity_and_envelope_overrides(field: str) -> None:
    body = _command().model_dump()
    body[field] = "forged"
    with pytest.raises(ValidationError):
        ChildResponseCommandV1.model_validate(body)


@pytest.mark.parametrize("action", ["available", "approve", "accept_edit", "VIEWED"])
def test_command_has_only_three_child_actions(action: str) -> None:
    with pytest.raises(ValidationError):
        ChildResponseCommandV1.model_validate({**_command().model_dump(), "action": action})


@pytest.mark.parametrize("version", [True, "1", 1.0, 0])
def test_command_version_is_a_strict_positive_integer(version: object) -> None:
    with pytest.raises(ValidationError):
        ChildResponseCommandV1.model_validate({
            **_command().model_dump(), "expected_proposal_version": version,
        })


def test_semantic_fingerprint_ignores_json_formatting_but_preserves_values() -> None:
    command = _command()
    original = command_fingerprint("proposal_fx", command)
    reordered = dict(reversed(list(command.model_dump().items())))
    decoded = ChildResponseCommandV1.model_validate_json(json.dumps(reordered, indent=3))
    assert original == command_fingerprint("proposal_fx", decoded)
    changed = command.model_copy(update={"turn_id": "TURN_FX"})
    assert original != command_fingerprint("proposal_fx", changed)
    assert original != command_fingerprint("other_proposal", command)


@pytest.mark.parametrize("field", ["text", "audience", "asset", "producer", "job_id", "epoch"])
def test_access_snapshot_cannot_transport_full_target_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        ReviewAccessSnapshotV1.model_validate({**_access().model_dump(), field: "private"})


def test_initial_projection_does_not_invent_available_response_attribution() -> None:
    projection = _projection()
    assert projection.child_response is None and projection.response_revision == 1
    with pytest.raises(ValidationError):
        ChildResponseProjectionV1.model_validate({
            **projection.model_dump(), "child_response": _choice("available"),
        })


def test_real_choice_requires_bound_participant_and_aware_server_time() -> None:
    with pytest.raises(ValidationError):
        ChildResponseProjectionV1.model_validate({
            **_projection("viewed").model_dump(), "child_response": _choice(participant="child_b"),
        })
    with pytest.raises(ValidationError):
        ChildResponseV1.model_validate({
            "action": "viewed", "participant_id": "child_a", "turn_id": "turn_fx",
            "responded_at": NOW.replace(tzinfo=None),
        })


@pytest.mark.parametrize("change", [
    {"proposal_id": "other"}, {"review_ref": "other"}, {"status": "pending"},
])
def test_explicit_read_wrapper_rejects_mixed_result_identity(change: dict[str, str]) -> None:
    payload = SketchChildPayloadV0.model_validate({**_payload().model_dump(), **change})
    with pytest.raises(ValidationError):
        AuthorizedChildReadV1(access=_access(), payload=payload)


def test_hidden_read_can_explicitly_reveal_without_rewriting_historical_choice() -> None:
    read = ChildResponseReadV1(projection=_projection("hidden"), payload=_payload())
    assert read.projection.child_response is not None
    assert read.projection.child_response.action == "hidden"
    assert ChildResponseReadV1(projection=_projection("hidden"), payload=None).payload is None
    with pytest.raises(ValidationError):
        ChildResponseReadV1(projection=_projection("declined"), payload=_payload())


def test_command_outcome_is_content_free_and_preserves_real_attribution() -> None:
    outcome = ChildResponseOutcomeV1(
        applied=True, response_id="response_fx", response_revision=2, etag=ETAG,
        proposal_id="proposal_fx", proposal_version=1, content_sha256=DIGEST,
        review_ref="review_fx", participant_id="child_a", child_response=_choice(),
    )
    assert set(ChildResponseOutcomeV1.model_fields) == {
        "contract_name", "contract_version", "applied", "response_id", "response_revision", "etag",
        "proposal_id", "proposal_version", "content_sha256", "review_ref", "participant_id",
        "child_response",
    }
    with pytest.raises(ValidationError):
        ChildResponseOutcomeV1.model_validate({
            **outcome.model_dump(), "text_or_question": "secret",
        })
    with pytest.raises(ValidationError):
        ChildResponseOutcomeV1.model_validate({
            **outcome.model_dump(), "child_response": _choice("available"),
        })


def test_teacher_event_contains_only_typed_response_scope_and_neutral_action() -> None:
    event = TeacherResponseEventV1(
        event_id="event_fx", response_id="response_fx", operation_key="operation_fx",
        access=_access(), response_revision=2, turn_id="turn_fx", turn_revision=1,
        action="declined", responded_at=NOW,
    )
    for field in ("text", "asset_ref", "media_url", "deficit", "provider"):
        with pytest.raises(ValidationError):
            TeacherResponseEventV1.model_validate({**event.model_dump(), field: "private"})
