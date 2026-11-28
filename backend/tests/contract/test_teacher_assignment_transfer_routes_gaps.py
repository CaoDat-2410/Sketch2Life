"""Additional HTTP contract tests for T-6b gaps identified in cold review R1."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.teacher_assignment_transfer import (
    TeacherAssignmentTransferError,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.routers import be1_registry
from tests.contract.test_teacher_assignment_transfer_routes import (
    _BASE,
    _CLASS,
    _app,
    _FakeSession,
)


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL",
        "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db",
    )
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize(
    ("method", "path", "headers", "body"),
    [
        (
            "post",
            f"{_BASE}/{_CLASS}/assignments",
            {"If-Match": '"1"'},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "post",
            f"{_BASE}/{_CLASS}/assignments",
            {"Idempotency-Key": "bad key with spaces", "If-Match": '"1"'},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "post",
            f"{_BASE}/{_CLASS}/assignments",
            {"Idempotency-Key": "valid-key"},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "post",
            f"{_BASE}/{_CLASS}/assignments",
            {"Idempotency-Key": "valid-key", "If-Match": 'W/"1"'},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "delete",
            f"{_BASE}/{_CLASS}/assignments/current",
            {"If-Match": '"1"'},
            None,
        ),
        (
            "delete",
            f"{_BASE}/{_CLASS}/assignments/current",
            {"Idempotency-Key": "valid-key", "If-Match": "not-an-etag"},
            None,
        ),
        (
            "delete",
            f"{_BASE}/{_CLASS}/assignments/current",
            {"Idempotency-Key": "valid-key", "If-Match": '"1"'},
            {"unexpected": "body"},
        ),
    ],
)
def test_conv1_invalid_headers_and_non_empty_offboard_body_return_400(
    method: str,
    path: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    session = _FakeSession(
        role="school_manager", assignment_role="school_admin", assignment_class_id=None
    )
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.request(method, path, headers=headers, json=body)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    ("method", "path", "headers", "body"),
    [
        (
            "post",
            f"{_BASE}/{_CLASS}/assignments",
            {"Idempotency-Key": "role-key", "If-Match": '"1"'},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "get",
            f"{_BASE}/{_CLASS}/assignment-transfers/11111111-1111-4111-8111-111111111111",
            {},
            None,
        ),
    ],
)
def test_role_refusal_403_for_post_and_get(
    method: str, path: str, headers: dict[str, str], body: dict[str, Any] | None
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    session = _FakeSession(role="teacher", assignment_role="teacher", assignment_class_id=_CLASS)
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.request(method, path, headers=headers, json=body)

    assert response.status_code == 403
    assert response.json()["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.parametrize(
    ("method", "path", "headers", "body"),
    [
        (
            "post",
            f"{_BASE}/{_CLASS}/assignments",
            {"Idempotency-Key": "foreign-key", "If-Match": '"1"'},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "delete",
            f"{_BASE}/{_CLASS}/assignments/current",
            {"Idempotency-Key": "foreign-key", "If-Match": '"1"'},
            None,
        ),
        (
            "get",
            f"{_BASE}/{_CLASS}/assignment-transfers/11111111-1111-4111-8111-111111111111",
            {},
            None,
        ),
    ],
)
def test_foreign_org_manager_gets_uniform_404_across_all_transfer_routes(
    method: str, path: str, headers: dict[str, str], body: dict[str, Any] | None
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    session = _FakeSession(
        role="school_manager", assignment_role=None, assignment_class_id=None
    )
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.request(method, path, headers=headers, json=body)

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_changed_payload_same_key_returns_400_invalid_idempotency_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    session = _FakeSession(
        role="school_manager", assignment_role="school_admin", assignment_class_id=None
    )

    def raise_mismatch(*_args: Any, **_kwargs: Any) -> Any:
        raise TeacherAssignmentTransferError(400, "INVALID_IDEMPOTENCY_KEY")

    monkeypatch.setattr(be1_registry, "_session_factory", lambda _runtime: object())
    monkeypatch.setattr(be1_registry, "_receipt_hmac_key", lambda _runtime: b"k" * 32)
    monkeypatch.setattr(be1_registry.TeacherAssignmentTransferService, "execute", raise_mismatch)
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.delete(
            f"{_BASE}/{_CLASS}/assignments/current",
            headers={"Idempotency-Key": "reused-key", "If-Match": '"1"'},
        )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_stale_revision_409_includes_current_version_after_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    session = _FakeSession(
        role="school_manager", assignment_role="school_admin", assignment_class_id=None
    )

    def raise_stale(*_args: Any, **_kwargs: Any) -> Any:
        raise TeacherAssignmentTransferError(409, "STALE_REVISION", current_version=5)

    monkeypatch.setattr(be1_registry, "_session_factory", lambda _runtime: object())
    monkeypatch.setattr(be1_registry, "_receipt_hmac_key", lambda _runtime: b"k" * 32)
    monkeypatch.setattr(be1_registry.TeacherAssignmentTransferService, "execute", raise_stale)
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.delete(
            f"{_BASE}/{_CLASS}/assignments/current",
            headers={"Idempotency-Key": "stale-key", "If-Match": '"1"'},
        )

    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == 5
