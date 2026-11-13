"""Owner-run Gate P2 for the approved Parent-owned PostgreSQL behavior only."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, Table, bindparam, func, inspect, select, text
from sqlalchemy.engine import Engine, URL, create_engine

ROOT = Path(__file__).resolve().parents[4]
APPROVAL_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md"
)
DECISIONS_REL = Path("features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md")
RUNNER_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/"
    "m2_s1a_p2_gate_p2_20261112.py"
)
LAUNCH_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/plan/"
    "M2_S1A_P2_GATE_P2_LAUNCH_INSTRUCTION_20261112.md"
)
TEST_REL = Path("backend/tests/integration/test_m2_s1a_p2_parent_postgres.py")
TEST_BACKEND_REL = TEST_REL.relative_to("backend").as_posix()
BASELINE_SHA256 = "5A5DBC464ED1FD57C88860BD9E0313920B328A9EF39BB37EA4C91B631B8C1D98"
EXPECTED_BRANCH = "feature/feat063-m2-parent-teacher-foundation"
EXPECTED_HEAD = "c32d0b060e9625854dbdb781d7f8b11467bdca34"
EXPECTED_DATABASE = "sketch2life_m2_s1a"
EXPECTED_HOST = "127.0.0.1"
EXPECTED_PORT = 5433
EXPECTED_USER = "postgres"
EXPECTED_PG_MAJOR = 17
EXPECTED_REVISION = "20261109_m2_parent_profiles"
GATE_B_RUN_ID = "8b64744372454dadb5e3d75b14288853"
OWNER_ISSUER = "synthetic-parent-issuer"
OWNER_SUBJECT = f"s1a-p-{GATE_B_RUN_ID}-owner"
LOG_ROOT_REL = Path(".claude/handoff/logs/M2_S1A_P2_20261112")
PYTHON = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
TIMEOUT_SECONDS = 300
APPROVAL_PREFIX = "## M2 S1a-P2 Gate P2 Approval —"
TRACKED_ALLOWLIST = {
    "backend/src/sketch2life/interfaces/http/routers/parent_profiles.py",
    "backend/src/sketch2life/interfaces/http/parent_runtime.py",
    "backend/src/sketch2life/interfaces/http/app.py",
    "backend/src/sketch2life/application/ports/parent_profiles.py",
    "backend/src/sketch2life/application/services/parent_profiles.py",
    "backend/src/sketch2life/domain/parent_profiles.py",
    "backend/src/sketch2life/contracts/schemas/parent_profiles.py",
    "backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py",
    "backend/src/sketch2life/interfaces/http/openapi_contract.py",
    "backend/src/sketch2life/interfaces/http/openapi_srs_v22.py",
    "backend/src/sketch2life/interfaces/http/router_composition.py",
    "backend/tests/contract/test_app_composition.py",
    "backend/tests/contract/test_openapi_contract_catalog.py",
    "backend/tests/contract/test_parent_profiles_routes.py",
    "backend/tests/unit/test_parent_profiles.py",
    "backend/tests/unit/test_parent_profiles_service.py",
    "features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md",
    "features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md",
}
URI_RE = re.compile(r"(?i)\b[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
SENSITIVE_PATTERNS = {
    "userinfo": re.compile(r"[^\s:/]+:[^\s@/]+@[^\s/]+"),
    "password_assignment": re.compile(r"(?i)\bpassword\s*="),
    "pgpassword": re.compile(r"(?i)\bPGPASSWORD\b"),
    "bearer_token": re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~-]{30,}"),
    "credential_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|"
        r"client[_-]?secret|secret(?:[_-]?key)?|credential|authorization)\s*[:=]\s*"
        r"[\"']?[A-Za-z0-9._~+/=-]{8,}"
    ),
}


class SafeStop(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        raise SafeStop("PINNED_FILE_UNREADABLE") from None


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise SafeStop("GIT_GUARD_FAILED") from None
    if result.returncode != 0:
        raise SafeStop("GIT_GUARD_FAILED")
    return result.stdout.strip()


def _section_text(raw: bytes) -> tuple[str, bytes]:
    try:
        text_value = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise SafeStop("APPROVAL_ENCODING_INVALID") from None
    lines = text_value.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(APPROVAL_PREFIX)]
    if len(starts) != 1:
        raise SafeStop("GATE_P2_APPROVAL_SECTION_INVALID")
    start = starts[0]
    byte_offset = sum(len(line.encode("utf-8")) for line in lines[:start])
    section = "".join(lines[start:])
    return section, raw[:byte_offset]


def _field(section: str, label: str) -> str:
    matches = re.findall(
        rf"^- \*\*{re.escape(label)}:\*\*\s*(.*?)\s*$", section, re.MULTILINE
    )
    if len(matches) != 1:
        raise SafeStop("GATE_P2_APPROVAL_FIELD_INVALID")
    return matches[0].strip().strip("`")


def _table_rows(section: str, marker: str) -> list[list[str]]:
    lines = section.splitlines()
    marker_indexes = [index for index, line in enumerate(lines) if marker in line]
    if len(marker_indexes) != 1:
        raise SafeStop("GATE_P2_APPROVAL_TABLE_INVALID")
    index = marker_indexes[0] + 1
    while index < len(lines) and not lines[index].startswith("|"):
        index += 1
    rows: list[list[str]] = []
    while index < len(lines) and lines[index].startswith("|"):
        cells = [cell.strip().strip("`") for cell in lines[index].strip().strip("|").split("|")]
        if not all(set(cell) <= {"-", ":", " "} for cell in cells):
            rows.append(cells)
        index += 1
    if len(rows) < 2:
        raise SafeStop("GATE_P2_APPROVAL_TABLE_INVALID")
    return rows[1:]


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if (
        path.is_absolute()
        or path.drive
        or ":" in value
        or ".." in path.parts
        or "\\" in value
    ):
        raise SafeStop("APPROVAL_PATH_INVALID")
    return path


def _verify_approval() -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    approval_path = ROOT / APPROVAL_REL
    try:
        approval_bytes = approval_path.read_bytes()
    except OSError:
        raise SafeStop("TASK_APPROVAL_UNREADABLE") from None
    section, prefix = _section_text(approval_bytes)
    if _sha256_bytes(prefix) != _field(section, "Approval prefix SHA-256").upper():
        raise SafeStop("APPROVAL_PREFIX_MISMATCH")
    if _field(section, "Status") != "APPROVED / NOT LAUNCHED":
        raise SafeStop("GATE_P2_APPROVAL_STATUS_INVALID")
    if _field(section, "Branch") != EXPECTED_BRANCH:
        raise SafeStop("APPROVAL_BRANCH_MISMATCH")
    if _field(section, "HEAD").lower() != EXPECTED_HEAD:
        raise SafeStop("APPROVAL_HEAD_MISMATCH")
    if _field(section, "OWNER_MODAL_CALL_APPROVED") != "NO":
        raise SafeStop("MODAL_APPROVAL_MISMATCH")

    artifact_rows = _table_rows(section, "### Pinned artifacts")
    pins: dict[str, str] = {}
    for row in artifact_rows:
        if len(row) != 3 or row[1] in pins or not re.fullmatch(r"[0-9A-Fa-f]{64}", row[2]):
            raise SafeStop("GATE_P2_ARTIFACT_PINS_INVALID")
        pins[row[1]] = row[2].upper()
    required = {
        RUNNER_REL.as_posix(),
        LAUNCH_REL.as_posix(),
        TEST_REL.as_posix(),
        DECISIONS_REL.as_posix(),
    }
    if not required <= pins.keys():
        raise SafeStop("GATE_P2_ARTIFACT_PIN_SET_INVALID")
    for relative, expected_hash in pins.items():
        path = ROOT / _safe_relative_path(relative)
        if _sha256_file(path) != expected_hash:
            raise SafeStop("PINNED_ARTIFACT_MISMATCH")

    baseline_rows = _table_rows(section, "### Accepted Gate B post-inventory")
    if len(baseline_rows) != 1 or len(baseline_rows[0]) != 2:
        raise SafeStop("GATE_B_BASELINE_PIN_INVALID")
    baseline_relative = _safe_relative_path(baseline_rows[0][0])
    if baseline_rows[0][1].upper() != BASELINE_SHA256:
        raise SafeStop("GATE_B_BASELINE_PIN_INVALID")
    baseline_path = ROOT / baseline_relative
    if _sha256_file(baseline_path) != BASELINE_SHA256:
        raise SafeStop("GATE_B_BASELINE_PIN_MISMATCH")
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise SafeStop("GATE_B_BASELINE_INVALID") from None
    table_rows = baseline.get("table_rows") if isinstance(baseline, dict) else None
    if (
        not isinstance(baseline, dict)
        or baseline.get("read_only") is not True
        or baseline.get("status") != "MARKER_COUNTS_MATCH"
        or not isinstance(table_rows, dict)
        or len(table_rows) != 120
        or any(
            not isinstance(name, str) or type(count) is not int
            for name, count in table_rows.items()
        )
        or sum(table_rows.values()) != 36
        or baseline.get("alembic_versions") != [EXPECTED_REVISION]
    ):
        raise SafeStop("GATE_B_BASELINE_INVALID")

    manifest_rows = _table_rows(section, "### Exact current untracked manifest")
    manifest: dict[str, str] = {}
    for row in manifest_rows:
        if len(row) != 2 or row[0] in manifest or not re.fullmatch(r"[0-9A-Fa-f]{64}", row[1]):
            raise SafeStop("UNTRACKED_MANIFEST_INVALID")
        manifest[row[0]] = row[1].upper()
    if not manifest:
        raise SafeStop("UNTRACKED_MANIFEST_MISSING")
    for relative, expected_hash in manifest.items():
        if _sha256_file(ROOT / _safe_relative_path(relative)) != expected_hash:
            raise SafeStop("UNTRACKED_MANIFEST_HASH_MISMATCH")
    untracked = set(_git("ls-files", "--others", "--exclude-standard").splitlines())
    if untracked != set(manifest):
        raise SafeStop("UNTRACKED_MANIFEST_SET_MISMATCH")

    source_rows = _table_rows(section, "### Current implementation file pins")
    source_pins: dict[str, str] = {}
    for row in source_rows:
        if len(row) != 2 or row[0] in source_pins or not re.fullmatch(r"[0-9A-Fa-f]{64}", row[1]):
            raise SafeStop("IMPLEMENTATION_PINS_INVALID")
        source_pins[row[0]] = row[1].upper()
    if not source_pins:
        raise SafeStop("IMPLEMENTATION_PINS_MISSING")
    for relative, expected_hash in source_pins.items():
        if _sha256_file(ROOT / _safe_relative_path(relative)) != expected_hash:
            raise SafeStop("IMPLEMENTATION_PIN_MISMATCH")

    changed = set(_git("diff", "--name-only").splitlines())
    if not changed <= TRACKED_ALLOWLIST:
        raise SafeStop("TRACKED_PATH_OUTSIDE_ALLOWLIST")
    if _git("diff", "--cached", "--name-only"):
        raise SafeStop("INDEX_NOT_EMPTY")
    return pins, manifest, baseline


def _verify_environment() -> None:
    if _git("branch", "--show-current") != EXPECTED_BRANCH:
        raise SafeStop("BRANCH_MISMATCH")
    if _git("rev-parse", "HEAD").lower() != EXPECTED_HEAD:
        raise SafeStop("HEAD_MISMATCH")
    prefixes = (
        "PYTHON",
        "PYTEST",
        "DATABASE",
        "PG",
        "POSTGRES",
        "SQLALCHEMY",
        "ALEMBIC",
    )
    unexpected = sorted(name for name in os.environ if name.upper().startswith(prefixes))
    if unexpected:
        raise SafeStop("UNEXPECTED_CONTROL_ENVIRONMENT")
    if not PYTHON.is_file() or not (ROOT / "backend" / "pyproject.toml").is_file():
        raise SafeStop("PINNED_PYTHON_UNAVAILABLE")
    log_root = ROOT / LOG_ROOT_REL
    if log_root.exists() and any(log_root.iterdir()):
        raise SafeStop("GATE_P2_OUTPUT_ROOT_NOT_EMPTY")


def _snapshot(engine: Engine) -> dict[str, Any]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            identity = connection.execute(
                text(
                    "SELECT current_database(), host(inet_server_addr()), "
                    "inet_server_port(), current_user, "
                    "current_setting('server_version_num')::integer"
                )
            ).one()
            database, host_text, port, user, version = identity
            if (
                str(database) != EXPECTED_DATABASE
                or not ipaddress.ip_address(str(host_text)).is_loopback
                or int(port) != EXPECTED_PORT
                or str(user) != EXPECTED_USER
                or int(version) // 10000 != EXPECTED_PG_MAJOR
            ):
                raise SafeStop("DATABASE_IDENTITY_MISMATCH")
            inspector = inspect(connection)
            table_rows: dict[str, int] = {}
            for schema in sorted(inspector.get_schema_names()):
                if (
                    schema in {"pg_catalog", "information_schema"}
                    or schema.startswith("pg_toast")
                    or schema.startswith("pg_temp_")
                ):
                    continue
                for name in sorted(inspector.get_table_names(schema=schema)):
                    table = Table(name, MetaData(), schema=schema, autoload_with=connection)
                    count = connection.scalar(select(func.count()).select_from(table))
                    table_rows[f"{schema}.{name}"] = int(count or 0)
            versions = connection.execute(
                text("SELECT version_num FROM public.alembic_version ORDER BY version_num")
            ).scalars().all()
            connection.rollback()
    except SafeStop:
        raise
    except Exception:
        raise SafeStop("READ_ONLY_INVENTORY_FAILED") from None
    return {
        "identity": {
            "database": str(database),
            "host": str(host_text),
            "port": int(port),
            "user": str(user),
            "postgres_major": int(version) // 10000,
        },
        "table_rows": dict(sorted(table_rows.items())),
        "alembic_versions": [str(value) for value in versions],
        "total_rows": sum(table_rows.values()),
    }


def _marker_counts(engine: Engine, run_id: str) -> dict[str, int]:
    display_names = [f"Gate P2 {run_id}", f"Gate P2 updated {run_id}"]
    key_hashes = [
        hashlib.sha256(f"{run_id}-{suffix}".encode("ascii")).digest()
        for suffix in ("create", "patch", "delete")
    ]
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        profiles = connection.scalar(
            text(
                "SELECT count(DISTINCT p.parent_profile_id) "
                "FROM parent.child_profiles p "
                "JOIN parent.profile_revisions r USING (parent_profile_id) "
                "WHERE p.owner_issuer=:issuer AND p.owner_subject=:subject "
                "AND r.display_name IN :names"
            ).bindparams(bindparam("names", expanding=True)),
            {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT, "names": display_names},
        )
        revisions = connection.scalar(
            text(
                "SELECT count(*) FROM parent.profile_revisions r "
                "JOIN parent.child_profiles p USING (parent_profile_id) "
                "WHERE p.owner_issuer=:issuer AND p.owner_subject=:subject "
                "AND r.authored_by_issuer=:issuer AND r.authored_by_subject=:subject "
                "AND r.display_name IN :names"
            ).bindparams(bindparam("names", expanding=True)),
            {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT, "names": display_names},
        )
        receipts = connection.scalar(
            text(
                "SELECT count(*) FROM parent.command_receipts "
                "WHERE principal_issuer=:issuer AND principal_subject=:subject "
                "AND key_hash IN :hashes"
            ).bindparams(bindparam("hashes", expanding=True)),
            {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT, "hashes": key_hashes},
        )
        connection.rollback()
    return {
        "parent.child_profiles": int(profiles or 0),
        "parent.profile_revisions": int(revisions or 0),
        "parent.command_receipts": int(receipts or 0),
    }


def _gate_b_owner_counts(engine: Engine) -> dict[str, int]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            profiles = connection.scalar(
                text(
                    "SELECT count(*) FROM parent.child_profiles "
                    "WHERE owner_issuer=:issuer AND owner_subject=:subject"
                ),
                {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT},
            )
            active_profiles = connection.scalar(
                text(
                    "SELECT count(*) FROM parent.child_profiles "
                    "WHERE owner_issuer=:issuer AND owner_subject=:subject "
                    "AND state='ACTIVE' AND deleted_at IS NULL"
                ),
                {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT},
            )
            revisions = connection.scalar(
                text(
                    "SELECT count(*) FROM parent.profile_revisions r "
                    "JOIN parent.child_profiles p USING (parent_profile_id) "
                    "WHERE p.owner_issuer=:issuer AND p.owner_subject=:subject "
                    "AND r.authored_by_issuer=:issuer "
                    "AND r.authored_by_subject=:subject"
                ),
                {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT},
            )
            receipts = connection.scalar(
                text(
                    "SELECT count(*) FROM parent.command_receipts "
                    "WHERE principal_issuer=:issuer AND principal_subject=:subject"
                ),
                {"issuer": OWNER_ISSUER, "subject": OWNER_SUBJECT},
            )
            connection.rollback()
    except Exception:
        raise SafeStop("READ_ONLY_MARKER_CHECK_FAILED") from None
    return {
        "profiles": int(profiles or 0),
        "active_profiles": int(active_profiles or 0),
        "revisions": int(revisions or 0),
        "receipts": int(receipts or 0),
    }


def _write(path: Path, data: bytes) -> None:
    try:
        if path.exists():
            raise SafeStop("OUTPUT_PATH_ALREADY_EXISTS")
        path.write_bytes(data)
    except SafeStop:
        raise
    except OSError:
        raise SafeStop("GATE_P2_LOG_WRITE_FAILED") from None


def _atomic_replace(path: Path, data: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_bytes(data)
        temporary.replace(path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise SafeStop("GATE_P2_LOG_WRITE_FAILED") from None


def _write_status(run_dir: Path, status: dict[str, object]) -> None:
    payload = (json.dumps(status, sort_keys=True) + "\n").encode("utf-8")
    _atomic_replace(run_dir / "runner-status.json", payload)


def _safety_counts(values: dict[str, bytes]) -> dict[str, int]:
    counts = {name: 0 for name in SENSITIVE_PATTERNS}
    counts["scheme_url"] = 0
    for value in values.values():
        decoded = value.decode("utf-8", errors="replace")
        counts["scheme_url"] += len(URI_RE.findall(decoded))
        for name, pattern in SENSITIVE_PATTERNS.items():
            counts[name] += len(pattern.findall(decoded))
    counts["sensitive_output_matches"] = counts["scheme_url"] + sum(
        counts[name] for name in SENSITIVE_PATTERNS
    )
    return counts


def _store_pytest_output(run_dir: Path, stdout: bytes, stderr: bytes) -> bool:
    counts = _safety_counts({"stdout": stdout, "stderr": stderr})
    has_finding = counts["sensitive_output_matches"] > 0
    if has_finding:
        _write(run_dir / "pytest.stdout.txt", b"[WITHHELD: output safety match]\n")
        _write(run_dir / "pytest.stderr.txt", b"[WITHHELD: output safety match]\n")
    else:
        _write(run_dir / "pytest.stdout.txt", stdout)
        _write(run_dir / "pytest.stderr.txt", stderr)
    _atomic_replace(
        run_dir / "safety-scan.json",
        (
            json.dumps(
                {"status": "FINDING" if has_finding else "PASS", **counts},
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    )
    return has_finding


def _scan_run_files(run_dir: Path) -> dict[str, int]:
    values: dict[str, bytes] = {}
    try:
        for path in run_dir.iterdir():
            if path.name in {"safety-scan.json", "runner-status.json"}:
                continue
            if path.is_file():
                values[path.name] = path.read_bytes()
    except OSError:
        raise SafeStop("OUTPUT_SCAN_FAILED") from None
    return _safety_counts(values)


def _run_pytest(
    run_id: str, run_dir: Path, database_url: str
) -> tuple[int, str, bool]:
    child_env: dict[str, str] = {}
    for name in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            child_env[name] = value
    child_env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "SKETCH2LIFE_DATABASE_URL": database_url,
            "S1A_P_TEST_DATABASE_URL": database_url,
            "S1A_P_GATE_P2_RUN_ID": run_id,
            "SKETCH2LIFE_ENV": "test",
            "SKETCH2LIFE_AUTH_PROVIDER": "firebase",
            "SKETCH2LIFE_FIREBASE_PROJECT_ID": "synthetic-parent-gate-p2",
            "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "1",
            "STORYRUN_LITE_MAIN_DEMO_ENABLED": "0",
        }
    )
    temporary = run_dir / "pytest-tmp"
    command = [
        str(PYTHON),
        "-m",
        "pytest",
        TEST_BACKEND_REL,
        "-p",
        "no:cacheprovider",
        f"--basetemp={temporary}",
        "-rA",
        "-v",
    ]
    _write(
        run_dir / "pytest.command.txt",
        (
            "CWD=backend\n"
            "COMMAND=.venv/Scripts/python.exe -m pytest "
            f"{TEST_BACKEND_REL} -p no:cacheprovider --basetemp=<run-dir>/pytest-tmp -rA -v\n"
        ).encode("utf-8"),
    )
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT / "backend",
            env=child_env,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        has_finding = _store_pytest_output(run_dir, stdout, stderr)
        _write(run_dir / "pytest.exit.txt", b"TIMEOUT\n")
        return -1, "", has_finding
    finally:
        child_env.clear()
    has_finding = _store_pytest_output(
        run_dir, completed.stdout, completed.stderr
    )
    _write(run_dir / "pytest.exit.txt", f"{completed.returncode}\n".encode("ascii"))
    output = (completed.stdout + b"\n" + completed.stderr).decode(
        "utf-8", errors="replace"
    )
    summaries = re.findall(
        r"(?m)^=+\s*([^=\r\n]+?)\s+in [0-9.]+s\s*=+$",
        output,
    )
    summary = summaries[0] if len(summaries) == 1 else ""
    return completed.returncode, summary, has_finding


def _reserve_run_dir() -> tuple[str, Path]:
    run_id = uuid.uuid4().hex
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / LOG_ROOT_REL / f"{stamp}_gate_p2_{run_id[:12]}"
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except OSError:
        raise SafeStop("GATE_P2_OUTPUT_RESERVATION_FAILED") from None
    _write_status(
        run_dir,
        {
            "GATE_P2": "INCOMPLETE",
            "RUN_ID": run_id,
            "SAFETY_SCAN": "NOT_RUN",
        },
    )
    return run_id, run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-gate-p2", action="store_true")
    args = parser.parse_args(argv)
    if not args.run_gate_p2:
        print("NOT LAUNCHED: Gate P2 requires its separate reviewed owner approval.")
        return 2
    run_dir: Path | None = None
    engine: Engine | None = None
    password = ""
    database_url = ""
    try:
        pins, manifest, baseline = _verify_approval()
        del pins, manifest
        _verify_environment()
        run_id, run_dir = _reserve_run_dir()
        _write_status(
            run_dir,
            {
                "GATE_P2": "INCOMPLETE",
                "RUN_ID": run_id,
                "SAFETY_SCAN": "NOT_RUN",
                "PHASE": "WAITING_FOR_PASSWORD",
            },
        )
        password = getpass.getpass(
            "PostgreSQL password (hidden; sketch2life_m2_s1a only): "
        )
        if not password:
            raise SafeStop("EMPTY_PASSWORD")
        database_url = URL.create(
            "postgresql+psycopg",
            username=EXPECTED_USER,
            password=password,
            host=EXPECTED_HOST,
            port=EXPECTED_PORT,
            database=EXPECTED_DATABASE,
        ).render_as_string(hide_password=False)
        password = ""
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5},
        )
        _write_status(
            run_dir,
            {
                "GATE_P2": "INCOMPLETE",
                "RUN_ID": run_id,
                "SAFETY_SCAN": "NOT_RUN",
                "PHASE": "DATABASE_GUARDS",
            },
        )
        before = _snapshot(engine)
        baseline_rows = baseline["table_rows"]
        if (
            before["table_rows"] != baseline_rows
            or before["alembic_versions"] != [EXPECTED_REVISION]
            or before["total_rows"] != 36
            or len(before["table_rows"]) != 120
            or _gate_b_owner_counts(engine)
            != {
                "profiles": 1,
                "active_profiles": 1,
                "revisions": 2,
                "receipts": 3,
            }
            or _marker_counts(engine, run_id)
            != {
                "parent.child_profiles": 0,
                "parent.profile_revisions": 0,
                "parent.command_receipts": 0,
            }
        ):
            raise SafeStop("GATE_B_BASELINE_MISMATCH")
        _write(
            run_dir / "pre-inventory.json",
            (
                json.dumps(before, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n"
            ).encode("utf-8"),
        )
        _write_status(
            run_dir,
            {
                "GATE_P2": "INCOMPLETE",
                "RUN_ID": run_id,
                "SAFETY_SCAN": "NOT_RUN",
                "PHASE": "PYTEST_RUNNING",
            },
        )
        exit_code, summary, output_finding = _run_pytest(
            run_id, run_dir, database_url
        )
        _write(
            run_dir / "pytest.summary.txt",
            (summary or "NO_OFFICIAL_SUMMARY")
            .replace("\r", "")
            .encode("utf-8")
            + b"\n",
        )
        after = _snapshot(engine)
        expected = dict(before["table_rows"])
        expected["parent.child_profiles"] += 1
        expected["parent.profile_revisions"] += 2
        expected["parent.command_receipts"] += 3
        if (
            after["table_rows"] != expected
            or after["alembic_versions"] != before["alembic_versions"]
            or after["total_rows"] != before["total_rows"] + 6
            or _marker_counts(engine, run_id)
            != {
                "parent.child_profiles": 1,
                "parent.profile_revisions": 2,
                "parent.command_receipts": 3,
            }
        ):
            raise SafeStop("GATE_P2_POST_INVENTORY_MISMATCH")
        _write(
            run_dir / "post-inventory.json",
            (
                json.dumps(after, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n"
            ).encode("utf-8"),
        )
        safety = _scan_run_files(run_dir)
        safety_pass = (
            not output_finding and safety["sensitive_output_matches"] == 0
        )
        _atomic_replace(
            run_dir / "safety-scan.json",
            (
                json.dumps(
                    {"status": "PASS" if safety_pass else "FINDING", **safety},
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8"),
        )
        if not safety_pass:
            raise SafeStop("PYTEST_OUTPUT_SAFETY_FINDING")
        if (
            exit_code != 0
            or not summary.startswith("1 passed")
            or re.search(r"\b(?:failed|error|skipped|xfailed|xpassed)\b", summary)
        ):
            raise SafeStop("GATE_P2_PYTEST_NOT_PASS")
        post_inventory_hash = _sha256_file(run_dir / "post-inventory.json")
        print(f"RUN_ID={run_id}")
        print(f"LOG_DIR={(LOG_ROOT_REL / run_dir.name).as_posix()}")
        print(f"POST_INVENTORY_SHA256={post_inventory_hash}")
        print(f"PYTEST_SUMMARY={summary}")
        _write_status(
            run_dir,
            {
                "GATE_P2": "PASS",
                "RUN_ID": run_id,
                "PRE_INVENTORY": "MATCHED_ACCEPTED_GATE_B_POST_INVENTORY",
                "PYTEST": "EXIT_0; OFFICIAL_SUMMARY=1_PASSED",
                "POST_INVENTORY": "PASS; ROW_DELTA=6",
                "SAFETY_SCAN": "PASS",
            },
        )
        try:
            print("GATE_P2=PASS")
        except OSError:
            pass
        return 0
    except SafeStop as stop:
        if run_dir is not None:
            try:
                _write_status(
                    run_dir,
                    {
                        "GATE_P2": "FAILED",
                        "STOP_CODE": stop.code,
                        "SAFETY_SCAN": "NOT_PASS",
                    },
                )
            except SafeStop:
                print(
                    "GATE_P2_STATUS_WRITE_FAILED: runner-status.json remains "
                    "non-PASS or unavailable",
                    file=sys.stderr,
                )
        print(f"STOPPED_SAFELY: {stop.code}")
        return 2
    except KeyboardInterrupt:
        if run_dir is not None:
            try:
                _write_status(
                    run_dir,
                    {
                        "GATE_P2": "STOPPED",
                        "STOP_CODE": "OWNER_INTERRUPTED",
                        "SAFETY_SCAN": "NOT_PASS",
                    },
                )
            except SafeStop:
                print(
                    "GATE_P2_STATUS_WRITE_FAILED: runner-status.json remains "
                    "non-PASS or unavailable",
                    file=sys.stderr,
                )
        print("STOPPED_SAFELY: OWNER_INTERRUPTED")
        return 130
    except Exception:
        if run_dir is not None:
            try:
                _write_status(
                    run_dir,
                    {
                        "GATE_P2": "FAILED",
                        "STOP_CODE": "UNEXPECTED_FAILURE",
                        "SAFETY_SCAN": "NOT_PASS",
                    },
                )
            except SafeStop:
                print(
                    "GATE_P2_STATUS_WRITE_FAILED: runner-status.json remains "
                    "non-PASS or unavailable",
                    file=sys.stderr,
                )
        print("STOPPED_SAFELY: UNEXPECTED_FAILURE", file=sys.stderr)
        return 2
    finally:
        if engine is not None:
            try:
                engine.dispose()
            except Exception:
                pass
        password = ""
        database_url = ""


if __name__ == "__main__":
    raise SystemExit(main())
