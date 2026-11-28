"""FEAT-066 T-4b1: the Teacher child selection routes (SRS l.341-352, l.1697-1699, AC-56).

Offline: no database. The service is replaced by a fake. The module checks the catalog (three
operations; the two commands are keyed), the published OpenAPI schema (a closed field set that has
no seed, index, name list or reason per child), headers (strong ETag, ``no-store``, ``If-Match``),
request validation in the CONV-1 envelope, the error mapping with no child field in any refusal
body, and the 304 rule (never for a body that carries child data). Behaviour against PostgreSQL
lives in ``tests/integration/lesson_occurrences/test_child_selection_postgres.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.child_selection import SelectionResult
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.routers.lesson_occurrences import (
    get_child_selection_service,
    get_transfer_guards,
)

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
BASE = "/v1/lesson-occurrences/{occurrence_id}/child-selections"
ONE = BASE + "/{selection_id}"
CONFIRMATION = ONE + "/confirmation"
URL = "/v1/lesson-occurrences/occ-1/child-selections"
ONE_URL = URL + "/sel-1"
CONFIRM_URL = ONE_URL + "/confirmation"
NOW = datetime(2026, 11, 21, 3, 0, tzinfo=UTC)
HASH = "a" * 64
CHILD_WORDS = ("seed", "draw_index", "candidate_names", "excluded", "reason")


class _NoOpTransferGuards:
    def create(self, _principal: VerifiedPrincipal, _class_id: str) -> None:
        pass

    def occurrence_write(self, _principal: VerifiedPrincipal, _occurrence_id: str) -> None:
        pass


def selection_json(
    *,
    state: str = "OPEN",
    revision: int | None = 1,
    child: bool = True,
    selection_id: str | None = "sel-1",
) -> dict[str, Any]:
    return {
        "contract": "ChildSelectionV1",
        "selection_id": selection_id,
        "occurrence_id": "occ-1",
        "outcome": "SELECTED" if state != "STOPPED" else "NO_ELIGIBLE_CHILD",
        "state": state,
        "revision": revision,
        "draw_no": 1,
        "reselect_available": True,
        "issued_at": NOW,
        "expires_at": NOW,
        "confirmation_expires_at": None,
        "selection_sha256": HASH,
        "plan": {"revision_no": 1, "plan_hash": HASH},
        "consumed_run_ref": None,
        "child": (
            {"profile_id": "child-1", "display_name": "Synthetic An", "age_months": 60}
            if child
            else None
        ),
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
        self.body = selection_json()
        self.status_code = 201
        self.stored_state: str | None = "OPEN"

    def _answer(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error

    def select(self, **kwargs: Any) -> SelectionResult:
        self._answer("select", kwargs)
        return SelectionResult(self.body, self.status_code)

    def get(self, **kwargs: Any) -> SelectionResult:
        self._answer("get", kwargs)
        return SelectionResult(self.body, 200, stored_state=self.stored_state)

    def confirm(self, **kwargs: Any) -> SelectionResult:
        self._answer("confirm", kwargs)
        return SelectionResult(self.body, 200)


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService]]:
    application = create_app()
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_child_selection_service] = lambda: service
    application.dependency_overrides[get_transfer_guards] = lambda: _NoOpTransferGuards()
    with TestClient(application) as client:
        yield client, service


def keyed(key: str | None = "key-1", **extra: str) -> dict[str, str]:
    headers = dict(extra)
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def confirm_headers(match: str | None = '"1"', key: str | None = "key-2") -> dict[str, str]:
    headers = keyed(key)
    if match is not None:
        headers["If-Match"] = match
    return headers


# ----------------------------------------------------------------------------- catalog
def test_catalog_lists_three_operations_and_two_are_keyed() -> None:
    for key in (("post", BASE), ("get", ONE), ("post", CONFIRMATION)):
        assert key in MOUNTED_OPERATIONS
        assert key in SRS_V22_INCLUDED_OPERATIONS
    assert ("post", BASE) in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert ("post", CONFIRMATION) in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert ("get", ONE) not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS


def test_published_schema_is_closed_and_has_no_seed_index_or_reason() -> None:
    schema = create_app().openapi()["components"]["schemas"]["ChildSelectionV1"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {
        "contract",
        "selection_id",
        "occurrence_id",
        "outcome",
        "state",
        "revision",
        "draw_no",
        "reselect_available",
        "issued_at",
        "expires_at",
        "confirmation_expires_at",
        "selection_sha256",
        "plan",
        "consumed_run_ref",
        "child",
    }
    names = " ".join(schema["properties"]).lower()
    assert not any(word in names for word in CHILD_WORDS)
    child = create_app().openapi()["components"]["schemas"]["ChildSelectionChildV1"]
    assert set(child["properties"]) == {"profile_id", "display_name", "age_months"}


def test_runtime_routes_declare_the_headers() -> None:
    paths = create_app().openapi()["paths"]
    post = paths[BASE]["post"]
    assert {p["name"] for p in post["parameters"] if p["in"] == "header"} >= {"Idempotency-Key"}
    confirm = paths[CONFIRMATION]["post"]
    assert {p["name"] for p in confirm["parameters"] if p["in"] == "header"} >= {
        "Idempotency-Key",
        "If-Match",
    }
    assert set(paths[ONE]) == {"get"}


# ----------------------------------------------------------------------------- the selection POST
def test_post_201_headers_and_arguments(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    response = client.post(URL, headers=keyed(), json={})
    assert response.status_code == 201
    assert response.headers["ETag"] == '"1"'
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Location"] == URL + "/sel-1"
    assert response.json()["child"]["display_name"] == "Synthetic An"
    name, kwargs = service.calls[0]
    assert name == "select"
    assert kwargs["occurrence_id"] == "occ-1" and kwargs["idempotency_key"] == "key-1"


def test_post_without_a_body_is_accepted_and_200_has_no_location(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.status_code = 200
    service.body = selection_json(state="STOPPED", revision=None, child=False, selection_id=None)
    response = client.post(URL, headers=keyed())
    assert response.status_code == 200
    assert "Location" not in response.headers and "ETag" not in response.headers
    assert response.json()["selection_id"] is None
    assert response.json()["child"] is None


@pytest.mark.parametrize(
    ("headers", "body", "field"),
    [
        (keyed(None), {}, "Idempotency-Key"),
        (keyed("bad key"), {}, "Idempotency-Key"),
        (keyed(), {"child_id": "child-1"}, None),
        (keyed(), {"seed": 7}, None),
    ],
)
def test_post_rejects_bad_requests_before_the_service(
    served: tuple[TestClient, FakeService],
    headers: dict[str, str],
    body: dict[str, Any],
    field: str | None,
) -> None:
    client, service = served
    response = client.post(URL, headers=headers, json=body)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    if field is not None:
        assert response.json()["field_errors"][0]["field"] == field
    assert service.calls == []


# ----------------------------------------------------------------------------- the GET
def test_get_200_headers_and_never_304_with_a_child(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.get(ONE_URL)
    assert response.status_code == 200
    assert (
        response.headers["ETag"] == '"1"'
        and response.headers["Cache-Control"] == "private, no-store"
    )
    # child data present: the strong ETag never short-circuits (BR-34).
    assert client.get(ONE_URL, headers={"If-None-Match": '"1"'}).status_code == 200
    # T4B1-IR-01: a stored OPEN or CONFIRMED row whose COMPUTED state is STALE or EXPIRED (the child
    # left the candidate set, or the 900 s passed) keeps its stored revision: never 304, so the
    # client drops the child it still shows.
    for computed in ("STALE", "EXPIRED"):
        service.body = selection_json(state=computed, child=False)
        for stored in ("OPEN", "CONFIRMED"):
            service.stored_state = stored
            assert client.get(ONE_URL, headers={"If-None-Match": '"1"'}).status_code == 200
    # a stored immutable row without a child may be answered 304
    service.stored_state = "STALE"
    service.body = selection_json(state="STALE", child=False)
    stale = client.get(ONE_URL, headers={"If-None-Match": '"1"'})
    assert stale.status_code == 304 and stale.headers["ETag"] == '"1"'
    assert stale.content == b""
    assert client.get(ONE_URL, headers={"If-None-Match": '"2"'}).status_code == 200


# ----------------------------------------------------------------------------- the confirmation
def test_confirm_sends_revision_and_hash(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    service.body = selection_json(state="CONFIRMED", revision=2)
    response = client.post(
        CONFIRM_URL, headers=confirm_headers('"1"'), json={"expected_selection_sha256": HASH}
    )
    assert response.status_code == 200
    assert (
        response.headers["ETag"] == '"2"'
        and response.headers["Cache-Control"] == "private, no-store"
    )
    _name, kwargs = service.calls[0]
    assert kwargs["expected_revision"] == 1 and kwargs["expected_sha256"] == HASH
    assert kwargs["selection_id"] == "sel-1" and kwargs["idempotency_key"] == "key-2"


@pytest.mark.parametrize(
    ("headers", "body", "field", "code"),
    [
        (confirm_headers(None), {"expected_selection_sha256": HASH}, "If-Match", "REQUIRED"),
        (
            confirm_headers('W/"1"'),
            {"expected_selection_sha256": HASH},
            "If-Match",
            "INVALID_FORMAT",
        ),
        (confirm_headers('"0"'), {"expected_selection_sha256": HASH}, "If-Match", "INVALID_FORMAT"),
        (confirm_headers("1"), {"expected_selection_sha256": HASH}, "If-Match", "INVALID_FORMAT"),
        (confirm_headers(key=None), {"expected_selection_sha256": HASH}, "Idempotency-Key", None),
        (confirm_headers(), {"expected_selection_sha256": "A" * 64}, None, None),
        (confirm_headers(), {"expected_selection_sha256": HASH, "child_id": "x"}, None, None),
        (confirm_headers(), {}, None, None),
    ],
)
def test_confirm_rejects_bad_requests_before_the_service(
    served: tuple[TestClient, FakeService],
    headers: dict[str, str],
    body: dict[str, Any],
    field: str | None,
    code: str | None,
) -> None:
    client, service = served
    response = client.post(CONFIRM_URL, headers=headers, json=body)
    assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST"
    if field is not None and code is not None:
        assert response.json()["field_errors"] == [{"field": field, "code": code}]
    assert service.calls == []


# ----------------------------------------------------------------------------- refusals
@pytest.mark.parametrize(
    ("status", "code"),
    [
        (403, "ACTION_NOT_ALLOWED"),
        (404, "RESOURCE_NOT_FOUND"),
        (409, "INVALID_STATE_TRANSITION"),
        (409, "SAMPLE_VIDEO_ALREADY_EXISTS"),
        (422, "LESSON_PLAN_NOT_APPROVED"),
        (400, "INVALID_IDEMPOTENCY_KEY"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_refusals_use_the_envelope_and_carry_no_child_data(
    served: tuple[TestClient, FakeService], status: int, code: str
) -> None:
    client, service = served
    service.error = LessonOccurrenceError(status, code)
    for response in (
        client.post(URL, headers=keyed(), json={}),
        client.get(ONE_URL),
        client.post(
            CONFIRM_URL, headers=confirm_headers(), json={"expected_selection_sha256": HASH}
        ),
    ):
        body = response.json()
        assert response.status_code == status and body["code"] == code
        assert body["message"] and body["correlation_id"]
        text = response.text.lower()
        assert "display_name" not in text and "age_months" not in text and "profile_id" not in text
        assert "synthetic" not in text


def test_stale_revision_carries_current_version(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    service.error = LessonOccurrenceError(409, "STALE_REVISION", current_version=3)
    response = client.post(
        CONFIRM_URL, headers=confirm_headers(), json={"expected_selection_sha256": HASH}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION" and response.json()["current_version"] == 3


def test_unauthenticated_calls_are_401() -> None:
    application = create_app()
    with TestClient(application) as client:
        assert client.post(URL, headers=keyed(), json={}).status_code == 401
        assert client.get(ONE_URL).status_code == 401
