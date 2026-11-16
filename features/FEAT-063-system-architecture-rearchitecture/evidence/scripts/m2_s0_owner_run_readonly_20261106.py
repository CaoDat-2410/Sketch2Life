"""Proposed read-only inventory for the FEAT-063 M2 S0-owner-run phase.

Draft only. Do not run until an independent review, a separate owner Task
Approval, an approved database identity, and the exact script hash are recorded.
The program never migrates, writes to database tables, or reads row contents.
"""

from __future__ import annotations

import argparse
import ast
import getpass
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None  # type: ignore[assignment]
    sql = None  # type: ignore[assignment]


LOG_ROOT_PARTS = (".claude", "handoff", "logs")
READ_ONLY_OPTIONS = (
    "-c default_transaction_read_only=on "
    "-c statement_timeout=20000 "
    "-c lock_timeout=3000"
)
CONNECT_TIMEOUT_SECONDS = 5
EXPECTED_SYNTHETIC_LABEL = "SYNTHETIC_DEV"
ORIGIN_CANDIDATE_COLUMNS = frozenset(
    {"data_origin", "origin", "data_source", "source_type", "age_source"}
)

# This exact manifest is used only by P1 static-AST mode. Draft 10 §8 names
# nine revision modules, while this graph calculation needs all 28. The owner
# must explicitly approve that wider read-only source scope before execution.
REVISION_FILES = (
    "20261014_0001_core_persistence.py",
    "20261014_0002_be1_runtime.py",
    "20261014_0003_canvas_payload.py",
    "20261014_0004_be1_constraint_names.py",
    "20261015_ai_0001_ai_jobs_schema.py",
    "20261017_ap_0001_policy_lifecycle.py",
    "20261017_ap_0002_effective_scope.py",
    "20261017_ap_0003_resource_ledger.py",
    "20261017_ap_0004_copy_inventory.py",
    "20261017_ap_0005_copy_evidence.py",
    "20261017_lc_0001_content_publication.py",
    "20261018_ap_0006_copy_operations.py",
    "20261018_ap_0007_copy_delivery.py",
    "20261018_ap_0008_delivery_authority.py",
    "20261018_ap_0009_copy_resolution.py",
    "20261018_kv_0001_knowledge_video.py",
    "20261018_vr_0001_video_review.py",
    "20261019_ae_0001_activity_execution.py",
    "20261019_pa_0001_preset_automation.py",
    "20261019_vf_0001_video_failure.py",
    "20261024_0005_classroom_srs_contracts.py",
    "20261028_ll_0001_lesson_library.py",
    "20261031_be1_synthetic_eligibility.py",
    "20261101_be1_age_provenance.py",
    "20261102_pilot_vision.py",
    "20261102_story_run_lite.py",
    "20261103_story_upload_compat.py",
    "20261104_story_revisions.py",
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
    parser = argparse.ArgumentParser(
        description="Read-only FEAT-063 S0-owner-run inventory; draft, approval required."
    )
    parser.add_argument("--expect-db", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--alembic-method",
        required=True,
        choices=("static-ast", "owner-cli"),
    )
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_]{1,63}", args.expect_db):
        raise SafeStop("DATABASE_NAME_FORMAT_REJECTED")
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


def as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


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
        source = (versions_dir / filename).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filename)
        revision = literal_value(tree, "revision")
        if not isinstance(revision, str) or not revision:
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
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "alembic_method": args.alembic_method,
        "checks": {
            f"K{number}": {"status": "NOT RUN"}
            for number in range(1, 7)
        },
        "source_schema_comparison": "NOT RUN; coordinator step after owner supplies output",
        "synthetic_scope_owner_proof": "NOT SUPPLIED TO SCRIPT",
        "stop_code": None,
    }


def set_status(
    report: dict[str, Any], key: str, status: str, detail: str
) -> None:
    report["checks"][key] = {"status": status, "detail": detail}


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
        db_versions: list[str] = []
    else:
        execute_allowed(cursor, connection, "alembic_versions")
        db_versions = sorted(as_text(row[0]) for row in cursor.fetchall())
        report["database_alembic_versions"] = db_versions
        if args_method := report["alembic_method"]:
            if args_method == "static-ast":
                try:
                    heads = source_heads(repo_root)
                except (OSError, SyntaxError, ValueError):
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
                set_status(report, "K3", "NOT RUN", "OWNER_CLI_OUTPUT_PENDING")

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
    set_status(report, "K4", "PASS", "INVENTORY_COLLECTED; SOURCE_COMPARISON_NOT_RUN")

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
        execute_allowed(
            cursor,
            connection,
            "table_count",
            identifiers=(schema_name, table_name),
        )
        row_count = int(cursor.fetchone()[0])
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

        execute_allowed(
            cursor,
            connection,
            "origin_counts",
            identifiers=(schema_name, table_name, origin_column),
        )
        buckets: dict[str, int] = defaultdict(int)
        for value, count in cursor.fetchall():
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
        raise SafeStop("K5_SYNTHETIC_ORIGIN_GATE_FAILED")
    if no_origin:
        set_status(report, "K5", "NOT RUN", "OWNER_PROOF_REQUIRED_FOR_TABLES_WITHOUT_DATA_ORIGIN")
    else:
        set_status(
            report,
            "K5",
            "NOT RUN",
            "OWNER_TABLE_SCOPE_AND_EXPECTED_COUNT_58_NOT_CONFIRMED",
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
    set_status(report, "K6", "PASS", "CHECK_DEFINITIONS_COLLECTED; NO_INTERPRETATION")


def validate_libpq_environment() -> dict[str, str]:
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
    return settings


def report_text(report: dict[str, Any]) -> str:
    lines = [
        "FEAT-063 M2 S0-owner-run — read-only observation",
        "This output is not an approval, acceptance, or phase closure.",
        f"Script SHA-256: {report['script_sha256']}",
        f"Expected database: {report['expected_database']}",
        f"PostgreSQL version: {report['postgresql_version'] or 'NOT VERIFIED'}",
        f"Generated UTC: {report['generated_at_utc']}",
        f"Alembic method: {report['alembic_method']}",
        f"Stop code: {report['stop_code'] or 'NONE'}",
        "",
        "Checks:",
    ]
    for key, value in report["checks"].items():
        lines.append(f"{key}: {value['status']} — {value['detail']}")
    lines.append(f"K4 source comparison: {report['source_schema_comparison']}")
    lines.append(f"K5 owner scope/proof: {report['synthetic_scope_owner_proof']}")
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
    try:
        with json_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json_payload)
        with text_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(report_text(report))
    except FileExistsError:
        raise SafeStop("OUTPUT_FILE_ALREADY_EXISTS") from None
    except OSError:
        raise SafeStop("OUTPUT_WRITE_FAILED") from None


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if sys.version_info[:2] != (3, 12):
            raise SafeStop("PYTHON_312_REQUIRED")
        reject_unsafe_inputs(raw_argv)
        args = parse_args(raw_argv)
        script_path = Path(__file__)
        repo_root = find_repository_root(script_path)
        settings = validate_libpq_environment()
        output_dir = prepare_output_directory(repo_root, args.out_dir)
    except SafeStop as stop:
        print(f"STOPPED_SAFELY: {stop.code}")
        return 2

    report = new_report(args, script_path)
    connection: Any | None = None
    exit_code = 0
    try:
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

        with connection.cursor() as cursor:
            # This must be the first SQL command. Connection options make the
            # first implicit transaction read-only before this SHOW is issued.
            execute_allowed(cursor, connection, "read_only")
            read_only_value = as_text(cursor.fetchone()[0]).lower()
            if read_only_value != "on":
                set_status(report, "K2", "FAIL", "READ_ONLY_TRANSACTION_NOT_CONFIRMED")
                report["stop_code"] = "K2_READ_ONLY_GATE_FAILED"
                exit_code = 3
                raise SafeStop(report["stop_code"])
            set_status(report, "K2", "PASS", "READ_ONLY_CONFIRMED_BEFORE_OTHER_QUERIES")

            execute_allowed(cursor, connection, "identity")
            actual_database, server_version = cursor.fetchone()
            if actual_database != args.expect_db:
                # Do not persist the unexpected database name or run another query.
                report["stop_code"] = "K1_IDENTITY_GATE_NOT_CONFIRMED"
                exit_code = 4
                raise SafeStop(report["stop_code"])
            set_status(report, "K1", "PASS", "EXPECTED_DATABASE_IDENTITY_CONFIRMED")
            report["postgresql_version"] = as_text(server_version)

            inventory(cursor, connection, repo_root, report)
    except SafeStop as stop:
        report["stop_code"] = report["stop_code"] or stop.code
        exit_code = exit_code or 5
    except Exception as exc:
        # Never print or serialize exception text; DB drivers can include
        # connection details in it. Only a coarse type label is recorded.
        error_type = type(exc).__name__
        safe_types = {
            "OperationalError": "DATABASE_CONNECTION_FAILED",
            "ProgrammingError": "READ_QUERY_FAILED",
            "QueryCanceled": "QUERY_TIMEOUT",
            "OSError": "LOCAL_READ_OR_WRITE_FAILED",
            "ValueError": "STATIC_METADATA_NOT_VERIFIABLE",
        }
        report["stop_code"] = safe_types.get(error_type, "UNEXPECTED_SAFE_STOP")
        exit_code = exit_code or 6
    finally:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                report["stop_code"] = report["stop_code"] or "ROLLBACK_NOT_CONFIRMED"
                exit_code = exit_code or 7
            try:
                connection.close()
            except Exception:
                report["stop_code"] = report["stop_code"] or "CONNECTION_CLOSE_NOT_CONFIRMED"
                exit_code = exit_code or 8

    try:
        write_reports(output_dir, report)
    except SafeStop as stop:
        print(f"STOPPED_SAFELY: {stop.code}")
        return exit_code or 9
    print("REPORTS_WRITTEN; see inventory.json and inventory.txt in the approved ignored output directory.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
