"""FEAT-066 T0.3: readiness against a real PostgreSQL engine (SRS l.814).

Runs only against a disposable database whose name contains ``be1_acceptance``. No container is
stopped: the "database down" case repoints the in-process engine at a closed local port.
"""

from __future__ import annotations

import os
import secrets
import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.database import create_core_engine
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.routers import health as health_module

CLOSED_URL = "postgresql+psycopg://synthetic_user:synthetic_pw@127.0.0.1:9/t03_closed"


@pytest.fixture
def probe_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, str]]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    probe_credential = secrets.token_urlsafe(32)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_OPS_PROBE_TOKEN", probe_credential)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    application = create_app()
    assert application.state.be1_runtime.engine is not None
    client = TestClient(
        application,
        base_url="http://api.example.test",
        client=("203.0.113.9", 4000),
        raise_server_exceptions=False,
    )
    yield client, probe_credential
    application.state.be1_runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _auth(probe_credential: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {probe_credential}"}


def test_ready_is_200_with_the_real_engine_and_requires_the_credential(
    probe_api: tuple[TestClient, str],
) -> None:
    client, probe_credential = probe_api

    assert client.get("/health/ready").status_code == 401
    response = client.get("/health/ready", headers=_auth(probe_credential))

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "up"}}
    assert response.headers["Cache-Control"] == "no-store"
    assert health_module._probe_threads == 0


def test_ready_does_not_use_the_request_pool_and_metrics_never_query(
    probe_api: tuple[TestClient, str],
) -> None:
    client, probe_credential = probe_api
    engine = client.app.state.be1_runtime.engine  # type: ignore[attr-defined]
    statements: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _record(_conn, _cursor, statement, *_rest) -> None:  # type: ignore[no-untyped-def]
        statements.append(statement)

    assert client.get("/metrics", headers=_auth(probe_credential)).status_code == 200
    assert client.get("/health/ready", headers=_auth(probe_credential)).status_code == 200
    assert statements == []
    assert engine.pool.checkedout() == 0


def test_ready_turns_503_when_the_engine_is_repointed_at_a_closed_port(
    probe_api: tuple[TestClient, str],
) -> None:
    client, probe_credential = probe_api
    runtime = client.app.state.be1_runtime  # type: ignore[attr-defined]
    assert client.get("/health/ready", headers=_auth(probe_credential)).status_code == 200

    runtime.engine.dispose()
    runtime.engine = create_core_engine(CLOSED_URL)
    started = time.monotonic()
    response = client.get("/health/ready", headers=_auth(probe_credential))

    assert time.monotonic() - started < 4.5
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "down"}}
    for word in ("synthetic", "127.0.0.1", "psycopg", "refused", "t03_closed"):
        assert word not in response.text
