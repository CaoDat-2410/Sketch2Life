from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_force_close import (
    ManagerStoryRunConflict,
    ManagerStoryRunForceClosed,
    ManagerStoryRunForceCloseFailure,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers import manager_story_run_force_close as routes

ORGANIZATION = "org-1"
RUN_ID = "4be7a402-dbab-4977-bd1a-63d4b580cf08"
GET_PATH = (
    "/api/be1/v1/organizations/{organization_id}/teachers/{teacher_ref}/"
    "active-story-run-conflict"
)
POST_PATH = "/api/be1/v1/organizations/{organization_id}/story-runs/{run_id}/force-close"


class _Service:
    def __init__(self, *, missing: bool = False) -> None:
        self.missing = missing
        self.received: dict[str, object] | None = None

    def get_active_conflict(self, **values: object) -> ManagerStoryRunConflict:
        if self.missing:
            raise ManagerStoryRunForceCloseFailure(404, "RESOURCE_NOT_FOUND")
        return ManagerStoryRunConflict(RUN_ID, "SCRIPT_REVIEW", 7)

    def force_close(self, **values: object) -> ManagerStoryRunForceClosed:
        if self.missing:
            raise ManagerStoryRunForceCloseFailure(404, "RESOURCE_NOT_FOUND")
        self.received = values
        return ManagerStoryRunForceClosed(RUN_ID, 8)


def _client(monkeypatch, service: _Service) -> TestClient:
    application = FastAPI()
    application.include_router(routes.router)
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject="manager-subject", issuer="synthetic-issuer", roles=frozenset()
    )
    application.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(routes, "_service", lambda _db: service)
    return TestClient(application)


def test_conflict_projection_is_metadata_only_and_not_cached(monkeypatch) -> None:
    client = _client(monkeypatch, _Service())
    response = client.get(
        GET_PATH.format(organization_id=ORGANIZATION, teacher_ref="teacher-account")
    )
    assert response.status_code == 200
    assert response.json() == {
        "contract": "ManagerActiveStoryRunConflictV1",
        "run_id": RUN_ID,
        "run_state": "SCRIPT_REVIEW",
        "revision": 7,
    }
    assert response.headers["Cache-Control"] == "private, no-store"


def test_force_close_requires_key_and_strict_reason_revision_body(monkeypatch) -> None:
    client = _client(monkeypatch, _Service())
    path = POST_PATH.format(organization_id=ORGANIZATION, run_id=RUN_ID)
    no_key = client.post(path, json={"expected_revision": 7, "reason": "approved"})
    assert no_key.status_code == 400
    assert no_key.headers["Cache-Control"] == "private, no-store"

    invalid_body = client.post(
        path,
        headers={"Idempotency-Key": "key-1"},
        json={"expected_revision": True, "reason": "   ", "extra": "rejected"},
    )
    assert invalid_body.status_code == 400
    assert invalid_body.headers["Cache-Control"] == "private, no-store"

    wrong_media_type = client.post(
        path,
        headers={"Idempotency-Key": "key-1", "Content-Type": "text/plain"},
        content='{"expected_revision":7,"reason":"approved"}',
    )
    assert wrong_media_type.status_code == 400
    assert wrong_media_type.headers["Cache-Control"] == "private, no-store"


def test_force_close_returns_minimal_projection_and_passes_normalized_reason(monkeypatch) -> None:
    service = _Service()
    client = _client(monkeypatch, service)
    response = client.post(
        POST_PATH.format(organization_id=ORGANIZATION, run_id=RUN_ID),
        headers={"Idempotency-Key": "key-1"},
        json={"expected_revision": 7, "reason": "  approved reassignment  "},
    )
    assert response.status_code == 200
    assert response.json() == {
        "contract": "ManagerForceClosedStoryRunV1",
        "run_id": RUN_ID,
        "run_state": "ABANDONED",
        "revision": 8,
    }
    assert response.headers["Cache-Control"] == "private, no-store"
    assert service.received is not None
    assert service.received["reason"] == "approved reassignment"
    assert service.received["idempotency_key"] == "key-1"


def test_unknown_and_out_of_scope_conflict_reads_share_one_404(monkeypatch) -> None:
    client = _client(monkeypatch, _Service(missing=True))
    unknown_teacher = client.get(
        GET_PATH.format(organization_id=ORGANIZATION, teacher_ref="unknown-teacher")
    )
    foreign_run = client.post(
        POST_PATH.format(organization_id="foreign-org", run_id=RUN_ID),
        headers={"Idempotency-Key": "key-1"},
        json={"expected_revision": 1, "reason": "approved"},
    )
    assert unknown_teacher.status_code == foreign_run.status_code == 404
    assert unknown_teacher.json() == foreign_run.json()
    assert unknown_teacher.headers["Cache-Control"] == "private, no-store"
    assert foreign_run.headers["Cache-Control"] == "private, no-store"


def test_openapi_catalog_exposes_both_operations() -> None:
    application = FastAPI()
    application.include_router(routes.router)
    paths = application.openapi()["paths"]
    assert GET_PATH in paths and "get" in paths[GET_PATH]
    assert POST_PATH in paths and "post" in paths[POST_PATH]
