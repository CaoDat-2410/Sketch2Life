"""Proposed read-only inventory for the FEAT-063 M2 S0-owner-run phase.

Draft only. Do not run until an independent review, a separate owner Task
Approval, an approved database identity, and the exact script hash are recorded.
The program never migrates, writes to database tables, or reads row contents.
"""

from __future__ import annotations

import sys

if sys.version_info[:2] != (3, 12):
    try:
        sys.stderr.write("STOPPED_SAFELY: PYTHON_312_REQUIRED\n")
    except Exception:
        pass
    raise SystemExit(2)

import argparse
import ast
import getpass
import hashlib
import ipaddress
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg
    from psycopg import sql
except Exception:
    psycopg = None  # type: ignore[assignment]
    sql = None  # type: ignore[assignment]


LOG_ROOT_PARTS = (".claude", "handoff", "logs")
READ_ONLY_OPTIONS = (
    "-c default_transaction_read_only=on "
    "-c statement_timeout=20000 "
    "-c lock_timeout=3000"
)
CONNECT_TIMEOUT_SECONDS = 5
MAX_NONLOCAL_REASON_LENGTH = 160
K5_TIMEOUT_EXCEPTION_DETAILS = {
    "QueryCanceled": "STATEMENT_TIMEOUT",
    "LockNotAvailable": "LOCK_TIMEOUT",
}
EXIT_CODES = {
    "SUCCESS": 0,
    "PRE_OUTPUT_SAFE_STOP": 2,
    "K2_READ_ONLY_GATE_FAILED": 3,
    "K1_IDENTITY_GATE_NOT_CONFIRMED": 4,
    "POST_OUTPUT_SAFE_STOP": 5,
    "UNEXPECTED_SAFE_EXCEPTION": 6,
    "ROLLBACK_NOT_CONFIRMED": 7,
    "CONNECTION_CLOSE_NOT_CONFIRMED": 8,
    "PAIRED_REPORT_WRITE_FAILED": 9,
    "INTERRUPTED": 130,
}
EXPECTED_SYNTHETIC_LABEL = "SYNTHETIC_DEV"
ORIGIN_CANDIDATE_COLUMNS = frozenset(
    {"data_origin", "origin", "data_source", "source_type", "age_source"}
)

# Exact SHA-256 manifest for P1 static-AST mode. Draft 10 §8 names nine
# revision modules; P1 reads all 28 and requires a separately approved scope
# expansion. A mismatch makes K3 NOT RUN before AST parsing.
REVISION_HASHES = {
    "20261014_0001_core_persistence.py": "55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C",
    "20261014_0002_be1_runtime.py": "08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520",
    "20261014_0003_canvas_payload.py": "194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5",
    "20261014_0004_be1_constraint_names.py": "AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD",
    "20261015_ai_0001_ai_jobs_schema.py": "D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714",
    "20261017_ap_0001_policy_lifecycle.py": "81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A",
    "20261017_ap_0002_effective_scope.py": "35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7",
    "20261017_ap_0003_resource_ledger.py": "FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924",
    "20261017_ap_0004_copy_inventory.py": "3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7",
    "20261017_ap_0005_copy_evidence.py": "9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12",
    "20261017_lc_0001_content_publication.py": "DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498",
    "20261018_ap_0006_copy_operations.py": "B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7",
    "20261018_ap_0007_copy_delivery.py": "3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52",
    "20261018_ap_0008_delivery_authority.py": "9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05",
    "20261018_ap_0009_copy_resolution.py": "465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44",
    "20261018_kv_0001_knowledge_video.py": "E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87",
    "20261018_vr_0001_video_review.py": "3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7",
    "20261019_ae_0001_activity_execution.py": "56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30",
    "20261019_pa_0001_preset_automation.py": "D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8",
    "20261019_vf_0001_video_failure.py": "0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178",
    "20261024_0005_classroom_srs_contracts.py": "E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C",
    "20261028_ll_0001_lesson_library.py": "733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83",
    "20261031_be1_synthetic_eligibility.py": "421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC",
    "20261101_be1_age_provenance.py": "2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E",
    "20261102_pilot_vision.py": "6335AD224708AEC8251447A296458854B663FC7DD763EFB184E4AFF156E86BD9",
    "20261102_story_run_lite.py": "D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143",
    "20261103_story_upload_compat.py": "F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166",
    "20261104_story_revisions.py": "3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8",
}
REVISION_FILES = tuple(REVISION_HASHES)
REVISION_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")
URL_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
WINDOWS_PATH_RE = re.compile(r"(?i)\b[A-Z]:[\\/][^\s\"'<>]*")
UNIX_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])/(?:home|root|Users|tmp|var|opt|srv|mnt|private|workspace|Volumes|System)/[^\s\"'<>]+"
)

FIXED_SQL = {
    "read_only": "SHOW transaction_read_only",
    "identity": (
        "SELECT current_database(), current_setting('server_version')"
    ),
    "schemas": """
        SELECT n.nspname
        FROM pg_catalog.pg_namespace AS n
        WHERE n.nspname <> 'information_schema'
          AND n.nspname <> 'pg_catalog'
          AND n.nspname NOT LIKE 'pg_toast%'
          AND n.nspname NOT LIKE 'pg_temp_%'
        ORDER BY n.nspname
    """,
    "tables": """
        SELECT n.nspname, c.relname, c.relkind
        FROM pg_catalog.pg_class AS c
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE c.relkind IN ('r', 'p')
          AND n.nspname <> 'information_schema'
          AND n.nspname <> 'pg_catalog'
          AND n.nspname NOT LIKE 'pg_toast%'
          AND n.nspname NOT LIKE 'pg_temp_%'
        ORDER BY n.nspname, c.relname
    """,
    "columns": """
        SELECT table_schema, table_name, ordinal_position, column_name,
               data_type, udt_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema <> 'information_schema'
          AND table_schema <> 'pg_catalog'
          AND table_schema NOT LIKE 'pg_toast%'
          AND table_schema NOT LIKE 'pg_temp_%'
          AND table_name IN (
              SELECT c.relname
              FROM pg_catalog.pg_class AS c
              JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
              WHERE c.relkind IN ('r', 'p')
                AND n.nspname = information_schema.columns.table_schema
          )
        ORDER BY table_schema, table_name, ordinal_position
    """,
    "constraints": """
        SELECT n.nspname, c.relname, con.conname, con.contype,
               pg_catalog.pg_get_constraintdef(con.oid, true)
        FROM pg_catalog.pg_constraint AS con
        JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE c.relkind IN ('r', 'p')
          AND n.nspname <> 'information_schema'
          AND n.nspname <> 'pg_catalog'
          AND n.nspname NOT LIKE 'pg_toast%'
          AND n.nspname NOT LIKE 'pg_temp_%'
        ORDER BY n.nspname, c.relname, con.conname
    """,
    "indexes": """
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_catalog.pg_indexes
        WHERE schemaname <> 'information_schema'
          AND schemaname <> 'pg_catalog'
          AND schemaname NOT LIKE 'pg_toast%'
          AND schemaname NOT LIKE 'pg_temp_%'
        ORDER BY schemaname, tablename, indexname
    """,
    "alembic_table": "SELECT pg_catalog.to_regclass('public.alembic_version')",
    "alembic_versions": (
        "SELECT version_num FROM public.alembic_version ORDER BY version_num"
    ),
    "check_constraints": """
        SELECT n.nspname, c.relname, con.conname,
               pg_catalog.pg_get_constraintdef(con.oid, true)
        FROM pg_catalog.pg_constraint AS con
        JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE con.contype = 'c'
          AND c.relkind IN ('r', 'p')
          AND n.nspname <> 'information_schema'
          AND n.nspname <> 'pg_catalog'
          AND n.nspname NOT LIKE 'pg_toast%'
          AND n.nspname NOT LIKE 'pg_temp_%'
        ORDER BY n.nspname, c.relname, con.conname
    """,
}

class SafeStop(Exception):
    """A sanitized fail-closed stop reason."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise SafeStop("ARGUMENTS_INVALID")


def find_repository_root(script_path: Path) -> Path:
    for parent in script_path.resolve().parents:
        if (parent / "backend" / "alembic" / "versions").is_dir():
            return parent
    raise SafeStop("REPOSITORY_ROOT_NOT_FOUND")


def reject_unsafe_inputs(argv: list[str]) -> None:
    for token in argv:
        if "://" in token or re.search(
            r"(password|passwd|passfile|secret|token)", token, re.IGNORECASE
        ):
            raise SafeStop("UNSAFE_ARGUMENT_REJECTED")
    for key, value in os.environ.items():
        if "://" in value:
            raise SafeStop("URL_LIKE_ENVIRONMENT_VALUE_REJECTED")
        if value and re.search(
            r"(password|passwd|passfile)", key, re.IGNORECASE
        ):
            raise SafeStop("SECRET_ENVIRONMENT_VARIABLE_REJECTED")
    for key in ("PGSERVICE", "PGSERVICEFILE", "PGHOSTADDR", "PGOPTIONS"):
        if os.environ.get(key):
            raise SafeStop("UNAPPROVED_LIBPQ_OVERRIDE_REJECTED")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = SafeArgumentParser(
        description="Read-only FEAT-063 S0-owner-run inventory; draft, approval required.",
        add_help=False,
        allow_abbrev=False,
    )
    parser.add_argument("--expect-db", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--alembic-method",
        required=True,
        choices=("static-ast", "not-run"),
    )
    parser.add_argument("--allow-nonlocal-host", action="store_true")
    parser.add_argument("--nonlocal-host-reason")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_]{1,63}", args.expect_db):
        raise SafeStop("DATABASE_NAME_FORMAT_REJECTED")
    if args.allow_nonlocal_host and not args.nonlocal_host_reason:
        raise SafeStop("NONLOCAL_HOST_REASON_REQUIRED")
    if not args.allow_nonlocal_host and args.nonlocal_host_reason is not None:
        raise SafeStop("NONLOCAL_HOST_REASON_WITHOUT_FLAG")
    return args


def prepare_output_directory(repo_root: Path, raw_out_dir: str) -> Path:
    rel = Path(raw_out_dir)
    if rel.is_absolute() or any(part in {"..", ""} for part in rel.parts):
        raise SafeStop("OUTPUT_DIRECTORY_MUST_BE_RELATIVE")
    log_root = (repo_root / Path(*LOG_ROOT_PARTS)).resolve()
    candidate = (repo_root / rel).resolve()
    if candidate == log_root or not candidate.is_relative_to(log_root):
        raise SafeStop("OUTPUT_DIRECTORY_OUTSIDE_IGNORED_LOG_ROOT")
    ignore_path = repo_root / ".gitignore"
    try:
        ignore_lines = ignore_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        raise SafeStop("IGNORE_RULE_UNAVAILABLE") from None
    if "/.claude/" not in ignore_lines:
        raise SafeStop("IGNORE_RULE_NOT_CONFIRMED")
    if candidate.exists():
        raise SafeStop("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def execute_allowed(
    cursor: Any,
    connection: Any,
    operation: str,
    identifiers: tuple[str, ...] = (),
    parameters: tuple[Any, ...] | None = None,
) -> None:
    if operation in FIXED_SQL:
        if identifiers:
            raise SafeStop("FIXED_QUERY_OVERRIDE_REJECTED")
        statement: Any = FIXED_SQL[operation]
        if not re.match(r"\s*(SELECT|SHOW)\b", statement, re.IGNORECASE):
            raise SafeStop("NON_READ_QUERY_IN_FIXED_ALLOWLIST")
    elif operation == "table_count":
        if sql is None or len(identifiers) != 2:
            raise SafeStop("DYNAMIC_QUERY_NOT_COMPOSED")
        statement = sql.SQL("SELECT count(*) FROM {}.{}").format(
            sql.Identifier(identifiers[0]),
            sql.Identifier(identifiers[1]),
        )
        rendered = statement.as_string(connection)
        if not re.match(r"\s*SELECT\b", rendered, re.IGNORECASE):
            raise SafeStop("NON_SELECT_DYNAMIC_QUERY_REJECTED")
    elif operation == "origin_counts":
        if sql is None or len(identifiers) != 3:
            raise SafeStop("DYNAMIC_QUERY_NOT_COMPOSED")
        origin_identifier = sql.Identifier(identifiers[2])
        statement = sql.SQL(
            "SELECT {}, count(*) FROM {}.{} "
            "GROUP BY {} ORDER BY {} NULLS FIRST"
        ).format(
            origin_identifier,
            sql.Identifier(identifiers[0]),
            sql.Identifier(identifiers[1]),
            origin_identifier,
            origin_identifier,
        )
        rendered = statement.as_string(connection)
        if not re.match(r"\s*SELECT\b", rendered, re.IGNORECASE):
            raise SafeStop("NON_SELECT_DYNAMIC_QUERY_REJECTED")
    else:
        raise SafeStop("QUERY_NOT_ALLOWLISTED")
    cursor.execute(statement, parameters)


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = URL_RE.sub("[REDACTED_URL]", text)
    text = WINDOWS_PATH_RE.sub("[REDACTED_PATH]", text)
    return UNIX_PATH_RE.sub("[REDACTED_PATH]", text)


def as_text(value: Any) -> str:
    return safe_text(value)


def clean_nonlocal_host_reason(
    reason: str | None, settings: dict[str, str]
) -> str | None:
    if reason is None:
        return None
    text = " ".join(reason.split())
    if (
        not text
        or URL_RE.search(text)
        or WINDOWS_PATH_RE.search(text)
        or UNIX_PATH_RE.search(text)
    ):
        raise SafeStop("NONLOCAL_HOST_REASON_REJECTED")
    for key in ("PGHOST", "PGPORT", "PGUSER"):
        value = settings.get(key, "")
        if value:
            text = re.sub(
                re.escape(value),
                "[REDACTED_TARGET]",
                text,
                flags=re.IGNORECASE,
            )
    text = re.sub(
        r"(?i)\b(host|port|user|username)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED_TARGET]",
        text,
    )
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_ADDRESS]", text)
    text = re.sub(
        r"(?i)(?<![0-9A-Za-z])(?:[0-9a-f]{0,4}:){2,}[0-9a-f]{0,4}(?![0-9A-Za-z])",
        "[REDACTED_ADDRESS]",
        text,
    )
    text = re.sub(
        r"\b(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b",
        "[REDACTED_HOST]",
        text,
    )
    text = re.sub(r"\b\d{1,5}\b", "[REDACTED_NUMBER]", text)
    text = " ".join(text.split())[:MAX_NONLOCAL_REASON_LENGTH].rstrip()
    return text or "OWNER_REASON_REDACTED"


def literal_value(module: ast.Module, field_name: str) -> Any:
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == field_name
                for target in node.targets
            ):
                return ast.literal_eval(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == field_name
            and node.value is not None
        ):
            return ast.literal_eval(node.value)
    raise ValueError("revision field missing or not literal")


def flatten_revision_refs(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (tuple, list)) and all(
        isinstance(item, str) for item in value
    ):
        return tuple(value)
    raise ValueError("revision reference is not a literal identifier")


def source_heads(repo_root: Path) -> list[str]:
    versions_dir = repo_root / "backend" / "alembic" / "versions"
    actual = tuple(sorted(path.name for path in versions_dir.glob("*.py")))
    if actual != tuple(sorted(REVISION_FILES)):
        raise ValueError("revision file manifest differs")

    revisions: dict[str, set[str]] = {}
    for filename in REVISION_FILES:
        path = versions_dir / filename
        raw = path.read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest().upper()
        if actual_hash != REVISION_HASHES[filename]:
            raise ValueError("revision file hash differs")
        source = raw.decode("utf-8")
        tree = ast.parse(source, filename=filename)
        revision = literal_value(tree, "revision")
        if not isinstance(revision, str) or not REVISION_ID_RE.fullmatch(revision):
            raise ValueError("revision identifier is not a literal string")
        if revision in revisions:
            raise ValueError("duplicate revision identifier")
        parents = set(flatten_revision_refs(literal_value(tree, "down_revision")))
        parents.update(flatten_revision_refs(literal_value(tree, "depends_on")))
        # Read and validate these fields too; labels do not form graph edges.
        labels = literal_value(tree, "branch_labels")
        if labels is not None and not (
            isinstance(labels, str)
            or (
                isinstance(labels, (tuple, list))
                and all(isinstance(item, str) for item in labels)
            )
        ):
            raise ValueError("branch labels are not literal")
        revisions[revision] = parents

    all_revisions = set(revisions)
    for parents in revisions.values():
        if not parents.issubset(all_revisions):
            raise ValueError("revision parent or dependency is missing")

    children: dict[str, set[str]] = defaultdict(set)
    for child, parents in revisions.items():
        for parent in parents:
            children[parent].add(child)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(revision: str) -> None:
        if revision in visiting:
            raise ValueError("revision graph contains a cycle")
        if revision in visited:
            return
        visiting.add(revision)
        for parent in revisions[revision]:
            visit(parent)
        visiting.remove(revision)
        visited.add(revision)

    for revision in revisions:
        visit(revision)
    return sorted(revision for revision in all_revisions if not children[revision])


def origin_bucket(value: Any) -> str:
    if value is None:
        return "NULL"
    label = str(value)
    if not label.strip():
        return "EMPTY"
    if label == EXPECTED_SYNTHETIC_LABEL:
        return EXPECTED_SYNTHETIC_LABEL
    if label == "REAL":
        return "REAL"
    if label == "LEGACY_UNCLASSIFIED":
        return "LEGACY_UNCLASSIFIED"
    return "OTHER"


def new_report(args: argparse.Namespace, script_path: Path) -> dict[str, Any]:
    digest = hashlib.sha256(script_path.read_bytes()).hexdigest().upper()
    return {
        "report_kind": "read_only_inventory_observation_not_approval",
        "script_sha256": digest,
        "expected_database": args.expect_db,
        "postgresql_version": None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "alembic_method": args.alembic_method,
        "nonlocal_host_flag_used": bool(args.allow_nonlocal_host),
        "nonlocal_host_reason": args.nonlocal_host_reason,
        "checks": {
            f"K{number}": {
                "status": "NOT RUN",
                "detail": "NOT_ATTEMPTED",
            }
            for number in range(1, 8)
        },
        "source_schema_comparison": "NOT RUN; coordinator step after owner supplies output",
        "synthetic_scope_owner_proof": "NOT SUPPLIED TO SCRIPT",
        "k5_not_run_tables": [],
        "inventory_limitations": [
            "information_schema.columns may hide columns when the connection role lacks privileges.",
            "Partition children can be listed and counted separately while the parent count includes child rows.",
        ],
        "stop_code": None,
    }


def set_status(
    report: dict[str, Any], key: str, status: str, detail: str
) -> None:
    report["checks"][key] = {"status": status, "detail": detail}


def mark_gates_stopped_after(report: dict[str, Any], failed_gate: str) -> None:
    failed_number = int(failed_gate[1:])
    for number in range(1, 8):
        key = f"K{number}"
        if key == failed_gate:
            continue
        current = report.get("checks", {}).get(key, {})
        if (
            current.get("status") != "NOT RUN"
            or current.get("detail") != "NOT_ATTEMPTED"
        ):
            continue
        if failed_gate == "K2" and number == 1:
            set_status(report, key, "NOT RUN", "STOPPED_AFTER_K2")
        elif number > failed_number:
            set_status(report, key, "NOT RUN", f"STOPPED_AFTER_{failed_gate}")


def record_k5_timeout(
    report: dict[str, Any], operation: str, exc: Exception
) -> str | None:
    if operation not in {"TABLE_COUNT", "ORIGIN_GROUP"}:
        return None
    timeout_detail = K5_TIMEOUT_EXCEPTION_DETAILS.get(type(exc).__name__)
    if timeout_detail is None:
        return None
    detail = f"{operation}_{timeout_detail}"
    set_status(report, "K5", "NOT RUN", detail)
    mark_gates_stopped_after(report, "K5")
    return detail


def inventory(
    cursor: Any,
    connection: Any,
    repo_root: Path,
    report: dict[str, Any],
) -> None:
    # K3: read DB revision rows and, only for the explicitly selected P1,
    # statically parse the exact pinned source manifest without importing it.
    execute_allowed(cursor, connection, "alembic_table")
    has_version_table = cursor.fetchone()[0] is not None
    if not has_version_table:
        set_status(report, "K3", "FAIL", "ALEMBIC_VERSION_TABLE_ABSENT")
    else:
        execute_allowed(cursor, connection, "alembic_versions")
        raw_versions = [str(row[0]) for row in cursor.fetchall()]
        if not all(REVISION_ID_RE.fullmatch(value) for value in raw_versions):
            set_status(report, "K3", "NOT RUN", "DATABASE_REVISION_VALUES_NOT_VERIFIABLE")
        else:
            db_versions = sorted(raw_versions)
            report["database_alembic_versions"] = db_versions
            method = report["alembic_method"]
            if method == "static-ast":
                try:
                    heads = source_heads(repo_root)
                except (
                    OSError,
                    UnicodeError,
                    SyntaxError,
                    ValueError,
                    TypeError,
                    RecursionError,
                    MemoryError,
                ):
                    set_status(
                        report,
                        "K3",
                        "NOT RUN",
                        "STATIC_REVISION_GRAPH_NOT_VERIFIABLE",
                    )
                else:
                    report["source_alembic_heads"] = heads
                    if db_versions == heads:
                        set_status(report, "K3", "PASS", "DB_REVISIONS_MATCH_STATIC_HEADS")
                    else:
                        set_status(report, "K3", "FAIL", "DB_REVISIONS_DIFFER_FROM_STATIC_HEADS")
            else:
                set_status(report, "K3", "NOT RUN", "OWNER_SELECTED_K3_NOT_RUN")

    # K4 inventory. This is collection only; source parity is not assessed here.
    execute_allowed(cursor, connection, "schemas")
    schemas = [as_text(row[0]) for row in cursor.fetchall()]
    execute_allowed(cursor, connection, "tables")
    tables = [
        {"schema": as_text(row[0]), "table": as_text(row[1]), "kind": as_text(row[2])}
        for row in cursor.fetchall()
    ]
    execute_allowed(cursor, connection, "columns")
    columns = [
        {
            "schema": as_text(row[0]),
            "table": as_text(row[1]),
            "ordinal": row[2],
            "name": as_text(row[3]),
            "data_type": as_text(row[4]),
            "udt_name": as_text(row[5]),
            "nullable": as_text(row[6]),
            "default": as_text(row[7]),
        }
        for row in cursor.fetchall()
    ]
    execute_allowed(cursor, connection, "constraints")
    constraints = [
        {
            "schema": as_text(row[0]),
            "table": as_text(row[1]),
            "name": as_text(row[2]),
            "kind": as_text(row[3]),
            "definition": as_text(row[4]),
        }
        for row in cursor.fetchall()
    ]
    execute_allowed(cursor, connection, "indexes")
    indexes = [
        {
            "schema": as_text(row[0]),
            "table": as_text(row[1]),
            "name": as_text(row[2]),
            "definition": as_text(row[3]),
        }
        for row in cursor.fetchall()
    ]
    report["schema_inventory"] = {
        "schemas": schemas,
        "tables": tables,
        "columns": columns,
        "constraints": constraints,
        "indexes": indexes,
    }
    set_status(report, "K4", "COLLECTED", "INVENTORY_COLLECTED; SOURCE_COMPARISON_NOT_RUN")

    # K5 counts are aggregates only. No application/data columns are selected.
    columns_by_table: dict[tuple[str, str], set[str]] = defaultdict(set)
    for item in columns:
        columns_by_table[(item["schema"], item["table"])].add(item["name"])
    row_counts: list[dict[str, Any]] = []
    origin_counts: list[dict[str, Any]] = []
    no_origin: list[dict[str, str]] = []
    unsafe_origin_found = False

    for table in tables:
        schema_name = table["schema"]
        table_name = table["table"]
        identifier = (schema_name, table_name)
        try:
            execute_allowed(
                cursor,
                connection,
                "table_count",
                identifiers=(schema_name, table_name),
            )
            row_count = int(cursor.fetchone()[0])
        except Exception as exc:
            timeout_detail = record_k5_timeout(report, "TABLE_COUNT", exc)
            if timeout_detail is None:
                raise
            row_counts.append(
                {
                    "schema": schema_name,
                    "table": table_name,
                    "row_count": None,
                    "status": "NOT RUN",
                    "detail": timeout_detail,
                }
            )
            report["row_counts"] = row_counts
            report["data_origin_counts"] = origin_counts
            report["tables_without_data_origin"] = no_origin
            report["k5_not_run_tables"].append(
                {
                    "schema": schema_name,
                    "table": table_name,
                    "status": "NOT RUN",
                    "detail": timeout_detail,
                }
            )
            raise SafeStop(f"K5_{timeout_detail}") from None
        row_counts.append(
            {"schema": schema_name, "table": table_name, "row_count": row_count}
        )

        available_columns = columns_by_table[identifier]
        origin_column = next(
            (
                name
                for name in available_columns
                if name.lower() == "data_origin"
            ),
            None,
        )
        if origin_column is None:
            candidate_names = sorted(
                name
                for name in available_columns
                if name.lower() in ORIGIN_CANDIDATE_COLUMNS
            )
            no_origin.append(
                {
                    "schema": schema_name,
                    "table": table_name,
                    "candidate_columns_not_treated_as_proof": ", ".join(candidate_names),
                }
            )
            continue

        try:
            execute_allowed(
                cursor,
                connection,
                "origin_counts",
                identifiers=(schema_name, table_name, origin_column),
            )
            grouped_origins = cursor.fetchall()
        except Exception as exc:
            timeout_detail = record_k5_timeout(report, "ORIGIN_GROUP", exc)
            if timeout_detail is None:
                raise
            report["row_counts"] = row_counts
            report["data_origin_counts"] = origin_counts
            report["tables_without_data_origin"] = no_origin
            report["k5_not_run_tables"].append(
                {
                    "schema": schema_name,
                    "table": table_name,
                    "status": "NOT RUN",
                    "detail": timeout_detail,
                }
            )
            raise SafeStop(f"K5_{timeout_detail}") from None
        buckets: dict[str, int] = defaultdict(int)
        for value, count in grouped_origins:
            bucket = origin_bucket(value)
            buckets[bucket] += int(count)
            if bucket != EXPECTED_SYNTHETIC_LABEL:
                unsafe_origin_found = True
        origin_counts.append(
            {
                "schema": schema_name,
                "table": table_name,
                "origin_counts": dict(sorted(buckets.items())),
            }
        )

    report["row_counts"] = row_counts
    report["data_origin_counts"] = origin_counts
    report["tables_without_data_origin"] = no_origin
    if unsafe_origin_found:
        set_status(report, "K5", "FAIL", "NON_SYNTHETIC_OR_EMPTY_ORIGIN_BUCKET_FOUND")
        mark_gates_stopped_after(report, "K5")
        raise SafeStop("K5_SYNTHETIC_ORIGIN_GATE_FAILED")
    if no_origin:
        set_status(report, "K5", "NOT RUN", "OWNER_PROOF_REQUIRED_FOR_TABLES_WITHOUT_DATA_ORIGIN")
    else:
        set_status(
            report,
            "K5",
            "NOT RUN",
            "OWNER_TABLE_SCOPE_AND_SYNTHETIC_PROOF_NOT_CONFIRMED",
        )

    # K6: emit CHECK definitions only, never infer whether they are correct.
    execute_allowed(cursor, connection, "check_constraints")
    report["check_constraints"] = [
        {
            "schema": as_text(row[0]),
            "table": as_text(row[1]),
            "name": as_text(row[2]),
            "definition": as_text(row[3]),
        }
        for row in cursor.fetchall()
    ]
    set_status(report, "K6", "COLLECTED", "CHECK_DEFINITIONS_COLLECTED; NO_INTERPRETATION")


def validate_libpq_environment(args: argparse.Namespace) -> dict[str, str]:
    settings: dict[str, str] = {}
    for name in ("PGHOST", "PGPORT", "PGUSER"):
        value = os.environ.get(name, "").strip()
        if not value or "://" in value or "\x00" in value:
            raise SafeStop("REQUIRED_LIBPQ_SETTING_MISSING_OR_INVALID")
        settings[name] = value
    if not settings["PGPORT"].isdigit() or not (
        1 <= int(settings["PGPORT"]) <= 65535
    ):
        raise SafeStop("LIBPQ_PORT_INVALID")
    host = settings["PGHOST"]
    is_loopback = host.casefold() == "localhost"
    if not is_loopback:
        try:
            is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback = False
    if not is_loopback and not args.allow_nonlocal_host:
        raise SafeStop("NONLOCAL_DATABASE_HOST_REJECTED")
    return settings


def report_text(report: dict[str, Any]) -> str:
    lines = [
        "FEAT-063 M2 S0-owner-run — read-only observation",
        "This output is not an approval, acceptance, or phase closure.",
        f"Script SHA-256: {report.get('script_sha256', 'NOT AVAILABLE')}",
        f"Expected database: {report.get('expected_database', 'NOT VERIFIED')}",
        f"PostgreSQL version: {report.get('postgresql_version') or 'NOT VERIFIED'}",
        f"Generated UTC: {report.get('generated_at_utc', 'NOT AVAILABLE')}",
        f"Alembic method: {report.get('alembic_method', 'NOT SELECTED')}",
        f"Stop code: {report.get('stop_code') or 'NONE'}",
        "nonlocal_host_flag_used: "
        f"{str(bool(report.get('nonlocal_host_flag_used', False))).lower()}",
        "nonlocal_host_reason: "
        f"{report.get('nonlocal_host_reason') or 'NOT APPLICABLE'}",
        "K1 checks only the database name; container and full manifest are owner checks.",
        "",
        "Checks:",
    ]
    checks = report.get("checks", {})
    for number in range(1, 8):
        key = f"K{number}"
        value = checks.get(key, {})
        lines.append(
            f"{key}: {value.get('status', 'NOT RUN')} — "
            f"{value.get('detail', 'NOT_ATTEMPTED')}"
        )
    lines.append(
        f"K4 source comparison: {report.get('source_schema_comparison', 'NOT RUN')}"
    )
    lines.append(
        f"K5 owner scope/proof: {report.get('synthetic_scope_owner_proof', 'NOT SUPPLIED')}"
    )
    for limitation in report.get("inventory_limitations", []):
        lines.append(f"Inventory limitation: {limitation}")
    lines.append("")
    lines.append(
        "Detailed counts and metadata are available in the paired JSON file."
    )
    return "\n".join(lines) + "\n"


def write_reports(output_dir: Path, report: dict[str, Any]) -> None:
    json_path = output_dir / "inventory.json"
    text_path = output_dir / "inventory.txt"
    json_payload = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    text_payload = report_text(report)
    created: list[Path] = []
    try:
        for path, payload in (
            (json_path, json_payload),
            (text_path, text_payload),
        ):
            stream = path.open("x", encoding="utf-8", newline="\n")
            created.append(path)
            with stream:
                stream.write(payload)
    except FileExistsError:
        for path in created:
            try:
                path.unlink()
            except OSError:
                pass
        raise SafeStop("OUTPUT_FILE_ALREADY_EXISTS") from None
    except KeyboardInterrupt:
        for path in created:
            try:
                path.unlink()
            except OSError:
                pass
        raise SafeStop("REPORT_WRITE_INTERRUPTED") from None
    except Exception:
        for path in created:
            try:
                path.unlink()
            except OSError:
                pass
        raise SafeStop("OUTPUT_WRITE_FAILED") from None


def safe_exception_code(exc: Exception) -> str:
    known_types = {
        "OperationalError": "DATABASE_CONNECTION_FAILED",
        "ProgrammingError": "READ_QUERY_FAILED",
        "QueryCanceled": "QUERY_TIMEOUT",
        "OSError": "LOCAL_READ_OR_WRITE_FAILED",
        "ValueError": "STATIC_METADATA_NOT_VERIFIABLE",
        "TypeError": "STATIC_METADATA_NOT_VERIFIABLE",
        "RecursionError": "STATIC_METADATA_NOT_VERIFIABLE",
        "MemoryError": "STATIC_METADATA_NOT_VERIFIABLE",
        "UnicodeDecodeError": "STATIC_METADATA_NOT_VERIFIABLE",
    }
    return known_types.get(type(exc).__name__, "UNEXPECTED_SAFE_STOP")


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args: argparse.Namespace | None = None
    report: dict[str, Any] | None = None
    output_dir: Path | None = None
    connection: Any | None = None
    exit_code = 0
    safe_stop_code = "SAFE_STOP"
    try:
        reject_unsafe_inputs(raw_argv)
        args = parse_args(raw_argv)
        script_path = Path(__file__)
        repo_root = find_repository_root(script_path)
        settings = validate_libpq_environment(args)
        args.nonlocal_host_reason = clean_nonlocal_host_reason(
            args.nonlocal_host_reason, settings
        )
        report = new_report(args, script_path)
        output_dir = prepare_output_directory(repo_root, args.out_dir)
        if psycopg is None:
            raise SafeStop("PSYCOPG_V3_UNAVAILABLE")
        if not sys.stdin.isatty():
            raise SafeStop("PASSWORD_PROMPT_REQUIRES_INTERACTIVE_TERMINAL")
        entered = getpass.getpass("Database password (input hidden): ")
        if not entered:
            raise SafeStop("EMPTY_PASSWORD_INPUT")
        try:
            connection = psycopg.connect(
                dbname=args.expect_db,
                host=settings["PGHOST"],
                port=int(settings["PGPORT"]),
                user=settings["PGUSER"],
                password=entered,
                connect_timeout=CONNECT_TIMEOUT_SECONDS,
                options=READ_ONLY_OPTIONS,
                autocommit=False,
            )
        finally:
            del entered
        connection.read_only = True

        with connection.cursor() as cursor:
            # The connection setting is applied before this first SQL command.
            execute_allowed(cursor, connection, "read_only")
            read_only_value = as_text(cursor.fetchone()[0]).lower()
            if read_only_value != "on":
                set_status(report, "K2", "FAIL", "READ_ONLY_TRANSACTION_NOT_CONFIRMED")
                report["stop_code"] = "K2_READ_ONLY_GATE_FAILED"
                mark_gates_stopped_after(report, "K2")
                exit_code = EXIT_CODES["K2_READ_ONLY_GATE_FAILED"]
                raise SafeStop(report["stop_code"])
            set_status(report, "K2", "PASS", "READ_ONLY_CONFIRMED_BEFORE_OTHER_QUERIES")

            execute_allowed(cursor, connection, "identity")
            actual_database, server_version = cursor.fetchone()
            if actual_database != args.expect_db:
                # Do not persist the unexpected database name or run another query.
                set_status(
                    report,
                    "K1",
                    "FAIL",
                    "DATABASE_NAME_MISMATCH; ACTUAL_NAME_WITHHELD",
                )
                mark_gates_stopped_after(report, "K1")
                report["stop_code"] = "K1_IDENTITY_GATE_NOT_CONFIRMED"
                exit_code = EXIT_CODES["K1_IDENTITY_GATE_NOT_CONFIRMED"]
                raise SafeStop(report["stop_code"])
            set_status(report, "K1", "PASS", "EXPECTED_DATABASE_IDENTITY_CONFIRMED")
            report["postgresql_version"] = as_text(server_version)

            inventory(cursor, connection, repo_root, report)
    except SafeStop as stop:
        safe_stop_code = stop.code
        if report is not None:
            report["stop_code"] = report.get("stop_code") or stop.code
        exit_code = exit_code or (
            EXIT_CODES["PRE_OUTPUT_SAFE_STOP"]
            if output_dir is None
            else EXIT_CODES["POST_OUTPUT_SAFE_STOP"]
        )
    except KeyboardInterrupt:
        safe_stop_code = "INTERRUPTED"
        if report is not None:
            report["stop_code"] = report.get("stop_code") or safe_stop_code
        exit_code = EXIT_CODES["INTERRUPTED"]
    except Exception as exc:
        safe_stop_code = safe_exception_code(exc)
        if report is not None:
            report["stop_code"] = report.get("stop_code") or safe_stop_code
        exit_code = EXIT_CODES["UNEXPECTED_SAFE_EXCEPTION"]
    finally:
        if connection is not None:
            try:
                connection.rollback()
            except KeyboardInterrupt:
                if report is not None:
                    report["stop_code"] = report.get("stop_code") or "ROLLBACK_INTERRUPTED"
                exit_code = exit_code or EXIT_CODES["ROLLBACK_NOT_CONFIRMED"]
            except Exception:
                if report is not None:
                    report["stop_code"] = report.get("stop_code") or "ROLLBACK_NOT_CONFIRMED"
                exit_code = exit_code or EXIT_CODES["ROLLBACK_NOT_CONFIRMED"]
            try:
                connection.close()
            except KeyboardInterrupt:
                if report is not None:
                    report["stop_code"] = report.get("stop_code") or "CONNECTION_CLOSE_INTERRUPTED"
                exit_code = exit_code or EXIT_CODES["CONNECTION_CLOSE_NOT_CONFIRMED"]
            except Exception:
                if report is not None:
                    report["stop_code"] = report.get("stop_code") or "CONNECTION_CLOSE_NOT_CONFIRMED"
                exit_code = exit_code or EXIT_CODES["CONNECTION_CLOSE_NOT_CONFIRMED"]

    if report is not None and output_dir is not None:
        try:
            write_reports(output_dir, report)
        except SafeStop as stop:
            print(f"STOPPED_SAFELY: {stop.code}")
            return exit_code or EXIT_CODES["PAIRED_REPORT_WRITE_FAILED"]
        except Exception:
            print("STOPPED_SAFELY: REPORT_WRITE_FAILED")
            return exit_code or EXIT_CODES["PAIRED_REPORT_WRITE_FAILED"]
        if report.get("stop_code"):
            print(f"STOPPED_SAFELY: {report['stop_code']}")
        else:
            print("REPORTS_WRITTEN; paired inventory artifacts are available.")
        return exit_code

    print(f"STOPPED_SAFELY: {safe_stop_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
