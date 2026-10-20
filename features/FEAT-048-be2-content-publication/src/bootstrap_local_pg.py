"""Create a constrained test role on the explicitly approved temporary cluster."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from psycopg import sql


def main() -> None:
    secret = Path(os.environ["LC_PG_BOOTSTRAP_PASSWORD_FILE"]).read_text().strip()
    runner_secret = Path(os.environ["LC_TEST_PG_PASSWORD_FILE"]).read_text().strip()
    with psycopg.connect(
        host="127.0.0.1", port=int(os.environ["LC_TEST_PG_PORT"]),
        user="lc_bootstrap", password=secret, dbname="postgres", autocommit=True,
    ) as connection:
        connection.execute(sql.SQL(
            "CREATE ROLE {} LOGIN CREATEDB NOSUPERUSER NOCREATEROLE PASSWORD {}"
        ).format(sql.Identifier("lc_test_runner"), sql.Literal(runner_secret)))
        row = connection.execute(
            "SELECT version(), inet_server_addr(), inet_server_port()").fetchone()
        assert row is not None
        print("LOCAL_POSTGRES_READY", row[0], row[1], row[2])


if __name__ == "__main__":
    main()
