"""Approved42 own PG cases. Fresh cluster only, native role/DB verified, strict evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[3]
CARDS = (
    ("10", "FEAT-052-be2-video-failure-disposition", "video_failure", "vf10", "VF10", 14),
    ("11", "FEAT-053-be2-activity-execution", "activity_execution", "ae11", "AE11", 17),
    ("13", "FEAT-054-be2-preset-automation", "preset_automation", "pa13", "PA13", 11),
)


def helper():
    path = ROOT / "features/FEAT-054-be2-preset-automation/src/run_component_checks.py"
    spec = importlib.util.spec_from_file_location("pg13_local_helpers", path)
    if spec is None or spec.loader is None:
        raise ValueError("missing helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sources() -> dict[str, str]:
    values = helper().source_hashes()
    paths = [Path(__file__).with_name("run_local_pg.ps1")]
    for _, feature, _, _, _, _ in CARDS:
        for name in ("approvals/LOCAL_POSTGRES_APPROVAL.md", "plan/LOCAL_POSTGRES_PLAN.md"):
            paths.append(ROOT / "features" / feature / name)
    for path in paths:
        values[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def main() -> int:
    out = Path(os.environ["BE2_SQL_RUN_ROOT"]).resolve()
    allowed = (ROOT / ".runtime/be2-101113-pg").resolve()
    if out.parent != allowed or not out.name.startswith("pg-"):
        raise ValueError("invalid run root")
    secret_path = Path(os.environ["BE2_SQL_BOOTSTRAP_FILE"]).resolve()
    if secret_path != out / "bootstrap.secret":
        raise ValueError("invalid secret target")
    port = int(os.environ["BE2_SQL_PORT"])
    before = sources()
    for _, feature, _, _, _, _ in CARDS:
        approval = ROOT / "features" / feature / "approvals/LOCAL_POSTGRES_APPROVAL.md"
        if "- Status: APPROVED" not in approval.read_text(encoding="utf-8"):
            raise ValueError("approval required")
    support = helper().evidence()
    passwords = [secret_path.read_text().strip()]
    results = {}
    with psycopg.connect(
        host="127.0.0.1",
        port=port,
        dbname="postgres",
        user="be2_pg_bootstrap",
        password=passwords[0],
        autocommit=True,
        connect_timeout=10,
    ) as admin:
        actual = admin.execute(
            "SELECT current_setting('data_directory'),host(inet_server_addr()),"
            "inet_server_port(),current_setting('server_version')"
        ).fetchone()
        if (
            actual is None
            or Path(actual[0]).resolve() != out / "data"
            or actual[1] != "127.0.0.1"
            or actual[2] != port
            or not actual[3].startswith("17.")
        ):
            raise ValueError("not exact owned cluster")
        for card, feature, suite, prefix, optin, expected_count in CARDS:
            suffix = secrets.token_hex(8)
            dbname, role = f"{prefix}_{suffix}", f"{prefix}_runner_{suffix}"
            password = secrets.token_urlsafe(32)
            passwords.append(password)
            admin.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                    "NOREPLICATION PASSWORD {}"
                ).format(sql.Identifier(role), sql.Literal(password))
            )
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0").format(
                    sql.Identifier(dbname), sql.Identifier(role)
                )
            )
            admin.execute(
                sql.SQL("REVOKE CONNECT ON DATABASE {} FROM PUBLIC").format(sql.Identifier(dbname))
            )
            with psycopg.connect(
                host="127.0.0.1",
                port=port,
                dbname=dbname,
                user=role,
                password=password,
                connect_timeout=10,
            ) as limited:
                checks = limited.execute(
                    "SELECT current_database(), current_user, rolsuper,rolcreatedb,"
                    "rolcreaterole,rolreplication FROM pg_roles WHERE rolname=current_user"
                ).fetchone()
                if checks != (dbname, role, False, False, False, False):
                    raise ValueError("not limited owner")
            url = URL.create(
                "postgresql+psycopg",
                username=role,
                password=password,
                host="127.0.0.1",
                port=port,
                database=dbname,
            ).render_as_string(hide_password=False)
            env = dict(os.environ)
            for key in tuple(env):
                if key.endswith(("_TEST_DATABASE_URL", "_TEST_ALLOW_SCHEMA_DDL")):
                    env.pop(key)
            env[optin + "_TEST_DATABASE_URL"] = url
            env[optin + "_TEST_ALLOW_SCHEMA_DDL"] = "1"
            path = f"tests/integration/{suite}/test_owned_sql.py"
            base = [sys.executable, "-m", "pytest", "-o", "addopts=", path]
            collected = subprocess.run(
                [*base, "--collect-only", "-q"],
                cwd=ROOT / "backend",
                env=env,
                text=True,
                capture_output=True,
                timeout=120,
                check=False,
            )
            nodes = support.inventory(collected.stdout)
            pin = json.loads((ROOT / "features" / feature / "src/TEST_INVENTORY.json").read_text())[
                "sql_collection_only"
            ]
            if (
                collected.returncode
                or len(nodes) != expected_count
                or not support.valid_pin(nodes, pin)
            ):
                raise ValueError("SQL node inventory differs")
            (out / f"be2-{card}-collection.log").write_text(collected.stdout, encoding="utf-8")
            junit = out / f"be2-{card}-junit.xml"
            process = subprocess.run(
                [*base, "-q", "--tb=short", f"--junitxml={junit}"],
                cwd=ROOT / "backend",
                env=env,
                text=True,
                capture_output=True,
                timeout=300,
                check=False,
            )
            log = process.stdout + process.stderr
            xml = junit.read_text(encoding="utf-8") if junit.exists() else ""
            for private in [url, *passwords]:
                log, xml = log.replace(private, "[private]"), xml.replace(private, "[private]")
            (out / f"be2-{card}-pytest.log").write_text(log, encoding="utf-8")
            if junit.exists():
                junit.write_text(xml, encoding="utf-8")
            state, _ = support.helpers().classify(nodes, junit, process.returncode)
            results[card] = dict(
                status=state,
                cases=len(nodes),
                process_exit=process.returncode,
                node_sha256=support.helpers().node_digest(nodes),
                limited_owner=True,
                junit_sha256=hashlib.sha256(junit.read_bytes()).hexdigest()
                if junit.exists()
                else None,
            )
            print(f"BE2-{card}: {state}, exact {len(nodes)} SQL cases", flush=True)
    unchanged = before == sources()
    passed = (
        unchanged
        and all(value["status"] == "PASS" for value in results.values())
        and len(results) == 3
    )
    summary = dict(
        status="PASS" if passed else "FAIL",
        scope="OWN_SQL_10_11_13_ONLY",
        cases=results,
        source_sha256=before,
        source_unchanged=unchanged,
        pg_version=actual[3],
        loopback_only=True,
        shared_database=False,
        actual_be1_p4_integration="NOT_RUN",
        full_cards_complete=False,
    )
    (out / "sql-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Exception, KeyboardInterrupt) as error:
        print("SQL_CHECK_ABORTED:", type(error).__name__, "private details not printed", flush=True)
        raise SystemExit(1) from None
