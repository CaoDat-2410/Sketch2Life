"""Disposable PostgreSQL databases for BE2-01 Phase B migration tests (synthetic only).

Configure with ``BE2_TEST_PG_HOST`` (plus optional ``BE2_TEST_PG_PORT``, ``BE2_TEST_PG_USER``,
``BE2_TEST_PG_MAINTENANCE_DB``) and ``BE2_TEST_PG_PASSWORD_FILE`` pointing at a private file.
Each test gets a freshly created ``be2_b2_<random>`` database that is dropped afterwards, so no
existing database is migrated, downgraded or read. Without ``BE2_TEST_PG_HOST`` the PostgreSQL
tests are skipped, which counts as NOT_RUN, never PASS.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.engine import URL


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "requires_postgres: needs a disposable PostgreSQL 17 server (else NOT_RUN)"
    )


def _server_url(database: str) -> URL | None:
    host = os.environ.get("BE2_TEST_PG_HOST")
    if not host:
        return None
    secret_path = os.environ.get("BE2_TEST_PG_PASSWORD_FILE")
    credential = Path(secret_path).read_text(encoding="utf-8").strip() if secret_path else None
    return URL.create(
        "postgresql+psycopg",
        username=os.environ.get("BE2_TEST_PG_USER", "be2_test"),
        password=credential,
        host=host,
        port=int(os.environ.get("BE2_TEST_PG_PORT", "5432")),
        database=database,
    )


@pytest.fixture
def disposable_database_url() -> Iterator[URL]:
    maintenance = _server_url(os.environ.get("BE2_TEST_PG_MAINTENANCE_DB", "postgres"))
    if maintenance is None:
        pytest.skip("BE2_TEST_PG_HOST not set: PostgreSQL migration checks NOT_RUN")
    import psycopg

    name = f"be2_b2_{uuid.uuid4().hex[:16]}"

    def admin() -> psycopg.Connection[tuple[object, ...]]:
        return psycopg.connect(
            host=maintenance.host,
            port=maintenance.port,
            user=maintenance.username,
            password=maintenance.password,
            dbname=maintenance.database,
            connect_timeout=10,
            autocommit=True,
        )

    with admin() as connection:
        version = connection.execute("SHOW server_version").fetchone()
        assert version is not None and str(version[0]).startswith("17."), "PostgreSQL 17 required"
        connection.execute(f'CREATE DATABASE "{name}"')
    try:
        yield maintenance.set(database=name)
    finally:
        with admin() as connection:
            connection.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
