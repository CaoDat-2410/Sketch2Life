from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.infrastructure.persistence.be1_models import OrganizationAssignmentModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service

_BASE = "/api/lesson-library/v1"
_PATH = (
    _BASE
    + "/organizations/{organization_id}/lessons/{lesson_id}/remixes"
)
_BODY = {
    "contract": "RemixLessonRequestV1",
    "source_version_id": "source-version-0001",
    "source_content_sha256": "a" * 64,
}


class _ScalarRows:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _TeacherDb:
    def __init__(self, *, role: str = "teacher") -> None:
        self.identity = SimpleNamespace(
            state="active", account_role=role, issuer="synthetic-remix-issuer"
        )
        self.assignment = OrganizationAssignmentModel(
            assignment_id="assignment-remix-1",
            organization_id="destination-org",
            subject="synthetic-remix-teacher",
            class_id=None,
            role="teacher",
            active=True,
        )

    def get(self, _model: Any, _subject: str) -> Any:
        return self.identity

    def scalars(self, _statement: Any) -> _ScalarRows:
        return _ScalarRows([self.assignment] if self.identity.account_role == "teacher" else [])


class _RemixService:
    def __init__(
        self,
        *,
        result: dict[str, Any] | None = None,
        error: LessonLibraryError | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def remix_public_lesson(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def _response_body() -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    return {
        "contract": "RemixLessonResponseV1",
        "lesson": {
            "contract": "LessonDetailV1",
            "lesson_id": "derived-lesson-0001",
            "organization_id": "destination-org",
            "owner_kind": "ORGANIZATION",
            "created_by": "synthetic-remix-teacher",
            "state": "ACTIVE",
            "visibility": "PRIVATE",
            "moderation_state": "VISIBLE",
            "current_version": {
                "contract": "LessonVersionV1",
                "lesson_id": "derived-lesson-0001",
                "version_id": "derived-version-0001",
                "version_no": 1,
                "review_state": "DRAFT",
                "structured_content_hash": "a" * 64,
                "source_document_revision_id": None,
                "authored_principal_ref": "synthetic-remix-teacher",
                "created_at": now,
                "content": {
                    "locale": "vi-VN",
                    "title": "Bài học sao chép",
                    "topic": "Quan sát",
                    "target_age_band_ref": "age-3-6",
                    "target_age_band_version": 1,
                    "objectives": ["Quan sát"],
                    "drawing_subject": "Lá cây",
                    "drawing_steps_text": "Quan sát đường viền.",
                    "subject_learning_notes": "Lá có gân.",
                    "script_direction": None,
                    "script_following_allowed": False,
                    "activities": [
                        {
                            "title": "Tìm lá",
                            "objective": "Quan sát lá",
                            "materials_text": "",
                            "preparation_text": "",
                            "instructions_text": "Tìm một chiếc lá.",
                            "observation_notes": "",
                            "safety_notes": "",
                            "activity_kind": "outdoor",
                        }
                    ],
                },
            },
            "revision": 1,
            "created_at": now,
            "updated_at": now,
        },
        "source": {
            "lesson_id": "source-lesson-0001",
            "version_id": "source-version-0001",
            "content_sha256": "a" * 64,
        },
    }


@contextmanager
def _client(
    service: _RemixService, *, actor_role: str = "teacher",
) -> Iterator[tuple[TestClient, _RemixService]]:
    application = create_app()
    db = _TeacherDb(role=actor_role)
    principal = VerifiedPrincipal(
        subject="synthetic-remix-teacher",
        issuer="synthetic-remix-issuer",
        roles=frozenset(),
        token_id="synthetic-remix-token",
    )
    application.dependency_overrides[get_verified_adult] = lambda: principal
    application.dependency_overrides[get_db] = lambda: db
    application.dependency_overrides[get_lesson_library_service] = lambda: service
    try:
        with TestClient(application) as client:
            yield client, service
    finally:
        application.dependency_overrides.clear()


def _post(
    client: TestClient,
    *,
    lesson_id: str = "source-lesson-0001",
    body: dict[str, Any] | None = None,
):
    return client.post(
        f"{_BASE}/organizations/destination-org/lessons/{lesson_id}/remixes",
        headers={"Idempotency-Key": "remix-key-1"},
        json=_BODY if body is None else body,
    )


def test_remix_contract_201_etag_and_fields() -> None:
    service = _RemixService(result=_response_body())
    with _client(service) as (client, _service):
        response = _post(client)

    assert response.status_code == 201
    assert response.headers["ETag"] == '"1"'
    assert response.headers["Cache-Control"] == "private, no-store"
    body = response.json()
    assert body["contract"] == "RemixLessonResponseV1"
    assert body["lesson"]["visibility"] == "PRIVATE"
    assert body["lesson"]["current_version"]["review_state"] == "DRAFT"
    assert body["source"] == {
        "lesson_id": "source-lesson-0001",
        "version_id": "source-version-0001",
        "content_sha256": "a" * 64,
    }
    assert "source_content_sha256" not in body["source"]
    assert service.calls[0]["source_content_sha256"] == "a" * 64
    assert service.calls[0]["idempotency_key"] == "remix-key-1"


def test_remix_validation_is_400_invalid_request() -> None:
    service = _RemixService(result=_response_body())
    invalid = {**_BODY, "source_content_sha256": "A" * 64, "content": {"title": "editable"}}
    with _client(service) as (client, _service):
        response = _post(client, body=invalid)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []


def test_remix_unknown_and_out_of_scope_equal_404() -> None:
    service = _RemixService(
        error=LessonLibraryError(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")
    )
    with _client(service) as (client, _service):
        unknown = client.post(
            f"{_BASE}/organizations/destination-org/lessons/unknown/remixes",
            headers={"Idempotency-Key": "remix-key-1", "X-Request-ID": "same-request"},
            json=_BODY,
        )
        out_of_scope = client.post(
            f"{_BASE}/organizations/destination-org/lessons/foreign/remixes",
            headers={"Idempotency-Key": "remix-key-1", "X-Request-ID": "same-request"},
            json=_BODY,
        )
    assert unknown.status_code == out_of_scope.status_code == 404
    assert unknown.json() == out_of_scope.json()
    assert "source" not in unknown.json()


def test_remix_stale_hash_409() -> None:
    service = _RemixService(
        error=LessonLibraryError(409, "STALE_SOURCE_VERSION", "The source version hash is stale")
    )
    with _client(service) as (client, _service):
        response = _post(client)
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_SOURCE_VERSION"


def test_remix_reused_key_changed_payload_400() -> None:
    service = _RemixService(
        error=LessonLibraryError(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    )
    with _client(service) as (client, _service):
        response = _post(client)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def _schema_refs(value: Any) -> set[str]:
    if isinstance(value, dict):
        refs = {value["$ref"].rsplit("/", 1)[-1]} if isinstance(value.get("$ref"), str) else set()
        return refs.union(*(_schema_refs(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(_schema_refs(child) for child in value)) if value else set()
    return set()


def test_remix_catalog_and_openapi() -> None:
    key = ("post", _PATH)
    assert key in MOUNTED_OPERATIONS
    assert key in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    application = create_app()
    operation = application.openapi(fe_projected=False)["paths"][_PATH]["post"]
    assert "RemixLessonRequestV1" in _schema_refs(operation["requestBody"])
    assert "RemixLessonResponseV1" in _schema_refs(operation["responses"]["201"])
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert parameters["Idempotency-Key"]["required"] is True
    assert "If-Match" not in parameters
    assert operation["responses"]["201"]["headers"]["ETag"]["schema"]["type"] == "string"
    assert operation["responses"]["400"]
    assert operation["responses"]["404"]
    assert operation["responses"]["409"]
    assert operation["responses"]["503"]
    assert "422" not in operation["responses"]


def test_remix_rejects_parent_actor() -> None:
    service = _RemixService(result=_response_body())
    with _client(service, actor_role="parent") as (client, _service):
        response = _post(client)
    assert response.status_code == 404
    assert service.calls == []
