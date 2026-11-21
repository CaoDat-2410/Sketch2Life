"""FEAT-066 T-1a: the ``video-generations`` route contract (SRS l.395, l.1670, l.1697-1699).

Offline: the real app with its real exception handlers, a fake database and a fake admission
service. Behaviour against PostgreSQL lives in
``tests/integration/story_video/test_video_generations_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.story_run_video as video_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body
from sketch2life.application.ports.story_video import GenerationRecord
from sketch2life.application.services.story_run_video import AdmissionOutcome
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
GEN_ID = "33333333-3333-4333-8333-333333333333"
OPERATION = ("post", "/v1/story-runs/{run_id}/video-generations")
HASH = "a" * 64
VOLATILE_KEYS = {"request_id", "correlation_id"}
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "s3mock", "parent/", "output")


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


def _record(**changes: Any) -> GenerationRecord:
    values: dict[str, Any] = {
        "generation_id": GEN_ID,
        "run_id": RUN_ID,
        "scope_kind": "PARENT_ACCOUNT",
        "scope_ref": "s" * 64,
        "state": "ACCEPTED",
        "kind": "INITIAL",
        "generation_no": 1,
        "job_ref": "vjob_" + "1" * 32,
        "key_hash": "k" * 64,
        "fingerprint": "f" * 64,
        "script_hash": HASH,
        "story_revision_id": "r1",
        "review_id": "rv1",
        "quality_reason_code": None,
        "compute_reservation_ref": "res-1",
        "compute_released_at": None,
        "billing_quota_usage_ref": "usage-1",
        "safe_failure_code": None,
        "started": False,
        "generation_revision": 2,
        "run_state": "VIDEO_QUEUED",
        "run_revision": 7,
    }
    values.update(changes)
    return GenerationRecord(**values)


class _Service:
    outcome: Any = None
    calls: list[dict[str, Any]] = []
    adapters: list[Any] = []

    def __init__(self, repository: object, adapters: Any, **kwargs: Any) -> None:
        type(self).adapters.append((adapters, kwargs))

    def request(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).outcome, BaseException):
            raise type(self).outcome
        return type(self).outcome


@pytest.fixture(autouse=True)
def _reset() -> None:
    _Service.outcome = AdmissionOutcome(_record())
    _Service.calls = []
    _Service.adapters = []


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t1a-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(video_routes, "StoryVideoAdmissionService", _Service)
    monkeypatch.setattr(video_routes, "SqlStoryVideoRepository", lambda db: SimpleNamespace(db=db))
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


def _post(
    client: TestClient, body: Any = None, *, key: str | None = "t1a-key-1", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = {"expected_revision": 6, "story_sha256": HASH} if body is None else body
    return client.post(f"/v1/story-runs/{run}/video-generations", json=payload, headers=headers)


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


# ------------------------------------------------------------------------- catalog
def test_the_operation_is_catalogued_projected_and_tagged() -> None:
    assert OPERATION in MOUNTED_OPERATIONS
    assert OPERATION in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[OPERATION] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[OPERATION]
    assert contract["handler"] == "story_run_video.py::create_parent_video_generation"
    assert {response["status"] for response in contract["responses"]} == {
        "202",
        "400",
        "401",
        "404",
        "409",
        "422",
        "503",
        "500",
    }
    assert "Idempotency-Key" in contract["request_inputs"]


def test_the_published_contract_has_no_storage_words_and_no_quota_figure(
    client: TestClient,
) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    operation = spec["paths"]["/v1/story-runs/{run_id}/video-generations"]["post"]
    assert operation["tags"] == ["Parent StoryRuns"]
    schemas = spec["components"]["schemas"]
    request = schemas["ParentVideoGenerationRequestV1"]
    assert set(request["properties"]) == {
        "expected_revision",
        "story_sha256",
        "quality_reason_code",
    }
    assert request["additionalProperties"] is False
    assert set(request["required"]) == {"expected_revision", "story_sha256"}
    wire = json.dumps(
        {
            name: schemas[name]
            for name in (
                "ParentVideoGenerationRequestV1",
                "ParentVideoGenerationAcceptedV1",
                "ParentVideoGenerationV1",
            )
        }
    ).lower()
    for word in (*STORAGE_WORDS, "url", "balance", "units", "price", "provider"):
        assert word not in wire, word
    assert set(schemas["ParentVideoGenerationV1"]["properties"]) == {
        "generation_id",
        "state",
        "generation_no",
        "kind",
        "job_id",
        "run_state",
        "run_revision",
    }


# ------------------------------------------------------------------------- 202 shapes
def test_an_accepted_request_is_202_with_the_job_id(client: TestClient) -> None:
    response = _post(client)
    status, body = _wire(response)
    assert status == 202
    assert body == {
        "video_generation": {
            "generation_id": GEN_ID,
            "state": "ACCEPTED",
            "generation_no": 1,
            "kind": "INITIAL",
            "job_id": "vjob_" + "1" * 32,
            "run_state": "VIDEO_QUEUED",
            "run_revision": 7,
        }
    }
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    call = _Service.calls[0]
    assert call["run_id"] == RUN_ID and call["idempotency_key"] == "t1a-key-1"
    assert call["expected_revision"] == 6 and call["story_sha256"] == HASH
    assert call["quality_reason_code"] is None


def test_an_intent_without_both_receipts_is_202_pending_with_no_job_id(client: TestClient) -> None:
    _Service.outcome = AdmissionOutcome(
        _record(
            state="ADMISSION_PENDING",
            generation_no=None,
            job_ref=None,
            run_state="VIDEO_ADMISSION_PENDING",
            run_revision=6,
        )
    )
    status, body = _wire(_post(client))
    assert status == 202
    generation = body["video_generation"]
    assert generation["state"] == "ADMISSION_PENDING"
    assert generation["job_id"] is None and generation["generation_no"] is None


def test_a_regeneration_carries_its_reason_to_the_service(client: TestClient) -> None:
    _Service.outcome = AdmissionOutcome(
        _record(kind="QUALITY_REGEN", generation_no=2, quality_reason_code="QUALITY_LOW")
    )
    response = _post(
        client,
        {"expected_revision": 6, "story_sha256": HASH, "quality_reason_code": "QUALITY_LOW"},
    )
    assert response.status_code == 202
    assert response.json()["video_generation"]["kind"] == "QUALITY_REGEN"
    assert _Service.calls[0]["quality_reason_code"] == "QUALITY_LOW"


def test_a_purged_replay_returns_the_lifecycle_projection(client: TestClient) -> None:
    projection = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETE_PENDING", revision=9, version=9)
    )
    _Service.outcome = AdmissionOutcome(None, projection)
    status, body = _wire(_post(client))
    assert status == 202 and set(body) == {"lifecycle"}
    assert body["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert "video_generation" not in json.dumps(body)


def test_the_service_receives_the_composed_ports_and_the_timeout(
    client: TestClient,
) -> None:
    client.app.state.story_video_ports = "ports"  # type: ignore[attr-defined]
    client.app.state.story_video_port_timeout_seconds = 3.5  # type: ignore[attr-defined]
    assert _post(client).status_code == 202
    adapters, kwargs = _Service.adapters[0]
    assert adapters == "ports" and kwargs == {"call_timeout_seconds": 3.5}


# ------------------------------------------------------------------------- errors
@pytest.mark.parametrize(
    ("error", "status", "code", "retryable"),
    [
        (ParentStoryRunError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND", False),
        (
            ParentStoryRunError(409, "INVALID_STATE_TRANSITION"),
            409,
            "INVALID_STATE_TRANSITION",
            False,
        ),
        (
            ParentStoryRunError(409, "VIDEO_REGENERATION_LIMIT_REACHED"),
            409,
            "VIDEO_REGENERATION_LIMIT_REACHED",
            False,
        ),
        (ParentStoryRunError(409, "VIDEO_QUOTA_EXCEEDED"), 409, "VIDEO_QUOTA_EXCEEDED", False),
        (
            ParentStoryRunError(409, "SUBSCRIPTION_RESTRICTED"),
            409,
            "SUBSCRIPTION_RESTRICTED",
            False,
        ),
        (ParentStoryRunError(503, "AI_COST_LIMIT_REACHED"), 503, "AI_COST_LIMIT_REACHED", True),
        (ParentStoryRunError(503, "PROVIDER_UNAVAILABLE"), 503, "PROVIDER_UNAVAILABLE", True),
        (ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED"), 422, "SUBJECT_NOT_CONFIRMED", False),
        (
            ParentStoryRunError(422, "PROFILE_CONTEXT_NOT_CONFIRMED"),
            422,
            "PROFILE_CONTEXT_NOT_CONFIRMED",
            False,
        ),
        (
            ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY"),
            400,
            "INVALID_IDEMPOTENCY_KEY",
            False,
        ),
    ],
)
def test_each_refusal_has_a_stable_code_a_safe_message_and_no_internals(
    client: TestClient, error: ParentStoryRunError, status: int, code: str, retryable: bool
) -> None:
    _Service.outcome = error
    response = _post(client)
    body = response.json()
    assert response.status_code == status
    assert body["code"] == code and body["retryable"] is retryable
    assert body["message"] and body["message"] != "Không thể hoàn tất yêu cầu."
    assert response.headers["X-Request-ID"] == body["correlation_id"]
    text = json.dumps(body).lower()
    for word in (*STORAGE_WORDS, "quota_units", "balance", "traceback", "reservation"):
        assert word not in text


def test_a_stale_request_carries_the_current_version(client: TestClient) -> None:
    _Service.outcome = ParentStoryRunError(409, "STALE_REVISION", current_version=8)
    status, body = _wire(_post(client))
    assert status == 409 and body["code"] == "STALE_REVISION" and body["current_version"] == 8


def test_a_missing_reason_is_a_field_error(client: TestClient) -> None:
    _Service.outcome = ParentStoryRunError(
        400, "INVALID_REQUEST", field_errors=[{"field": "quality_reason_code", "code": "REQUIRED"}]
    )
    status, body = _wire(_post(client))
    assert status == 400 and body["code"] == "INVALID_REQUEST"
    assert body["field_errors"] == [
        {
            "field": "quality_reason_code",
            "code": "REQUIRED",
            "message": "Giá trị trường không hợp lệ.",
        }
    ]


# ------------------------------------------------------------------------- request checks
def test_a_missing_key_is_a_plain_400_without_a_service_call(client: TestClient) -> None:
    status, body = _wire(_post(client, key=None))
    assert status == 400 and body["code"] == "INVALID_REQUEST" and not body.get("field_errors")
    assert _Service.calls == []


@pytest.mark.parametrize("key", [" ", "k" * 129, "bad key", "kéy"])
def test_an_invalid_key_is_a_400_before_the_run_lookup(client: TestClient, key: str) -> None:
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/video-generations",
        json={"expected_revision": 6, "story_sha256": HASH},
        headers={"Idempotency-Key": key.encode("utf-8")},  # type: ignore[arg-type]
    )
    assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST"
    assert _Service.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"expected_revision": 6},
        {"story_sha256": HASH},
        {"expected_revision": 0, "story_sha256": HASH},
        {"expected_revision": "6", "story_sha256": HASH},
        {"expected_revision": 6, "story_sha256": "A" * 64},
        {"expected_revision": 6, "story_sha256": "a" * 63},
        {"expected_revision": 6, "story_sha256": HASH, "quality_reason_code": "TOO_BAD"},
        {"expected_revision": 6, "story_sha256": HASH, "extra": True},
        {"expected_revision": 6, "story_sha256": HASH, "owner": "someone-else"},
    ],
)
def test_an_invalid_body_is_a_400_in_the_story_envelope(client: TestClient, body: Any) -> None:
    status, payload = _wire(_post(client, body))
    assert status == 400 and payload["code"] == "INVALID_REQUEST"
    assert _Service.calls == []


def test_the_body_cannot_name_an_owner_or_a_scope(client: TestClient) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    properties = spec["components"]["schemas"]["ParentVideoGenerationRequestV1"]["properties"]
    assert not {"owner", "scope", "organization_id", "account_id", "parent_profile_id"} & set(
        properties
    )


# ------------------------------------------------------------------------- roles
@pytest.mark.parametrize("role", ["teacher", "school_manager", "platform_admin", None])
def test_a_role_that_is_not_an_active_parent_gets_the_uniform_404(
    client: TestClient, role: str | None
) -> None:
    client.app.dependency_overrides[get_db] = lambda: _Db(role)  # type: ignore[attr-defined]
    response = _post(client)
    assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _Service.calls == []


def test_a_disabled_parent_or_another_issuer_gets_the_uniform_404(client: TestClient) -> None:
    for db in (_Db("parent", state="disabled"), _Db("parent", issuer="other-issuer")):
        client.app.dependency_overrides[get_db] = lambda db=db: db  # type: ignore[attr-defined]
        response = _post(client)
        assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _Service.calls == []


def test_the_only_method_on_the_path_is_post(client: TestClient) -> None:
    for method in ("get", "put", "patch", "delete"):
        response = getattr(client, method)(f"/v1/story-runs/{RUN_ID}/video-generations")
        assert response.status_code in {404, 405}, method


def test_a_malformed_run_id_is_a_400(client: TestClient) -> None:
    status, body = _wire(_post(client, run="not-a-uuid"))
    assert status == 400 and body["code"] == "INVALID_REQUEST"
