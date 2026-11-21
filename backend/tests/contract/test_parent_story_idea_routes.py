"""FEAT-066 T-2c: the idea, transcript read and transcript confirmation contracts (SRS l.1665).

Offline: the real app with its real exception handlers, a fake database, a fake idea service and a
fake repository. Behaviour against PostgreSQL and S3Mock lives in
``tests/integration/test_parent_story_idea_postgres.py``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_ai as parent_ai
import sketch2life.interfaces.http.routers.parent_story_inputs as input_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    IdeaOutcome,
    TranscriptConfirmOutcome,
    TranscriptView,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_runtime, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
RUN_ID = "22222222-2222-4222-8222-222222222222"
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"
HANDLE = "upl_11111111-1111-4111-8111-111111111111"
IDEA = ("post", "/v1/story-runs/{run_id}/idea")
READ = ("get", "/v1/story-runs/{run_id}/transcript")
CONFIRM = ("post", "/v1/story-runs/{run_id}/transcript-confirmation")
CHILD_WORDS = "CHILD_WORDS-CHILD-SENTENCE"
VOLATILE_KEYS = {"request_id", "correlation_id"}
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "s3mock", "parent/")
HASH = "a" * 64


class _Db:
    def __init__(self, role: str | None, *, state: str = "active", issuer: str = ISSUER) -> None:
        self._identity = (
            None
            if role is None
            else SimpleNamespace(
                account_id="account-1", issuer=issuer, account_role=role, state=state
            )
        )

    def get(self, _model: object, _key: object) -> Any:
        return self._identity


class _IdeaService:
    result: Any = None
    calls: list[dict[str, Any]] = []

    def __init__(self, db: object, *, storage: object) -> None:
        self.storage = storage

    def submit(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).result, BaseException):
            raise type(self).result
        return type(self).result


class _Repository:
    transcript: Any = None
    confirmation: Any = None
    calls: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, db: object) -> None:
        self.db = db

    def get_transcript(self, **kwargs: Any) -> Any:
        type(self).calls.append(("get", kwargs))
        if isinstance(type(self).transcript, BaseException):
            raise type(self).transcript
        return type(self).transcript

    def confirm_transcript(self, **kwargs: Any) -> Any:
        type(self).calls.append(("confirm", kwargs))
        if isinstance(type(self).confirmation, BaseException):
            raise type(self).confirmation
        return type(self).confirmation


class _Speech:
    scheduled: list[tuple[Any, ...]] = []

    def __init__(self, session_factory: object, transcriber: object) -> None:
        self.transcriber = transcriber

    def run(self, *args: Any) -> None:
        type(self).scheduled.append(args)


def _outcome(**changes: Any) -> IdeaOutcome:
    values: dict[str, Any] = {
        "input_revision": 3,
        "run_revision": 7,
        "run_state": "INPUT_PROCESSING",
        "idea_source": "VOICE",
        "transcript_revision": 1,
        "transcript_state": "PENDING",
        "new_transcript_id": "transcript-1",
    }
    values.update(changes)
    return IdeaOutcome(**values)


def _view(**changes: Any) -> TranscriptView:
    values: dict[str, Any] = {
        "run_revision": 7,
        "state": "NEEDS_CONFIRMATION",
        "transcript_revision": 2,
        "origin": "ASR",
        "text": CHILD_WORDS,
        "transcript_sha256": HASH,
        "language": "vi",
        "error_code": None,
    }
    values.update(changes)
    return TranscriptView(**values)


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    _IdeaService.result = _outcome()
    _IdeaService.calls = []
    _Repository.transcript = _view()
    _Repository.confirmation = TranscriptConfirmOutcome(2, 8, "SUBJECT_REVIEW")
    _Repository.calls = []
    _Speech.scheduled = []
    yield


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t2c-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(input_routes, "ParentRunIdeaService", _IdeaService)
    monkeypatch.setattr(input_routes, "SqlParentStoryRunRepository", _Repository)
    monkeypatch.setattr(input_routes, "ParentSpeechJobRunner", _Speech)
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: PRINCIPAL
    application.dependency_overrides[get_db] = lambda: _Db("parent")
    application.dependency_overrides[get_runtime] = lambda: SimpleNamespace(
        settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True), session_factory=None
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _use_db(client: TestClient, db: _Db) -> None:
    client.app.dependency_overrides[get_db] = lambda: db  # type: ignore[attr-defined]


def _idea(
    client: TestClient, body: Any = None, *, key: str | None = "t2c-key-1", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = {"expected_run_revision": 6, "text": "a cat"} if body is None else body
    return client.post(f"/v1/story-runs/{run}/idea", json=payload, headers=headers)


def _confirm(client: TestClient, body: Any = None, *, key: str | None = "t2c-key-2") -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = (
        {"expected_transcript_revision": 2, "transcript_sha256": HASH, "confirmed": True}
        if body is None
        else body
    )
    return client.post(
        f"/v1/story-runs/{RUN_ID}/transcript-confirmation", json=payload, headers=headers
    )


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


# ------------------------------------------------------------------------- catalog
@pytest.mark.parametrize(
    ("operation", "handler", "statuses"),
    [
        (
            IDEA,
            "parent_story_inputs.py::add_parent_run_idea",
            {"202", "400", "401", "404", "409", "413", "415", "422", "503", "500"},
        ),
        (
            READ,
            "parent_story_inputs.py::get_parent_run_transcript",
            {"200", "400", "401", "404", "409", "422", "503", "500"},
        ),
        (
            CONFIRM,
            "parent_story_inputs.py::confirm_parent_run_transcript",
            {"200", "400", "401", "404", "409", "422", "503", "500"},
        ),
    ],
)
def test_the_operations_are_catalogued_projected_and_tagged(
    operation: tuple[str, str], handler: str, statuses: set[str]
) -> None:
    assert operation in MOUNTED_OPERATIONS
    assert operation in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[operation] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[operation]
    assert contract["handler"] == handler
    assert {response["status"] for response in contract["responses"]} == statuses


def test_the_published_contract_has_no_storage_words_and_no_job_field(client: TestClient) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    for path, method in (
        ("/v1/story-runs/{run_id}/idea", "post"),
        ("/v1/story-runs/{run_id}/transcript", "get"),
        ("/v1/story-runs/{run_id}/transcript-confirmation", "post"),
    ):
        assert spec["paths"][path][method]["tags"] == ["Parent StoryRuns"]
    schemas = spec["components"]["schemas"]
    wire = json.dumps(
        {
            name: schemas[name]
            for name in (
                "AddRunIdeaRequestV1",
                "ParentRunIdeaAcceptedV1",
                "ParentRunTranscriptV1",
                "ConfirmTranscriptRequestV1",
                "ParentTranscriptConfirmationV1",
            )
        }
    ).lower()
    for word in STORAGE_WORDS:
        assert word not in wire, word
    assert '"job"' not in wire
    assert set(schemas["AddRunIdeaRequestV1"]["properties"]) == {
        "expected_run_revision",
        "text",
        "audio_ref",
        "transcript_correction",
    }
    assert schemas["AddRunIdeaRequestV1"]["additionalProperties"] is False


# ------------------------------------------------------------------------- /idea success
def test_the_idea_is_accepted_with_the_202_shape(client: TestClient) -> None:
    response = _idea(client)
    status, body = _wire(response)
    assert status == 202
    assert body == {
        "story_run_id": RUN_ID,
        "input_revision": 3,
        "run_revision": 7,
        "run_state": "INPUT_PROCESSING",
        "idea_source": "VOICE",
        "transcript": {"transcript_revision": 1, "state": "PENDING"},
    }
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    call = _IdeaService.calls[0]
    assert call["run_id"] == RUN_ID and call["idempotency_key"] == "t2c-key-1"
    assert call["payload"].text == "a cat" and call["payload"].expected_run_revision == 6


def test_a_text_only_idea_without_a_transcript(client: TestClient) -> None:
    _IdeaService.result = _outcome(
        idea_source="TEXT", transcript_revision=None, transcript_state=None, new_transcript_id=None
    )
    status, body = _wire(_idea(client))
    assert status == 202 and body["transcript"] is None and body["idea_source"] == "TEXT"


def test_a_purged_replay_returns_the_lifecycle_projection(client: TestClient) -> None:
    projection = ParentStoryLifecycleRecord.from_body(
        {
            **lifecycle_projection_body(
                run_id=RUN_ID, run_state="DELETE_PENDING", revision=9, version=9
            ),
        }
    )
    _IdeaService.result = projection
    status, body = _wire(_idea(client))
    assert status == 202 and set(body) == {"lifecycle"}
    assert body["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert "transcript" not in json.dumps(body)


def test_the_speech_job_is_scheduled_only_with_a_transcriber_and_a_new_transcript(
    client: TestClient,
) -> None:
    app = client.app
    app.state.speech_transcriber = None  # type: ignore[attr-defined]
    assert _idea(client).status_code == 202
    assert _Speech.scheduled == []  # nothing composed: the transcript waits
    app.state.speech_transcriber = object()  # type: ignore[attr-defined]
    app.state.be1_runtime = SimpleNamespace(session_factory=lambda: None)  # type: ignore[attr-defined]
    assert _idea(client).status_code == 202
    assert [args[1:] for args in _Speech.scheduled] == [(RUN_ID, "transcript-1")]
    _IdeaService.result = _outcome(replayed=True)
    assert _idea(client).status_code == 202
    _IdeaService.result = _outcome(new_transcript_id=None, idea_source="TEXT")
    assert _idea(client).status_code == 202
    assert len(_Speech.scheduled) == 1  # not on a replay, not without a new transcript


# ------------------------------------------------------------------------- /idea requests
def test_the_idempotency_key_is_required_and_parsed_after_the_role_check(
    client: TestClient,
) -> None:
    assert _idea(client, key=None).status_code == 400
    assert _idea(client, key="x" * 129).status_code == 400
    assert _idea(client, key="bad key\x7f").status_code == 400
    assert _IdeaService.calls == []
    _use_db(client, _Db("teacher"))
    assert _idea(client, key=None).status_code == 400  # header validation precedes the guard
    assert _idea(client).status_code == 404  # but a valid key from a non-Parent is the 404


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"text": "a cat"},  # no expected revision
        {"expected_run_revision": 0, "text": "a"},
        {"expected_run_revision": 6},
        {"expected_run_revision": 6, "text": ""},
        {"expected_run_revision": 6, "text": "   "},
        {"expected_run_revision": 6, "text": "x" * 501},
        {"expected_run_revision": 6, "audio_ref": "upl_bad"},
        {"expected_run_revision": 6, "audio_ref": "parent/run/original"},
        {"expected_run_revision": 6, "text": "a", "owner": "x"},
        {
            "expected_run_revision": 6,
            "text": "a",
            "transcript_correction": {"base_revision": 1, "text": "b"},
        },
        {"expected_run_revision": 6, "transcript_correction": {"base_revision": 0, "text": "b"}},
        {"expected_run_revision": 6, "transcript_correction": {"base_revision": 1}},
    ],
)
def test_a_malformed_body_is_a_400_invalid_request_that_never_echoes_the_text(
    client: TestClient, body: dict[str, Any]
) -> None:
    if "text" in body and isinstance(body["text"], str) and len(body["text"]) > 500:
        body = {**body, "text": CHILD_WORDS + "x" * 500}
    response = _idea(client, body)
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert CHILD_WORDS not in response.text
    assert _IdeaService.calls == []


def test_the_text_group_and_the_correction_group_reach_the_service(client: TestClient) -> None:
    assert (
        _idea(client, {"expected_run_revision": 6, "audio_ref": HANDLE, "text": " a "}).status_code
        == 202
    )
    assert _IdeaService.calls[-1]["payload"].audio_ref == HANDLE
    assert _IdeaService.calls[-1]["payload"].text == "a"
    correction = {
        "expected_run_revision": 6,
        "transcript_correction": {"base_revision": 2, "text": " fixed "},
    }
    assert _idea(client, correction).status_code == 202
    sent = _IdeaService.calls[-1]["payload"].transcript_correction
    assert (sent.base_revision, sent.text) == (2, "fixed")


# ------------------------------------------------------------------------- error mapping
def test_a_stale_revision_carries_current_version(client: TestClient) -> None:
    _IdeaService.result = ParentStoryRunError(409, "STALE_REVISION", current_version=9)
    status, body = _wire(_idea(client))
    assert status == 409 and body["code"] == "STALE_REVISION" and body["current_version"] == 9


def test_other_conflicts_do_not_carry_current_version(client: TestClient) -> None:
    _IdeaService.result = ParentStoryRunError(409, "INVALID_STATE_TRANSITION", current_version=9)
    status, body = _wire(_idea(client))
    assert status == 409 and body["code"] == "INVALID_STATE_TRANSITION"
    assert "current_version" not in body


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (ParentStoryRunError(413, "AUDIO_TOO_LARGE"), 413, "AUDIO_TOO_LARGE"),
        (ParentStoryRunError(415, "UNSUPPORTED_MEDIA_TYPE"), 415, "UNSUPPORTED_MEDIA_TYPE"),
        (ParentStoryRunError(422, "UPLOAD_CONTENT_MISMATCH"), 422, "UPLOAD_CONTENT_MISMATCH"),
        (ParentStoryRunError(422, "UPLOAD_INCOMPLETE"), 422, "UPLOAD_INCOMPLETE"),
        (ParentStoryRunError(422, "UPLOAD_CHECKSUM_MISMATCH"), 422, "UPLOAD_CHECKSUM_MISMATCH"),
        (ParentStoryRunError(503, "STORAGE_UNAVAILABLE"), 503, "STORAGE_UNAVAILABLE"),
        (ParentStoryRunError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND"),
    ],
)
def test_each_error_has_its_status_code_and_a_specific_message(
    client: TestClient, error: ParentStoryRunError, status: int, code: str
) -> None:
    _IdeaService.result = error
    response = _idea(client)
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code
    assert body["message"] not in {"", "Không thể hoàn tất yêu cầu."}
    assert body["retryable"] is (status == 503)
    assert "field_errors" in body


def test_a_too_long_transcript_is_a_400_with_field_errors(client: TestClient) -> None:
    _IdeaService.result = ParentStoryRunError(
        400, "INVALID_REQUEST", field_errors=[{"field": "text", "code": "TOO_LONG"}]
    )
    response = _idea(client)
    body = response.json()
    assert response.status_code == 400 and body["code"] == "INVALID_REQUEST"
    assert body["field_errors"] == [
        {"field": "text", "code": "TOO_LONG", "message": "Giá trị trường không hợp lệ."}
    ]


# ------------------------------------------------------------------------- uniform 404
@pytest.mark.parametrize(
    "db",
    [
        _Db(None),
        _Db("teacher"),
        _Db("school_manager"),
        _Db("platform_admin"),
        _Db("parent", state="suspended"),
        _Db("parent", issuer="another-issuer"),
    ],
    ids=["no-identity", "teacher", "manager", "admin", "inactive", "other-issuer"],
)
def test_a_non_parent_or_inactive_caller_gets_the_same_404_on_every_route(
    client: TestClient, db: _Db
) -> None:
    _use_db(client, db)
    unknown = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    _IdeaService.result = unknown
    _Repository.transcript = unknown
    _Repository.confirmation = unknown
    reference = _wire(_idea(client, run=UNKNOWN_ID))
    # the same body whether the actor, the run or the audio is wrong
    assert reference[0] == 404 and reference[1]["code"] == "RESOURCE_NOT_FOUND"
    assert _wire(_idea(client)) == reference
    assert _wire(client.get(f"/v1/story-runs/{RUN_ID}/transcript")) == reference
    assert _wire(_confirm(client)) == reference
    assert _IdeaService.calls == [] and _Repository.calls == []  # the guard ran first


def test_an_unknown_run_audio_or_foreign_asset_answers_the_same_404(client: TestClient) -> None:
    _IdeaService.result = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    first = _wire(_idea(client, {"expected_run_revision": 6, "audio_ref": HANDLE}))
    second = _wire(_idea(client, run=UNKNOWN_ID))
    assert first == second and first[0] == 404


# ------------------------------------------------------------------------- transcript read
def test_the_transcript_read_shape_and_cache_header(client: TestClient) -> None:
    response = client.get(f"/v1/story-runs/{RUN_ID}/transcript")
    status, body = _wire(response)
    assert status == 200
    assert body == {
        "story_run_id": RUN_ID,
        "transcript_revision": 2,
        "state": "NEEDS_CONFIRMATION",
        "origin": "ASR",
        "text": CHILD_WORDS,
        "transcript_sha256": HASH,
        "language": "vi",
        "error_code": None,
        "run_revision": 7,
    }
    assert response.headers["Cache-Control"] == "private, no-store"


def test_a_run_without_a_voice_idea_reads_as_none(client: TestClient) -> None:
    _Repository.transcript = TranscriptView(run_revision=3, state="NONE")
    status, body = _wire(client.get(f"/v1/story-runs/{RUN_ID}/transcript"))
    assert status == 200
    assert body["state"] == "NONE" and body["text"] is None and body["transcript_revision"] is None


def test_a_purged_run_has_no_transcript_to_read(client: TestClient) -> None:
    _Repository.transcript = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    response = client.get(f"/v1/story-runs/{RUN_ID}/transcript")
    assert response.status_code == 409 and CHILD_WORDS not in response.text


# ------------------------------------------------------------------------- confirmation
def test_the_confirmation_shape(client: TestClient) -> None:
    response = _confirm(client)
    status, body = _wire(response)
    assert status == 200
    assert body == {
        "story_run_id": RUN_ID,
        "transcript_revision": 2,
        "state": "CONFIRMED",
        "run_revision": 8,
        "run_state": "SUBJECT_REVIEW",
    }
    call = _Repository.calls[0][1]
    assert call["expected_transcript_revision"] == 2 and call["transcript_sha256"] == HASH
    assert call["idempotency_key"] == "t2c-key-2"
    assert response.headers["Cache-Control"] == "private, no-store"


def test_the_confirmation_needs_a_key_and_an_exact_body(client: TestClient) -> None:
    assert _confirm(client, key=None).status_code == 400
    for body in (
        {"expected_transcript_revision": 2, "transcript_sha256": HASH},
        {"expected_transcript_revision": 2, "transcript_sha256": HASH, "confirmed": False},
        {"expected_transcript_revision": 0, "transcript_sha256": HASH, "confirmed": True},
        {"expected_transcript_revision": 2, "transcript_sha256": "z" * 64, "confirmed": True},
        {"expected_transcript_revision": 2, "transcript_sha256": HASH, "confirmed": True, "x": 1},
    ):
        assert _confirm(client, body).status_code == 400
    assert _Repository.calls == []


def test_the_confirmation_errors_follow_the_envelope(client: TestClient) -> None:
    _Repository.confirmation = ParentStoryRunError(409, "STALE_REVISION", current_version=4)
    status, body = _wire(_confirm(client))
    assert (status, body["code"], body["current_version"]) == (409, "STALE_REVISION", 4)
    _Repository.confirmation = ParentStoryRunError(
        400, "INVALID_REQUEST", field_errors=[{"field": "transcript", "code": "TOO_LONG"}]
    )
    status, body = _wire(_confirm(client))
    assert status == 400 and body["field_errors"][0]["field"] == "transcript"
    assert body["field_errors"][0]["code"] == "TOO_LONG"
    _Repository.confirmation = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    assert _wire(_confirm(client))[0] == 409


def test_a_purged_confirmation_replay_is_the_lifecycle_projection(client: TestClient) -> None:
    _Repository.confirmation = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETED", revision=4, version=4)
    )
    status, body = _wire(_confirm(client))
    assert status == 200 and set(body) == {"lifecycle"}


# ------------------------------------------------------------------------- privacy
def test_no_transcript_text_reaches_the_logs_or_an_error_body(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    _IdeaService.result = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    response = _idea(client, {"expected_run_revision": 6, "text": CHILD_WORDS})
    assert CHILD_WORDS not in response.text
    assert _wire(client.get(f"/v1/story-runs/{RUN_ID}/transcript"))[0] == 200
    assert CHILD_WORDS not in caplog.text
    _Repository.confirmation = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    assert CHILD_WORDS not in _confirm(client).text
    assert CHILD_WORDS not in caplog.text


# ------------------------------------------------------------------------- the story gate
def test_the_legacy_story_route_answers_422_when_the_transcript_is_not_confirmed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate lives in ``reserve_story_revision``, which both story routes call (T2C-D6)."""

    class _Reserve:
        def reserve_story_revision(self, **_kwargs: Any) -> Any:
            raise ParentStoryRunError(422, "TRANSCRIPT_NOT_CONFIRMED")

    monkeypatch.setattr(parent_ai, "_story_service", lambda _db: _Reserve())
    monkeypatch.setattr(parent_ai, "_require_modal_dev", lambda: None)
    monkeypatch.setattr(parent_ai, "SqlParentStoryRunRepository", lambda _db: object())
    response = client.post(
        f"/api/parent/v1/ai/story-runs/{RUN_ID}/story-revisions",
        json={"expected_understanding_revision": 1},
        headers={"Idempotency-Key": "gate-key"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "TRANSCRIPT_NOT_CONFIRMED"
    assert body["message"] not in {"", "Không thể hoàn tất yêu cầu."}
    assert CHILD_WORDS not in response.text
