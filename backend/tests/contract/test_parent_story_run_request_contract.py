"""Offline request-level contracts for the composed Parent StoryRun routes."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import NoReturn, cast
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import Response

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRunError,
    ParentStoryRunSummary,
)
from sketch2life.application.ports.story_run_lifecycle import (
    CANCEL_ELIGIBLE_STATES,
    DELETE_ELIGIBLE_STATES,
    PUBLIC_RUN_STATES,
    PURGE_STATES,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    run_summary_capabilities,
)
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
# FR-C-08 (Contract Draft 11 §3.1-§3.2, D-217 item 7): cancel and delete read the key with
# the CONV-1 parser (1-128 visible ASCII); the other Parent commands keep 1-256.
_LIFECYCLE_REQUESTS = (
    ("POST", f"/v1/story-runs/{_RUN_ID}/cancel", {"expected_revision": 1}),
    ("DELETE", f"/v1/story-runs/{_RUN_ID}", None),
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

    def list_runs(self, **_kwargs: object) -> list[object]:
        return []

    def cancel_run(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def delete_run(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def confirm_context(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def confirm_subject(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def confirm_story_revision(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")


class _FakeCancelRepository:
    def cancel_run(self, **_kwargs: object) -> NoReturn:
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
    monkeypatch.setattr(
        story_routes,
        "SqlParentStoryRunRepository",
        lambda _db: _FakeCancelRepository(),
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


def test_parent_story_run_routes_are_mounted_with_the_story_error_shape(
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
        (
            "POST",
            f"/v1/story-runs/{_RUN_ID}/cancel",
            {"expected_revision": 1},
            "INVALID_STATE_TRANSITION",
            409,
        ),
        (
            "DELETE",
            f"/v1/story-runs/{_RUN_ID}",
            None,
            "INVALID_STATE_TRANSITION",
            409,
        ),
        ("GET", "/v1/story-runs/active/current", None, None, 200),
        # FEAT-081 C3b: the history list on the collection path.
        ("GET", "/v1/story-runs", None, "list", 200),
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
        if method in {"POST", "DELETE"}:
            headers["Idempotency-Key"] = "valid-key"
        response = request_client.request(method, path, json=payload, headers=headers)
        if code == "list":
            assert response.status_code == status
            assert set(response.json()) == {"request_id", "items", "next_cursor"}
        elif code is None:
            assert response.status_code == status
            assert set(response.json()) == {"request_id", "story_run"}
            assert response.json()["story_run"] is None
        else:
            _assert_story_error(response, status=status, code=code, request_id=request_id)


def test_cancel_stale_revision_adds_current_version_only_to_cancel_error(
    request_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def stale_cancel(**_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "STALE_REVISION", current_version=9)

    def stale_delete(**_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "STALE_REVISION", current_version=9)

    monkeypatch.setattr(
        story_routes,
        "_service",
        lambda _db: SimpleNamespace(
            cancel_run=stale_cancel,
            delete_run=stale_delete,
            confirm_context=_FakeStoryRunService().confirm_context,
        ),
    )
    delete = request_client.delete(
        f"/v1/story-runs/{_RUN_ID}",
        headers={"Idempotency-Key": "delete-key", "X-Request-ID": "delete-stale"},
    )
    assert delete.status_code == 409
    assert "current_version" not in delete.json()  # the delete route never carries it
    cancel = request_client.post(
        f"/v1/story-runs/{_RUN_ID}/cancel",
        json={"expected_revision": 8},
        headers={"Idempotency-Key": "cancel-key", "X-Request-ID": "cancel-stale"},
    )
    assert cancel.status_code == 409
    assert set(cancel.json()) == _STORY_ERROR_KEYS | {"current_version"}
    assert cancel.json()["code"] == "STALE_REVISION"
    assert cancel.json()["current_version"] == 9

    context = request_client.post(
        f"/v1/story-runs/{_RUN_ID}/context-confirmation",
        json={
            "expected_context_revision": 1,
            "context_snapshot_sha256": "a" * 64,
            "confirmed": True,
        },
        headers={"Idempotency-Key": "context-key", "X-Request-ID": "context-error"},
    )
    _assert_story_error(
        context, status=409, code="INVALID_STATE_TRANSITION", request_id="context-error"
    )


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


@pytest.mark.parametrize(("method", "path", "payload"), _LIFECYCLE_REQUESTS)
@pytest.mark.parametrize("key_length", (1, 128))
def test_lifecycle_commands_accept_keys_of_1_to_128_characters(
    request_client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object] | None,
    key_length: int,
) -> None:
    response = request_client.request(
        method,
        path,
        json=payload,
        headers={"Idempotency-Key": "k" * key_length, "X-Request-ID": "lifecycle-key"},
    )
    _assert_story_error(
        response, status=409, code="INVALID_STATE_TRANSITION", request_id="lifecycle-key"
    )


@pytest.mark.parametrize(("method", "path", "payload"), _LIFECYCLE_REQUESTS)
@pytest.mark.parametrize("key", ("", "k" * 129, "with space", "tab\tkey", None))
def test_lifecycle_commands_refuse_a_missing_or_invalid_key_with_invalid_request(
    request_client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object] | None,
    key: str | None,
) -> None:
    headers = {"X-Request-ID": "lifecycle-bad-key"}
    if key is not None:
        headers["Idempotency-Key"] = key
    response = request_client.request(method, path, json=payload, headers=headers)
    _assert_story_error(
        response, status=400, code="INVALID_REQUEST", request_id="lifecycle-bad-key"
    )
    # Contract Draft 11 §3.6 (N-1): key errors raised by parse_idempotency_key carry null.
    assert response.json()["field_errors"] is None


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


# --- FEAT-081 C3b: Parent run-history list ------------------------------------------------------

_SUMMARY_KEYS = {
    "run_id",
    "parent_profile_id",
    "run_state",
    "revision",
    "deleting",
    "can_cancel",
    "can_delete",
    "created_at",
    "updated_at",
}


def _history_rows(count: int) -> list[ParentStoryRunSummary]:
    moment = datetime(2026, 11, 19, 8, 0, tzinfo=UTC)
    return [
        ParentStoryRunSummary(
            run_id=f"33333333-3333-4333-8333-{index:012d}",
            parent_profile_id=UUID(_PROFILE_ID) if index % 2 == 0 else None,
            run_state="COMPLETED" if index % 2 == 0 else "DELETE_PENDING",
            revision=2,
            deleting=index % 2 == 1,
            can_cancel=False,
            can_delete=index % 2 == 0,
            created_at=moment,
            updated_at=moment,
        )
        for index in range(count)
    ]


def test_history_list_returns_summary_items_only(
    request_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, object] = {}

    def list_runs(**kwargs: object) -> list[ParentStoryRunSummary]:
        seen.update(kwargs)
        return _history_rows(3)

    monkeypatch.setattr(story_routes, "_service", lambda _db: SimpleNamespace(list_runs=list_runs))
    response = request_client.get("/v1/story-runs?limit=2", headers={"X-Request-ID": "history-1"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"request_id", "items", "next_cursor"}
    assert len(body["items"]) == 2
    assert all(set(item) == _SUMMARY_KEYS for item in body["items"])
    assert body["items"][1]["parent_profile_id"] is None
    assert body["next_cursor"]
    assert seen["limit"] == 2 and seen["after"] is None and seen["profile_id"] is None

    follow = request_client.get(
        f"/v1/story-runs?cursor={body['next_cursor']}", headers={"X-Request-ID": "history-2"}
    )
    assert follow.status_code == 200
    created_at, run_id = cast(tuple[datetime, str], seen["after"])
    assert run_id == body["items"][1]["run_id"]
    assert created_at.tzinfo is not None


@pytest.mark.parametrize(
    "query", ["limit=101", "limit=0", "parent_profile_id=not-a-uuid", "cursor="]
)
def test_history_list_validation_uses_the_story_envelope(
    request_client: TestClient, query: str
) -> None:
    response = request_client.get(f"/v1/story-runs?{query}", headers={"X-Request-ID": "history-v"})
    _assert_story_error(response, status=400, code="INVALID_REQUEST", request_id="history-v")
    assert isinstance(response.json()["field_errors"], list)


def test_history_list_malformed_cursor_is_400_without_field_errors(
    request_client: TestClient,
) -> None:
    response = request_client.get(
        "/v1/story-runs?cursor=bm90LWEtY3Vyc29y", headers={"X-Request-ID": "history-c"}
    )
    _assert_story_error(response, status=400, code="INVALID_REQUEST", request_id="history-c")
    assert response.json()["field_errors"] is None


def test_history_list_refuses_a_non_parent(request_client: TestClient) -> None:
    class _TeacherDb:
        def get(self, _model: object, _identity: object) -> SimpleNamespace:
            return SimpleNamespace(
                account_id="account-2",
                issuer=_PRINCIPAL.issuer,
                account_role="teacher",
                state="active",
            )

    request_client.app.dependency_overrides[get_db] = _TeacherDb  # type: ignore[attr-defined]
    response = request_client.get("/v1/story-runs", headers={"X-Request-ID": "history-403"})
    _assert_story_error(response, status=403, code="ACTION_NOT_ALLOWED", request_id="history-403")


def test_history_capabilities_follow_the_lifecycle_sets() -> None:
    for state in PUBLIC_RUN_STATES:
        deleting, can_cancel, can_delete = run_summary_capabilities(state)
        assert deleting == (state in PURGE_STATES)
        assert can_cancel == (state in CANCEL_ELIGIBLE_STATES and state not in PURGE_STATES)
        assert can_delete == (state in DELETE_ELIGIBLE_STATES)
    assert run_summary_capabilities("ABANDONED") == (False, False, True)
    assert run_summary_capabilities("DELETE_PENDING") == (True, False, False)


def test_history_cursor_round_trip_and_rejections() -> None:
    moment = datetime(2026, 11, 19, 8, 0, 0, 123456, tzinfo=UTC)
    cursor = story_routes._encode_history_cursor(moment, _RUN_ID)
    assert story_routes._decode_history_cursor(cursor) == (moment, _RUN_ID)
    import base64
    import json

    def raw(payload: object) -> str:
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    for bad in (
        raw({"created_at": moment.isoformat(), "run_id": _RUN_ID, "v": 2}),
        raw({"created_at": "2026-11-19T08:00:00", "run_id": _RUN_ID, "v": 1}),
        raw({"created_at": moment.isoformat(), "run_id": "not-a-uuid", "v": 1}),
        "%%%",
    ):
        with pytest.raises(HTTPException) as caught:
            story_routes._decode_history_cursor(bad)
        assert caught.value.status_code == 400
