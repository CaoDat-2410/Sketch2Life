"""Owner-only guarded runner for S1a-T PostgreSQL acceptance (R6).

Draft artifact: do not execute until the S1a-T approval and an accepted
baseline closure record are present. It never migrates, cleans up, or reads
application row values. Test output and inventory are kept in ignored paths.

Revision note: compared with R5 using git diff --no-index, R6 removes the
redundant explicit pytest quiet flag, counts the aggregate-revision organization
marker, and accepts pytest summaries with an optional elapsed-time suffix. All
R5 guards, including termination handling and the accepted baseline-closure
check, remain unchanged.
"""

from __future__ import annotations

import getpass
import hashlib
import ipaddress
import json
import os
import re
import secrets
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    import psycopg
    from psycopg import sql
except Exception:
    psycopg = None  # type: ignore[assignment]
    sql = None  # type: ignore[assignment]


EXPECTED_BRANCH = "feature/feat063-be-foundation"
EXPECTED_HEAD = "dd70685eae58aaaefea3e567f5c23d09345a8513"
EXPECTED_DATABASE = "sketch2life_m2_s1a"
EXPECTED_USER = "postgres"
EXPECTED_HOST = "127.0.0.1"
EXPECTED_PORT = 5433
EXPECTED_PG_MAJOR = 17
POSTGRES_TIMEOUT_SECONDS = 1800
CHILD_PROCESS_MAY_HAVE_STARTED = False
ROOT_PROCESS_TERMINATION_CONFIRMED = False
READ_ONLY_OPTIONS = (
    "-c default_transaction_read_only=on "
    "-c statement_timeout=20000 "
    "-c lock_timeout=3000"
)

REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_ROOT = REPO_ROOT / "backend"
APPROVAL_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md"
)
S1AT_SPEC_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/plan/"
    "M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R6.md"
)
S1AT_LAUNCH_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/plan/"
    "M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R6.md"
)
TEST_REL = Path("backend/tests/integration/test_m2_s1a_teacher_postgres.py")
LOG_BASE_REL = Path(".claude/handoff/logs/M2_S1A_T_20261107")
TMP_BASE_REL = Path("tmp/M2_S1A_T_20261107")

REQUIRED_MARKER_COLUMNS = {
    ("be1_organizations", "organization_id"),
    ("be1_classrooms", "class_id"),
    ("be1_adult_identities", "subject"),
    ("be1_organization_assignments", "subject"),
    ("be1_managed_profiles", "display_name"),
    ("be1_enrollments", "child_id"),
    ("be1_synthetic_eligibility_proofs", "run_ref"),
    ("core_audit_entries", "organization_id"),
    ("core_aggregate_revisions", "organization_id"),
    ("core_outbox_events", "organization_id"),
}

PARENT_DB_VARIABLES = (
    "SKETCH2LIFE_DATABASE_URL",
    "BE1_TEST_DATABASE_URL",
    "S1A_T_TEST_DATABASE_URL",
    "S1A_P_TEST_DATABASE_URL",
    "DATABASE_URL",
    "PGHOST",
    "PGPORT",
    "PGUSER",
    "PGPASSWORD",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGOPTIONS",
)

class SafeStop(Exception):
    """A safe stop with a fixed, non-sensitive reason code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SafeStop("GIT_PREFLIGHT_FAILED")
    return result.stdout.strip()


def require_repository_state() -> None:
    if git_output("branch", "--show-current") != EXPECTED_BRANCH:
        raise SafeStop("BRANCH_MISMATCH")
    if git_output("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise SafeStop("HEAD_MISMATCH")
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SafeStop("INDEX_NOT_EMPTY")

    spec_path = REPO_ROOT / S1AT_SPEC_REL
    if not spec_path.is_file():
        raise SafeStop("S1AT_SPEC_MISSING")
    spec_text = spec_path.read_text(encoding="utf-8")
    allowed_code_paths: set[str] = set()
    for line in spec_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] not in {"E", "R/E", "N"}:
            continue
        allowed_code_paths.add(cells[1].replace("\\", "/"))

    tracked = set(
        git_output("diff", "--name-only", "HEAD", "--", "backend/src", "backend/tests")
        .splitlines()
    )
    untracked = set(
        git_output(
            "ls-files", "--others", "--exclude-standard", "--", "backend/src", "backend/tests"
        ).splitlines()
    )
    changed_code = {path.replace("\\", "/") for path in tracked | untracked}
    if changed_code - allowed_code_paths:
        raise SafeStop("CODE_CHANGE_OUTSIDE_ALLOWLIST")
    if not (REPO_ROOT / TEST_REL).is_file():
        raise SafeStop("S1AT_POSTGRES_TEST_MISSING")


def section_by_prefix(text: str, heading_prefix: str) -> str:
    lines = text.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if line.startswith("## ") and line[3:].startswith(heading_prefix)
    ]
    if not starts:
        return ""
    start = starts[-1]
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def require_approval_records() -> tuple[str, str, str]:
    approval_path = REPO_ROOT / APPROVAL_REL
    launch_path = REPO_ROOT / S1AT_LAUNCH_REL
    spec_path = REPO_ROOT / S1AT_SPEC_REL
    if not approval_path.is_file() or not launch_path.is_file() or not spec_path.is_file():
        raise SafeStop("APPROVAL_ARTIFACT_MISSING")

    approval_text = approval_path.read_text(encoding="utf-8")
    launch_text = launch_path.read_text(encoding="utf-8")
    baseline_spec_hash = sha256_file(
        REPO_ROOT
        / "features/FEAT-063-system-architecture-rearchitecture/plan/"
        / "M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md"
    )
    baseline_launch_hash = sha256_file(
        REPO_ROOT
        / "features/FEAT-063-system-architecture-rearchitecture/plan/"
        / "M2_BASELINE_LAUNCH_INSTRUCTION_20261107_R2.md"
    )
    s1at_spec_hash = sha256_file(spec_path)
    s1at_launch_hash = sha256_file(launch_path)
    launcher_hash = sha256_file(Path(__file__).resolve())

    baseline = section_by_prefix(approval_text, "M2 Baseline Run Approval")
    if (
        "APPROVED / NOT LAUNCHED" not in baseline
        or baseline_spec_hash not in baseline
        or baseline_launch_hash not in baseline
    ):
        raise SafeStop("BASELINE_APPROVAL_MISSING_OR_STALE")

    s1at = section_by_prefix(approval_text, "M2 S1a-T Approval")
    if (
        "APPROVED / NOT LAUNCHED" not in s1at
        or s1at_spec_hash not in s1at
        or s1at_launch_hash not in s1at
        or launcher_hash not in s1at
        or "OWNER_MODAL_CALL_APPROVED=NO" not in s1at
    ):
        raise SafeStop("S1AT_APPROVAL_MISSING_OR_STALE")

    closure_path = (
        REPO_ROOT
        / "features/FEAT-063-system-architecture-rearchitecture/plan/"
        / "M2_BASELINE_CLOSURE_RECORD_20261108.md"
    )
    if not closure_path.is_file():
        raise SafeStop("ACCEPTED_BASELINE_CLOSURE_REQUIRED")
    closure_hash = sha256_file(closure_path)
    closure_candidates = re.findall(
        r"(?ms)^## M2 Baseline Closure Acceptance[^\n]*\n.*?(?=^## |\Z)",
        approval_text,
    )
    baseline_closed = any(
        re.search(r"(?im)^[-* ]*\*\*Status:\*\*\s*ACCEPTED\b", section)
        and closure_hash in section
        for section in closure_candidates
    )
    if not baseline_closed:
        raise SafeStop("ACCEPTED_BASELINE_CLOSURE_REQUIRED")

    if s1at_spec_hash not in launch_text or launcher_hash not in launch_text:
        raise SafeStop("S1AT_LAUNCH_PIN_MISMATCH")
    if "DO NOT LAUNCH" not in launch_text or "OWNER_MODAL_CALL_APPROVED=NO" not in launch_text:
        raise SafeStop("S1AT_LAUNCH_GUARD_MISSING")
    return baseline_spec_hash, s1at_spec_hash, launcher_hash


def require_clean_parent_environment() -> None:
    if any(os.environ.get(name) for name in PARENT_DB_VARIABLES):
        raise SafeStop("DATABASE_ENVIRONMENT_NOT_CLEAN")


def ignored_path(relative_path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative_path.as_posix()],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def require_new_ignored_output_paths() -> None:
    for path in (LOG_BASE_REL, TMP_BASE_REL):
        if (REPO_ROOT / path).exists():
            raise SafeStop("OUTPUT_PATH_ALREADY_EXISTS")
        if not ignored_path(path / "probe"):
            raise SafeStop("OUTPUT_PATH_NOT_IGNORED")


def build_child_environment(password: str, run_id: str, artifact_root: Path) -> dict[str, str]:
    child_env = dict(os.environ)
    for name in tuple(child_env):
        if name.startswith("SKETCH2LIFE_") or name.startswith("PG"):
            child_env.pop(name, None)
    for name in (
        "BE1_TEST_DATABASE_URL",
        "S1A_T_TEST_DATABASE_URL",
        "STORYRUN_LITE_MAIN_DEMO_ENABLED",
        "DATABASE_URL",
    ):
        child_env.pop(name, None)

    database_url = (
        "postgresql+psycopg" + ":" + "/" * 2 + "postgres:"
        + quote(password, safe="")
        + "@127.0.0.1:5433/sketch2life_m2_s1a"
    )
    child_env.update(
        {
            "S1A_T_TEST_DATABASE_URL": database_url,
            "SKETCH2LIFE_DATABASE_URL": database_url,
            "SKETCH2LIFE_ENV": "test",
            "SKETCH2LIFE_AUTH_PROVIDER": "development",
            "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "1",
            "SKETCH2LIFE_ROOM_CODE_HMAC_KEY": secrets.token_urlsafe(48),
            "SKETCH2LIFE_BE1_ARTIFACT_ROOT": str(artifact_root),
            "STORYRUN_LITE_MAIN_DEMO_ENABLED": "0",
            "S1A_T_RUN_ID": run_id,
            "PYTHONPATH": "src",
        }
    )
    return child_env


def create_output_directories(run_id: str) -> tuple[Path, Path]:
    logs_base = REPO_ROOT / LOG_BASE_REL
    tmp_base = REPO_ROOT / TMP_BASE_REL
    logs_base.mkdir(parents=True, exist_ok=False)
    tmp_base.mkdir(parents=True, exist_ok=False)
    run_logs = logs_base / run_id
    run_tmp = tmp_base / run_id
    run_logs.mkdir(exist_ok=False)
    run_tmp.mkdir(exist_ok=False)
    (run_tmp / "pytest").mkdir(exist_ok=False)
    (run_tmp / "artifacts").mkdir(exist_ok=False)
    return run_logs, run_tmp


def command_text(run_id: str) -> str:
    return (
        ".venv\\Scripts\\python.exe -m pytest "
        "tests\\integration\\test_m2_s1a_teacher_postgres.py "
        "-p no:cacheprovider "
        f"--basetemp ..\\tmp\\M2_S1A_T_20261107\\{run_id}\\pytest"
    )


def terminate_process_tree(process: subprocess.Popen[bytes]) -> bool:
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except KeyboardInterrupt:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    try:
        process.wait(timeout=20)
    except KeyboardInterrupt:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    except subprocess.TimeoutExpired:
        return False
    return process.poll() is not None


def run_postgres_test(
    run_id: str, run_logs: Path, child_env: dict[str, str]
) -> tuple[int | None, bool]:
    global CHILD_PROCESS_MAY_HAVE_STARTED, ROOT_PROCESS_TERMINATION_CONFIRMED

    command = command_text(run_id)
    metadata = (
        f"RUN_ID={run_id}\n"
        "CWD=backend\n"
        f"COMMAND={command}\n"
        f"TIMEOUT_SECONDS={POSTGRES_TIMEOUT_SECONDS}\n"
        "DATABASE_URL=CHILD_ENV_ONLY;VALUE_REDACTED\n"
    )
    (run_logs / "runner-metadata.txt").write_text(metadata, encoding="utf-8", newline="\n")

    exit_code: int | None = None
    timed_out = False
    interrupted = False
    with (run_logs / "pytest.stdout.txt").open("xb") as stdout_file:
        with (run_logs / "pytest.stderr.txt").open("xb") as stderr_file:
            try:
                CHILD_PROCESS_MAY_HAVE_STARTED = True
                process = subprocess.Popen(
                    ["cmd.exe", "/d", "/c", command],
                    cwd=BACKEND_ROOT,
                    env=child_env,
                    stdin=None,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                )
                try:
                    exit_code = process.wait(timeout=POSTGRES_TIMEOUT_SECONDS)
                    ROOT_PROCESS_TERMINATION_CONFIRMED = process.poll() is not None
                except KeyboardInterrupt:
                    if not terminate_process_tree(process):
                        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")
                    ROOT_PROCESS_TERMINATION_CONFIRMED = True
                    interrupted = True
                except subprocess.TimeoutExpired:
                    timed_out = True
                    terminated = terminate_process_tree(process)
                    if not terminated:
                        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")
                    ROOT_PROCESS_TERMINATION_CONFIRMED = True
            except SafeStop:
                raise
            except Exception:
                raise SafeStop("POSTGRES_TEST_LAUNCH_FAILED") from None

    if interrupted:
        (run_logs / "pytest.exit.txt").write_text(
            "INTERRUPTED\n",
            encoding="ascii",
            newline="\n",
        )
        (run_logs / "runner-status.txt").write_text(
            "PYTEST_EXIT=INTERRUPTED\n"
            "POST_RUN_INVENTORY=NOT_RUN\n"
            "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n",
            encoding="ascii",
            newline="\n",
        )
        return None, True

    (run_logs / "pytest.exit.txt").write_text(
        "TIMEOUT\n" if timed_out else f"{exit_code}\n",
        encoding="ascii",
        newline="\n",
    )
    if timed_out:
        return None, False
    return exit_code, False


def output_has_sensitive_material(run_logs: Path, password: str, database_url: str) -> bool:
    url_delimiter = ":" + "/" * 2
    patterns = (
        re.compile(r"(?i)postgres(?:ql)?(?:\+psycopg)?" + re.escape(url_delimiter)),
        re.compile(r"(?i)\bPGPASSWORD\b|\bpassword\s*="),
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{16,}"),
    )
    for name in ("pytest.stdout.txt", "pytest.stderr.txt"):
        content = (run_logs / name).read_bytes().decode("utf-8", errors="ignore")
        if password and (password in content or quote(password, safe="") in content):
            return True
        if database_url and database_url in content:
            return True
        if any(pattern.search(content) for pattern in patterns):
            return True
    return False


def official_pytest_summary_present(run_logs: Path) -> bool:
    content = "\n".join(
        (run_logs / name).read_bytes().decode("utf-8", errors="ignore")
        for name in ("pytest.stdout.txt", "pytest.stderr.txt")
    )
    return bool(
        re.search(
            r"(?m)^\d+\s+(?:passed|failed|error|errors|skipped|xfailed|xpassed)\b.*\bin\s+[0-9.]+s(?:\s+\(\d+:\d{2}:\d{2}\))?$",
            content,
        )
    )


def _verify_read_only_target(cursor: Any, *, stage: str) -> None:
    execute = cursor.execute
    fetchone = cursor.fetchone
    execute("SELECT current_setting('transaction_read_only')")
    if fetchone()[0] != "on":
        raise SafeStop(f"{stage}_READ_ONLY_NOT_CONFIRMED")
    execute(
        "SELECT current_database(), current_user, inet_server_port(), "
        "inet_server_addr()::text, current_setting('server_version_num')"
    )
    database, user, port, address, version_num = fetchone()
    try:
        identity_ok = (
            database == EXPECTED_DATABASE
            and user == EXPECTED_USER
            and port == EXPECTED_PORT
            and ipaddress.ip_address(str(address)).is_loopback
            and int(version_num) // 10000 == EXPECTED_PG_MAJOR
        )
    except (ValueError, TypeError, OverflowError):
        identity_ok = False
    if not identity_ok:
        raise SafeStop(f"{stage}_DATABASE_IDENTITY_MISMATCH")


def _all_table_row_counts(cursor: Any) -> dict[str, int]:
    if sql is None:
        raise SafeStop("PSYCOPG_UNAVAILABLE")
    execute = cursor.execute
    fetchall = cursor.fetchall
    fetchone = cursor.fetchone
    execute(
        "SELECT n.nspname, c.relname "
        "FROM pg_catalog.pg_class AS c "
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
        "WHERE c.relkind IN ('r', 'p') "
        "AND n.nspname NOT IN ('pg_catalog', 'information_schema') "
        "AND n.nspname NOT LIKE 'pg_toast%' "
        "AND n.nspname NOT LIKE 'pg_temp_%' "
        "ORDER BY n.nspname, c.relname"
    )
    relations = [(str(schema), str(table)) for schema, table in fetchall()]
    counts: dict[str, int] = {}
    for schema, table in relations:
        statement = sql.SQL("SELECT count(*) FROM {}.{}").format(
            sql.Identifier(schema), sql.Identifier(table)
        )
        execute(statement)
        counts[f"{schema}.{table}"] = int(fetchone()[0])
    return counts


def _marked_row_counts(cursor: Any, run_id: str) -> dict[str, int]:
    if sql is None:
        raise SafeStop("PSYCOPG_UNAVAILABLE")
    execute = cursor.execute
    fetchone = cursor.fetchone
    organization_pattern = f"synthetic-s1at-{run_id}-org%"
    class_pattern = f"synthetic-s1at-{run_id}-class%"
    subject_pattern = f"synthetic-s1at-{run_id}-teacher%"
    display_pattern = f"Synthetic S1AT {run_id} %"
    proof_ref = f"s1at-run-{run_id}"
    markers = (
        ("public.be1_organizations", "organization_id", organization_pattern),
        ("public.be1_classrooms", "class_id", class_pattern),
        ("public.be1_adult_identities", "subject", subject_pattern),
        ("public.be1_organization_assignments", "subject", subject_pattern),
        ("public.be1_managed_profiles", "display_name", display_pattern),
        ("public.be1_synthetic_eligibility_proofs", "run_ref", proof_ref),
        ("public.core_audit_entries", "organization_id", organization_pattern),
        ("public.core_aggregate_revisions", "organization_id", organization_pattern),
        ("public.core_outbox_events", "organization_id", organization_pattern),
    )
    counts: dict[str, int] = {}
    for qualified_table, column, marker in markers:
        table = qualified_table.removeprefix("public.")
        statement = sql.SQL("SELECT count(*) FROM {}.{} WHERE {} LIKE %s").format(
            sql.Identifier("public"), sql.Identifier(table), sql.Identifier(column)
        )
        execute(statement, (marker,))
        counts[qualified_table] = int(fetchone()[0])
    execute(
        "SELECT count(*) FROM public.be1_enrollments e "
        "JOIN public.be1_managed_profiles p ON p.child_id = e.child_id "
        "WHERE p.display_name LIKE %s",
        (display_pattern,),
    )
    counts["public.be1_enrollments"] = int(fetchone()[0])
    return counts


def collect_inventory(
    password: str,
    run_id: str,
    *,
    include_markers: bool,
    stage: str,
) -> dict[str, Any]:
    if psycopg is None or sql is None:
        raise SafeStop("PSYCOPG_UNAVAILABLE")
    connection = None
    try:
        connection = psycopg.connect(
            dbname=EXPECTED_DATABASE,
            host=EXPECTED_HOST,
            port=EXPECTED_PORT,
            user=EXPECTED_USER,
            password=password,
            connect_timeout=5,
            options=READ_ONLY_OPTIONS,
            autocommit=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("BEGIN READ ONLY")
            _verify_read_only_target(cursor, stage=stage.upper())
            cursor.execute(
                "SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema = 'public'"
            )
            observed = {(str(table), str(column)) for table, column in cursor.fetchall()}
            if not REQUIRED_MARKER_COLUMNS.issubset(observed):
                raise SafeStop("SYNTHETIC_MARKER_SCHEMA_MISMATCH")
            table_counts = _all_table_row_counts(cursor)
            marker_counts = _marked_row_counts(cursor, run_id) if include_markers else {}
        connection.rollback()
    except SafeStop:
        raise
    except Exception:
        raise SafeStop(f"{stage.upper()}_INVENTORY_FAILED") from None
    finally:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

    total_rows = sum(table_counts.values())
    marker_total = sum(marker_counts.values())
    unmatched = {
        table: count
        for table, count in table_counts.items()
        if count != marker_counts.get(table, 0)
    }
    if include_markers:
        status = (
            "UNKNOWN_ROWS_FOUND"
            if unmatched or total_rows != marker_total
            else "MARKER_COUNTS_MATCH"
        )
    else:
        status = "COUNTS_ONLY"
    return {
        "run_id": run_id,
        "read_only": True,
        "table_rows": table_counts,
        "total_rows": total_rows,
        "marker_rows": marker_counts,
        "marker_total": marker_total,
        "unmatched_tables": unmatched,
        "status": status,
    }


def write_inventory(run_logs: Path, name: str, inventory: dict[str, Any]) -> None:
    (run_logs / name).write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_inventory_status(run_logs: Path, name: str, status: str) -> None:
    (run_logs / name).write_text(status + "\n", encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args != ["--run-postgres-test"]:
        raise SafeStop("EXPLICIT_RUN_FLAG_REQUIRED")


def main(argv: list[str] | None = None) -> int:
    global CHILD_PROCESS_MAY_HAVE_STARTED, ROOT_PROCESS_TERMINATION_CONFIRMED

    CHILD_PROCESS_MAY_HAVE_STARTED = False
    ROOT_PROCESS_TERMINATION_CONFIRMED = False
    password = ""
    child_env: dict[str, str] | None = None
    run_logs: Path | None = None
    try:
        parse_args(argv)
        if sys.version_info[:2] != (3, 12):
            raise SafeStop("PYTHON_312_REQUIRED")
        expected_python = (BACKEND_ROOT / ".venv/Scripts/python.exe").resolve()
        if Path(sys.executable).resolve() != expected_python:
            raise SafeStop("BACKEND_VENV_PYTHON_REQUIRED")
        require_repository_state()
        require_approval_records()
        require_clean_parent_environment()
        require_new_ignored_output_paths()
        if not sys.stdin.isatty():
            raise SafeStop("PASSWORD_PROMPT_REQUIRES_INTERACTIVE_TERMINAL")

        password = getpass.getpass("PostgreSQL password (hidden; target is the S1a-T test database): ")
        if not password:
            raise SafeStop("EMPTY_PASSWORD_INPUT")
        run_id = uuid.uuid4().hex
        run_logs, run_tmp = create_output_directories(run_id)
        pre_inventory = collect_inventory(
            password, run_id, include_markers=False, stage="pre"
        )
        write_inventory(run_logs, "inventory.pre.json", pre_inventory)
        if pre_inventory["total_rows"] != 0:
            write_inventory_status(run_logs, "inventory.pre.status.txt", "PRE_RUN_ROWS_FOUND")
            (run_logs / "runner-status.txt").write_text(
                "STOPPED_SAFELY=PRE_RUN_ROWS_FOUND; PYTEST=NOT_RUN\n",
                encoding="ascii",
                newline="\n",
            )
            print(f"RUN_ID={run_id}")
            print("PRE_RUN_INVENTORY=ROWS_FOUND; PYTEST=NOT_RUN")
            print(f"LOG_DIR={LOG_BASE_REL.as_posix()}/{run_id}")
            return 2
        write_inventory_status(run_logs, "inventory.pre.status.txt", "PASS_EMPTY")

        child_env = build_child_environment(password, run_id, run_tmp / "artifacts")
        database_url = child_env["S1A_T_TEST_DATABASE_URL"]
        exit_code, interrupted = run_postgres_test(run_id, run_logs, child_env)
        if interrupted:
            print(f"RUN_ID={run_id}")
            print("PYTEST_EXIT=INTERRUPTED")
            print("POST_RUN_INVENTORY=NOT_RUN")
            print(f"LOG_DIR={LOG_BASE_REL.as_posix()}/{run_id}")
            return 2
        timed_out = exit_code is None
        summary_present = official_pytest_summary_present(run_logs)
        output_safe = not output_has_sensitive_material(run_logs, password, database_url)
        if not summary_present:
            write_inventory_status(
                run_logs,
                "inventory.post.status.txt",
                "NOT RUN: no official pytest summary",
            )
            status_line = "OUTPUT_SAFETY=FAIL; " if not output_safe else ""
            (run_logs / "runner-status.txt").write_text(
                f"{status_line}OFFICIAL_SUMMARY_PRESENT=false; POST_RUN_INVENTORY=NOT_RUN\n",
                encoding="ascii",
                newline="\n",
            )
            print(f"RUN_ID={run_id}")
            print("OFFICIAL_SUMMARY_PRESENT=false; POST_RUN_INVENTORY=NOT_RUN")
            print(f"LOG_DIR={LOG_BASE_REL.as_posix()}/{run_id}")
            return 2

        if not output_safe:
            write_inventory_status(
                run_logs,
                "inventory.post.status.txt",
                "NOT RUN: test output safety scan failed",
            )
            (run_logs / "runner-status.txt").write_text(
                "OUTPUT_SAFETY=FAIL; POST_RUN_INVENTORY=NOT_RUN\n",
                encoding="ascii",
                newline="\n",
            )
            print(f"RUN_ID={run_id}")
            print("OUTPUT_SAFETY=FAIL; POST_RUN_INVENTORY=NOT_RUN; inspect local logs without sharing secrets")
            print(f"LOG_DIR={LOG_BASE_REL.as_posix()}/{run_id}")
            return 2

        post_inventory = collect_inventory(
            password, run_id, include_markers=True, stage="post"
        )
        write_inventory(run_logs, "inventory.post.json", post_inventory)
        post_status = str(post_inventory["status"])
        write_inventory_status(run_logs, "inventory.post.status.txt", post_status)
        (run_logs / "runner-status.txt").write_text(
            f"PYTEST_EXIT={'TIMEOUT' if timed_out else exit_code}\n"
            f"OFFICIAL_SUMMARY_PRESENT={str(summary_present).lower()}\n"
            f"POST_RUN_INVENTORY={post_status}\n"
            "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n",
            encoding="ascii",
            newline="\n",
        )
        print(f"RUN_ID={run_id}")
        print(f"PYTEST_EXIT={'TIMEOUT' if timed_out else exit_code}")
        print(f"OFFICIAL_SUMMARY_PRESENT={str(summary_present).lower()}")
        print(f"POST_RUN_INVENTORY={post_status}")
        print("PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED")
        print(f"LOG_DIR={LOG_BASE_REL.as_posix()}/{run_id}")
        if timed_out or post_status == "UNKNOWN_ROWS_FOUND":
            return 2
        return 0 if exit_code == 0 else 1
    except SafeStop as stop:
        termination_unconfirmed = stop.code == "PROCESS_TERMINATION_UNCONFIRMED" or (
            CHILD_PROCESS_MAY_HAVE_STARTED and not ROOT_PROCESS_TERMINATION_CONFIRMED
        )
        if run_logs is not None:
            try:
                if termination_unconfirmed:
                    status = (
                        "PROCESS_TERMINATION_UNCONFIRMED\n"
                        "POST_RUN_INVENTORY=NOT_RUN\n"
                        "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n"
                    )
                else:
                    status = f"STOPPED_SAFELY={stop.code}\n"
                (run_logs / "runner-status.txt").write_text(
                    status, encoding="ascii", newline="\n"
                )
            except Exception:
                pass
        if termination_unconfirmed:
            print("PROCESS_TERMINATION_UNCONFIRMED; POST_RUN_INVENTORY=NOT_RUN")
        else:
            print(f"STOPPED_SAFELY: {stop.code}")
        return 2
    except KeyboardInterrupt:
        if not CHILD_PROCESS_MAY_HAVE_STARTED or ROOT_PROCESS_TERMINATION_CONFIRMED:
            print("STOPPED_SAFELY: INTERRUPTED")
            return 130
        if run_logs is not None:
            try:
                (run_logs / "runner-status.txt").write_text(
                    "PROCESS_TERMINATION_UNCONFIRMED\n"
                    "POST_RUN_INVENTORY=NOT_RUN\n"
                    "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n",
                    encoding="ascii",
                    newline="\n",
                )
            except Exception:
                pass
        print("PROCESS_TERMINATION_UNCONFIRMED; POST_RUN_INVENTORY=NOT_RUN")
        return 2
    except Exception:
        if CHILD_PROCESS_MAY_HAVE_STARTED and not ROOT_PROCESS_TERMINATION_CONFIRMED:
            if run_logs is not None:
                try:
                    (run_logs / "runner-status.txt").write_text(
                        "PROCESS_TERMINATION_UNCONFIRMED\n"
                        "POST_RUN_INVENTORY=NOT_RUN\n"
                        "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n",
                        encoding="ascii",
                        newline="\n",
                    )
                except Exception:
                    pass
            print("PROCESS_TERMINATION_UNCONFIRMED; POST_RUN_INVENTORY=NOT_RUN")
        else:
            print("STOPPED_SAFELY: UNEXPECTED_LOCAL_FAILURE")
        return 2
    finally:
        password = ""
        if child_env is not None:
            child_env.clear()


if __name__ == "__main__":
    raise SystemExit(main())
