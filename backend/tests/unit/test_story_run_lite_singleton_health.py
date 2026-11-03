from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text

from sketch2life.domain.story_run_lite import StoryRunLiteError
from sketch2life.infrastructure.story_run_lite.composition import (
    StoryRunLiteRuntime,
    goal_database_url,
    verify_goal_database_owner,
)
from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineStore
from sketch2life.infrastructure.story_run_lite.repository import SqlStoryRunLiteRepository
from sketch2life.interfaces.http.story_run_lite_app import create_app


def _repository(tmp_path, *, acquired: bool = True):
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    connection.closed = False
    connection.invalidated = False
    connection.execution_options.return_value = connection
    connection.execute.return_value.one.return_value = (41, acquired)
    engine = Mock()
    engine.connect.return_value = connection
    repository = SqlStoryRunLiteRepository(
        engine=cast(Engine, engine), quarantine=QuarantineStore(tmp_path)
    )
    return repository, engine, connection


def test_startup_uses_nonblocking_lock_and_refuses_second_owner(tmp_path):
    repository, _engine, connection = _repository(tmp_path, acquired=False)
    with pytest.raises(RuntimeError, match="already held"):
        repository.acquire_singleton_lock()
    sql = str(connection.execute.call_args.args[0])
    assert "pg_try_advisory_lock" in sql
    assert "pg_advisory_lock(" not in sql
    connection.invalidate.assert_called_once()
    connection.close.assert_called_once()


def test_probe_checks_session_identity_and_exact_advisory_lock(tmp_path):
    repository, engine, connection = _repository(tmp_path)
    repository.acquire_singleton_lock()
    repository.require_singleton_lock()
    sql = str(connection.execute.call_args.args[0])
    assert "pg_locks" in sql and "pg_backend_pid()" in sql
    assert "classid" in sql and "objid" in sql and "objsubid = 1" in sql
    assert connection.execute.call_args.args[1] == {"scope": "storyrun-lite-singleton-v1"}
    engine.connect.assert_called_once()


def test_concurrent_probes_serialize_the_pinned_connection(tmp_path):
    repository, engine, connection = _repository(tmp_path)
    repository.acquire_singleton_lock()
    counter_lock = Lock()
    active = 0
    maximum = 0

    def probe(*_args, **_kwargs):
        nonlocal active, maximum
        with counter_lock:
            active += 1
            maximum = max(maximum, active)
        time.sleep(0.005)
        with counter_lock:
            active -= 1
        result = Mock()
        result.one.return_value = (41, True)
        return result

    connection.execute.side_effect = probe
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _index: repository.require_singleton_lock(), range(16)))
    assert maximum == 1
    assert connection.execute.call_count == 17
    engine.connect.assert_called_once()


@pytest.mark.parametrize("backend_pid, owns_lock", [(42, True), (41, False)])
def test_lost_or_replaced_session_latches_unready_without_reacquiring(
    tmp_path, backend_pid, owns_lock
):
    repository, engine, connection = _repository(tmp_path)
    repository.acquire_singleton_lock()
    connection.execute.return_value.one.return_value = (backend_pid, owns_lock)
    with pytest.raises(StoryRunLiteError) as error:
        repository.require_singleton_lock()
    assert error.value.status_code == 503
    assert error.value.code == "SERVICE_NOT_READY"
    assert error.value.retryable is False
    before = connection.execute.call_count
    with pytest.raises(StoryRunLiteError):
        repository.require_singleton_lock()
    with pytest.raises(RuntimeError, match="ownership was lost"):
        repository.acquire_singleton_lock()
    assert connection.execute.call_count == before
    engine.connect.assert_called_once()
    connection.invalidate.assert_called_once()


@pytest.mark.parametrize("mode", ["invalidated", "closed", "network"])
def test_dead_connection_fails_closed_and_release_does_not_query_it(tmp_path, mode):
    repository, _engine, connection = _repository(tmp_path)
    repository.acquire_singleton_lock()
    if mode == "network":
        connection.execute.side_effect = OSError("connection terminated")
    else:
        setattr(connection, mode, True)
    with pytest.raises(StoryRunLiteError, match="ownership is unavailable"):
        repository.require_singleton_lock()
    before = connection.execute.call_count
    repository.release_singleton_lock()
    assert connection.execute.call_count == before


def test_shutdown_closes_physical_session_without_waiting_for_unlock_query(tmp_path):
    repository, _engine, connection = _repository(tmp_path)
    repository.acquire_singleton_lock()
    before = connection.execute.call_count
    repository.release_singleton_lock()
    assert connection.execute.call_count == before
    connection.invalidate.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.parametrize(
    "method, path, body",
    [
        ("GET", "/v1/story-runs/synthetic", None),
        ("POST", "/v1/story-runs", {"profile_ref": "synthetic-parent-demo"}),
        ("POST", "/v1/story-runs/synthetic/cancel", {"expected_revision": 1}),
    ],
)
def test_http_readiness_failure_rejects_new_work_before_service(method, path, body):
    service = Mock()
    repository = Mock()
    repository.require_singleton_lock.side_effect = StoryRunLiteError(
        503, "SERVICE_NOT_READY", "singleton ownership unavailable", retryable=False
    )
    app = create_app(service=service)
    app.state.story_run_lite_runtime = SimpleNamespace(repository=repository)
    with TestClient(app) as client:
        response = client.request(
            method,
            path,
            json=body,
            headers={"Idempotency-Key": "synthetic-key", "If-Match": '"v1"'},
        )
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_NOT_READY"
    assert response.json()["retryable"] is False
    assert service.mock_calls == []


def test_public_readiness_requires_runtime_even_with_injected_service():
    service = Mock()
    with TestClient(create_app(service=service)) as client:
        response = client.get("/v1/story-runs/readiness")
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_NOT_READY"
    assert response.headers["cache-control"] == "no-store"
    service.get_run.assert_not_called()


def test_public_readiness_checks_runtime_without_calling_business_service(tmp_path):
    repository, engine, connection = _repository(tmp_path)
    repository.acquire_singleton_lock()
    service = Mock()
    runtime = StoryRunLiteRuntime(engine, repository, service, Mock())
    app = create_app(service=service)
    app.state.story_run_lite_runtime = runtime
    with TestClient(app) as client:
        ready = client.get("/v1/story-runs/readiness")
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready", "service": "storyrun-lite"}
        assert ready.headers["cache-control"] == "no-store"
        connection.execute.return_value.one.return_value = (41, False)
        assert client.get("/v1/story-runs/readiness").status_code == 503
        before = connection.execute.call_count
        assert client.get("/v1/story-runs/readiness").status_code == 503
        assert connection.execute.call_count == before
    assert service.mock_calls == []


def test_postgres_terminated_session_fails_old_instance_and_allows_new_owner(tmp_path):
    value = os.environ.get("STORYRUN_LITE_DATABASE_URL")
    if not value:
        pytest.skip("requires a separately verified task-owned loopback PostgreSQL database")
    safe_url, database_name = goal_database_url(value)
    engine = create_engine(safe_url, pool_pre_ping=True, hide_parameters=True)
    assert verify_goal_database_owner(engine, database_name)
    old = SqlStoryRunLiteRepository(engine=engine, quarantine=QuarantineStore(tmp_path / "old"))
    new = SqlStoryRunLiteRepository(engine=engine, quarantine=QuarantineStore(tmp_path / "new"))
    service = Mock()
    app = create_app(service=service)
    app.state.story_run_lite_runtime = StoryRunLiteRuntime(engine, old, service, Mock())
    try:
        old.acquire_singleton_lock()
        with TestClient(app) as client:
            assert client.get("/v1/story-runs/readiness").status_code == 200
        started = time.monotonic()
        with pytest.raises(RuntimeError, match="already held"):
            new.acquire_singleton_lock()
        assert time.monotonic() - started < 5
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT pg_terminate_backend(:pid)"), {"pid": old._singleton_backend_pid}
            ).scalar_one()
        with pytest.raises(StoryRunLiteError):
            old.require_singleton_lock()
        with TestClient(app) as client:
            assert client.get("/v1/story-runs/readiness").status_code == 503
        new.acquire_singleton_lock()
        new.require_singleton_lock()
        app.state.story_run_lite_runtime = StoryRunLiteRuntime(engine, new, service, Mock())
        with TestClient(app) as client:
            assert client.get("/v1/story-runs/readiness").status_code == 200
        with pytest.raises(StoryRunLiteError):
            old.require_singleton_lock()
    finally:
        old.release_singleton_lock()
        new.release_singleton_lock()
        engine.dispose()
