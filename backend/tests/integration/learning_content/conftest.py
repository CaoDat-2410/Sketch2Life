"""Explicitly opted-in disposable PostgreSQL 17 only; no server/container start."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

from sketch2life.infrastructure.config.settings import get_core_database_settings


@pytest.fixture(autouse=True)
def isolated_database_config() -> Iterator[None]:
    """Every disposable DB has its own URL; never retain a dropped DB in cache."""
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_core_database_settings.cache_clear()


@pytest.fixture
def content_engine() -> Iterator[Engine]:
    if (os.environ.get("LC_TEST_ALLOW_CREATE") != "1"
            or not os.environ.get("LC_TEST_PG_HOST")):
        pytest.skip("NOT_RUN: authorized disposable PostgreSQL profile not configured")
    import psycopg
    from psycopg import sql

    secret_file = os.environ.get("LC_TEST_PG_PASSWORD_FILE")
    password = Path(secret_file).read_text().strip() if secret_file else None
    host = os.environ["LC_TEST_PG_HOST"]
    port = int(os.environ.get("LC_TEST_PG_PORT", "5432"))
    user = os.environ.get("LC_TEST_PG_USER", "be2_test")
    database = "lc_48_" + uuid.uuid4().hex

    def admin():
        return psycopg.connect(
            host=host, port=port, user=user, password=password,
            dbname=os.environ.get("LC_TEST_PG_MAINTENANCE_DB", "postgres"),
            autocommit=True, connect_timeout=10)

    with admin() as connection:
        version = connection.execute("SHOW server_version").fetchone()
        assert version and str(version[0]).startswith("17."), "PostgreSQL 17 required"
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    engine = create_engine(URL.create(
        "postgresql+psycopg", username=user, password=password, host=host, port=port,
        database=database), hide_parameters=True)
    try:
        yield engine
    finally:
        engine.dispose()
        # Exact locally generated target only; no caller-provided DB is dropped.
        assert database.startswith("lc_48_") and len(database) == 38
        with admin() as connection:
            connection.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                sql.Identifier(database)))
