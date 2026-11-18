"""Offline request-level contracts for the composed Parent StoryRun routes."""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import NoReturn

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_profile_service,
    get_parent_role_reader,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_PROFILE_ID = "11111111-1111-4111-8111-111111111111"
_RUN_ID = "22222222-2222-4222-8222-222222222222"
_STORY_ERROR_KEYS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
}
_COMMAND_REQUESTS = (
    ("POST", "/v1/story-runs", {"parent_profile_id": _PROFILE_ID}),
    (
        "POST",
        f"/v1/story-runs/{_RUN_ID}/context-confirmation",
        {
            "expected_context_revision": 1,
            "context_snapshot_sha256": "a" * 64,
            "confirmed": True,
        },
    ),
    (
        "POST",
        f"/v1/story-runs/{_RUN_ID}/subject-confirmation",
        {"expected_understanding_revision": 1, "confirmed_subject": "butterfly"},
    ),
    (
        "POST",
        f"/v1/story-runs/{_RUN_ID}/script-confirmation",
        {"expected_revision": 1, "story_sha256": "b" * 64},
    ),
)


class _FakeDb:
    def get(self, _model: object, _identity: object) -> SimpleNamespace:
        return SimpleNamespace(
            account_id="account-1",
            issuer=_PRINCIPAL.issuer,
            account_role="parent",
            state="active",
        )


class _FakeStoryRunService:
    def replay_create_run(self, **_kwargs: object) -> None:
        return None

    def create_run(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS")

    def get_run(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    def get_active_run(self, **_kwargs: object) -> None:
        return None

    def confirm_context(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def confirm_subject(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def confirm_story_revision(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")


class _DenyParentRoleReader:
    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        del principal
        return False


@pytest.fixture
def request_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-storyrun-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    monkeypatch.setattr(
        story_routes,
        "_service",
        lambda _db: _FakeStoryRunService(),
    )
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: _PRINCIPAL
    application.dependency_overrides[get_db] = _FakeDb
    application.dependency_overrides[get_parent_principal] = lambda: _PRINCIPAL
    application.dependency_overrides[get_parent_profile_service] = lambda: SimpleNamespace()
    application.dependency_overrides[get_parent_role_reader] = _DenyParentRoleReader
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _assert_story_error(
    response: Response, *, status: int, code: str, request_id: str
) -> None:
    assert response.status_code == status
    body = response.json()
    assert set(body) == _STORY_ERROR_KEYS
    assert "detail" not in body
    assert body["code"] == code
    assert isinstance(body["message"], str) and body["message"]
    assert body["correlation_id"] == request_id
    assert body["retryable"] is False
    assert body["retry_after_seconds"] is None
    assert body["field_errors"] is None or isinstance(body["field_errors"], list)
    assert response.headers["X-Request-ID"] == request_id


def _command_response(
    client: TestClient,
    *,
    method: str,
    path: str,
    payload: dict[str, object],
    key: str,
) -> Response:
    return client.request(
        method,
        path,
        json=payload,
        headers={"Idempotency-Key": key, "X-Request-ID": "story-command-1"},
    )


def test_six_parent_story_run_routes_are_mounted_with_the_story_error_shape(
    request_client: TestClient,
) -> None:
    requests = (
        (
            "POST",
            "/v1/story-runs",
            {"parent_profile_id": _PROFILE_ID},
            "ACTIVE_RUN_EXISTS",
            409,
        ),
        (
            "GET",
            f"/v1/story-runs/{_RUN_ID}",
            None,
            "RESOURCE_NOT_FOUND",
            404,
        ),
        ("GET", "/v1/story-runs/active/current", None, None, 200),
        (
            "POST",
            f"/v1/story-runs/{_RUN_ID}/context-confirmation",
            {
                "expected_context_revision": 1,
                "context_snapshot_sha256": "a" * 64,
                "confirmed": True,
            },
            "INVALID_STATE_TRANSITION",
            409,
        ),
        (
            "POST",
            f"/v1/story-runs/{_RUN_ID}/subject-confirmation",
            {"expected_understanding_revision": 1, "confirmed_subject": "butterfly"},
            "INVALID_STATE_TRANSITION",
            409,
        ),
        (
            "POST",
            f"/v1/story-runs/{_RUN_ID}/script-confirmation",
            {"expected_revision": 1, "story_sha256": "b" * 64},
            "INVALID_STATE_TRANSITION",
            409,
        ),
    )

    for index, (method, path, payload, code, status) in enumerate(requests):
        request_id = f"story-route-{index}"
        headers = {"X-Request-ID": request_id}
        if method == "POST":
            headers["Idempotency-Key"] = "valid-key"
        response = request_client.request(method, path, json=payload, headers=headers)
        if code is None:
            assert response.status_code == status
            assert set(response.json()) == {"request_id", "story_run"}
            assert response.json()["story_run"] is None
        else:
            _assert_story_error(response, status=status, code=code, request_id=request_id)


@pytest.mark.parametrize(("method", "path", "payload"), _COMMAND_REQUESTS)
@pytest.mark.parametrize("key_length", (1, 256))
def test_story_command_idempotency_key_accepts_both_length_bounds(
    request_client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object],
    key_length: int,
) -> None:
    response = _command_response(
        request_client,
        method=method,
        path=path,
        payload=payload,
        key="k" * key_length,
    )
    expected_code = (
        "ACTIVE_RUN_EXISTS" if path == "/v1/story-runs" else "INVALID_STATE_TRANSITION"
    )
    _assert_story_error(
        response,
        status=409,
        code=expected_code,
        request_id="story-command-1",
    )


@pytest.mark.parametrize(("method", "path", "payload"), _COMMAND_REQUESTS)
@pytest.mark.parametrize("key_length", (0, 257))
def test_story_command_idempotency_key_rejects_out_of_range_lengths(
    request_client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object],
    key_length: int,
) -> None:
    request_id = "story-invalid-key"
    response = request_client.request(
        method,
        path,
        json=payload,
        headers={"Idempotency-Key": "k" * key_length, "X-Request-ID": request_id},
    )
    _assert_story_error(
        response,
        status=400,
        code="INVALID_IDEMPOTENCY_KEY",
        request_id=request_id,
    )
    assert response.json()["field_errors"] == [
        {
            "field": "Idempotency-Key",
            "code": "INVALID_FIELD",
            "message": "Giá trị trường không hợp lệ.",
        }
    ]


def test_parent_profile_errors_keep_the_parent_specific_shape(
    request_client: TestClient,
) -> None:
    story_request_id = "story-shape-1"
    story = request_client.get(
        f"/v1/story-runs/{_RUN_ID}", headers={"X-Request-ID": story_request_id}
    )
    _assert_story_error(
        story, status=404, code="RESOURCE_NOT_FOUND", request_id=story_request_id
    )

    parent_request_id = "parent-shape-1"
    parent = request_client.get(
        "/v1/parent/profiles", headers={"X-Request-ID": parent_request_id}
    )
    assert parent.status_code == 403
    body = parent.json()
    assert set(body) == {
        "code",
        "message",
        "correlation_id",
        "retryable",
        "request_id",
    }
    assert "detail" not in body
    assert "retry_after_seconds" not in body
    assert body["code"] == "ACTION_NOT_ALLOWED"
    assert body["request_id"] == parent_request_id
    assert body["correlation_id"] == parent_request_id
