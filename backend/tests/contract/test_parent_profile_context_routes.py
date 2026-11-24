"""FEAT-066 goal v4 T-12a: the Parent context-entry routes and the optional selection (offline).

``GET`` and ``POST /v1/parent/profiles/{profile_id}/context-entries`` use the Parent profile error
envelope; the optional ``selected_context_entry_ids`` of ``POST /v1/story-runs/{run_id}/
context-confirmation`` uses the story envelope. PostgreSQL behaviour is in
``tests/integration/test_parent_profile_context_postgres.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profile_context import ParentContextEntryPage
from sketch2life.application.ports.parent_profiles import ParentCommandResult
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.domain.parent_profile_context import ContextEntryDraft
from sketch2life.domain.parent_profiles import ParentProfileError
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.identity.firebase_token_verifier import FirebaseTokenVerifier
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_profile_context_service,
    get_parent_role_reader,
)

PROFILE_ID = "a3a878cf-7b93-4f25-a71d-6a3b09351a11"
FOREIGN_PROFILE_ID = "00000000-0000-0000-0000-000000000001"
RUN_ID = "22222222-2222-4222-8222-222222222222"
ENTRY = {
    "context_entry_id": "b3a878cf-7b93-4f25-a71d-6a3b09351a12",
    "entry_kind": "OBSERVATION",
    "short_text": "thich ve ca",
    "source_kind": "PARENT_NOTE",
    "approximate_date": "2026-05-01",
    "created_at": "2026-11-23T10:00:00+00:00",
}
BASE_PATH = f"/v1/parent/profiles/{PROFILE_ID}/context-entries"
PRINCIPAL = VerifiedPrincipal("subject-1", "issuer-1", frozenset())
HEADERS = {"Authorization": "Bearer synthetic-token", "X-Request-ID": "parent-entry-1"}
VALID_BODY = {
    "entry_kind": "OBSERVATION",
    "short_text": "thich ve ca",
    "source_kind": "PARENT_NOTE",
    "source_ref": "note-1",
    "approximate_date": "2026-05-01",
}


class _EntryService:
    def __init__(self) -> None:
        self.owned: list[UUID] = []
        self.lists: list[tuple[UUID, int, str | None]] = []
        self.creates: list[tuple[UUID, ContextEntryDraft, str]] = []

    def assert_profile_owned(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> None:
        self.owned.append(profile_id)
        if principal.issuer != "issuer-1" or str(profile_id) == FOREIGN_PROFILE_ID:
            raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")

    def list_context_entries(
        self, *, principal: VerifiedPrincipal, profile_id: UUID, limit: int, cursor: str | None
    ) -> ParentContextEntryPage:
        del principal
        self.lists.append((profile_id, limit, cursor))
        return ParentContextEntryPage(items=[ENTRY], next_cursor="next-1")

    def create_context_entry(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        entry: ContextEntryDraft,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        del principal, request_id
        self.creates.append((profile_id, entry, idempotency_key))
        return ParentCommandResult(201, {"context_entry": ENTRY})


class _MismatchService(_EntryService):
    def create_context_entry(self, **kwargs: Any) -> ParentCommandResult:
        raise ParentProfileError(
            400,
            "INVALID_IDEMPOTENCY_KEY",
            "The idempotency key was already used for a different request",
        )


class _ReplayService(_EntryService):
    def create_context_entry(self, **kwargs: Any) -> ParentCommandResult:
        self.creates.append((kwargs["profile_id"], kwargs["entry"], kwargs["idempotency_key"]))
        return ParentCommandResult(201, {"context_entry": ENTRY, "request_id": "stored-1"})


class _Role:
    def __init__(self, active: bool = True) -> None:
        self.active = active

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        del principal
        return self.active


class _StoryService:
    def __init__(self) -> None:
        self.confirmed: list[dict[str, Any]] = []
        self.error: ParentStoryRunError | None = None

    def confirm_context(self, **kwargs: Any) -> Any:
        self.confirmed.append(kwargs)
        raise self.error or ParentStoryRunError(409, "INVALID_STATE_TRANSITION")


class _FakeDb:
    def get(self, _model: object, _identity: object) -> SimpleNamespace:
        return SimpleNamespace(
            account_id="account-1", issuer="issuer-1", account_role="parent", state="active"
        )


@pytest.fixture
def entry_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, _EntryService]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-parent-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    application = app_module.create_app()
    application.state.be1_runtime.identity_verifier = FirebaseTokenVerifier(settings)
    service = _EntryService()
    application.dependency_overrides[get_parent_profile_context_service] = lambda: service
    application.dependency_overrides[get_parent_role_reader] = lambda: _Role()
    application.dependency_overrides[get_parent_principal] = lambda: PRINCIPAL
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client, service
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _overrides(client: TestClient) -> dict[Any, Any]:
    return cast(FastAPI, client.app).dependency_overrides


def _assert_error(response: Any, *, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    body = response.json()
    assert body["code"] == code
    assert body["request_id"] == body["correlation_id"] == response.headers["X-Request-ID"]
    return cast(dict[str, Any], body)


def test_context_entry_routes_return_exact_shapes(
    entry_client: tuple[TestClient, _EntryService],
) -> None:
    client, service = entry_client
    listed = client.get(BASE_PATH, headers=HEADERS)
    assert listed.status_code == 200
    assert listed.json() == {"context_entries": [ENTRY], "next_cursor": "next-1", "limit": 25}
    assert set(listed.json()["context_entries"][0]) == {
        "context_entry_id",
        "entry_kind",
        "short_text",
        "source_kind",
        "approximate_date",
        "created_at",
    }  # no source_ref, no created_by
    assert listed.headers["Cache-Control"] == "private, no-store"
    created = client.post(
        BASE_PATH, headers={**HEADERS, "Idempotency-Key": "create-1"}, json=VALID_BODY
    )
    assert created.status_code == 201
    assert created.json() == {"context_entry": ENTRY}
    assert created.headers["Cache-Control"] == "private, no-store"
    assert created.headers["X-Request-ID"] == "parent-entry-1"
    profile_id, draft, key = service.creates[0]
    assert (str(profile_id), key) == (PROFILE_ID, "create-1")
    assert draft.source_ref == "note-1" and draft.approximate_date is not None
    assert draft.approximate_date.isoformat() == "2026-05-01"


def test_list_enforces_cursor_default_max_unknown_query(
    entry_client: tuple[TestClient, _EntryService],
) -> None:
    client, service = entry_client
    assert client.get(BASE_PATH, headers=HEADERS).json()["limit"] == 25
    assert client.get(BASE_PATH + "?limit=100&cursor=abc", headers=HEADERS).status_code == 200
    assert service.lists[-1][1:] == (100, "abc")
    count = len(service.lists)
    for query, field, code in (
        ("limit=0", "limit", "OUT_OF_RANGE"),
        ("limit=101", "limit", "OUT_OF_RANGE"),
        ("limit=x", "limit", "INVALID_TYPE"),
        ("limit=1&limit=2", "limit", "INVALID_FORMAT"),
        ("cursor=a&cursor=b", "cursor", "INVALID_FORMAT"),
        ("unknown=1", "<unknown>", "UNKNOWN_FIELD"),
    ):
        response = client.get(f"{BASE_PATH}?{query}", headers=HEADERS)
        body = _assert_error(response, status=400, code="INVALID_REQUEST")
        assert {"field": field, "code": code} in body["field_errors"], query
    assert len(service.lists) == count  # nothing reached the service


def test_create_requires_one_visible_ascii_key_and_strict_body(
    entry_client: tuple[TestClient, _EntryService],
) -> None:
    client, service = entry_client
    no_key = client.post(BASE_PATH, headers=HEADERS, json=VALID_BODY)
    body = _assert_error(no_key, status=400, code="INVALID_REQUEST")
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in body["field_errors"]
    bad_key = client.post(
        BASE_PATH, headers={**HEADERS, "Idempotency-Key": "bad key"}, json=VALID_BODY
    )
    body = _assert_error(bad_key, status=400, code="INVALID_REQUEST")
    assert {"field": "Idempotency-Key", "code": "INVALID_FORMAT"} in body["field_errors"]
    too_long = client.post(
        BASE_PATH, headers={**HEADERS, "Idempotency-Key": "k" * 129}, json=VALID_BODY
    )
    _assert_error(too_long, status=400, code="INVALID_REQUEST")
    keyed = {**HEADERS, "Idempotency-Key": "create-2"}
    for payload, field, code in (
        ({**VALID_BODY, "extra": 1}, "<unknown>", "UNKNOWN_FIELD"),
        ({**VALID_BODY, "entry_kind": "DIAGNOSIS"}, "entry_kind", "INVALID_FORMAT"),
        ({**VALID_BODY, "short_text": "   "}, "short_text", "EMPTY"),
        ({**VALID_BODY, "short_text": "a" * 501}, "short_text", "TOO_LONG"),
        ({**VALID_BODY, "short_text": "a\u0000b"}, "short_text", "INVALID_FORMAT"),
        ({**VALID_BODY, "short_text": "a\u0001b"}, "short_text", "INVALID_FORMAT"),
        ({**VALID_BODY, "source_ref": "r\u0000"}, "source_ref", "INVALID_FORMAT"),
        ({**VALID_BODY, "source_kind": "lower"}, "source_kind", "INVALID_FORMAT"),
        ({**VALID_BODY, "approximate_date": "2026-13-01"}, "approximate_date", "INVALID_FORMAT"),
        ({k: v for k, v in VALID_BODY.items() if k != "entry_kind"}, "entry_kind", "REQUIRED"),
    ):
        body = _assert_error(
            client.post(BASE_PATH, headers=keyed, json=payload), status=400, code="INVALID_REQUEST"
        )
        assert {"field": field, "code": code} in body["field_errors"], payload
    assert client.post(BASE_PATH, headers=keyed, content=b"{not json").status_code == 400
    assert service.creates == []  # no write for any refusal
    # a minimal body is valid: only the three required fields
    minimal = {k: VALID_BODY[k] for k in ("entry_kind", "short_text", "source_kind")}
    assert client.post(BASE_PATH, headers=keyed, json=minimal).status_code == 201
    assert (
        service.creates[0][1].source_ref is None and service.creates[0][1].approximate_date is None
    )


def test_wrong_role_and_foreign_resources_use_the_uniform_404(
    entry_client: tuple[TestClient, _EntryService],
) -> None:
    client, service = entry_client
    keyed = {**HEADERS, "Idempotency-Key": "create-3"}
    foreign = f"/v1/parent/profiles/{FOREIGN_PROFILE_ID}/context-entries"
    for response in (
        client.get(foreign, headers=HEADERS),
        client.post(foreign, headers=keyed, json=VALID_BODY),
    ):
        _assert_error(response, status=404, code="PROFILE_NOT_FOUND")
    _overrides(client)[get_parent_role_reader] = lambda: _Role(active=False)
    for response in (
        client.get(BASE_PATH, headers=HEADERS),
        client.post(BASE_PATH, headers=keyed, json=VALID_BODY),
    ):
        _assert_error(response, status=404, code="PROFILE_NOT_FOUND")
    assert service.creates == [] and service.lists == []
    # an invalid profile id is a 400 before any lookup
    invalid = client.get("/v1/parent/profiles/not-a-uuid/context-entries", headers=HEADERS)
    body = _assert_error(invalid, status=400, code="INVALID_REQUEST")
    assert {"field": "profile_id", "code": "INVALID_FORMAT"} in body["field_errors"]
    # the owner lookup runs before the body: a foreign profile with a bad body is still 404
    _overrides(client)[get_parent_role_reader] = lambda: _Role()
    _assert_error(
        client.post(foreign, headers=keyed, json={"x": 1}), status=404, code="PROFILE_NOT_FOUND"
    )


def test_create_replay_and_key_mismatch(entry_client: tuple[TestClient, _EntryService]) -> None:
    client, _service = entry_client
    keyed = {**HEADERS, "Idempotency-Key": "create-4"}
    _overrides(client)[get_parent_profile_context_service] = _ReplayService
    replay = client.post(BASE_PATH, headers=keyed, json=VALID_BODY)
    assert replay.status_code == 201
    assert replay.headers["X-Request-ID"] == "stored-1"  # the stored request id of the first call
    _overrides(client)[get_parent_profile_context_service] = _MismatchService
    mismatch = client.post(BASE_PATH, headers=keyed, json=VALID_BODY)
    _assert_error(mismatch, status=400, code="INVALID_IDEMPOTENCY_KEY")


def test_confirmation_accepts_the_legacy_and_the_selected_body(
    entry_client: tuple[TestClient, _EntryService], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _service = entry_client
    story = _StoryService()
    monkeypatch.setattr(story_routes, "_service", lambda _db: story)
    _overrides(client)[get_verified_adult] = lambda: PRINCIPAL
    _overrides(client)[get_db] = _FakeDb
    path = f"/v1/story-runs/{RUN_ID}/context-confirmation"
    base = {"expected_context_revision": 1, "context_snapshot_sha256": "a" * 64, "confirmed": True}
    headers = {"Idempotency-Key": "confirm-1", "X-Request-ID": "story-confirm-1"}
    first = UUID("11111111-1111-4111-8111-111111111111")
    second = UUID("33333333-3333-4333-8333-333333333333")
    for body, expected in (
        (base, None),
        ({**base, "selected_context_entry_ids": None}, None),
        ({**base, "selected_context_entry_ids": []}, []),
        ({**base, "selected_context_entry_ids": [str(first), str(second)]}, [first, second]),
    ):
        response = client.post(path, headers=headers, json=body)
        assert response.status_code == 409  # the fake service stops after recording the call
        assert story.confirmed[-1]["selected_context_entry_ids"] == expected
    for bad in (
        [str(first), str(first)],
        [str(UUID(int=n + 1)) for n in range(11)],
        ["not-a-uuid"],
        "x",
    ):
        response = client.post(
            path, headers=headers, json={**base, "selected_context_entry_ids": bad}
        )
        assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST", bad
    assert len(story.confirmed) == 4  # the invalid bodies never reached the service
    # a plain field error of the service reaches the story envelope (the Teacher refusal)
    story.error = ParentStoryRunError(
        400,
        "INVALID_REQUEST",
        field_errors=[{"field": "selected_context_entry_ids", "code": "NOT_ALLOWED"}],
    )
    refused = client.post(
        path, headers=headers, json={**base, "selected_context_entry_ids": [str(first)]}
    )
    assert refused.status_code == 400
    body = refused.json()
    assert body["code"] == "INVALID_REQUEST"
    assert [(item["field"], item["code"]) for item in body["field_errors"]] == [
        ("selected_context_entry_ids", "NOT_ALLOWED")
    ]


def test_catalog_projection_and_runtime_schema_entries(
    entry_client: tuple[TestClient, _EntryService],
) -> None:
    client, _service = entry_client
    template = "/v1/parent/profiles/{profile_id}/context-entries"
    for method in ("get", "post"):
        assert (method, template) in MOUNTED_OPERATIONS
        assert (method, template) in SRS_V22_INCLUDED_OPERATIONS
    cast(FastAPI, client.app).openapi()
    document = cast(FastAPI, client.app).state.runtime_openapi_schema
    operations = document["paths"][template]
    assert operations["get"]["operationId"] == "listParentProfileContextEntriesV1"
    assert operations["post"]["operationId"] == "createParentProfileContextEntryV1"
    schemas = document["components"]["schemas"]
    assert {"CreateParentContextEntryRequest", "ParentContextEntryView"} <= set(schemas)
    assert "source_ref" not in schemas["ParentContextEntryView"]["properties"]
    assert "created_by" not in schemas["ParentContextEntryView"]["properties"]
    assert set(schemas["CreateParentContextEntryRequest"]["required"]) == {
        "entry_kind",
        "short_text",
        "source_kind",
    }
    assert schemas["CreateParentContextEntryRequest"]["additionalProperties"] is False
    get_statuses = {row["status"] for row in MOUNTED_OPERATIONS[("get", template)]["responses"]}
    post_statuses = {row["status"] for row in MOUNTED_OPERATIONS[("post", template)]["responses"]}
    assert "200" in get_statuses and "201" in post_statuses
    assert {"400", "401", "404", "409", "503"} <= get_statuses & post_statuses
    confirmation = MOUNTED_OPERATIONS[("post", "/v1/story-runs/{run_id}/context-confirmation")]
    assert "selected_context_entry_ids" in confirmation["request_inputs"]
    assert "Teacher" in confirmation["purpose"]
