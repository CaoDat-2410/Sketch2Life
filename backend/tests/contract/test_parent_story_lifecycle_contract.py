"""FR-C-08 Parent lifecycle API contract over the composed app (Contract Draft 11 §3).

Cancel and delete return 202 with the lifecycle envelope; GET returns the live envelope before
DELETE_PENDING and the lifecycle envelope from it on; replays of the create and three
confirmation routes of a purged run return the lifecycle envelope under their normal status;
the two Parent AI routes refuse a purged run with 409 or replay the envelope. Errors use the M2
Parent envelope. The services are fakes: no database, storage or provider is reached.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, NoReturn
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_ai as parent_ai
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_request_id
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"
_PROJECTION_KEYS = {
    "run_id",
    "run_state",
    "revision",
    "version",
    "lifecycle_request_ref",
    "purge_state",
}
_ERROR_KEYS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
}


def _lifecycle(state: str = "DELETE_PENDING") -> ParentStoryLifecycleRecord:
    return ParentStoryLifecycleRecord(
        run_id=_RUN_ID,
        run_state=state,
        revision=4,
        version=6,
        lifecycle_request_ref=lifecycle_request_id(_RUN_ID),
        purge_state="COMPLETED" if state == "DELETED" else "PENDING",
    )


def _live() -> ParentStoryRunRecord:
    now = datetime.now(UTC)
    return ParentStoryRunRecord(
        run_id=_RUN_ID,
        run_state="SCRIPT_REVIEW",
        run_revision=3,
        parent_profile_id=UUID("11111111-1111-4111-8111-111111111111"),
        profile_revision_ref=UUID("33333333-3333-4333-8333-333333333333"),
        context_revision=1,
        context_confirmed=True,
        context_snapshot={
            "schema_version": "sketch2life.parent-context.v1",
            "profile_revision_ref": "33333333-3333-4333-8333-333333333333",
            "age_months": 72,
            "interests_summary": "",
            "topic": "",
            "adult_confirmed_idea": "",
        },
        context_snapshot_sha256="a" * 64,
        current_input_revision=2,
        understanding_revision=1,
        subject_label="butterfly",
        candidate=None,
        story_revision_id=None,
        story_revision_no=None,
        story_status=None,
        story_sha256=None,
        story_content=None,
        job_state="SUCCEEDED",
        retryable=False,
        error_code=None,
        created_at=now,
        updated_at=now,
    )


class _Service:
    def __init__(self) -> None:
        self.view: Any = _lifecycle()
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _record(self, name: str, kwargs: dict[str, Any]) -> Any:
        self.calls.append((name, kwargs))
        if isinstance(self.view, Exception):
            raise self.view
        return self.view

    def replay_create_run(self, **kwargs: Any) -> Any:
        return self._record("replay_create_run", kwargs)

    def get_run(self, **kwargs: Any) -> Any:
        return self._record("get_run", kwargs)

    def get_active_run(self, **_kwargs: Any) -> None:
        return None

    def cancel_run(self, **kwargs: Any) -> Any:
        return self._record("cancel_run", kwargs)

    def delete_run(self, **kwargs: Any) -> Any:
        return self._record("delete_run", kwargs)

    def confirm_context(self, **kwargs: Any) -> Any:
        return self._record("confirm_context", kwargs)

    def confirm_subject(self, **kwargs: Any) -> Any:
        return self._record("confirm_subject", kwargs)

    def confirm_story_revision(self, **kwargs: Any) -> Any:
        return self._record("confirm_story_revision", kwargs)

    def reserve_story_revision(self, **kwargs: Any) -> Any:
        self.calls.append(("reserve_story_revision", kwargs))
        return ParentStoryRevisionReservation(
            run_id=_RUN_ID,
            story_revision_id="r",
            revision_no=0,
            understanding_revision=0,
            context_revision=0,
            source_asset_sha256="",
            worker_input={},
            request_sha256="0" * 64,
            receipt_id="r",
            replayed=True,
            lifecycle=_lifecycle("DELETED"),
        )


class _Repository:
    def read_current_input(self, **_kwargs: Any) -> NoReturn:
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def get_run(self, **_kwargs: Any) -> NoReturn:
        raise AssertionError("a purged replay must not rebuild the run")


class _FakeDb:
    def get(self, _model: object, _identity: object) -> SimpleNamespace:
        return SimpleNamespace(
            account_id="account-1",
            issuer=_PRINCIPAL.issuer,
            account_role="parent",
            state="active",
        )


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, _Service]]:
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
    service = _Service()
    monkeypatch.setattr(story_routes, "_service", lambda _db: service)
    monkeypatch.setattr(parent_ai, "_story_service", lambda _db: service)
    monkeypatch.setattr(parent_ai, "SqlParentStoryRunRepository", lambda _db: _Repository())
    monkeypatch.setattr(parent_ai, "_require_modal_dev", lambda: None)
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: _PRINCIPAL
    application.dependency_overrides[get_db] = _FakeDb
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client, service
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _assert_lifecycle(response: Any, status: int, state: str = "DELETE_PENDING") -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"request_id", "lifecycle"}
    assert set(body["lifecycle"]) == _PROJECTION_KEYS
    assert body["lifecycle"]["run_state"] == state
    assert body["lifecycle"]["lifecycle_request_ref"] == lifecycle_request_id(_RUN_ID)
    assert body["lifecycle"]["purge_state"] == ("COMPLETED" if state == "DELETED" else "PENDING")
    for leaked in ("story_run", "context_snapshot", "subject_label", "profile", "asset"):
        assert leaked not in response.text


def test_cancel_returns_202_with_the_lifecycle_envelope(
    harness: tuple[TestClient, _Service],
) -> None:
    client, service = harness
    response = client.post(
        f"/v1/story-runs/{_RUN_ID}/cancel",
        json={"expected_revision": 3},
        headers={"Idempotency-Key": "c" * 128},
    )
    _assert_lifecycle(response, 202)
    assert service.calls[-1][1]["expected_revision"] == 3


def test_delete_returns_202_with_the_lifecycle_envelope_and_takes_no_body(
    harness: tuple[TestClient, _Service],
) -> None:
    client, service = harness
    response = client.delete(f"/v1/story-runs/{_RUN_ID}", headers={"Idempotency-Key": "d-1"})
    _assert_lifecycle(response, 202)
    assert service.calls[-1][0] == "delete_run"
    assert "expected_revision" not in service.calls[-1][1]


def test_get_returns_the_live_envelope_before_and_the_projection_after_delete_pending(
    harness: tuple[TestClient, _Service],
) -> None:
    client, service = harness
    service.view = _live()
    live = client.get(f"/v1/story-runs/{_RUN_ID}")
    assert live.status_code == 200
    assert set(live.json()) == {"request_id", "story_run"}
    service.view = _lifecycle("DELETE_PENDING")
    _assert_lifecycle(client.get(f"/v1/story-runs/{_RUN_ID}"), 200)
    service.view = _lifecycle("DELETED")
    _assert_lifecycle(client.get(f"/v1/story-runs/{_RUN_ID}"), 200, "DELETED")


@pytest.mark.parametrize(
    ("path", "payload", "status"),
    (
        ("/v1/story-runs", {"parent_profile_id": "11111111-1111-4111-8111-111111111111"}, 201),
        (
            f"/v1/story-runs/{_RUN_ID}/context-confirmation",
            {
                "expected_context_revision": 1,
                "context_snapshot_sha256": "a" * 64,
                "confirmed": True,
            },
            200,
        ),
        (
            f"/v1/story-runs/{_RUN_ID}/subject-confirmation",
            {"expected_understanding_revision": 1, "confirmed_subject": "butterfly"},
            200,
        ),
        (
            f"/v1/story-runs/{_RUN_ID}/script-confirmation",
            {"expected_revision": 1, "story_sha256": "b" * 64},
            200,
        ),
    ),
)
def test_replays_of_a_purged_run_return_the_lifecycle_envelope_under_the_normal_status(
    harness: tuple[TestClient, _Service], path: str, payload: dict[str, Any], status: int
) -> None:
    client, service = harness
    service.view = _lifecycle("DELETED")
    response = client.post(path, json=payload, headers={"Idempotency-Key": "replay-1"})
    _assert_lifecycle(response, status, "DELETED")


def test_drawing_understanding_refuses_a_purged_run_with_409(
    harness: tuple[TestClient, _Service],
) -> None:
    client, _service = harness
    response = client.post(
        "/api/parent/v1/ai/drawing-understandings",
        json={
            "story_run_id": _RUN_ID,
            "media_type": "image/png",
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",
        },
        headers={"X-Request-ID": "drawing-purged"},
    )
    assert response.status_code == 409, response.text
    assert set(response.json()) >= _ERROR_KEYS
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert response.json()["correlation_id"] == "drawing-purged"


def test_story_revision_replay_of_a_purged_run_returns_the_lifecycle_envelope(
    harness: tuple[TestClient, _Service],
) -> None:
    client, _service = harness
    response = client.post(
        f"/api/parent/v1/ai/story-runs/{_RUN_ID}/story-revisions",
        json={"expected_understanding_revision": 1},
        headers={"Idempotency-Key": "story-replay"},
    )
    _assert_lifecycle(response, 200, "DELETED")
    assert response.headers["Idempotency-Replayed"] == "true"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    (
        ("POST", f"/v1/story-runs/{_RUN_ID}/cancel", {"expected_revision": 3}),
        ("DELETE", f"/v1/story-runs/{_RUN_ID}", None),
    ),
)
def test_a_second_command_on_a_purged_run_is_a_409_parent_error(
    harness: tuple[TestClient, _Service], method: str, path: str, payload: Any
) -> None:
    client, service = harness
    service.view = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    response = client.request(
        method, path, json=payload, headers={"Idempotency-Key": "k-2", "X-Request-ID": "second"}
    )
    assert response.status_code == 409
    assert set(response.json()) == _ERROR_KEYS
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert response.headers["X-Request-ID"] == "second"


def test_only_the_cancel_stale_revision_error_carries_current_version(
    harness: tuple[TestClient, _Service],
) -> None:
    client, service = harness
    service.view = ParentStoryRunError(409, "STALE_REVISION", current_version=4)
    cancel = client.post(
        f"/v1/story-runs/{_RUN_ID}/cancel",
        json={"expected_revision": 3},
        headers={"Idempotency-Key": "k-3"},
    )
    assert cancel.json()["current_version"] == 4
    delete = client.delete(f"/v1/story-runs/{_RUN_ID}", headers={"Idempotency-Key": "k-4"})
    assert "current_version" not in delete.json()


def test_a_missing_run_is_404_before_anything_else(harness: tuple[TestClient, _Service]) -> None:
    client, service = harness
    service.view = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    for method, path, payload in (
        ("POST", f"/v1/story-runs/{_RUN_ID}/cancel", {"expected_revision": 3}),
        ("DELETE", f"/v1/story-runs/{_RUN_ID}", None),
        ("GET", f"/v1/story-runs/{_RUN_ID}", None),
    ):
        response = client.request(method, path, json=payload, headers={"Idempotency-Key": "k"})
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
