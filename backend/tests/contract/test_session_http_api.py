from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.services.ephemeral_sessions import (
    DEMO_ACTOR_REF,
    EphemeralSessionService,
    SessionWorkflowError,
)
from sketch2life.contracts.schemas.workflow_records import SessionSnapshotV1
from sketch2life.infrastructure.storage.in_memory import (
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemorySessionRepository,
)
from sketch2life.interfaces.http.app import create_app


class MutableClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.value


def _service(clock: MutableClock | None = None) -> EphemeralSessionService:
    return EphemeralSessionService(
        sessions=InMemorySessionRepository[SessionSnapshotV1](),
        idempotency=InMemoryIdempotencyStore(),
        artifacts=InMemoryArtifactStore(),
        idle_ttl_seconds=60,
        now=clock or MutableClock(),
    )


def _create_payload(session_id: str | None = None) -> dict[str, object]:
    return {
        "contract_name": "MobileWorkflowCommandV1",
        "contract_version": "1.0",
        "request_id": "request-create-1",
        "idempotency_key": "idem-create-1",
        "session_id": session_id or str(uuid4()),
        "expected_session_version": 0,
        "actor_ref": DEMO_ACTOR_REF,
        "payload": {"operation": "CREATE_SESSION"},
    }


def test_session_create_is_ephemeral_client_idempotent_and_replayable() -> None:
    client = TestClient(create_app(session_service=_service()))
    command = _create_payload()

    created = client.post("/v1/sessions", json=command)
    replayed = client.post("/v1/sessions", json=command)

    assert created.status_code == 201
    assert created.json()["status"] == "SUCCEEDED"
    snapshot = created.json()["payload"]
    assert snapshot["session_id"] == command["session_id"]
    assert snapshot["state"] == "CREATED"
    assert snapshot["version"] == 0
    assert snapshot["durable"] is False
    assert replayed.status_code == 200
    assert replayed.headers["idempotency-replayed"] == "true"
    assert replayed.json() == created.json()


def test_session_create_rejects_conflicting_retry_key_and_duplicate_id() -> None:
    client = TestClient(create_app(session_service=_service()))
    command = _create_payload()
    assert client.post("/v1/sessions", json=command).status_code == 201

    conflicting_retry = {**command, "request_id": "request-create-different"}
    conflict = client.post("/v1/sessions", json=conflicting_retry)
    assert conflict.status_code == 409
    assert conflict.json()["failure"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"

    duplicate_id = {
        **command,
        "request_id": "request-create-2",
        "idempotency_key": "idem-create-2",
    }
    duplicate = client.post("/v1/sessions", json=duplicate_id)
    assert duplicate.status_code == 409
    assert duplicate.json()["failure"]["code"] == "SESSION_ALREADY_EXISTS"


def test_session_create_validates_uuid_actor_version_and_operation() -> None:
    client = TestClient(create_app(session_service=_service()))
    command = _create_payload(session_id="not-a-uuid")
    response = client.post("/v1/sessions", json=command)
    assert response.status_code == 422
    assert response.json()["failure"]["code"] == "INVALID_SESSION_ID"

    command = {**_create_payload(), "actor_ref": "user-supplied-id"}
    response = client.post("/v1/sessions", json=command)
    assert response.status_code == 422
    assert response.json()["failure"]["code"] == "DEMO_ACTOR_INVALID"

    command = {**_create_payload(), "expected_session_version": 1}
    response = client.post("/v1/sessions", json=command)
    assert response.status_code == 409
    assert response.json()["failure"]["code"] == "BOOTSTRAP_VERSION_MUST_BE_ZERO"


def test_session_read_returns_typed_snapshot_and_requires_trace_headers() -> None:
    client = TestClient(create_app(session_service=_service()))
    command = _create_payload()
    client.post("/v1/sessions", json=command)

    response = client.get(
        f"/v1/sessions/{command['session_id']}",
        headers={
            "X-Request-ID": "request-read-1",
            "X-Expected-Session-Version": "0",
            "Idempotency-Key": "idem-read-1",
            "X-Actor-Ref": DEMO_ACTOR_REF,
        },
    )
    assert response.status_code == 200
    assert response.json()["payload"]["session_id"] == command["session_id"]
    assert response.json()["observed_session_version"] == 0

    missing = client.get(f"/v1/sessions/{command['session_id']}")
    assert missing.status_code == 422


def test_expired_session_returns_410_and_removes_ephemeral_state() -> None:
    clock = MutableClock()
    service = _service(clock)
    client = TestClient(create_app(session_service=service))
    command = _create_payload()
    client.post("/v1/sessions", json=command)
    clock.value += timedelta(seconds=61)

    response = client.get(
        f"/v1/sessions/{command['session_id']}",
        headers={
            "X-Request-ID": "request-read-2",
            "X-Expected-Session-Version": "0",
            "Idempotency-Key": "idem-read-2",
            "X-Actor-Ref": DEMO_ACTOR_REF,
        },
    )
    assert response.status_code == 410
    assert response.json()["failure"]["code"] == "SESSION_EXPIRED"
    with pytest.raises(SessionWorkflowError, match="SESSION_NOT_FOUND"):
        service.read(
            session_id=str(command["session_id"]),
            request_id="request-read-3",
            expected_session_version=0,
        )


def test_openapi_exposes_session_contract_but_not_legacy_audio_route() -> None:
    schema = create_app(session_service=_service()).openapi()
    paths = schema["paths"]
    assert "/v1/sessions" in paths
    assert "/v1/sessions/{session_id}" in paths
    assert "/v1/live-understanding" not in paths
