"""BE2-03 A1.5 isolated CMD-32/CMD-33 fixture API (A1-C03) and live-route absence."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.contracts.schemas.ai_jobs import CollaborationErrorV1
from sketch2life.contracts.schemas.assistance_requests import AssistanceReceiptEnvelopeV1
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_P,
    CHILD_A,
    CONTEXT_REVISION,
    DEVICE_A,
    LEVEL,
    OUTSIDER,
    TEACHER,
    AssistanceHarness,
    build_assistance_harness,
)
from sketch2life.interfaces.http.ai_jobs_fixture_app import route_surface
from sketch2life.interfaces.http.assistance_requests_fixture_app import (
    create_assistance_requests_fixture_app,
)
from sketch2life.interfaces.http.routers.assistance_requests import MAX_BODY_BYTES

PREFIX = "/api/collaboration/v1"
FIXTURE_PRINCIPALS = {"teacher": TEACHER, "device-a": DEVICE_A, "outsider": OUTSIDER}


@pytest.fixture
def h() -> AssistanceHarness:
    return build_assistance_harness()


@pytest.fixture
def client(h: AssistanceHarness) -> TestClient:
    return TestClient(create_assistance_requests_fixture_app(h.service, FIXTURE_PRINCIPALS))


def body(h: AssistanceHarness, **changes: Any) -> dict[str, Any]:
    checkpoint = h.source_p.snapshot.checkpoint
    payload: dict[str, Any] = {
        "canvas_id": CANVAS_P,
        "checkpoint_ref": {"checkpoint_id": checkpoint.checkpoint_id,
                           "document_epoch": checkpoint.document_epoch,
                           "server_sequence": h.source_p.server_sequence,
                           "hash": checkpoint.checksum_sha256},
        "target_scope": {"kind": "individual", "participant_id": CHILD_A},
        "requested_level": LEVEL,
        "request_reason": "child_request",
        "context_revision": CONTEXT_REVISION,
        "client_request_id": "client_fx_api",
    }
    payload.update(changes)
    return payload


def post(client: TestClient, who: str | None, payload: Any, *, key: str | None = "k1",
         path: str = "/assistance-requests", if_match: str | None = None) -> Any:
    headers = {}
    if who is not None:
        headers["Authorization"] = f"Fixture {who}"
    if key is not None:
        headers["Idempotency-Key"] = key
    if if_match is not None:
        headers["If-Match"] = if_match
    return client.post(PREFIX + path, json=payload, headers=headers)


def error_code(response: Any) -> str:
    return CollaborationErrorV1.model_validate_json(response.text).error.code


def test_submit_returns_202_device_view_and_replays(client: TestClient,
                                                    h: AssistanceHarness) -> None:
    first = post(client, "device-a", body(h))
    assert first.status_code == 202
    envelope = AssistanceReceiptEnvelopeV1.model_validate_json(first.text)
    assert envelope.meta.projection == "device" and envelope.meta.outcome == "created"
    assert set(first.json()["data"]) == {"contract_name", "contract_version", "assistance_id",
                                         "request_revision", "status", "job_id",
                                         "poll_after_ms"}
    assert first.headers["etag"] == f'"assistance:{envelope.data.assistance_id}:1"'
    assert first.headers["cache-control"] == "no-store"
    replay = post(client, "device-a", body(h))
    assert replay.status_code == 202 and replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["data"] == first.json()["data"]
    mismatch = post(client, "device-a", body(h, requested_level="level_fx_2"))
    assert mismatch.status_code == 409
    assert error_code(mismatch) == "IDEMPOTENCY_PAYLOAD_MISMATCH"


def test_teacher_cancel_returns_teacher_record(client: TestClient, h: AssistanceHarness) -> None:
    created = post(client, "device-a", body(h)).json()["data"]
    assistance_id = created["assistance_id"]
    missing = post(client, "teacher", {}, key="c1", path=f"/assistance-requests/{assistance_id}"
                   "/cancel")
    assert missing.status_code == 428 and error_code(missing) == "PRECONDITION_REQUIRED"
    etag = f'"assistance:{assistance_id}:1"'
    cancelled = post(client, "teacher", {"reason": "not needed"}, key="c2",
                     path=f"/assistance-requests/{assistance_id}/cancel", if_match=etag)
    assert cancelled.status_code == 200
    envelope = AssistanceReceiptEnvelopeV1.model_validate_json(cancelled.text)
    assert envelope.meta.projection == "teacher" and envelope.meta.outcome == "cancelled"
    assert cancelled.json()["data"]["status"] == "cancelled"
    assert cancelled.json()["data"]["status_reason"] == "CANCELLED_BY_TEACHER"
    stale = post(client, "teacher", {}, key="c3",
                 path=f"/assistance-requests/{assistance_id}/cancel", if_match=etag)
    assert stale.status_code == 412 and error_code(stale) == "STALE_AGGREGATE"


@pytest.mark.parametrize(("who", "key", "payload", "status", "code"), [
    (None, "k1", None, 401, "UNAUTHENTICATED"),
    ("device-a", None, None, 400, "MALFORMED_REQUEST"),
    ("device-a", "k1", {"role": "teacher"}, 422, "FIELD_NOT_ALLOWED"),
    ("device-a", "k1", {"request_reason": "inactivity"}, 422, "FIELD_VALIDATION_FAILED"),
    ("outsider", "k1", {"request_reason": "teacher_request"}, 404, "RESOURCE_NOT_FOUND"),
])
def test_submit_errors(client: TestClient, h: AssistanceHarness, who: str | None,
                       key: str | None, payload: dict[str, Any] | None, status: int,
                       code: str) -> None:
    response = post(client, who, body(h, **(payload or {})), key=key)
    assert response.status_code == status
    assert error_code(response) == code


def test_rate_limit_sets_retry_after(client: TestClient, h: AssistanceHarness) -> None:
    post(client, "device-a", body(h))
    limited = post(client, "device-a", body(h, requested_level="level_fx_2"), key="k2")
    assert limited.status_code == 429 and error_code(limited) == "RATE_LIMITED"
    assert limited.headers["retry-after"] == "5"


def test_transport_limits(client: TestClient) -> None:
    raw = client.post(PREFIX + "/assistance-requests", content=b"x",
                      headers={"Authorization": "Fixture device-a", "Idempotency-Key": "k",
                               "Content-Type": "text/plain"})
    assert raw.status_code == 415
    big = client.post(PREFIX + "/assistance-requests", content=b"{" + b" " * MAX_BODY_BYTES,
                      headers={"Authorization": "Fixture device-a", "Idempotency-Key": "k",
                               "Content-Type": "application/json"})
    assert big.status_code == 413


def test_fixture_app_surface_is_cmd32_cmd33_only(client: TestClient) -> None:
    surface = route_surface(client.app.routes)  # type: ignore[attr-defined]
    assert surface == {(PREFIX + "/assistance-requests", "POST"),
                       (PREFIX + "/assistance-requests/{assistance_id}/cancel", "POST")}


def test_live_app_has_no_assistance_route() -> None:
    pytest.importorskip("PIL", reason="live app import needs Pillow (not in this env)")
    from sketch2life.interfaces.http.app import create_app

    live = route_surface(create_app().routes)
    assert live, "route walk found no live routes"
    assert not any("assistance-requests" in path for path, _ in live)


def test_cr05_api_normalizes_child_intent_and_replays_equivalent_text(
    client: TestClient, h: AssistanceHarness
) -> None:
    import unicodedata

    decomposed = unicodedata.normalize("NFD", " con mèo ")
    first = post(client, "device-a", body(h, child_intent=decomposed), key="k-nfc")
    assert first.status_code == 202
    assert h.request(first.json()["data"]["assistance_id"]).child_intent == "con mèo"
    equivalent = post(client, "device-a", body(h, child_intent="con mèo"), key="k-nfc")
    assert equivalent.status_code == 202
    assert equivalent.headers["idempotency-replayed"] == "true"
    changed = post(client, "device-a", body(h, child_intent="con chó"), key="k-nfc")
    assert changed.status_code == 409
    assert error_code(changed) == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    blank = post(client, "device-a", body(h, child_intent="   "), key="k-blank")
    assert blank.status_code == 422 and error_code(blank) == "FIELD_VALIDATION_FAILED"
