from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from fastapi import Depends
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.interfaces.http.admin_contract import ADMIN_OPERATIONS
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_feedback import (
    parent_feedback_actor,
    parent_feedback_service,
)

_BASE = "/api/lesson-library/v1/me/lessons/lesson-1/feedback"
_PARENT = VerifiedPrincipal(
    subject="feedback-parent",
    issuer="synthetic-feedback-issuer",
    roles=frozenset(),
    token_id="synthetic-feedback-token",
)


class _IdentityDb:
    def __init__(self, role: str) -> None:
        self.identity = SimpleNamespace(
            subject=_PARENT.subject,
            issuer=_PARENT.issuer,
            state="active",
            account_role=role,
        )

    def get(self, _model: Any, _subject: str) -> Any:
        return self.identity


class _FakeParentFeedbackService:
    def __init__(self, *, error: LessonLibraryError | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def submit(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("submit", kwargs))
        if self.error is not None:
            raise self.error
        now = datetime.now(UTC)
        return {
            "contract": "ParentLessonFeedbackV1",
            "feedback_id": "feedback-1",
            "lesson_id": "lesson-1",
            "version_id": "version-1",
            "revision": 1,
            "feedback_text": kwargs["feedback_text"],
            "created_at": now,
            "updated_at": now,
            "reply_count": 0,
        }

    def state(self, lesson_id: str) -> dict[str, Any]:
        self.calls.append(("state", {"lesson_id": lesson_id}))
        if self.error is not None:
            raise self.error
        return {"contract": "ParentLessonFeedbackStateV1", "lesson_id": lesson_id, "feedback": None}

    def replies(self, lesson_id: str, *, limit: int, cursor: str | None) -> dict[str, Any]:
        self.calls.append(("replies", {"lesson_id": lesson_id, "limit": limit, "cursor": cursor}))
        if self.error is not None:
            raise self.error
        return {
            "contract": "ParentLessonFeedbackReplyPageV1",
            "feedback_id": None,
            "items": [],
            "next_cursor": None,
        }


def _client(
    *, role: str = "parent", error: LessonLibraryError | None = None
) -> tuple[TestClient, _FakeParentFeedbackService, Any]:
    app = create_app()
    db = _IdentityDb(role)
    service = _FakeParentFeedbackService(error=error)
    app.dependency_overrides[get_verified_adult] = lambda: _PARENT
    app.dependency_overrides[get_db] = lambda: db

    def fake_parent_feedback_service(
        _principal: VerifiedPrincipal = Depends(parent_feedback_actor),  # noqa: B008
    ) -> _FakeParentFeedbackService:
        return service

    app.dependency_overrides[parent_feedback_service] = fake_parent_feedback_service
    client = TestClient(app)
    return client, service, app


def test_parent_feedback_routes_are_mounted_and_in_admin_operations() -> None:
    template = "/api/lesson-library/v1/me/lessons/{lesson_id}/feedback"
    expected = {
        ("post", template),
        ("get", template),
        ("get", template + "/replies"),
    }
    assert expected <= ADMIN_OPERATIONS

    client, _service, app = _client()
    try:
        app.openapi()
        paths = {
            (method.lower(), path)
            for path, path_item in app.state.runtime_openapi_schema["paths"].items()
            for method in path_item
        }
        assert expected <= paths
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_submit_feedback_uses_required_key_and_private_cache_control() -> None:
    client, service, app = _client()
    try:
        response = client.post(
            _BASE,
            headers={"Idempotency-Key": "feedback-key-1"},
            json={"feedback_text": "  Please add another example.  "},
        )
        missing_key = client.post(_BASE, json={"feedback_text": "A note"})
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["feedback_text"] == "Please add another example."
    assert service.calls[0][1]["idempotency_key"] == "feedback-key-1"
    assert missing_key.status_code == 400
    assert missing_key.json()["code"] == "INVALID_REQUEST"


def test_parent_feedback_reads_use_private_cache_control() -> None:
    client, _service, app = _client()
    try:
        state = client.get(_BASE)
        replies = client.get(_BASE + "/replies")
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert state.status_code == 200
    assert state.headers["Cache-Control"] == "private, no-store"
    assert replies.status_code == 200
    assert replies.headers["Cache-Control"] == "private, no-store"


def test_parent_feedback_service_404_is_resource_not_found() -> None:
    client, _service, app = _client(
        error=LessonLibraryError(404, "LESSON_NOT_FOUND", "Lesson was not found")
    )
    try:
        response = client.get(_BASE)
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_non_parent_is_rejected_before_feedback_service() -> None:
    client, service, app = _client(role="teacher")
    try:
        response = client.get(_BASE)
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_SCOPE_UNAVAILABLE"
    assert service.calls == []


def test_reply_page_limit_out_of_range_is_invalid_request() -> None:
    client, service, app = _client()
    try:
        lower = client.get(_BASE + "/replies?limit=0")
        upper = client.get(_BASE + "/replies?limit=101")
    finally:
        client.close()
        app.dependency_overrides.clear()

    assert lower.status_code == upper.status_code == 400
    assert lower.json()["code"] == upper.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []
