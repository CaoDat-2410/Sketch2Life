# ruff: noqa: E501, F811, SIM117, B023
"""Missing contract tests for E6 T-FBK1 named in IMPL_REVIEW_E_E6_R1_20261125.md and E6_PROMPT.md."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from test_parent_lesson_feedback_routes import _BASE, _PARENT, _client

from sketch2life.infrastructure.identity.firebase_token_verifier import (
    IdentityVerificationUnavailable,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_runtime

ERROR_FIELDS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
    "request_id",
}


def test_missing_idempotency_key_returns_conv1_400_required_envelope() -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Finding 5 (explicit missing Idempotency-Key 400 CONV-1 envelope)"""
    client, service, app = _client()
    try:
        response = client.post(
            _BASE,
            headers={"X-Request-ID": "fbk-missing-key"},
            json={"feedback_text": "Helpful lesson"},
        )
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert response.status_code == 400
    body = response.json()
    assert set(body) == ERROR_FIELDS
    assert body["code"] == "INVALID_REQUEST"
    assert body["retryable"] is False
    assert body["request_id"] == "fbk-missing-key"
    assert body["field_errors"] == [{"field": "Idempotency-Key", "code": "REQUIRED"}]
    assert service.calls == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"feedback_text": "   "},
        {"feedback_text": "x" * 1201},
        {"feedback_text": "A note", "profile_id": "profile-1"},
        {"feedback_text": "A note", "child_id": "child-a"},
        {"feedback_text": "A note", "media_url": "https://example.invalid/img.png"},
    ],
)
def test_post_body_validation_faults_return_400_invalid_request_not_422(
    payload: dict[str, Any],
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §3 400 INVALID_REQUEST on body/extra fields)"""
    client, service, app = _client()
    try:
        response = client.post(
            _BASE,
            headers={"Idempotency-Key": "fbk-bad-body"},
            json=payload,
        )
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert response.status_code == 400
    body = response.json()
    assert set(body) == ERROR_FIELDS
    assert body["code"] == "INVALID_REQUEST"
    assert service.calls == []


def test_unauthenticated_and_inactive_or_mismatch_parent_identities_are_rejected() -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §3 401 AUTH_REQUIRED & 403 ACCOUNT_SCOPE_UNAVAILABLE)"""
    app = create_app()

    class _DummyVerifier:
        async def verify(self, _token: str) -> Any:
            raise IdentityVerificationUnavailable("invalid")

    app.dependency_overrides[get_runtime] = lambda: SimpleNamespace(
        session_factory=object(),
        database_error=None,
        identity_verifier=_DummyVerifier(),
    )
    with TestClient(app) as client:
        unauth = client.get(_BASE)
    app.dependency_overrides.clear()
    assert unauth.status_code == 401
    assert unauth.json()["code"] == "AUTH_REQUIRED"

    for state, issuer in (("disabled", _PARENT.issuer), ("active", "other-issuer")):
        client, service, app = _client(role="parent")
        try:
            identity_db = SimpleNamespace(
                identity=SimpleNamespace(
                    subject=_PARENT.subject,
                    issuer=issuer,
                    state=state,
                    account_role="parent",
                ),
                get=lambda _model, _subject, _id=None: identity_db.identity,
            )
            app.dependency_overrides[get_db] = lambda _db=identity_db: _db
            response = client.get(_BASE)
        finally:
            client.close()
            app.dependency_overrides.clear()

        assert response.status_code == 403
        assert response.json()["code"] == "ACCOUNT_SCOPE_UNAVAILABLE"
        assert service.calls == []


def test_service_error_mapping_and_oversized_cursor_rejected_as_400() -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §3 503 PROVIDER_UNAVAILABLE, 409, cursor max 768)"""
    for err, expected_status, expected_code, expected_retryable in (
        (
            LessonLibraryError(503, "DEPENDENCY_UNAVAILABLE", "Database unavailable"),
            503,
            "PROVIDER_UNAVAILABLE",
            True,
        ),
        (
            LessonLibraryError(409, "RESOURCE_CONFLICT", "Conflict"),
            409,
            "RESOURCE_CONFLICT",
            False,
        ),
    ):
        client, _service, app = _client(error=err)
        try:
            response = client.post(
                _BASE,
                headers={"Idempotency-Key": "fbk-err-map"},
                json={"feedback_text": "Note"},
            )
        finally:
            client.close()
            app.dependency_overrides.clear()
        assert response.status_code == expected_status
        body = response.json()
        assert set(body) == ERROR_FIELDS
        assert body["code"] == expected_code
        assert body["retryable"] is expected_retryable

    client, service, app = _client()
    try:
        bad_cursor = client.get(_BASE + f"/replies?cursor={'a' * 769}")
    finally:
        client.close()
        app.dependency_overrides.clear()
    assert bad_cursor.status_code == 400
    assert bad_cursor.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []
