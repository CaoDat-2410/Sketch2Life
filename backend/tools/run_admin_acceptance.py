"""Create, migrate, test and remove a disposable local Admin acceptance database."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from sketch2life.infrastructure.config.settings import get_core_database_settings


def main():
    configured = get_core_database_settings().database_url
    if configured is None:
        raise RuntimeError("Configure the local database before running acceptance checks")
    url = make_url(configured.get_secret_value()).set(
        host=os.environ.get("ADMIN_TEST_POSTGRES_HOST", "127.0.0.1"),
        port=int(os.environ.get("ADMIN_TEST_POSTGRES_PORT", "5432")),
    )
    if url.host not in {"127.0.0.1", "localhost", "postgres"}:
        raise RuntimeError(
            "This runner only creates disposable databases on a local PostgreSQL host"
        )
    admin_url = url.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    name = "sketch2life_admin_acceptance_" + uuid4().hex[:12]
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    env = os.environ.copy()
    env["SKETCH2LIFE_DATABASE_URL"] = url.set(database=name).render_as_string(hide_password=False)
    env["ADMIN_TEST_DATABASE_URL"] = env["SKETCH2LIFE_DATABASE_URL"]
    env["SKETCH2LIFE_ENV"] = "test"
    env["PYTHONIOENCODING"] = "utf-8"
    root = Path(__file__).resolve().parents[1]
    try:
        migration = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "heads"], env=env, cwd=root
        )
        if migration.returncode:
            return migration.returncode
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/test_platform_admin_workflows.py",
                "-x",
            ],
            env=env,
            cwd=root,
        ).returncode
    finally:
        with psycopg.connect(admin_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )
        print("Disposable Admin acceptance database removed")


if __name__ == "__main__":
    raise SystemExit(main())
