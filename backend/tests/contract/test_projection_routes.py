"""FEAT-066 T-5a: the class projection routes (SRS l.396, l.552-555, l.777, l.1449, l.1661-1662,
l.1691-1693).

Offline: no database. The service is replaced by a fake. The module checks the catalog (two
operations; the confirmation is keyed), the published OpenAPI schemas (closed field sets, no name,
no storage location, no token in the receipt), headers (strong ``ETag``, ``no-store``,
``If-Match``), request validation in the CONV-1 envelope, the error mapping, the token route (a
real codec, the signed claims, 503 without a secret AFTER the Lesson checks) and the order of the
guards of the stream route. Behaviour against PostgreSQL lives in
``tests/integration/lesson_occurrences/test_projection_postgres.py``; the Parent bytes of the
stream route are pinned by ``test_teacher_run_video_contract.py`` (golden recorded at HEAD).
"""

from __future__ import annotations

import inspect
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.projection import (
    ProjectionGrantFacts,
    ProjectionResult,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.story_video.playback_tokens import PlaybackTokenCodec
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.routers import story_run_video
from sketch2life.interfaces.http.routers.lesson_occurrences import get_projection_service

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
CONFIRMATION = "/v1/lesson-occurrences/{occurrence_id}/projection-confirmation"
GRANT_PATH = "/v1/lesson-occurrences/{occurrence_id}/projection-playback-token"
OCCURRENCE = str(uuid4())
RUN = str(uuid4())
GENERATION = str(uuid4())
CONFIRM_URL = f"/v1/lesson-occurrences/{OCCURRENCE}/projection-confirmation"
GRANT_URL = f"/v1/lesson-occurrences/{OCCURRENCE}/projection-playback-token"
NOW = datetime(2026, 11, 22, 3, 0, tzinfo=UTC)
HASH = "a" * 64
BODY = {"run_id": RUN, "generation_id": GENERATION, "audience": "CLASS", "use": "CLASS_PROJECTION"}


def receipt(revision: int = 4) -> dict[str, Any]:
    return {
        "contract": "ClassProjectionConfirmationV1",
        "occurrence_id": OCCURRENCE,
        "run_id": RUN,
        "generation_id": GENERATION,
        "audience": "CLASS",
        "use": "CLASS_PROJECTION",
        "confirmed_at": NOW.isoformat(),
        "confirmed_by_ref": "account-1",
        "assignment": {"class_revision": 2},
        "plan": {"revision_no": 1, "plan_hash": HASH, "is_current": True},
        "occurrence_revision": revision,
        "sample_video": {"slot_state": "CLAIMED", "claimed_at": NOW.isoformat(), "run_ref": RUN},
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
        self.revision = 4
        self.grant_facts = ProjectionGrantFacts(
            run_id=RUN,
            generation_id=GENERATION,
            occurrence_id=OCCURRENCE,
            confirmed_ms=1_795_341_600_123,
            actor_scope_ref="scope-of-the-caller",
        )

    def _answer(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error

    def confirm(self, **kwargs: Any) -> ProjectionResult:
        self._answer("confirm", kwargs)
        return ProjectionResult(receipt(self.revision), False)

    def grant(self, **kwargs: Any) -> ProjectionGrantFacts:
        self._answer("grant", kwargs)
        return self.grant_facts


class _Clock:
    def __call__(self) -> float:
        return 1_900_000_000.0


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService, PlaybackTokenCodec]]:
    application = create_app()
    service = FakeService()
    codec = PlaybackTokenCodec(
        active_key_id="k1", keys={"k1": b"synthetic-t5a-secret-0123456789abcdef"}, clock=_Clock()
    )
    application.state.story_playback_tokens = codec

    async def verified() -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_projection_service] = lambda: service
    with TestClient(application) as client:
        yield client, service, codec


def keyed(key: str | None = "key-1", match: str | None = '"3"') -> dict[str, str]:
    headers: dict[str, str] = {}
    if key is not None:
        headers["Idempotency-Key"] = key
    if match is not None:
        headers["If-Match"] = match
    return headers


# ----------------------------------------------------------------------------- catalog
def test_the_catalog_lists_both_operations_and_only_the_confirmation_is_keyed() -> None:
    for operation in (("post", CONFIRMATION), ("post", GRANT_PATH)):
        assert operation in MOUNTED_OPERATIONS
        assert operation in SRS_V22_INCLUDED_OPERATIONS
    assert ("post", CONFIRMATION) in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert ("post", GRANT_PATH) not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert "If-Match" in MOUNTED_OPERATIONS[("post", CONFIRMATION)]["request_inputs"]


def test_the_published_schemas_are_closed_and_the_receipt_has_no_name_or_token() -> None:
    document = create_app().openapi()
    schemas = document["components"]["schemas"]
    confirmation = schemas["ClassProjectionConfirmationV1"]
    assert confirmation["additionalProperties"] is False
    assert set(confirmation["properties"]) == {
        "contract",
        "occurrence_id",
        "run_id",
        "generation_id",
        "audience",
        "use",
        "confirmed_at",
        "confirmed_by_ref",
        "assignment",
        "plan",
        "occurrence_revision",
        "sample_video",
    }
    assert set(schemas["ProjectionPlanV1"]["properties"]) == {
        "revision_no",
        "plan_hash",
        "is_current",
    }
    assert set(schemas["ProjectionAssignmentV1"]["properties"]) == {"class_revision"}
    assert set(schemas["ProjectionSampleVideoV1"]["properties"]) == {
        "slot_state",
        "claimed_at",
        "run_ref",
    }
    request = schemas["ProjectionConfirmationRequestV1"]
    assert request["additionalProperties"] is False
    assert set(request["required"]) == {"run_id", "generation_id", "audience", "use"}
    assert request["properties"]["audience"]["const"] == "CLASS"
    assert request["properties"]["use"]["const"] == "CLASS_PROJECTION"
    token = schemas["ProjectionPlaybackTokenV1"]
    assert token["additionalProperties"] is False
    assert set(token["properties"]) == {
        "contract",
        "token",
        "expires_at",
        "stream_path",
        "media_type",
    }
    names = " ".join(confirmation["properties"]).lower()
    for word in ("token", "url", "bucket", "key", "name", "child", "profile", "asset", "seed"):
        assert word not in names, word


def test_the_runtime_routes_declare_their_headers_and_only_post() -> None:
    paths = create_app().openapi()["paths"]
    post = paths[CONFIRMATION]["post"]
    assert {p["name"] for p in post["parameters"] if p["in"] == "header"} >= {
        "Idempotency-Key",
        "If-Match",
    }
    assert set(paths[CONFIRMATION]) == {"post"} and set(paths[GRANT_PATH]) == {"post"}
    token_headers = {p["name"] for p in paths[GRANT_PATH]["post"].get("parameters", [])}
    assert not token_headers & {"Idempotency-Key", "If-Match"}  # a grant, not a command
    assert "requestBody" not in paths[GRANT_PATH]["post"]


# ----------------------------------------------------------------------------- the confirmation
def test_a_confirmation_passes_the_revision_the_key_and_the_body_and_sets_the_headers(
    served: tuple[TestClient, FakeService, PlaybackTokenCodec],
) -> None:
    client, service, _codec = served
    response = client.post(CONFIRM_URL, headers=keyed(), json=BODY)
    assert response.status_code == 200
    assert response.headers["ETag"] == '"4"'
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["contract"] == "ClassProjectionConfirmationV1"
    assert response.json()["plan"] == {"revision_no": 1, "plan_hash": HASH, "is_current": True}
    name, kwargs = service.calls[0]
    assert name == "confirm"
    assert kwargs["occurrence_id"] == OCCURRENCE and kwargs["idempotency_key"] == "key-1"
    assert kwargs["expected_revision"] == 3
    assert kwargs["payload"].run_id == RUN and kwargs["payload"].generation_id == GENERATION


@pytest.mark.parametrize(
    ("headers", "body", "field", "code"),
    [
        (keyed(match=None), BODY, "If-Match", "REQUIRED"),
        (keyed(match='W/"3"'), BODY, "If-Match", "INVALID_FORMAT"),
        (keyed(match='"0"'), BODY, "If-Match", "INVALID_FORMAT"),
        (keyed(match="3"), BODY, "If-Match", "INVALID_FORMAT"),
        (keyed(key=None), BODY, "Idempotency-Key", None),
        (keyed(key="bad key"), BODY, "Idempotency-Key", None),
        (keyed(), {**BODY, "audience": "GROUP"}, None, None),
        (keyed(), {**BODY, "audience": "class"}, None, None),
        (keyed(), {**BODY, "use": "PROJECTION"}, None, None),
        (keyed(), {**BODY, "run_id": "not-a-uuid"}, None, None),
        (keyed(), {**BODY, "generation_id": RUN.upper()}, None, None),
        (keyed(), {**BODY, "child_id": "child-1"}, None, None),
        (keyed(), {key: value for key, value in BODY.items() if key != "use"}, None, None),
        (keyed(), {}, None, None),
    ],
)
def test_a_bad_request_is_400_before_the_service(
    served: tuple[TestClient, FakeService, PlaybackTokenCodec],
    headers: dict[str, str],
    body: dict[str, Any],
    field: str | None,
    code: str | None,
) -> None:
    client, service, _codec = served
    response = client.post(CONFIRM_URL, headers=headers, json=body)
    assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST"
    if field is not None and code is not None:
        assert response.json()["field_errors"] == [{"field": field, "code": code}]
    assert service.calls == []


def test_a_request_without_a_json_body_is_400_too(
    served: tuple[TestClient, FakeService, PlaybackTokenCodec],
) -> None:
    client, service, _codec = served
    assert client.post(CONFIRM_URL, headers=keyed()).status_code == 400
    assert client.post(CONFIRM_URL, headers=keyed(), content=b"{").status_code == 400
    assert service.calls == []


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "INVALID_IDEMPOTENCY_KEY"),
        (403, "ACTION_NOT_ALLOWED"),
        (404, "RESOURCE_NOT_FOUND"),
        (409, "INVALID_STATE_TRANSITION"),
        (409, "SAMPLE_VIDEO_ALREADY_EXISTS"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_refusals_use_the_envelope_on_both_routes_and_name_nothing(
    served: tuple[TestClient, FakeService, PlaybackTokenCodec], status: int, code: str
) -> None:
    client, service, _codec = served
    service.error = LessonOccurrenceError(status, code)
    for response in (
        client.post(CONFIRM_URL, headers=keyed(), json=BODY),
        client.post(GRANT_URL),
    ):
        body = response.json()
        assert response.status_code == status and body["code"] == code
        assert body["message"] and body["correlation_id"]
        assert response.headers.get("Cache-Control", "") != "public"
        text = response.text.lower()
        assert RUN not in text and "token" not in text.replace("playback", "")


def test_a_stale_revision_carries_the_current_version(
    served: tuple[TestClient, FakeService, PlaybackTokenCodec],
) -> None:
    client, service, _codec = served
    service.error = LessonOccurrenceError(409, "STALE_REVISION", current_version=7)
    response = client.post(CONFIRM_URL, headers=keyed(), json=BODY)
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION" and response.json()["current_version"] == 7


# ----------------------------------------------------------------------------- the token
def test_the_token_route_signs_the_projection_claims_for_the_caller_digest(
    served: tuple[TestClient, FakeService, PlaybackTokenCodec],
) -> None:
    client, service, codec = served
    response = client.post(GRANT_URL)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert set(body) == {"contract", "token", "expires_at", "stream_path", "media_type"}
    assert body["stream_path"] == f"/v1/story-runs/{RUN}/playback"
    assert body["media_type"] == "video/mp4"
    assert "http" not in body["stream_path"] and "bucket" not in response.text.lower()
    grant = codec.verify(body["token"])
    assert (grant.run_id, grant.generation_id) == (RUN, GENERATION)
    assert grant.audience == "projection" and grant.occurrence_id == OCCURRENCE
    assert grant.confirmed_ms == 1_795_341_600_123
    assert grant.actor_digest == codec.actor_binding("scope-of-the-caller")
    assert service.calls == [
        ("grant", {"principal": service.calls[0][1]["principal"], "occurrence_id": OCCURRENCE})
    ]


def test_without_a_signing_secret_the_token_is_503_after_the_lesson_checks() -> None:
    application = create_app()
    application.state.story_playback_tokens = None
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_projection_service] = lambda: service
    with TestClient(application) as client:
        response = client.post(GRANT_URL)
        assert response.status_code == 503 and response.json()["code"] == "PROVIDER_UNAVAILABLE"
        assert [name for name, _ in service.calls] == ["grant"]  # the checks ran first
        service.error = LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
        assert client.post(GRANT_URL).status_code == 404  # a foreign caller never sees 503 first
        service.error = LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
        assert client.post(GRANT_URL).status_code == 409


def test_unauthenticated_calls_are_401_on_both_routes() -> None:
    application = create_app()
    with TestClient(application) as client:
        assert client.post(CONFIRM_URL, headers=keyed(), json=BODY).status_code == 401
        assert client.post(GRANT_URL).status_code == 401


# ----------------------------------------------------------------------------- the stream guards
def test_the_stream_branches_on_the_audience_after_the_token_and_the_actor_checks() -> None:
    source = inspect.getsource(story_run_video.stream_parent_playback)
    token_check = source.index("check_playback_token(")
    actor = source.index("require_story_run_actor(")
    branch = source.index("grant.audience is None")
    owner = source.index(").authorize(")
    projection = source.index(".authorize_projection(")
    storage = source.index("storage.get_object(")
    assert token_check < actor < branch < owner < projection < storage
    # the projection branch is for a Teacher and builds the Lesson port from the same session
    assert "elif actor.is_teacher:" in source
    assert "SqlProjectionAuthorization(db)" in source
    assert "story_video_repository(db, actor)" in source
    # one stream route, one handler: no second streaming path (SRS l.1692)
    assert source.count("StreamingResponse(") == 1
