from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import TypeAdapter, ValidationError

from sketch2life.application.services.contract_version_adapter import (
    from_learning_media_version,
    from_renderer_version,
    to_learning_media_version,
    to_renderer_version,
)
from sketch2life.application.services.mobile_command_adapter import adapt_mobile_command
from sketch2life.contracts.schemas.gate_a import GateAConfirmationV1
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
    WorkflowFailureV1,
    WorkflowResultProvenanceV1,
)
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.workflow_records import (
    FeedbackV1,
    SessionGalleryV1,
    SessionSnapshotV1,
    WorkflowJobV1,
)


def test_mobile_command_requires_frozen_concurrency_and_actor_fields() -> None:
    command = MobileWorkflowCommandV1(
        request_id="request-1",
        idempotency_key="idem-1",
        session_id="session-1",
        expected_session_version=0,
        actor_ref="demo:local",
        payload={"operation": "CREATE_SESSION"},
    )

    assert command.request_id == "request-1"
    assert command.created_at.tzinfo is not None
    schema = TypeAdapter(MobileWorkflowCommandV1).json_schema()
    required = {
        "request_id",
        "idempotency_key",
        "session_id",
        "expected_session_version",
        "actor_ref",
    }
    assert required.issubset(schema["required"])


def test_mobile_request_id_maps_once_and_idempotency_remains_transport_only() -> None:
    command = MobileWorkflowCommandV1(
        request_id="command-once",
        idempotency_key="retry-key",
        session_id="session-1",
        expected_session_version=0,
        actor_ref="demo:local",
        payload={"operation": "CREATE_SESSION"},
    )

    adapted = adapt_mobile_command(command)
    assert adapted.runtime_envelope.command_id == command.request_id
    assert adapted.idempotency_key == command.idempotency_key
    assert not hasattr(adapted.runtime_envelope, "idempotency_key")


def test_mobile_command_rejects_naive_timestamp_and_unknown_fields() -> None:
    base = {
        "request_id": "request-1",
        "idempotency_key": "idem-1",
        "session_id": "session-1",
        "expected_session_version": 0,
        "actor_ref": "demo:local",
        "payload": {},
    }
    with pytest.raises(ValidationError, match="timezone-aware"):
        MobileWorkflowCommandV1(**base, created_at=datetime(2026, 9, 18))
    with pytest.raises(ValidationError):
        MobileWorkflowCommandV1(**base, unregistered_field=True)


def test_mobile_result_requires_typed_failure_only_for_failed_status() -> None:
    provenance = WorkflowResultProvenanceV1(
        producer="APPLICATION", component="session-runtime", component_version="1.0"
    )
    failed = MobileWorkflowResultV1(
        status="FAILED",
        request_id="request-1",
        session_id="session-1",
        expected_session_version=0,
        observed_session_version=0,
        provenance=provenance,
        failure=WorkflowFailureV1(
            domain="SESSION",
            code="STALE_SESSION_VERSION",
            retryable=True,
            safe_message="Refresh the session before continuing.",
        ),
    )
    assert failed.failure is not None
    with pytest.raises(ValidationError, match="typed failure"):
        MobileWorkflowResultV1(
            status="FAILED",
            request_id="request-1",
            session_id="session-1",
            expected_session_version=0,
            observed_session_version=0,
            provenance=provenance,
            payload={"status": "FAILED"},
        )
    with pytest.raises(ValidationError, match="payload"):
        MobileWorkflowResultV1(
            status="SUCCEEDED",
            request_id="request-1",
            session_id="session-1",
            expected_session_version=0,
            observed_session_version=1,
            provenance=provenance,
            failure=failed.failure,
        )


def test_gate_a_confirmation_is_versioned_and_preserves_actor_and_meaning() -> None:
    decision = GateAConfirmationV1(
        session_id="session-1",
        expected_session_version=3,
        actor_ref="demo:local",
        meaning_version=2,
        confirmed_claim_ids=("claim-1",),
    )
    assert decision.contract_name == "GateAConfirmationV1"
    assert decision.confirmed_claim_ids == ("claim-1",)
    with pytest.raises(ValidationError):
        GateAConfirmationV1(
            session_id="session-1",
            expected_session_version=3,
            actor_ref="demo:local",
            meaning_version=2,
            confirmed_claim_ids=(),
        )


def test_contract_version_adapter_round_trips_and_rejects_ambiguous_values() -> None:
    assert to_learning_media_version(12) == "v12"
    assert from_learning_media_version("v12") == 12
    assert to_renderer_version(12) == "12"
    assert from_renderer_version("12") == 12
    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            to_learning_media_version(invalid)  # type: ignore[arg-type]
    for invalid in ("0", "v0", "v01", "V1", "1", "v1.0"):
        with pytest.raises(ValueError):
            from_learning_media_version(invalid)
    for invalid in ("0", "01", "1.0", "v1", "１２"):
        with pytest.raises(ValueError):
            from_renderer_version(invalid)


def test_session_gallery_is_ephemeral_and_excludes_media_payloads() -> None:
    schema = SessionGalleryV1.model_json_schema()
    gallery = SessionGalleryV1(
        session_id="session-1",
        session_version=4,
        status="ACTIVE",
        entries=(),
    )
    assert gallery.media_bytes_included is False
    assert gallery.durable is False
    assert schema["additionalProperties"] is False
    assert "owner_ref" not in schema["properties"]
    with pytest.raises(ValueError):
        SessionGalleryV1.model_validate({**gallery.model_dump(), "owner_ref": "user-1"})


def test_workflow_job_terminal_contracts_are_typed_and_ordered() -> None:
    now = datetime.now(UTC)
    queued = WorkflowJobV1(
        job_id="job-1",
        session_id="session-1",
        request_id="request-1",
        status="QUEUED",
        created_at=now,
        updated_at=now,
    )
    assert queued.status == "QUEUED"
    with pytest.raises(ValueError, match="typed failure"):
        WorkflowJobV1(
            job_id="job-1",
            session_id="session-1",
            request_id="request-1",
            status="FAILED",
            created_at=now,
            updated_at=now,
        )
    with pytest.raises(ValueError, match="result reference"):
        WorkflowJobV1(
            job_id="job-1",
            session_id="session-1",
            request_id="request-1",
            status="SUCCEEDED",
            created_at=now,
            updated_at=now,
        )


def test_session_snapshot_freezes_process_expiry_without_claiming_durability() -> None:
    now = datetime.now(UTC)
    snapshot = SessionSnapshotV1(
        session_id="session-1",
        version=0,
        state="CREATED",
        status="ACTIVE",
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(days=30),
    )
    assert snapshot.durable is False
    assert "owner_ref" not in SessionSnapshotV1.model_json_schema()["properties"]
    with pytest.raises(ValidationError, match="expiry"):
        SessionSnapshotV1(
            session_id="session-2",
            version=0,
            state="CREATED",
            status="ACTIVE",
            created_at=now,
            updated_at=now,
            expires_at=now,
        )


def test_feedback_is_non_identifying_and_locks_exact_approved_identity() -> None:
    ref = lambda value: VersionedRefV1(id=value, version=1)  # noqa: E731
    feedback = FeedbackV1(
        session_id="session-1",
        expected_session_version=5,
        actor_ref="demo:local",
        activity_ref=ref("activity-1"),
        objective_ref=ref("objective-1"),
        template_ref=ref("template-1"),
        spec_ref=ref("spec-1"),
        completion_status="PARTIAL",
        observation_tags=("ASKED_FOR_HELP",),
        recorded_at=datetime.now(UTC),
    )
    assert feedback.spec_ref.id == "spec-1"
    with pytest.raises(ValidationError):
        FeedbackV1.model_validate(
            {**feedback.model_dump(), "parent_notes": "free text with personal data"}
        )
