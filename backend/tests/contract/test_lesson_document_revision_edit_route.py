"""FEAT-066 T-3c: the Teacher text edit as its own immutable revision (SRS l.546, l.1437, l.1699).

Offline: no database, no storage. The service is replaced by a fake, except for the text-rule cases
that run the real service up to its first database access (the text is validated before anything
else). The module checks the catalog (one new keyed operation; the library version route is
unchanged), the published OpenAPI, request validation in the CONV-1 envelope, the 201 and 200
headers, the stale 409 (``current_version`` and ``ETag``), the request size guard (413 before any
parsing, authorisation or service call) and the 401. Behaviour against PostgreSQL lives in
``tests/integration/lesson_occurrences/test_document_revision_edit_postgres.py``.
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
    DocumentError,
    EditResult,
    OccurrenceDocumentService,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    MAX_REVISION_EDIT_BODY_BYTES,
)
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.routers.lesson_occurrences import get_document_service

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
BASE = "/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions"
EDIT = ("post", BASE)
URL = "/v1/lesson-occurrences/occ-1/documents/doc-1/revisions"
VERSIONS = (
    "post",
    "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions",
)
NOW = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)
TEXT = "Tiêu đề: Vẽ con mèo\nBước 1: vẽ đầu tròn"
HASH = rules.text_sha256(TEXT)
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "organization_ref", "scanner")


def revision_body(number: int = 3, review_state: str = "NEEDS_REVIEW") -> dict[str, Any]:
    return {
        "contract": "LessonDocumentRevisionV2",
        "source_document_id": "doc-1",
        "revision_no": number,
        "origin": "TEACHER_EDIT",
        "review_state": review_state,
        "base_revision_no": number - 1,
        "extracted_text": TEXT,
        "text_hash": HASH,
        "text_length": len(TEXT),
        "parser": None,
        "warnings": [],
        "page_coverage": [],
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
        self.status_code = 201
        self.calls: list[dict[str, Any]] = []

    def edit_revision(self, **kwargs: Any) -> EditResult:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return EditResult(revision_body(), self.status_code, replayed=False)


class NoDatabase:
    """Stands in for the session of the real service: any database call fails the test."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"the text rules must refuse before the database ({name})")


def principal() -> VerifiedPrincipal:
    return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService]]:
    application = create_app()
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return principal()

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_document_service] = lambda: service
    with TestClient(application) as client:
        yield client, service


@pytest.fixture
def served_real_rules() -> Iterator[TestClient]:
    """The real service with no database: only the pre-database text rules can answer."""
    application = create_app()

    async def verified() -> VerifiedPrincipal:
        return principal()

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_document_service] = lambda: OccurrenceDocumentService(
        NoDatabase(),  # type: ignore[arg-type]
        storage=None,
        parser=None,
    )
    with TestClient(application) as client:
        yield client


def headers(key: str | None = "key-1") -> dict[str, str]:
    return {"Idempotency-Key": key} if key is not None else {}


def good(**overrides: Any) -> dict[str, Any]:
    return {"extracted_text": TEXT, "expected_head_revision_no": 2, **overrides}


# ----------------------------------------------------------------------------- catalog
def test_one_new_keyed_operation_and_the_library_version_route_is_unchanged() -> None:
    assert EDIT in MOUNTED_OPERATIONS and EDIT in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    contract = MOUNTED_OPERATIONS[EDIT]
    assert contract["tag"] == "Lesson Occurrences"
    assert contract["authentication"] == "HTTPBearer (bearer)"
    assert contract["handler"] == "lesson_occurrences.py::edit_document_revision"
    statuses = {row["status"] for row in contract["responses"]}
    assert {"200", "201", "400", "401", "403", "404", "409", "413", "503"} == statuses
    # the same path keeps its GET list and the library version create is the library's own route
    assert ("get", BASE) in MOUNTED_OPERATIONS
    library = MOUNTED_OPERATIONS[VERSIONS]
    assert library["tag"] != "Lesson Occurrences"
    assert library["handler"].startswith("lesson_library.py::")
    assert {row["status"] for row in library["responses"]} >= {"201", "400"}


def test_published_contract_documents_the_edit_and_leaks_nothing() -> None:
    application = create_app()
    projected = application.openapi()
    assert not [path for path in projected["paths"] if "/documents" in path]
    spec = application.state.runtime_openapi_schema
    operation = spec["paths"][BASE]["post"]
    assert operation["tags"] == ["Lesson Occurrences"] and operation["security"]
    for status in ("200", "201"):
        assert operation["responses"][status]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/LessonDocumentRevisionV2"
        }
    assert "413" in operation["responses"] and "409" in operation["responses"]
    assert "422" not in operation["responses"]  # validation answers 400, never FastAPI's 422
    parameters = {(p["in"], p["name"]): p for p in operation["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    description = operation["description"]
    for needle in ("STALE_REVISION", "expected_head_revision_no", "13 MiB", "50 revisions"):
        assert needle in description
    schema = spec["components"]["schemas"]["EditDocumentRevisionRequestV1"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"extracted_text", "expected_head_revision_no"}
    assert set(schema["required"]) == {"extracted_text", "expected_head_revision_no"}
    text = schema["properties"]["extracted_text"]
    assert text["minLength"] == 1 and text["maxLength"] == 2_097_152
    head = schema["properties"]["expected_head_revision_no"]
    assert head["minimum"] == 1 and head["type"] == "integer"
    published = json.dumps(operation).lower() + json.dumps(schema).lower()
    for word in STORAGE_WORDS:
        assert word not in published, word


# ----------------------------------------------------------------------------- validation
def test_a_missing_or_malformed_key_is_400_and_nothing_runs(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    missing = client.post(URL, json=good())
    assert missing.status_code == 400 and missing.json()["code"] == "INVALID_REQUEST"
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
    for bad in ("has space", "x" * 129):
        assert client.post(URL, json=good(), headers=headers(bad)).status_code == 400
    assert service.calls == []


@pytest.mark.parametrize(
    ("body", "field", "code"),
    [
        ({"expected_head_revision_no": 1}, "extracted_text", "REQUIRED"),
        ({"extracted_text": TEXT}, "expected_head_revision_no", "REQUIRED"),
        ({"extracted_text": "", "expected_head_revision_no": 1}, "extracted_text", "EMPTY"),
        ({"extracted_text": 5, "expected_head_revision_no": 1}, "extracted_text", "INVALID_TYPE"),
        (
            {"extracted_text": "<2 MiB + 1 characters>", "expected_head_revision_no": 1},
            "extracted_text",
            "TOO_LONG",
        ),
        (
            {"extracted_text": TEXT, "expected_head_revision_no": 0},
            "expected_head_revision_no",
            "OUT_OF_RANGE",
        ),
        (
            {"extracted_text": TEXT, "expected_head_revision_no": 1_000_001},
            "expected_head_revision_no",
            "OUT_OF_RANGE",
        ),
        (
            {"extracted_text": TEXT, "expected_head_revision_no": "2"},
            "expected_head_revision_no",
            "INVALID_TYPE",
        ),
        (
            {"extracted_text": TEXT, "expected_head_revision_no": True},
            "expected_head_revision_no",
            "INVALID_TYPE",
        ),
        (
            {"extracted_text": TEXT, "expected_head_revision_no": 1.5},
            "expected_head_revision_no",
            "INVALID_TYPE",
        ),
    ],
)
def test_invalid_bodies_are_400_with_field_errors_never_422(
    served: tuple[TestClient, FakeService], body: dict[str, Any], field: str, code: str
) -> None:
    client, service = served
    if body.get("extracted_text") == "<2 MiB + 1 characters>":
        body = {**body, "extracted_text": "x" * 2_097_153}
    response = client.post(URL, json=body, headers=headers())
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert {"field": field, "code": code} in payload["field_errors"]
    assert service.calls == []


def test_unknown_body_fields_are_refused(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    for extra in (
        "text_hash",
        "origin",
        "revision_no",
        "base_revision_no",
        "review_state",
        "organization_id",
        "created_by",
        "source_document_id",
    ):
        response = client.post(URL, json=good(**{extra: "x"}), headers=headers())
        assert response.status_code == 400, extra
        assert any(item["code"] == "UNKNOWN_FIELD" for item in response.json()["field_errors"])
    assert service.calls == []


def test_the_text_is_passed_through_exactly_as_sent(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    padded = "  \t dòng 1\r\ndòng 2  \n\n"
    response = client.post(URL, json=good(extracted_text=padded), headers=headers("k"))
    assert response.status_code == 201
    ((kwargs),) = service.calls
    assert kwargs["payload"].extracted_text == padded  # no strip, no normalisation
    assert kwargs["payload"].expected_head_revision_no == 2
    assert kwargs["occurrence_id"] == "occ-1" and kwargs["document_id"] == "doc-1"
    assert kwargs["idempotency_key"] == "k" and kwargs["principal"].subject == "subject-1"


TEXT_CASES = {
    "blank": ("   \n\t\u00a0  ", "EMPTY"),
    "nul": ("co NUL \x00 giua", "INVALID_FORMAT"),
    # 2 MiB + 1 byte with 1,048,577 characters
    "two_byte_over": ("\u00e9" * 1_048_576 + "a", "TOO_LONG"),
    # three bytes each: 2,097,153 bytes
    "three_byte_over": ("\u20ac" * 699_051, "TOO_LONG"),
}


@pytest.mark.parametrize("case", sorted(TEXT_CASES))
def test_text_rules_answer_400_before_any_database_access(
    served_real_rules: TestClient, case: str
) -> None:
    text, code = TEXT_CASES[case]
    response = served_real_rules.post(URL, json=good(extracted_text=text), headers=headers())
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert payload["field_errors"] == [{"field": "extracted_text", "code": code}]


def test_a_lone_surrogate_is_a_400_not_a_500(served_real_rules: TestClient) -> None:
    raw = b'{"extracted_text":"abc\\ud800def","expected_head_revision_no":1}'
    response = served_real_rules.post(
        URL, content=raw, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert any(item["field"] == "extracted_text" for item in payload["field_errors"])
    assert "abc" not in response.text and "ud800" not in response.text  # nothing is echoed


def test_a_text_of_exactly_two_mib_in_bytes_passes_the_rules(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    text = "é" * 1_048_576  # 2,097,152 bytes, 1,048,576 characters
    assert rules.edit_text_problem(text) is None
    response = client.post(URL, json=good(extracted_text=text), headers=headers())
    assert response.status_code == 201
    assert len(service.calls) == 1


# ----------------------------------------------------------------------------- behaviour
def test_a_new_revision_is_201_with_location_and_a_strong_etag(
    served: tuple[TestClient, FakeService],
) -> None:
    client, _service = served
    response = client.post(URL, json=good(), headers=headers())
    assert response.status_code == 201
    assert response.headers["Location"] == f"{URL}/3"
    assert "Content-Location" not in response.headers
    assert response.headers["ETag"] == rules.revision_etag(HASH, "NEEDS_REVIEW")
    assert response.headers["Cache-Control"] == "private, no-cache"
    body = response.json()
    assert body["origin"] == "TEACHER_EDIT" and body["base_revision_no"] == 2
    assert body["parser"] is None and body["warnings"] == [] and body["page_coverage"] == []
    assert body["review_state"] == "NEEDS_REVIEW" and body["extracted_text"] == TEXT


def test_an_unchanged_text_is_200_with_content_location(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.status_code = 200
    response = client.post(URL, json=good(), headers=headers())
    assert response.status_code == 200
    assert response.headers["Content-Location"] == f"{URL}/3"
    assert "Location" not in response.headers
    assert response.headers["ETag"] == rules.revision_etag(HASH, "NEEDS_REVIEW")


def test_the_stale_409_carries_current_version_as_an_integer_and_the_head_etag(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = DocumentError(409, "STALE_REVISION", current_version=4, etag="4")
    response = client.post(URL, json=good(), headers=headers())
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_REVISION" and body["message"]
    assert body["current_version"] == 4 and type(body["current_version"]) is int
    assert response.headers["ETag"] == '"4"'


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (404, "RESOURCE_NOT_FOUND"),
        (403, "ACTION_NOT_ALLOWED"),
        (409, "INVALID_STATE_TRANSITION"),
        (409, "RESOURCE_CONFLICT"),
        (400, "INVALID_IDEMPOTENCY_KEY"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_refusals_use_the_conv1_envelope(
    served: tuple[TestClient, FakeService], status: int, code: str
) -> None:
    client, service = served
    service.error = DocumentError(status, code)
    response = client.post(URL, json=good(), headers=headers())
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code and body["message"] and body["request_id"] == body["correlation_id"]
    assert "current_version" not in body or body["current_version"] is None


def test_the_routes_need_a_bearer_token() -> None:
    with TestClient(create_app()) as client:
        response = client.post(URL, json=good(), headers=headers())
        assert response.status_code == 401 and response.json()["code"] == "AUTH_REQUIRED"


# ----------------------------------------------------------------------------- request size guard
def test_the_body_cap_is_13_mib() -> None:
    assert MAX_REVISION_EDIT_BODY_BYTES == 13 * 1024 * 1024
    # a 2 MiB text of control characters is six bytes a character once JSON-escaped
    assert 6 * rules.MAX_TEXT_BYTES + 64 * 1024 < MAX_REVISION_EDIT_BODY_BYTES


def test_an_oversize_body_is_413_before_parsing_authorisation_or_the_service(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    body = b'{"extracted_text":"' + b"a" * MAX_REVISION_EDIT_BODY_BYTES + b'","x":1}'
    response = client.post(
        URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 413
    payload = response.json()
    assert payload["code"] == "MEDIA_TOO_LARGE" and payload["message"]
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert service.calls == []


def test_an_oversize_chunked_body_is_413_too(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    chunk = b"a" * (1024 * 1024)

    def stream() -> Iterator[bytes]:
        yield b'{"extracted_text":"'
        for _ in range(14):
            yield chunk
        yield b'","expected_head_revision_no":1}'

    response = client.post(
        URL, content=stream(), headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["code"] == "MEDIA_TOO_LARGE"
    assert service.calls == []


def test_a_body_exactly_at_the_cap_is_not_a_413(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    prefix, suffix = b'{"extracted_text":"', b'","expected_head_revision_no":1}'
    filler = MAX_REVISION_EDIT_BODY_BYTES - len(prefix) - len(suffix)
    body = prefix + b"a" * filler + suffix
    assert len(body) == MAX_REVISION_EDIT_BODY_BYTES
    response = client.post(
        URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    # past the transport guard the text is simply too long: the field rule answers
    assert response.status_code == 400
    assert response.json()["field_errors"] == [{"field": "extracted_text", "code": "TOO_LONG"}]
    assert service.calls == []


def test_a_valid_two_mib_text_of_control_characters_fits_under_the_cap(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    text = "\u0001" * (rules.MAX_TEXT_BYTES)  # six bytes each once escaped: about 12 MiB
    body = json.dumps({"extracted_text": text, "expected_head_revision_no": 1}).encode()
    assert 12 * 1024 * 1024 < len(body) <= MAX_REVISION_EDIT_BODY_BYTES
    response = client.post(
        URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 201
    assert len(service.calls) == 1


def test_the_guard_leaves_other_routes_alone(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    big = b"a" * (MAX_REVISION_EDIT_BODY_BYTES + 1)
    response = client.post(
        "/v1/lesson-occurrences/occ-1/documents",
        content=big,
        headers={**headers(), "Content-Type": "application/json"},
    )
    assert response.status_code != 413
    assert service.calls == []
