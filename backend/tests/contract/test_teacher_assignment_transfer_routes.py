from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.teacher_assignment_transfers import (
    Be1TeacherAssignmentTransferAcceptedV1,
    Be1TeacherAssignmentTransferStatusV1,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.routers.be1_registry import router
from sketch2life.interfaces.http.routers.lesson_occurrences import (
    get_child_selection_service,
    get_transfer_guards,
)

_POST = ("post", "/api/be1/v1/classes/{class_id}/assignments")
_OFFBOARD = ("delete", "/api/be1/v1/classes/{class_id}/assignments/current")
_STATUS = ("get", "/api/be1/v1/classes/{class_id}/assignment-transfers/{transfer_id}")
_ORG = "synthetic-transfer-org"
_CLASS = "synthetic-transfer-class"
_SUBJECT = "synthetic-transfer-manager"
_ISSUER = "synthetic-transfer-issuer"
_BASE = "/api/be1/v1/classes"
DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class _FakeSession:
    def __init__(
        self,
        *,
        role: str,
        assignment_role: str | None,
        assignment_class_id: str | None,
    ) -> None:
        self.identity = AdultIdentityModel(
            subject=_SUBJECT,
            issuer=_ISSUER,
            state="active",
            account_role=role,
        )
        self.assignments = (
            [
                OrganizationAssignmentModel(
                    assignment_id="synthetic-transfer-assignment",
                    organization_id=_ORG,
                    subject=_SUBJECT,
                    class_id=assignment_class_id,
                    role=assignment_role,
                    active=True,
                )
            ]
            if assignment_role is not None
            else []
        )
        self.classroom = SimpleNamespace(
            class_id=_CLASS,
            organization_id=_ORG,
            state="active",
        )

    def scalar(self, statement: Any) -> Any:
        values = statement.compile().params.values()
        return self.classroom if _CLASS in values else None

    def get(self, model: object, key: object) -> AdultIdentityModel | None:
        return self.identity if model is AdultIdentityModel and key == _SUBJECT else None

    def scalars(self, _statement: Any) -> Any:
        return SimpleNamespace(all=lambda: self.assignments)

    def rollback(self) -> None:
        return None


def _app(session: _FakeSession) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=_SUBJECT, issuer=_ISSUER, roles=frozenset()
    )
    application.dependency_overrides[get_db] = lambda: session
    return application


def _responses(key: tuple[str, str]) -> dict[str, dict[str, str]]:
    return {row["status"]: row for row in MOUNTED_OPERATIONS[key]["responses"]}


def test_assignment_routes_keep_first_assignment_and_publish_transfer_status() -> None:
    route_methods = {
        (
            method.lower(),
            route.path
            if route.path.startswith(router.prefix)
            else f"{router.prefix.rstrip('/')}{route.path}",
        )
        for route in router.routes
        for method in (route.methods or set())
    }
    assert {_POST, _OFFBOARD, _STATUS} <= route_methods
    post = _responses(_POST)
    assert post["200"]["schema_name"] == "object"
    assert post["202"]["schema_name"] == "Be1TeacherAssignmentTransferAcceptedV1"
    assert "private, no-store" in post["202"]["description"]
    offboard = _responses(_OFFBOARD)
    assert offboard["202"]["schema_name"] == "Be1TeacherAssignmentTransferAcceptedV1"
    assert "private, no-store" in offboard["202"]["description"]
    status = _responses(_STATUS)
    assert status["200"]["schema_name"] == "Be1TeacherAssignmentTransferStatusV1"
    assert "private, no-store" in status["200"]["description"]
    assert "404" in status
    assert "Idempotency-Key" in MOUNTED_OPERATIONS[_POST]["request_inputs"]
    assert "Idempotency-Key" in MOUNTED_OPERATIONS[_OFFBOARD]["request_inputs"]
    assert "Idempotency-Key" not in MOUNTED_OPERATIONS[_STATUS]["request_inputs"]


def test_transfer_responses_are_metadata_only_and_bound_to_the_class() -> None:
    accepted = Be1TeacherAssignmentTransferAcceptedV1(
        transfer_id="11111111-1111-4111-8111-111111111111",
        class_id="synthetic-class",
        action="REASSIGN",
        state="TRANSFER_PENDING",
        assignment_revision=2,
        status_url="/api/be1/v1/classes/synthetic-class/assignment-transfers/"
        "11111111-1111-4111-8111-111111111111",
    )
    status = Be1TeacherAssignmentTransferStatusV1(
        transfer_id=accepted.transfer_id,
        class_id=accepted.class_id,
        action=accepted.action,
        state="COMPLETED",
        assignment_revision=3,
        created_at="2026-11-25T00:00:00Z",
        updated_at="2026-11-25T00:00:01Z",
        status_url=accepted.status_url,
    )
    for body in (accepted.model_dump(mode="json"), status.model_dump(mode="json")):
        assert not {"email", "subject", "uid", "token", "link", "child_name"} & set(body)


class _PendingTransferGuards:
    def create(self, _principal: VerifiedPrincipal, _class_id: str) -> None:
        raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")

    def occurrence_write(self, _principal: VerifiedPrincipal, _occurrence_id: str) -> None:
        raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")


class _GuardOrderSelectionService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def select(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


def test_pending_transfer_guard_returns_409_before_selection_service() -> None:
    application = create_app()
    service = _GuardOrderSelectionService()
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=_SUBJECT, issuer=_ISSUER, roles=frozenset()
    )
    application.dependency_overrides[get_transfer_guards] = lambda: _PendingTransferGuards()
    application.dependency_overrides[get_child_selection_service] = lambda: service

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.post(
            "/v1/lesson-occurrences/occ-1/child-selections",
            headers={"Idempotency-Key": "pending-transfer-key"},
            json={},
        )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert service.calls == []


@pytest.mark.parametrize(
    ("method", "path", "headers", "body"),
    [
        (
            "post",
            f"{_BASE}/contract-class/assignments",
            {"Idempotency-Key": "contract-key", "If-Match": '"1"'},
            {"candidate_ref": "synthetic-candidate"},
        ),
        (
            "delete",
            f"{_BASE}/contract-class/assignments/current",
            {"Idempotency-Key": "contract-key", "If-Match": '"1"'},
            None,
        ),
        (
            "get",
            f"{_BASE}/contract-class/assignment-transfers/11111111-1111-4111-8111-111111111111",
            {},
            None,
        ),
    ],
)
def test_transfer_routes_require_a_bearer_token(
    method: str, path: str, headers: dict[str, str], body: dict[str, str] | None
) -> None:
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.request(method, path, headers=headers, json=body)
    assert response.status_code == 401


def test_assignment_rejects_extra_body_fields_with_400() -> None:
    session = _FakeSession(
        role="school_manager", assignment_role="school_admin", assignment_class_id=None
    )
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.post(
            f"{_BASE}/{_CLASS}/assignments",
            headers={"Idempotency-Key": "contract-key", "If-Match": '"1"'},
            json={"candidate_ref": "synthetic-candidate", "unexpected": True},
        )
    assert response.status_code == 400


def test_offboard_role_refusal_is_403() -> None:
    session = _FakeSession(
        role="teacher", assignment_role="teacher", assignment_class_id=_CLASS
    )
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.delete(
            f"{_BASE}/{_CLASS}/assignments/current",
            headers={"Idempotency-Key": "contract-key", "If-Match": '"1"'},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "ACTION_NOT_ALLOWED"


def test_status_uses_the_same_404_for_unknown_and_foreign_transfer_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(
        role="school_manager", assignment_role="school_admin", assignment_class_id=None
    )
    monkeypatch.setattr(
        be1_registry.SqlTeacherAssignmentTransferRepository,
        "status",
        lambda _repository, **_kwargs: None,
    )
    monkeypatch.setattr(be1_registry, "_session_factory", lambda _runtime: object())
    first_transfer_id = str(uuid4())
    second_transfer_id = str(uuid4())
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        missing = client.get(
            f"{_BASE}/{_CLASS}/assignment-transfers/{first_transfer_id}"
        )
        foreign = client.get(
            f"{_BASE}/{_CLASS}/assignment-transfers/{second_transfer_id}"
        )
    assert missing.status_code == foreign.status_code == 404
    assert (missing.json()["code"], missing.json()["message"]) == (
        foreign.json()["code"],
        foreign.json()["message"],
    )
    assert missing.json()["code"] == "RESOURCE_NOT_FOUND"
    assert missing.headers["Cache-Control"] == "private, no-store"
    assert foreign.headers["Cache-Control"] == "private, no-store"


def test_offboard_success_keeps_private_no_store_cache_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(
        role="school_manager", assignment_role="school_admin", assignment_class_id=None
    )
    accepted = Be1TeacherAssignmentTransferAcceptedV1(
        transfer_id="11111111-1111-4111-8111-111111111111",
        class_id=_CLASS,
        action="OFFBOARD",
        state="TRANSFER_PENDING",
        assignment_revision=2,
        status_url=(
            f"/api/be1/v1/classes/{_CLASS}/assignment-transfers/"
            "11111111-1111-4111-8111-111111111111"
        ),
    )

    def accept_transfer(
        _runtime: Any, response: Any, _principal: Any, **_kwargs: Any
    ) -> Be1TeacherAssignmentTransferAcceptedV1:
        response.status_code = 202
        return accepted

    monkeypatch.setattr(be1_registry, "_execute_transfer", accept_transfer)
    with TestClient(_app(session), raise_server_exceptions=False) as client:
        response = client.delete(
            f"{_BASE}/{_CLASS}/assignments/current",
            headers={"Idempotency-Key": "contract-key", "If-Match": '"1"'},
        )
    assert response.status_code == 202
    assert response.headers["Cache-Control"] == "private, no-store"
