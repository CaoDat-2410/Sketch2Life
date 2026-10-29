"""BE2-02 C1 isolated CMD-34 fixture API (V12) plus transport-level V05/V08/V09/V10/V15."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.contracts.schemas.ai_jobs import CollaborationErrorV1
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisCorrectionChildEnvelopeV1,
    AnalysisCorrectionEnvelopeV1,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    CANVAS,
    DEVICE_A,
    DEVICE_B,
    OUTSIDER,
    SESSION,
    TEACHER,
    AnalysisHarness,
    build_analysis_harness,
)
from sketch2life.interfaces.http.ai_jobs_fixture_app import route_surface
from sketch2life.interfaces.http.analysis_corrections_fixture_app import (
    create_analysis_corrections_fixture_app,
)
from sketch2life.interfaces.http.routers.analysis_corrections import MAX_BODY_BYTES

PREFIX = "/api/collaboration/v1"
FIXTURE_PRINCIPALS = {"teacher": TEACHER, "device-a": DEVICE_A, "device-b": DEVICE_B,
                      "outsider": OUTSIDER}


@pytest.fixture
def h() -> AnalysisHarness:
    return build_analysis_harness()


@pytest.fixture
def client(h: AnalysisHarness) -> TestClient:
    return TestClient(create_analysis_corrections_fixture_app(h.service, FIXTURE_PRINCIPALS))


def _body(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"intended_objects": ["tiger"],
                            "correction_reason": "Child says it is a tiger",
                            "expected_context_revision": 3}
    body.update(changes)
    return body


def _post(client: TestClient, analysis_id: str, *, token: str | None = "teacher",
          key: str | None = "key_api_1", if_match: str | None = '"analysis:{id}:1"',
          body: Any = None, raw: bytes | None = None,
          content_type: str = "application/json") -> Any:
    headers = {"Content-Type": content_type}
    if token is not None:
        headers["Authorization"] = f"Fixture {token}"
    if key is not None:
        headers["Idempotency-Key"] = key
    if if_match is not None:
        headers["If-Match"] = if_match.format(id=analysis_id)
    content = raw if raw is not None else json.dumps(_body() if body is None else body).encode()
    return client.post(f"{PREFIX}/analysis-results/{analysis_id}/corrections",
                       content=content, headers=headers)


def _code(response: Any) -> str:
    return str(CollaborationErrorV1.model_validate_json(response.content).error.code)


def test_v12_teacher_confirmation_returns_teacher_projection(
    client: TestClient, h: AnalysisHarness
) -> None:
    analysis_id = h.accepted_analysis()
    response = _post(client, analysis_id)
    assert response.status_code == 200
    assert response.headers["ETag"] == f'"analysis:{analysis_id}:2"'
    assert "Idempotency-Replayed" not in response.headers
    envelope = AnalysisCorrectionEnvelopeV1.model_validate_json(response.content)
    assert envelope.meta.projection == "teacher" and envelope.meta.resource_revision == 2
    data = envelope.data
    assert data.correction.kind == "teacher_confirmation"
    assert data.correction.author.principal_ref == TEACHER.principal_id
    assert data.object_candidates[0].label == "cat"
    assert data.original.accepted_status == "accepted"
    assert data.invalidation.reason == "teacher_meaning_confirmed"


def test_v12_v15_device_proposal_returns_refs_only_child_projection(
    client: TestClient, h: AnalysisHarness
) -> None:
    analysis_id = h.accepted_analysis()
    response = _post(client, analysis_id, token="device-a",
                     body=_body(child_explanation="It has stripes"))
    assert response.status_code == 200
    envelope = AnalysisCorrectionChildEnvelopeV1.model_validate_json(response.content)
    assert envelope.meta.projection == "child_device"
    assert envelope.data.meaning_status == "proposed"
    text = response.text
    for leaked in ('"cat"', "0.62", "confidence", "uncertainty", "provenance", "moderation",
                   "stripes", "tiger", "age", "teacher"):
        assert leaked not in text


def test_v12_v08_v09_replay_and_payload_mismatch(client: TestClient, h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    first = _post(client, analysis_id, key="key_api_replay")
    replay = _post(client, analysis_id, key="key_api_replay")  # old If-Match rev 1
    assert replay.status_code == 200 and replay.headers["Idempotency-Replayed"] == "true"
    assert replay.headers["ETag"] == first.headers["ETag"]
    assert replay.json()["data"] == first.json()["data"]
    assert replay.json()["meta"]["replayed"] is True
    mismatch = _post(client, analysis_id, key="key_api_replay",
                     body=_body(intended_objects=["lion"]))
    assert mismatch.status_code == 409 and _code(mismatch) == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    h.authority.revoke(TEACHER.principal_id)
    revoked = _post(client, analysis_id, key="key_api_replay")
    assert revoked.status_code == 403 and _code(revoked) == "GRANT_REVOKED"
    assert '"tiger"' not in revoked.text and '"cat"' not in revoked.text


@pytest.mark.parametrize(
    ("kwargs", "status", "code"),
    [
        ({"token": None}, 401, "UNAUTHENTICATED"),
        ({"token": "unknown"}, 401, "UNAUTHENTICATED"),
        ({"key": None}, 400, "MALFORMED_REQUEST"),
        ({"key": "bad key!"}, 400, "MALFORMED_REQUEST"),
        ({"if_match": None}, 428, "PRECONDITION_REQUIRED"),
        ({"if_match": '"analysis:{id}:7"'}, 412, "STALE_AGGREGATE"),
        ({"if_match": '"session:session_fx_001:1"'}, 412, "STALE_AGGREGATE"),
        ({"raw": b"{not json"}, 400, "MALFORMED_REQUEST"),
        ({"content_type": "text/plain"}, 415, "UNSUPPORTED_MEDIA_TYPE"),
        ({"raw": b'{"x":"' + b"a" * MAX_BODY_BYTES + b'"}'}, 413, "PAYLOAD_TOO_LARGE"),
        ({"body": _body(intended_objects=[])}, 422, "FIELD_VALIDATION_FAILED"),
        ({"body": _body(expected_context_revision="3")}, 422, "FIELD_VALIDATION_FAILED"),
        ({"body": _body(role="teacher")}, 422, "FIELD_NOT_ALLOWED"),
        ({"body": _body(author={"principal_ref": "teacher_fx_001"})}, 422, "FIELD_NOT_ALLOWED"),
        ({"body": _body(expected_context_revision=2)}, 409, "STALE_CONTEXT"),
        ({"body": _body(child_explanation="words")}, 422, "FIELD_NOT_ALLOWED"),
        ({"token": "device-b"}, 404, "RESOURCE_NOT_FOUND"),
        ({"token": "outsider"}, 404, "RESOURCE_NOT_FOUND"),
    ],
)
def test_v12_negative_cases_have_safe_typed_codes(
    client: TestClient, h: AnalysisHarness, kwargs: dict[str, Any], status: int, code: str
) -> None:
    analysis_id = h.accepted_analysis()
    response = _post(client, analysis_id, **kwargs)
    assert response.status_code == status and _code(response) == code
    for leaked in ('"cat"', "0.62", "participant_fx", "teacher_fx", "Traceback"):
        assert leaked not in response.text
    state = h.store.snapshot()
    assert state.corrections == {} and state.receipts == {} and state.invalidations == {}


def test_v12_field_errors_never_echo_submitted_values(client: TestClient,
                                                      h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    response = _post(client, analysis_id,
                     body=_body(role="teacher", intended_objects=["x" * 200]))
    error = CollaborationErrorV1.model_validate_json(response.content).error
    assert error.code == "FIELD_NOT_ALLOWED"
    assert {fe.path for fe in error.field_errors} >= {"role", "intended_objects.0"}
    assert "x" * 50 not in response.text


def test_v12_stale_aggregate_reports_current_revision_to_authorized_caller(
    client: TestClient, h: AnalysisHarness
) -> None:
    analysis_id = h.accepted_analysis()
    response = _post(client, analysis_id, if_match='"analysis:{id}:9"')
    error = CollaborationErrorV1.model_validate_json(response.content).error
    assert error.current_revisions == {"analysis": 1}
    denied = _post(client, analysis_id, token="device-b", if_match='"analysis:{id}:9"')
    assert CollaborationErrorV1.model_validate_json(denied.content).error.current_revisions is None


def test_v12_turn_closed_stale_context_and_storage_failure(
    client: TestClient, h: AnalysisHarness
) -> None:
    analysis_id = h.accepted_analysis()
    h.authority.close_turn(DEVICE_A.principal_id)
    closed = _post(client, analysis_id, token="device-a")
    assert closed.status_code == 409 and _code(closed) == "TURN_CLOSED"
    h.store.fail_next_commit = True
    failed = _post(client, analysis_id)
    assert failed.status_code == 503 and _code(failed) == "DEPENDENCY_UNAVAILABLE"
    assert failed.json()["error"]["retryable"] is True
    h.context.bump(SESSION, CANVAS)
    stale = _post(client, analysis_id, body=_body(expected_context_revision=4))
    assert stale.status_code == 409 and _code(stale) == "STALE_CONTEXT"


def test_v12_fixture_app_exposes_only_the_cmd34_post(client: TestClient,
                                                     h: AnalysisHarness) -> None:
    surface = route_surface(client.app.routes)  # type: ignore[attr-defined]
    assert surface == {(f"{PREFIX}/analysis-results/{{analysis_id}}/corrections", "POST")}
    analysis_id = h.accepted_analysis()
    for path in (f"{PREFIX}/analysis-results/{analysis_id}",
                 f"{PREFIX}/analysis-results/{analysis_id}/corrections"):
        response = client.get(path, headers={"Authorization": "Fixture teacher"})
        assert response.status_code in {404, 405}


def test_v12_production_app_source_does_not_import_cmd34() -> None:
    app_source = Path(__file__).resolve().parents[2] / "src/sketch2life/interfaces/http/app.py"
    text = app_source.read_text(encoding="utf-8")
    assert "analysis_corrections" not in text and "vision_analysis" not in text


def test_v12_production_app_routes_do_not_mount_cmd34() -> None:
    pytest.importorskip("PIL", reason="live app import needs Pillow (not in this env)")
    from sketch2life.interfaces.http.app import create_app

    live = route_surface(create_app().routes)
    assert live, "route walk found no live routes"
    assert not any("analysis-results" in path for path, _ in live)
