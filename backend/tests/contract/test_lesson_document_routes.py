"""FEAT-066 T-3b: the occurrence document route contract (SRS l.545, l.1437, l.1653, l.1692).

Offline: no database, no storage. The service is replaced by a fake, so the module checks the
catalog, the published OpenAPI (no storage word, no asset ref in a read body), request validation
(CONV-1 400 bodies, never 422), the 202 headers, ETag handling and the error mapping of every
refusal of a file. Behaviour against PostgreSQL lives in
``tests/integration/lesson_occurrences/test_document_attach_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences import documents as rules
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.documents import (
    AttachResult,
    DocumentError,
    accepted_body,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.routers.lesson_occurrences import (
    get_document_service,
    get_transfer_guards,
)

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"


class _NoOpTransferGuards:
    def create(self, _principal: VerifiedPrincipal, _class_id: str) -> None:
        pass

    def occurrence_write(self, _principal: VerifiedPrincipal, _occurrence_id: str) -> None:
        pass


BASE = "/v1/lesson-occurrences/{occurrence_id}/documents"
ATTACH = ("post", BASE)
LIST = ("get", BASE)
ONE = ("get", BASE + "/{document_id}")
REVISIONS = ("get", BASE + "/{document_id}/revisions")
REVISION = ("get", BASE + "/{document_id}/revisions/{revision_no}")
OPERATIONS = (ATTACH, LIST, ONE, REVISIONS, REVISION)
STORAGE_WORDS = (
    "bucket",
    "object_key",
    "storage_object_ref",
    "presigned",
    "credential",
    "amazonaws",
    "minio",
    "scanner",
    "organization_ref",
    "organization_id",
)
NOW = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)
HASH = "c" * 64
DOCUMENT: dict[str, Any] = {
    "contract": "LessonSourceDocumentV1",
    "source_document_id": "doc-1",
    "occurrence_id": "occ-1",
    "file_name": "giao-an.pdf",
    "file_extension": ".pdf",
    "page_or_slide_count": 3,
    "document_state": "EXTRACTED",
    "head_revision_no": 2,
    "job_ref": "lsd-1",
    "warnings": ["OCR_NOT_SUPPORTED_PAGES"],
    "page_coverage": [1, 3],
    "uploaded_at": NOW,
}
REVISION_BODY: dict[str, Any] = {
    "contract": "LessonDocumentRevisionV2",
    "source_document_id": "doc-1",
    "revision_no": 1,
    "origin": "EXTRACTION",
    "review_state": "NEEDS_REVIEW",
    "base_revision_no": None,
    "extracted_text": "Tiêu đề: Vẽ con mèo",
    "text_hash": HASH,
    "text_length": 19,
    "parser": {"name": "p", "version": "1"},
    "warnings": [],
    "page_coverage": [1],
    "created_at": NOW,
}


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class FakeService:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _maybe_fail(self) -> None:
        if self.error is not None:
            raise self.error

    def attach(self, **kwargs: Any) -> AttachResult:
        self.calls.append(("attach", kwargs))
        self._maybe_fail()
        return AttachResult(accepted_body("doc-1", "lsd-1"), replayed=False)

    def get_document(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("get_document", kwargs))
        self._maybe_fail()
        return dict(DOCUMENT)

    def list_documents(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("list_documents", kwargs))
        self._maybe_fail()
        return {
            "contract": "LessonSourceDocumentPageV1",
            "items": [dict(DOCUMENT)],
            "next_cursor": "n",
        }

    def list_revisions(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("list_revisions", kwargs))
        self._maybe_fail()
        return {
            "contract": "LessonDocumentRevisionPageV1",
            "items": [
                {
                    "revision_no": 1,
                    "origin": "EXTRACTION",
                    "review_state": "NEEDS_REVIEW",
                    "text_hash": HASH,
                    "text_length": 19,
                    "created_at": NOW,
                }
            ],
            "next_cursor": None,
        }

    def get_revision(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("get_revision", kwargs))
        self._maybe_fail()
        return dict(REVISION_BODY)


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService]]:
    application = create_app()
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_document_service] = lambda: service
    application.dependency_overrides[get_transfer_guards] = lambda: _NoOpTransferGuards()
    with TestClient(application) as client:
        yield client, service


def headers(key: str | None = "key-1") -> dict[str, str]:
    return {"Idempotency-Key": key} if key is not None else {}


URL = "/v1/lesson-occurrences/occ-1/documents"


# ----------------------------------------------------------------------------- catalog
def test_the_five_operations_are_catalogued_and_only_the_attach_is_keyed() -> None:
    for key in OPERATIONS:
        assert key in MOUNTED_OPERATIONS
        assert MOUNTED_OPERATIONS[key]["tag"] == "Lesson Occurrences"
        assert MOUNTED_OPERATIONS[key]["authentication"] == "HTTPBearer (bearer)"
    assert ATTACH in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    for key in OPERATIONS[1:]:
        assert key not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    statuses = {row["status"] for row in MOUNTED_OPERATIONS[ATTACH]["responses"]}
    assert {"202", "400", "401", "403", "404", "409", "413", "415", "422", "503"} == statuses
    for key in (ONE, REVISION):
        assert "304" in {row["status"] for row in MOUNTED_OPERATIONS[key]["responses"]}


def test_published_contract_documents_the_routes_and_leaks_nothing() -> None:
    application = create_app()
    projected = application.openapi()
    # The FE-projected SRS spec is not widened by T-3b (coordinator ruling): the five operations
    # are catalogued and served, and join the projection when the FE sync task adds them.
    assert not [path for path in projected["paths"] if "/documents" in path]
    spec = application.state.runtime_openapi_schema
    published = spec["paths"]
    attach = published[BASE]["post"]
    assert attach["tags"] == ["Lesson Occurrences"] and attach["security"]
    assert attach["responses"]["202"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/LessonSourceDocumentAcceptedV1"
    }
    assert "422" in attach["responses"]  # a refused file; never FastAPI's undeclared validation 422
    parameters = {(p["in"], p["name"]): p for p in attach["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    for path, method in (
        (BASE + "/{document_id}", "get"),
        (BASE + "/{document_id}/revisions/{revision_no}", "get"),
    ):
        assert "304" in published[path][method]["responses"]
    query = {p["name"]: p for p in published[BASE]["get"]["parameters"] if p["in"] == "query"}
    assert query["limit"]["schema"]["maximum"] == 100 and query["limit"]["schema"]["default"] == 25
    assert set(query) == {"limit", "cursor"}
    revision_path = published[BASE + "/{document_id}/revisions/{revision_no}"]["get"]
    revision_parameter = {p["name"]: p for p in revision_path["parameters"]}["revision_no"]
    assert revision_parameter["schema"]["minimum"] == 1

    schemas = spec["components"]["schemas"]
    request = schemas["AttachOccurrenceDocumentRequestV1"]
    assert request["additionalProperties"] is False
    assert set(request["properties"]) == {"asset_ref"} and request["required"] == ["asset_ref"]
    assert set(schemas["LessonSourceDocumentAcceptedV1"]["properties"]) == {
        "contract",
        "source_document_id",
        "document_revision_no",
        "job",
    }
    assert set(schemas["LessonSourceDocumentV1"]["properties"]) == set(DOCUMENT)
    assert set(schemas["LessonDocumentRevisionV2"]["properties"]) == set(REVISION_BODY)
    names = {
        "AttachOccurrenceDocumentRequestV1",
        "ExtractionJobRefV1",
        "LessonSourceDocumentAcceptedV1",
        "LessonSourceDocumentV1",
        "LessonSourceDocumentPageV1",
        "LessonDocumentRevisionSummaryV1",
        "LessonDocumentRevisionPageV1",
        "LessonDocumentRevisionV2",
        "DocumentParserV1",
    }
    scoped = json.dumps({path: published[path] for path in published if "/documents" in path})
    scoped += json.dumps({name: schemas[name] for name in names})
    for word in STORAGE_WORDS:
        assert word not in scoped.lower(), word
    # Only the request carries the opaque handle; no read body returns an asset ref (l.1692).
    read_schemas = json.dumps(
        {name: schemas[name] for name in names - {"AttachOccurrenceDocumentRequestV1"}}
    )
    assert "asset_ref" not in read_schemas
    assert "latest" not in scoped.lower()


# ----------------------------------------------------------------------------- validation
def test_missing_or_malformed_keys_are_400_with_a_field_error(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    body = {"asset_ref": "upl_abc"}
    missing = client.post(URL, json=body)
    assert missing.status_code == 400 and missing.json()["code"] == "INVALID_REQUEST"
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
    for bad in ("has space", "x" * 129):
        response = client.post(URL, json=body, headers=headers(bad))
        assert response.status_code == 400, bad
    assert service.calls == []


@pytest.mark.parametrize(
    ("body", "field", "code"),
    [
        ({}, "asset_ref", "REQUIRED"),
        ({"asset_ref": ""}, "asset_ref", "EMPTY"),
        ({"asset_ref": 5}, "asset_ref", "INVALID_TYPE"),
        ({"asset_ref": "x" * 129}, "asset_ref", "TOO_LONG"),
        # an object key or a path is not an asset handle: only the opaque ``upl_`` form passes
        ({"asset_ref": "occurrences/org/occ/abc/original"}, "asset_ref", "INVALID_FORMAT"),
        ({"asset_ref": "upl_ spaced"}, "asset_ref", "INVALID_FORMAT"),
        ({"asset_ref": "upl_\x00"}, "asset_ref", "INVALID_FORMAT"),
    ],
)
def test_invalid_bodies_are_400_never_422(
    served: tuple[TestClient, FakeService], body: dict[str, Any], field: str, code: str
) -> None:
    client, service = served
    response = client.post(URL, json=body, headers=headers())
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert {"field": field, "code": code} in payload["field_errors"]
    assert service.calls == []


def test_unknown_body_fields_are_refused_so_a_client_cannot_name_a_hash_a_type_or_an_owner(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for extra in (
        "organization_id",
        "file_name",
        "sha256",
        "content_sha256",
        "media_type",
        "uploaded_by",
        "extracted_text",
    ):
        response = client.post(URL, json={"asset_ref": "upl_abc", extra: "x"}, headers=headers())
        assert response.status_code == 400, extra
        assert any(item["code"] == "UNKNOWN_FIELD" for item in response.json()["field_errors"])
    assert service.calls == []


def test_list_and_path_parameters_are_validated(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    for url, field, code in (
        (URL + "?limit=101", "limit", "OUT_OF_RANGE"),
        (URL + "?limit=0", "limit", "OUT_OF_RANGE"),
        (URL + "/doc-1/revisions?limit=101", "limit", "OUT_OF_RANGE"),
        (URL + "/doc-1/revisions/0", "revision_no", "OUT_OF_RANGE"),
        (URL + "/doc-1/revisions/abc", "revision_no", "INVALID_TYPE"),
    ):
        response = client.get(url)
        assert response.status_code == 400, url
        assert {"field": field, "code": code} in response.json()["field_errors"], url
    assert service.calls == []
    assert client.get(URL + "?limit=100").status_code == 200


# ----------------------------------------------------------------------------- behaviour
def test_attach_returns_202_with_the_job_location_and_the_document_content_location(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.post(URL, json={"asset_ref": "upl_abc"}, headers=headers("k"))
    assert response.status_code == 202
    assert response.headers["Location"] == "/v1/jobs/lsd-1"
    assert response.headers["Content-Location"] == "/v1/lesson-occurrences/occ-1/documents/doc-1"
    assert response.json() == {
        "contract": "LessonSourceDocumentAcceptedV1",
        "source_document_id": "doc-1",
        "document_revision_no": 1,
        "job": {"job_id": "lsd-1", "target_kind": "LESSON_SOURCE_DOCUMENT", "state": "succeeded"},
    }
    ((name, kwargs),) = service.calls
    assert name == "attach" and kwargs["idempotency_key"] == "k"
    assert kwargs["occurrence_id"] == "occ-1" and kwargs["payload"].asset_ref == "upl_abc"
    assert kwargs["principal"].subject == "subject-1"


def test_a_document_read_has_a_strong_etag_and_answers_304_for_a_matching_validator(
    served: tuple[TestClient, FakeService],
) -> None:
    client, _service = served
    first = client.get(URL + "/doc-1")
    assert first.status_code == 200 and first.headers["ETag"] == '"2"'
    assert first.headers["Cache-Control"] == "private, no-cache"
    body = first.json()
    assert body["job_ref"] == "lsd-1" and body["warnings"] == ["OCR_NOT_SUPPORTED_PAGES"]
    assert set(body) == set(DOCUMENT)
    again = client.get(URL + "/doc-1", headers={"If-None-Match": '"2"'})
    assert again.status_code == 304 and again.content == b"" and again.headers["ETag"] == '"2"'
    assert client.get(URL + "/doc-1", headers={"If-None-Match": '"1"'}).status_code == 200


def test_a_revision_read_validates_on_the_hash_and_the_review_state(
    served: tuple[TestClient, FakeService],
) -> None:
    client, _service = served
    etag = rules.revision_etag(HASH, "NEEDS_REVIEW")
    first = client.get(URL + "/doc-1/revisions/1")
    assert first.status_code == 200 and first.headers["ETag"] == etag
    assert first.json()["extracted_text"] == "Tiêu đề: Vẽ con mèo"
    again = client.get(URL + "/doc-1/revisions/1", headers={"If-None-Match": etag})
    assert again.status_code == 304
    confirmed = rules.revision_etag(HASH, "CONFIRMED")
    assert (
        client.get(URL + "/doc-1/revisions/1", headers={"If-None-Match": confirmed}).status_code
        == 200
    )


def test_lists_have_no_etag_and_pass_the_page_arguments(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    listing = client.get(URL + "?limit=10&cursor=abc")
    assert listing.status_code == 200 and "ETag" not in listing.headers
    assert listing.json()["next_cursor"] == "n"
    revisions = client.get(URL + "/doc-1/revisions")
    assert revisions.status_code == 200 and "ETag" not in revisions.headers
    assert "extracted_text" not in revisions.text
    first, second = service.calls
    assert first[1]["limit"] == 10 and first[1]["cursor"] == "abc"
    assert second[1]["limit"] == 25 and second[1]["document_id"] == "doc-1"


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "INVALID_FILE_CONTENT"),
        (404, "RESOURCE_NOT_FOUND"),
        (409, "INVALID_STATE_TRANSITION"),
        (409, "RESOURCE_CONFLICT"),
        (413, "LESSON_FILE_TOO_LARGE"),
        (415, "UNSUPPORTED_LESSON_TYPE"),
        (422, "OCR_NOT_SUPPORTED"),
        (422, "ENCRYPTED_DOCUMENT_UNSUPPORTED"),
        (422, "DOCUMENT_PAGE_LIMIT_EXCEEDED"),
        (422, "DOCUMENT_TEXT_LIMIT_EXCEEDED"),
        (422, "UPLOAD_CHECKSUM_MISMATCH"),
        (422, "UPLOAD_INCOMPLETE"),
        (503, "STORAGE_UNAVAILABLE"),
    ],
)
def test_every_refusal_of_a_file_uses_the_conv1_envelope_with_a_vietnamese_message(
    served: tuple[TestClient, FakeService], status: int, code: str
) -> None:
    client, service = served
    service.error = DocumentError(status, code)
    response = client.post(URL, json={"asset_ref": "upl_abc"}, headers=headers())
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code and body["message"] and body["request_id"] == body["correlation_id"]
    assert set(body) >= {"retryable", "retry_after_seconds", "field_errors"}
    assert body["retryable"] is (status == 503)


def test_a_busy_parser_is_a_503_with_retry_after(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    service.error = DocumentError(503, "PROVIDER_UNAVAILABLE", retry_after=5)
    response = client.post(URL, json={"asset_ref": "upl_abc"}, headers=headers())
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json()["retry_after_seconds"] == 5 and response.json()["retryable"] is True


def test_in_scope_refusals_keep_their_status(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    service.error = LessonOccurrenceError(403, "ACTION_NOT_ALLOWED")
    assert client.post(URL, json={"asset_ref": "upl_a"}, headers=headers()).status_code == 403
    service.error = LessonOccurrenceError(400, "INVALID_IDEMPOTENCY_KEY")
    response = client.post(URL, json={"asset_ref": "upl_a"}, headers=headers())
    assert response.status_code == 400 and response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_a_malformed_cursor_is_400_on_the_cursor_field(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = rules.DocumentRuleError("cursor", "INVALID_FORMAT")
    for url in (URL + "?cursor=zzz", URL + "/doc-1/revisions?cursor=zzz"):
        response = client.get(url)
        assert response.status_code == 400
        assert response.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]


def test_reads_refused_by_scope_are_the_uniform_404(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
    bodies = []
    for url in (URL, URL + "/doc-1", URL + "/doc-1/revisions", URL + "/doc-1/revisions/1"):
        response = client.get(url)
        assert response.status_code == 404
        body = response.json()
        bodies.append(
            {
                key: value
                for key, value in body.items()
                if key not in {"request_id", "correlation_id"}
            }
        )
    assert all(item == bodies[0] for item in bodies)


def test_the_routes_need_a_bearer_token() -> None:
    with TestClient(create_app()) as client:
        for response in (
            client.get(URL),
            client.get(URL + "/doc-1"),
            client.get(URL + "/doc-1/revisions"),
            client.get(URL + "/doc-1/revisions/1"),
            client.post(URL, json={"asset_ref": "upl_a"}, headers=headers()),
        ):
            assert response.status_code == 401 and response.json()["code"] == "AUTH_REQUIRED"


def test_a_sibling_path_is_outside_the_family() -> None:
    from sketch2life.interfaces.http import error_envelope as envelope

    assert envelope.is_conv1_path("/v1/lesson-occurrences/occ/documents/doc/revisions/1")
    assert not envelope.is_conv1_path("/v1/lesson-occurrencesfoo/documents")
