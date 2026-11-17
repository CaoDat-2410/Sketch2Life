"""BE2-14 PG17 opt-in only. Never starts a server or reuses another card's opt-in."""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL

from sketch2life.infrastructure.config.settings import get_core_database_settings


@pytest.fixture(autouse=True)
def clear_policy_database_cache() -> Iterator[None]:
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_core_database_settings.cache_clear()


@pytest.fixture
def policy_engine() -> Iterator[Engine]:
    if os.environ.get("AP_TEST_ALLOW_CREATE") != "1" or not os.environ.get("AP_TEST_PG_HOST"):
        pytest.skip("NOT_RUN: authorized BE2-14 disposable PostgreSQL profile required")
    import psycopg
    from psycopg import sql

    host = os.environ["AP_TEST_PG_HOST"]
    port = int(os.environ.get("AP_TEST_PG_PORT", "5432"))
    user = os.environ.get("AP_TEST_PG_USER", "be2_test")
    secret = os.environ.get("AP_TEST_PG_PASSWORD_FILE")
    password = Path(secret).read_text().strip() if secret else None
    database = "ap49_" + uuid.uuid4().hex

    def admin():
        return psycopg.connect(host=host, port=port, user=user, password=password,
                               dbname=os.environ.get("AP_TEST_PG_MAINTENANCE_DB", "postgres"),
                               autocommit=True, connect_timeout=10)

    with admin() as connection:
        version = connection.execute("SHOW server_version").fetchone()
        assert version and str(version[0]).startswith("17."), "PostgreSQL17 required"
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    engine = create_engine(URL.create("postgresql+psycopg", username=user, password=password,
                                     host=host, port=port, database=database), hide_parameters=True)
    try:
        yield engine
    finally:
        engine.dispose()
        assert database.startswith("ap49_") and len(database) == 37
        with admin() as connection:
            connection.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                sql.Identifier(database)))
