"""Owner-only Gate B: run the isolated Parent PostgreSQL acceptance once."""

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
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
SPEC_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/plan/"
    "M2_S1A_P_TASK_APPROVAL_DRAFT8_20261109.md"
)
LAUNCH_REL = Path(
    "features/FEAT-063-system-architecture-rearchitecture/plan/"
    "M2_S1A_P_GATE_B_LAUNCH_INSTRUCTION_DRAFT1_20261109.md"
)
APPROVAL_REL = Path("features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md")
DECISIONS_REL = Path("features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md")
APPEND_ONLY_READ_ONLY_INPUTS = frozenset(
    {
        DECISIONS_REL.as_posix(),
        APPROVAL_REL.as_posix(),
        (
            "features/FEAT-063-system-architecture-rearchitecture/plan/"
            "M2_PROGRESS_REPORT_FOR_CODEX_20261109.md"
        ),
    }
)
GATE_A_LOG_ROOT = Path(".claude/handoff/logs/M2_S1A_P_20261109")
GATE_B_LOG_ROOT = Path(".claude/handoff/logs/M2_S1A_P_GATE_B_20261109")
TEST_REL = Path("tests/integration/test_m2_s1a_parent_postgres.py")
EXPECTED_BRANCH = "feature/feat063-m2-parent-teacher-foundation"
EXPECTED_DATABASE = "sketch2life_m2_s1a"
EXPECTED_HOST = "127.0.0.1"
EXPECTED_PORT = 5433
EXPECTED_USER = "postgres"
EXPECTED_PG_MAJOR = 17
PARENT_REVISION = "20261109_m2_parent_profiles"
GATE_B_TIMEOUT_SECONDS = 1800
PARENT_TABLES = (
    "parent.child_profiles",
    "parent.profile_revisions",
    "parent.command_receipts",
)
PARENT_DB_ENV = (
    "BE1_TEST_DATABASE_URL",
    "S1A_P_TEST_DATABASE_URL",
    "S1A_P_ALEMBIC_DATABASE_URL",
    "S1A_T_TEST_DATABASE_URL",
    "DATABASE_URL",
    "SKETCH2LIFE_DATABASE_URL",
    "PGPASSWORD",
    "PGHOST",
    "PGPORT",
    "PGUSER",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGPASSFILE",
)
FILE_NAMES = (
    "pre-inventory.json",
    "pytest.command.txt",
    "pytest.stdout.txt",
    "pytest.stderr.txt",
    "pytest.exit.txt",
    "post-inventory.json",
    "runner-metadata.txt",
    "runner-status.txt",
    "safety-scan.json",
)
URI_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
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
    """A fixed stop code that does not include connection or credential data."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        raise SafeStop("PINNED_FILE_UNREADABLE") from None


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SafeStop("GIT_PREFLIGHT_FAILED")
    return result.stdout


def _matching_sections(text: str, prefix: str) -> list[tuple[str, str, int]]:
    lines = text.splitlines()
    matches = [
        index
        for index, line in enumerate(lines)
        if line.startswith("## ") and line[3:].startswith(prefix)
    ]
    sections: list[tuple[str, str, int]] = []
    for start in matches:
        end = next(
            (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
            len(lines),
        )
        sections.append((lines[start], "\n".join(lines[start:end]), start))
    return sections


def _section(text: str, prefix: str) -> tuple[str, str]:
    matches = _matching_sections(text, prefix)
    if len(matches) != 1:
        raise SafeStop("APPROVAL_SECTION_INVALID")
    heading, section, _start = matches[0]
    return heading, section


def _latest_section(text: str, prefix: str, missing_code: str) -> tuple[str, str]:
    matches = _matching_sections(text, prefix)
    if not matches:
        raise SafeStop(missing_code)
    heading, section, _start = matches[-1]
    return heading, section


def _latest_gate_a_approval(
    approval_text: str,
    approval_bytes: bytes,
    expected_branch: str,
    expected_head: str,
) -> tuple[str, str]:
    entries = _matching_sections(
        approval_text, "M2 S1a-P Gate A Approval —"
    )
    if not entries:
        raise SafeStop("GATE_A_APPROVAL_SECTION_MISSING")

    heading, section, _latest_start = entries[-1]
    if (
        _status_value(section, "APPROVED / NOT LAUNCHED")
        != "APPROVED / NOT LAUNCHED"
    ):
        raise SafeStop("GATE_A_APPROVAL_REQUIRED")

    branch = _field(section, "Approved branch")
    head = _field(section, "Approved HEAD")
    modal = _field(section, "OWNER_MODAL_CALL_APPROVED")
    prefix_hash = _field(section, "Approval prefix SHA-256").upper()
    if branch != expected_branch or head.lower() != expected_head.lower():
        raise SafeStop("GATE_A_APPROVAL_REPOSITORY_PIN_MISMATCH")
    if modal != "NO":
        raise SafeStop("MODAL_APPROVAL_STATE_MISMATCH")

    first_heading, _first_section, first_start = entries[0]
    lines = approval_bytes.splitlines(keepends=True)
    if first_start >= len(lines):
        raise SafeStop("GATE_A_APPROVAL_PREFIX_MISMATCH")
    first_heading_offset = sum(len(line) for line in lines[:first_start])
    if (
        not approval_bytes[first_heading_offset:].startswith(
            first_heading.encode("utf-8")
        )
        or _sha256_bytes(approval_bytes[:first_heading_offset]) != prefix_hash
    ):
        raise SafeStop("GATE_A_APPROVAL_PREFIX_MISMATCH")
    return heading, section


def _field(section: str, label: str) -> str:
    pattern = re.compile(rf"^- \*\*{re.escape(label)}:\*\* `([^`]+)`$", re.MULTILINE)
    matches = pattern.findall(section)
    if len(matches) != 1:
        raise SafeStop("APPROVAL_FIELD_INVALID")
    return matches[0]


def _status_value(section: str, expected_value: str) -> str:
    matches = re.findall(
        r"^(?:- )?\*\*Status:\*\* (.+)$", section, re.MULTILINE
    )
    if len(matches) != 1:
        raise SafeStop("APPROVAL_STATUS_INVALID")
    value = matches[0].strip()
    if value.startswith("`"):
        if not re.fullmatch(r"`[^`]+`", value):
            raise SafeStop("APPROVAL_STATUS_INVALID")
        value = value[1:-1]
    else:
        value = value.removesuffix(".")
    if value != expected_value:
        raise SafeStop("APPROVAL_STATUS_INVALID")
    return value


def _pin_table(section: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    in_table = False
    for line in section.splitlines():
        if line == "| Artifact | Repository-relative path | SHA-256 |":
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) != 3 or cells[0] == "---":
            continue
        if cells[0] in {"Artifact", "---"}:
            continue
        path = cells[1]
        if "\\" in path:
            raise SafeStop("APPROVAL_PIN_TABLE_INVALID")
        digest = cells[2].upper()
        if cells[0] in result or not re.fullmatch(r"[A-F0-9]{64}", digest):
            raise SafeStop("APPROVAL_PIN_TABLE_INVALID")
        result[cells[0]] = (path, digest)
    if not result:
        raise SafeStop("APPROVAL_PIN_TABLE_MISSING")
    return result


def _verify_gate_a_artifact_pins(section: str) -> None:
    expected_paths = {
        "S1a-P specification": SPEC_REL.as_posix(),
        "Gate A launch instruction": (
            "features/FEAT-063-system-architecture-rearchitecture/plan/"
            "M2_S1A_P_GATE_A_LAUNCH_INSTRUCTION_DRAFT1_20261109.md"
        ),
        "Gate A runner": (
            "features/FEAT-063-system-architecture-rearchitecture/evidence/"
            "scripts/m2_s1a_p_gate_a_20261109.py"
        ),
        "DECISIONS.md": DECISIONS_REL.as_posix(),
        "S1a-T pre-migration inventory": (
            ".claude/handoff/logs/M2_S1A_T_20261107/"
            "f7fe88273c7f4dd89b3913efeac6f8fb/inventory.post.json"
        ),
    }
    pins = _pin_table(section)
    if set(pins) != set(expected_paths):
        raise SafeStop("GATE_A_APPROVAL_PIN_SET_INVALID")
    for name, (relative, expected_hash) in pins.items():
        if relative != expected_paths[name]:
            raise SafeStop("GATE_A_APPROVAL_PIN_MISMATCH")
        path = (ROOT / Path(relative)).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SafeStop("GATE_A_APPROVAL_PIN_MISMATCH")
        if _sha256_file(path) != expected_hash:
            raise SafeStop("GATE_A_APPROVAL_PIN_MISMATCH")


def _manifest_hashes(section: str) -> dict[str, str]:
    result: dict[str, str] = {}
    roots = (
        "features/FEAT-063-system-architecture-rearchitecture/evidence/",
        "features/FEAT-063-system-architecture-rearchitecture/plan/",
    )
    lines = section.splitlines()
    markers = [
        index
        for index, line in enumerate(lines)
        if line == "**Exact current untracked Markdown manifest:**"
    ]
    if len(markers) != 1:
        raise SafeStop("UNTRACKED_MANIFEST_INVALID")
    marker_index = markers[0]
    table_index = marker_index + 1
    if table_index < len(lines) and lines[table_index] == "":
        table_index += 1
    if (
        table_index + 1 >= len(lines)
        or lines[table_index] != "| Path | SHA-256 |"
        or lines[table_index + 1] != "|---|---|"
    ):
        raise SafeStop("UNTRACKED_MANIFEST_INVALID")
    for line in lines[table_index + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) != 2:
            raise SafeStop("UNTRACKED_MANIFEST_INVALID")
        path, digest = cells[0], cells[1].upper()
        path_parts = path.split("/")
        if (
            path in result
            or not path.endswith(".md")
            or not path.startswith(roots)
            or any(part in {"", ".", ".."} for part in path_parts)
            or not re.fullmatch(r"[A-F0-9]{64}", digest)
        ):
            raise SafeStop("UNTRACKED_MANIFEST_INVALID")
        file_path = (ROOT / Path(*path_parts)).resolve()
        allowed_paths = tuple(
            (ROOT / root.rstrip("/")).resolve() for root in roots
        )
        if (
            ROOT.resolve() not in file_path.parents
            or not any(root in file_path.parents for root in allowed_paths)
            or not file_path.is_file()
        ):
            raise SafeStop("UNTRACKED_MANIFEST_INVALID")
        if _sha256_file(file_path) != digest:
            raise SafeStop("UNTRACKED_MANIFEST_HASH_MISMATCH")
        result[path] = digest
    if not result:
        raise SafeStop("UNTRACKED_MANIFEST_MISSING")
    return result


def _gate_a_inventory_path(relative: str) -> Path:
    root_prefix = GATE_A_LOG_ROOT.as_posix()
    parts = relative.split("/")
    if (
        "\\" in relative
        or not relative.startswith(root_prefix + "/")
        or not relative.endswith("/post-inventory.json")
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise SafeStop("GATE_A_INVENTORY_PATH_INVALID")
    path = (ROOT / Path(*parts)).resolve()
    resolved_root = (ROOT / GATE_A_LOG_ROOT).resolve()
    if (
        ROOT.resolve() not in path.parents
        or resolved_root not in path.parents
        or not path.is_file()
    ):
        raise SafeStop("GATE_A_INVENTORY_PATH_INVALID")
    return path


def _validate_inventory_shape(value: object) -> dict[str, Any]:
    expected_fields = {
        "run_id",
        "source_marker_run_id",
        "read_only",
        "identity",
        "parent_schema_exists",
        "table_rows",
        "total_rows",
        "marker_rows",
        "marker_total",
        "known_control_rows",
        "unmatched_tables",
        "alembic_versions",
        "status",
    }
    if type(value) is not dict or set(value) != expected_fields:
        raise SafeStop("GATE_A_INVENTORY_INVALID")
    inventory: dict[str, Any] = value
    identity = inventory["identity"]
    if (
        type(identity) is not dict
        or set(identity) != {"database", "host", "port", "user", "postgres_major"}
        or not all(type(identity[key]) is str for key in ("database", "host", "user"))
        or type(identity["port"]) is not int
        or type(identity["postgres_major"]) is not int
        or type(inventory["run_id"]) is not str
        or type(inventory["source_marker_run_id"]) is not str
        or inventory["read_only"] is not True
        or inventory["parent_schema_exists"] is not True
        or type(inventory["status"]) is not str
        or type(inventory["alembic_versions"]) is not list
        or not all(type(item) is str for item in inventory["alembic_versions"])
    ):
        raise SafeStop("GATE_A_INVENTORY_INVALID")
    count_maps = (
        "table_rows",
        "marker_rows",
        "known_control_rows",
        "unmatched_tables",
    )
    for key in count_maps:
        counts = inventory[key]
        if type(counts) is not dict or not all(
            type(name) is str and type(count) is int and count >= 0
            for name, count in counts.items()
        ):
            raise SafeStop("GATE_A_INVENTORY_INVALID")
    table_rows = inventory["table_rows"]
    marker_rows = inventory["marker_rows"]
    if (
        len(table_rows) != 120
        or type(inventory["total_rows"]) is not int
        or inventory["total_rows"] < 0
        or inventory["total_rows"] != sum(table_rows.values())
        or type(inventory["marker_total"]) is not int
        or inventory["marker_total"] < 0
        or inventory["marker_total"] != sum(marker_rows.values())
    ):
        raise SafeStop("GATE_A_INVENTORY_INVALID")
    return inventory


def _mode_backend_paths(spec_text: str) -> set[str]:
    result: set[str] = set()
    for line in spec_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] not in {"E", "R/E", "N"}:
            continue
        relative = cells[1].strip("`").replace("\\", "/")
        if relative.startswith("backend/"):
            if relative in result:
                raise SafeStop("SOURCE_ALLOWLIST_DUPLICATE")
            result.add(relative)
    if not result:
        raise SafeStop("SOURCE_ALLOWLIST_MISSING")
    return result


def _source_hashes(document: str, marker: str) -> dict[str, str]:
    lines = document.splitlines()
    marker_indexes = [index for index, line in enumerate(lines) if line == marker]
    if len(marker_indexes) != 1:
        raise SafeStop("SOURCE_HASH_MANIFEST_MISSING")
    result: dict[str, str] = {}
    for line in lines[marker_indexes[0] + 1 :]:
        if not line.startswith("|"):
            if result:
                break
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) != 2 or cells[0] in {"Path", "---"}:
            continue
        relative, expected = cells[0].replace("\\", "/"), cells[1].upper()
        if (
            relative in result
            or not relative.startswith("backend/")
            or ".." in Path(relative).parts
            or not re.fullmatch(r"[A-F0-9]{64}", expected)
        ):
            raise SafeStop("SOURCE_HASH_MANIFEST_INVALID")
        result[relative] = expected
    if not result:
        raise SafeStop("SOURCE_HASH_MANIFEST_MISSING")
    return result


def _verify_mode_backend_source_hashes(
    spec_text: str, gate_a_section: str, gate_b_section: str, launch_text: str
) -> None:
    marker = "**Mode E/R/E/N backend source SHA-256:**"
    gate_a_hashes = _source_hashes(gate_a_section, marker)
    gate_b_hashes = _source_hashes(gate_b_section, marker)
    launch_hashes = _source_hashes(launch_text, marker)
    expected_paths = _mode_backend_paths(spec_text)
    if (
        set(gate_a_hashes) != expected_paths
        or set(gate_b_hashes) != expected_paths
        or set(launch_hashes) != expected_paths
        or gate_a_hashes != gate_b_hashes
        or gate_b_hashes != launch_hashes
    ):
        raise SafeStop("SOURCE_HASH_MANIFEST_MISMATCH")
    for relative, expected in gate_b_hashes.items():
        path = (ROOT / Path(relative)).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SafeStop("PINNED_SOURCE_FILE_MISSING")
        if _sha256_file(path) != expected:
            raise SafeStop("PINNED_SOURCE_HASH_MISMATCH")


def _read_only_input_hashes(spec_text: str) -> dict[str, str]:
    lines = spec_text.splitlines()
    heading = "### 5.1 Read-only inputs (R)"
    heading_indexes = [index for index, line in enumerate(lines) if line == heading]
    if len(heading_indexes) != 1:
        raise SafeStop("READ_ONLY_PIN_TABLE_INVALID")
    table_start = next(
        (
            index
            for index in range(heading_indexes[0] + 1, len(lines))
            if lines[index].startswith("|")
        ),
        -1,
    )
    if (
        table_start < 0
        or lines[table_start] != "| Mode | Repository-relative path | SHA-256 |"
        or table_start + 1 >= len(lines)
        or lines[table_start + 1] != "|---|---|---|"
    ):
        raise SafeStop("READ_ONLY_PIN_TABLE_INVALID")

    result: dict[str, str] = {}
    for line in lines[table_start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) != 3:
            raise SafeStop("READ_ONLY_PIN_TABLE_INVALID")
        mode = cells[0]
        relative = cells[1].replace("\\", "/")
        digest = cells[2].upper()
        if mode in {"Mode", "---"} or mode not in {"R", "H"}:
            continue
        path_parts = relative.split("/")
        if (
            relative in result
            or not relative
            or relative.startswith("/")
            or re.match(r"^[A-Za-z]:", relative)
            or "\\" in cells[1]
            or any(part in {"", ".", ".."} for part in path_parts)
            or not re.fullmatch(r"[A-F0-9]{64}", digest)
        ):
            raise SafeStop("READ_ONLY_PIN_TABLE_INVALID")
        result[relative] = digest
    if not result or not APPEND_ONLY_READ_ONLY_INPUTS.issubset(result):
        raise SafeStop("READ_ONLY_PIN_TABLE_INVALID")
    return result


def _has_pinned_append_only_prefix(path: Path, expected: str) -> bool:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for line in source:
                digest.update(line)
                if digest.hexdigest().upper() == expected:
                    return True
    except OSError:
        raise SafeStop("PINNED_FILE_UNREADABLE") from None
    return False


def _verify_read_only_input_hashes(
    spec_text: str,
    approval_section: str,
    approval_bytes: bytes,
    approval_heading_offset: int,
    decisions_pin: tuple[str, str],
) -> None:
    pins = _read_only_input_hashes(spec_text)
    approval_prefix_hash = _field(approval_section, "Approval prefix SHA-256").upper()
    if (
        approval_heading_offset < 0
        or _sha256_bytes(approval_bytes[:approval_heading_offset])
        != approval_prefix_hash
    ):
        raise SafeStop("APPROVAL_PREFIX_MISMATCH")

    for relative, expected in pins.items():
        path = (ROOT / Path(*relative.split("/"))).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SafeStop("PINNED_FILE_UNREADABLE")
        if relative in APPEND_ONLY_READ_ONLY_INPUTS:
            if not _has_pinned_append_only_prefix(path, expected):
                raise SafeStop("READ_ONLY_APPEND_PREFIX_MISMATCH")
            continue
        if _sha256_file(path) != expected:
            raise SafeStop("READ_ONLY_INPUT_HASH_MISMATCH")

    decision_path, decision_hash = decisions_pin
    if (
        decision_path != DECISIONS_REL.as_posix()
        or _sha256_file(ROOT / DECISIONS_REL) != decision_hash
    ):
        raise SafeStop("APPROVAL_PIN_MISMATCH")


def _verify_allowlisted_changes(spec_text: str, approval_section: str) -> None:
    editable: set[str] = set()
    new_paths: set[str] = set()
    for line in spec_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        path = cells[1].strip("`").replace("\\", "/")
        if cells[0] in {"E", "R/E"}:
            editable.add(path)
        elif cells[0] == "N":
            new_paths.add(path)

    scope_prefixes = (
        "backend/alembic/",
        "backend/src/",
        "backend/tests/",
        "features/FEAT-063-system-architecture-rearchitecture/evidence/",
        "features/FEAT-063-system-architecture-rearchitecture/plan/",
    )
    tracked_changes = {
        path.replace("\\", "/")
        for path in _git("diff", "--name-only", "HEAD").splitlines()
        if path.replace("\\", "/").startswith(scope_prefixes)
    }
    if tracked_changes - editable:
        raise SafeStop("CHANGE_OUTSIDE_APPROVED_ALLOWLIST")

    # Check every untracked path. Prefix filtering here would let an unrelated
    # untracked file bypass the Gate A/B allowlist and pinned manifest.
    untracked_paths = {
        path.replace("\\", "/")
        for path in _git("ls-files", "--others", "--exclude-standard").splitlines()
    }
    manifest = _manifest_hashes(approval_section)
    unexpected = untracked_paths - new_paths - set(manifest)
    if unexpected:
        raise SafeStop("UNTRACKED_PATH_OUTSIDE_APPROVED_ALLOWLIST")


def _verify_repository() -> None:
    if _git("branch", "--show-current").strip() != EXPECTED_BRANCH:
        raise SafeStop("BRANCH_MISMATCH")
    if _git("rev-parse", "HEAD").strip().lower() != _field_from_gate_b("Approved HEAD").lower():
        raise SafeStop("HEAD_MISMATCH")
    if _git("diff", "--cached", "--name-only").strip():
        raise SafeStop("INDEX_NOT_EMPTY")


def _field_from_gate_b(label: str) -> str:
    approval_path = ROOT / APPROVAL_REL
    try:
        text = approval_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise SafeStop("APPROVAL_UNREADABLE") from None
    _heading, section = _section(text, "M2 S1a-P Gate B Approval —")
    return _field(section, label)


def _verify_approval() -> tuple[dict[str, Any], str]:
    approval_path = ROOT / APPROVAL_REL
    try:
        approval_bytes = approval_path.read_bytes()
        approval_text = approval_bytes.decode("utf-8")
        spec_text = (ROOT / SPEC_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise SafeStop("APPROVAL_INPUT_UNREADABLE") from None
    gate_heading, gate_b = _section(approval_text, "M2 S1a-P Gate B Approval —")
    if (
        _status_value(gate_b, "APPROVED / NOT LAUNCHED")
        != "APPROVED / NOT LAUNCHED"
    ):
        raise SafeStop("GATE_B_APPROVAL_REQUIRED")
    if _field(gate_b, "OWNER_MODAL_CALL_APPROVED") != "NO":
        raise SafeStop("MODAL_APPROVAL_STATE_MISMATCH")
    branch = _field(gate_b, "Approved branch")
    head = _field(gate_b, "Approved HEAD")
    if branch != EXPECTED_BRANCH or not re.fullmatch(r"[0-9a-f]{40}", head.lower()):
        raise SafeStop("APPROVAL_REPOSITORY_PIN_INVALID")
    start = approval_bytes.find(gate_heading.encode("utf-8"))
    if start < 0 or _sha256_bytes(approval_bytes[:start]) != _field(
        gate_b, "Approval prefix SHA-256"
    ).upper():
        raise SafeStop("APPROVAL_PREFIX_MISMATCH")

    pins = _pin_table(gate_b)
    required_artifacts = {
        "S1a-P specification": SPEC_REL.as_posix(),
        "Gate B launch instruction": "features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_GATE_B_LAUNCH_INSTRUCTION_DRAFT1_20261109.md",
        "Gate B runner": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "DECISIONS.md": DECISIONS_REL.as_posix(),
        "Gate A post-inventory": "",
    }
    if set(pins) != set(required_artifacts):
        raise SafeStop("APPROVAL_PIN_SET_INVALID")
    gate_a_inventory_bytes: bytes | None = None
    for name, (relative, expected) in pins.items():
        expected_path = required_artifacts[name]
        if name == "Gate A post-inventory":
            path = _gate_a_inventory_path(relative)
            try:
                gate_a_inventory_bytes = path.read_bytes()
            except OSError:
                raise SafeStop("GATE_A_INVENTORY_INVALID") from None
            if _sha256_bytes(gate_a_inventory_bytes) != expected:
                raise SafeStop("APPROVAL_PIN_MISMATCH")
            continue
        if relative != expected_path:
            raise SafeStop("APPROVAL_PIN_MISMATCH")
        path = (ROOT / Path(relative)).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SafeStop("APPROVAL_PIN_MISMATCH")
        if _sha256_file(path) != expected:
            raise SafeStop("APPROVAL_PIN_MISMATCH")

    gate_a_heading, gate_a = _latest_section(
        approval_text,
        "M2 S1a-P Gate A Closure Acceptance —",
        "GATE_A_ACCEPTANCE_REQUIRED",
    )
    if _status_value(gate_a, "ACCEPTED") != "ACCEPTED":
        raise SafeStop("GATE_A_ACCEPTANCE_REQUIRED")
    _gate_a_approval_heading, gate_a_approval = _latest_gate_a_approval(
        approval_text,
        approval_bytes,
        branch,
        head,
    )
    _verify_gate_a_artifact_pins(gate_a_approval)
    gate_a_manifest = _manifest_hashes(gate_a_approval)
    gate_b_manifest = _manifest_hashes(gate_b)
    if gate_a_manifest != gate_b_manifest:
        raise SafeStop("GATE_A_UNTRACKED_MANIFEST_MISMATCH")
    gate_a_pins = _pin_table(gate_a)
    gate_a_inventory_path, gate_a_inventory_hash = pins["Gate A post-inventory"]
    if (
        gate_a_pins.get("Gate A post-inventory")
        != (gate_a_inventory_path, gate_a_inventory_hash)
        or not gate_a_heading
    ):
        raise SafeStop("GATE_A_INVENTORY_ACCEPTANCE_REQUIRED")

    _verify_allowlisted_changes(spec_text, gate_b)
    try:
        launch_text = (ROOT / LAUNCH_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise SafeStop("LAUNCH_INPUT_UNREADABLE") from None
    _verify_mode_backend_source_hashes(
        spec_text, gate_a_approval, gate_b, launch_text
    )
    _verify_read_only_input_hashes(
        spec_text,
        gate_b,
        approval_bytes,
        start,
        pins["DECISIONS.md"],
    )

    if gate_a_inventory_bytes is None:
        raise SafeStop("GATE_A_INVENTORY_INVALID")
    try:
        baseline = json.loads(gate_a_inventory_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise SafeStop("GATE_A_INVENTORY_INVALID") from None
    baseline = _validate_inventory_shape(baseline)
    if (
        baseline.get("read_only") is not True
        or baseline.get("status") != "MARKER_COUNTS_MATCH"
        or baseline.get("parent_schema_exists") is not True
        or len(baseline.get("table_rows", {})) != 120
        or baseline.get("total_rows") != 30
        or baseline.get("marker_total") != 29
        or baseline.get("unmatched_tables") != {}
        or baseline.get("alembic_versions") != [PARENT_REVISION]
        or any(baseline.get("table_rows", {}).get(table) != 0 for table in PARENT_TABLES)
    ):
        raise SafeStop("GATE_A_INVENTORY_CONTENT_MISMATCH")
    return baseline, head


def _require_clean_database_environment() -> None:
    if os.environ.get("OWNER_MODAL_CALL_APPROVED", "NO") != "NO":
        raise SafeStop("MODAL_APPROVAL_STATE_MISMATCH")
    if any(os.environ.get(name) for name in PARENT_DB_ENV):
        raise SafeStop("DATABASE_ENVIRONMENT_NOT_CLEAN")
    if os.environ.get("S1A_P_GATE_B_RUN_ID"):
        raise SafeStop("GATE_B_RUN_ID_INHERITED")


def _reserve_outputs() -> tuple[str, Path, dict[str, Path]]:
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", (GATE_B_LOG_ROOT / "probe").as_posix()],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if ignored.returncode != 0:
        raise SafeStop("GATE_B_LOG_ROOT_NOT_IGNORED")
    base = ROOT / GATE_B_LOG_ROOT
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise SafeStop("GATE_B_LOG_ROOT_NOT_WRITABLE") from None
    run_id = uuid.uuid4().hex
    run_name = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{run_id[:12]}"
    run_dir = base / run_name
    try:
        run_dir.mkdir()
    except OSError:
        raise SafeStop("GATE_B_RUN_DIRECTORY_COLLISION") from None
    files = {name: run_dir / name for name in FILE_NAMES}
    try:
        for path in files.values():
            with path.open("xb"):
                pass
        (run_dir / "pytest-tmp").mkdir()
    except OSError:
        raise SafeStop("GATE_B_OUTPUT_RESERVATION_FAILED") from None
    return run_id, run_dir, files


def _write_reserved(path: Path, data: bytes) -> None:
    try:
        with path.open("r+b") as stream:
            stream.seek(0)
            written = stream.write(data)
            if written != len(data):
                raise OSError("short artifact write")
            stream.truncate()
    except OSError:
        raise SafeStop("GATE_B_LOG_WRITE_FAILED") from None


def _write_json(path: Path, value: object) -> None:
    _write_reserved(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def _database_identity(cursor: Any) -> dict[str, object]:
    cursor.execute("SELECT current_setting('transaction_read_only')")
    if cursor.fetchone()[0] != "on":
        raise SafeStop("READ_ONLY_NOT_CONFIRMED")
    cursor.execute(
        "SELECT current_database(), host(inet_server_addr()), inet_server_port(), "
        "current_user, current_setting('server_version_num')::integer"
    )
    database, host_text, port, user, version = cursor.fetchone()
    try:
        if (
            str(database) != EXPECTED_DATABASE
            or str(user) != EXPECTED_USER
            or int(port) != EXPECTED_PORT
            or not ipaddress.ip_address(str(host_text)).is_loopback
            or int(version) // 10000 != EXPECTED_PG_MAJOR
        ):
            raise SafeStop("DATABASE_IDENTITY_MISMATCH")
    except (ValueError, TypeError, OverflowError):
        raise SafeStop("DATABASE_IDENTITY_MISMATCH") from None
    return {
        "database": str(database),
        "host": str(host_text),
        "port": int(port),
        "user": str(user),
        "postgres_major": int(version) // 10000,
    }


def _source_marker_counts(cursor: Any, source_run_id: str) -> dict[str, int]:
    try:
        from psycopg import sql
    except ImportError:
        raise SafeStop("PSYCOPG_UNAVAILABLE") from None
    specs = (
        ("public.be1_organizations", "organization_id", f"synthetic-s1at-{source_run_id}-org", False),
        ("public.be1_classrooms", "class_id", f"synthetic-s1at-{source_run_id}-class", False),
        ("public.be1_adult_identities", "subject", f"synthetic-s1at-{source_run_id}-teacher", False),
        ("public.be1_organization_assignments", "subject", f"synthetic-s1at-{source_run_id}-teacher", False),
        ("public.be1_managed_profiles", "display_name", f"Synthetic S1AT {source_run_id} ", False),
        ("public.be1_synthetic_eligibility_proofs", "run_ref", f"s1at-run-{source_run_id}", True),
        ("public.core_audit_entries", "organization_id", f"synthetic-s1at-{source_run_id}-org", False),
        ("public.core_aggregate_revisions", "organization_id", f"synthetic-s1at-{source_run_id}-org", False),
        ("public.core_outbox_events", "organization_id", f"synthetic-s1at-{source_run_id}-org", False),
    )
    counts: dict[str, int] = {}
    for qualified, column, marker, exact in specs:
        schema, table = qualified.split(".", 1)
        operator = sql.SQL("{} = %s") if exact else sql.SQL("left({}::text, %s) = %s")
        predicate = operator.format(sql.Identifier(column))
        parameters: tuple[object, ...] = (marker,) if exact else (len(marker), marker)
        cursor.execute(
            sql.SQL("SELECT count(*) FROM {}.{} WHERE ").format(
                sql.Identifier(schema), sql.Identifier(table)
            ) + predicate,
            parameters,
        )
        counts[qualified] = int(cursor.fetchone()[0])
    cursor.execute(
        "SELECT count(*) FROM public.be1_enrollments e "
        "JOIN public.be1_managed_profiles p ON p.child_id=e.child_id "
        "WHERE left(p.display_name, %s)=%s",
        (len(f"Synthetic S1AT {source_run_id} "), f"Synthetic S1AT {source_run_id} "),
    )
    counts["public.be1_enrollments"] = int(cursor.fetchone()[0])
    return dict(sorted(counts.items()))


def _parent_marker_counts(cursor: Any, run_id: str) -> dict[str, int]:
    owner_subject = f"s1a-p-{run_id}-owner"
    issuer = "synthetic-parent-issuer"
    cursor.execute(
        "SELECT count(*) FROM parent.child_profiles "
        "WHERE owner_issuer=%s AND owner_subject=%s",
        (issuer, owner_subject),
    )
    profiles = int(cursor.fetchone()[0])
    cursor.execute(
        "SELECT count(*) FROM parent.profile_revisions r "
        "JOIN parent.child_profiles p ON p.parent_profile_id=r.parent_profile_id "
        "WHERE p.owner_issuer=%s AND p.owner_subject=%s "
        "AND r.authored_by_issuer=%s AND r.authored_by_subject=%s",
        (issuer, owner_subject, issuer, owner_subject),
    )
    revisions = int(cursor.fetchone()[0])
    cursor.execute(
        "SELECT count(*) FROM parent.command_receipts "
        "WHERE principal_issuer=%s AND principal_subject=%s",
        (issuer, owner_subject),
    )
    receipts = int(cursor.fetchone()[0])
    return {
        "parent.child_profiles": profiles,
        "parent.profile_revisions": revisions,
        "parent.command_receipts": receipts,
    }


def _inventory(password: str, run_id: str, source_run_id: str) -> dict[str, Any]:
    try:
        import psycopg
        from psycopg import sql
    except ImportError:
        raise SafeStop("PSYCOPG_UNAVAILABLE") from None
    connection = None
    try:
        connection = psycopg.connect(
            dbname=EXPECTED_DATABASE,
            host=EXPECTED_HOST,
            port=EXPECTED_PORT,
            user=EXPECTED_USER,
            password=password,
            connect_timeout=5,
            options="-c default_transaction_read_only=on",
            autocommit=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("BEGIN READ ONLY")
            identity = _database_identity(cursor)
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata "
                "WHERE schema_name='parent')"
            )
            parent_schema_exists = bool(cursor.fetchone()[0])
            cursor.execute(
                "SELECT n.nspname,c.relname FROM pg_catalog.pg_class c "
                "JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace "
                "WHERE c.relkind IN ('r','p') "
                "AND n.nspname NOT IN ('pg_catalog','information_schema') "
                "AND n.nspname NOT LIKE 'pg_toast%' "
                "AND n.nspname NOT LIKE 'pg_temp_%' ORDER BY n.nspname,c.relname"
            )
            relations = [(str(schema), str(table)) for schema, table in cursor.fetchall()]
            table_rows: dict[str, int] = {}
            for schema, table in relations:
                cursor.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier(schema), sql.Identifier(table)
                    )
                )
                table_rows[f"{schema}.{table}"] = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT version_num FROM public.alembic_version ORDER BY version_num"
            )
            versions = [str(row[0]) for row in cursor.fetchall()]
            markers = _source_marker_counts(cursor, source_run_id)
            parent_markers = _parent_marker_counts(cursor, run_id)
            markers.update({key: value for key, value in parent_markers.items() if value})
        connection.rollback()
    except SafeStop:
        raise
    except Exception:  # noqa: BLE001 -- All inventory errors must stop safely.
        raise SafeStop("READ_ONLY_INVENTORY_FAILED") from None
    finally:
        if connection is not None:
            with suppress(Exception):
                connection.rollback()
            with suppress(Exception):
                connection.close()

    total_rows = sum(table_rows.values())
    marker_total = sum(markers.values())
    known_control = {"public.alembic_version": 1} if versions == [PARENT_REVISION] else {}
    unmatched = {
        table: count - markers.get(table, 0) - known_control.get(table, 0)
        for table, count in table_rows.items()
        if count != markers.get(table, 0) + known_control.get(table, 0)
    }
    status = (
        "MARKER_COUNTS_MATCH"
        if not unmatched and total_rows == marker_total + sum(known_control.values())
        else "UNKNOWN_ROWS_FOUND"
    )
    return {
        "run_id": run_id,
        "source_marker_run_id": source_run_id,
        "read_only": True,
        "identity": identity,
        "parent_schema_exists": parent_schema_exists,
        "table_rows": dict(sorted(table_rows.items())),
        "total_rows": total_rows,
        "marker_rows": dict(sorted(markers.items())),
        "marker_total": marker_total,
        "known_control_rows": known_control,
        "unmatched_tables": dict(sorted(unmatched.items())),
        "alembic_versions": versions,
        "status": status,
    }


def _projection(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in {"run_id", "status"}}


def _check_gate_a_baseline(current: dict[str, Any], baseline: dict[str, Any]) -> None:
    if (
        current.get("read_only") is not True
        or current.get("status") != "MARKER_COUNTS_MATCH"
        or current.get("source_marker_run_id") != baseline.get("source_marker_run_id")
        or current.get("parent_schema_exists") is not True
        or len(current.get("table_rows", {})) != 120
        or current.get("total_rows") != 30
        or current.get("marker_total") != 29
        or current.get("unmatched_tables") != {}
        or current.get("alembic_versions") != [PARENT_REVISION]
        or any(current.get("table_rows", {}).get(table) != 0 for table in PARENT_TABLES)
        or _projection(current) != _projection(baseline)
    ):
        raise SafeStop("GATE_A_POST_INVENTORY_MISMATCH")


def _check_gate_b_post_inventory(
    post: dict[str, Any], pre: dict[str, Any], run_id: str
) -> None:
    expected_rows = dict(pre["table_rows"])
    expected_rows.update(
        {
            "parent.child_profiles": 1,
            "parent.profile_revisions": 2,
            "parent.command_receipts": 3,
        }
    )
    expected_markers = dict(pre["marker_rows"])
    expected_markers.update(
        {
            "parent.child_profiles": 1,
            "parent.profile_revisions": 2,
            "parent.command_receipts": 3,
        }
    )
    if (
        post.get("run_id") != run_id
        or post.get("read_only") is not True
        or post.get("status") != "MARKER_COUNTS_MATCH"
        or post.get("source_marker_run_id") != pre.get("source_marker_run_id")
        or post.get("table_rows") != dict(sorted(expected_rows.items()))
        or post.get("marker_rows") != dict(sorted(expected_markers.items()))
        or post.get("total_rows") != pre.get("total_rows", 0) + 6
        or post.get("marker_total") != pre.get("marker_total", 0) + 6
        or post.get("known_control_rows") != pre.get("known_control_rows")
        or post.get("unmatched_tables") != {}
        or post.get("alembic_versions") != [PARENT_REVISION]
    ):
        raise SafeStop("GATE_B_POST_INVENTORY_MISMATCH")


def _safety_counts_from_texts(texts: tuple[str, ...]) -> dict[str, int]:
    counts = {name: 0 for name in SENSITIVE_PATTERNS}
    counts["scheme_url"] = 0
    for text in texts:
        counts["scheme_url"] += len(URI_RE.findall(text))
        for name, pattern in SENSITIVE_PATTERNS.items():
            counts[name] += len(pattern.findall(text))
    counts["unverified_or_uri_matches"] = counts["scheme_url"] + sum(
        counts[name] for name in SENSITIVE_PATTERNS
    )
    return counts


def _store_pytest_output(
    files: dict[str, Path], stdout: bytes, stderr: bytes
) -> None:
    counts = _safety_counts_from_texts(
        (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )
    )
    if counts["unverified_or_uri_matches"]:
        withheld = b"[WITHHELD: output safety match]\n"
        try:
            _write_reserved(files["pytest.stdout.txt"], withheld)
            _write_reserved(files["pytest.stderr.txt"], withheld)
            _write_json(files["safety-scan.json"], counts)
        except SafeStop as stop:
            if stop.code == "GATE_B_LOG_WRITE_FAILED":
                raise
            raise SafeStop("OUTPUT_SAFETY_FINDING") from None
        raise SafeStop("OUTPUT_SAFETY_FINDING")
    _write_reserved(files["pytest.stdout.txt"], stdout)
    _write_reserved(files["pytest.stderr.txt"], stderr)


def _scan_safety(files: dict[str, Path]) -> dict[str, int]:
    texts: list[str] = []
    for path in files.values():
        if path.name == "safety-scan.json" or path.name.endswith(
            "-safety-scan.json"
        ):
            continue
        try:
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            raise SafeStop("OUTPUT_SCAN_FAILED") from None
    counts = _safety_counts_from_texts(tuple(texts))
    _write_json(files["safety-scan.json"], counts)
    if counts["unverified_or_uri_matches"]:
        raise SafeStop("OUTPUT_SAFETY_FINDING")
    return counts


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")
    try:
        result = subprocess.run(
            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired, KeyboardInterrupt):
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    if result.returncode != 0:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")
    try:
        process.wait(timeout=20)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    if process.poll() is None:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")


def _pytest_summary(stdout_path: Path) -> bool:
    try:
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        raise SafeStop("PYTEST_OUTPUT_UNREADABLE") from None
    summaries = re.findall(
        r"(?m)^(\d+) passed(?:, [^\r\n]*)? in [0-9]+(?:\.[0-9]+)?s\r?$",
        stdout,
    )
    return summaries == ["1"] and not re.search(r"(?i)\b(?:failed|error)\b", stdout)


def _pytest_child_environment(
    database_url: str, run_id: str, temp_directory: Path
) -> dict[str, str]:
    system_root = os.environ.get("SystemRoot")
    if not system_root or not Path(system_root).is_absolute():
        raise SafeStop("WINDOWS_SYSTEM_ROOT_UNAVAILABLE")

    system_root_path = Path(system_root)
    base_prefix = Path(sys.base_prefix)
    path_entries = (
        BACKEND / ".venv" / "Scripts",
        base_prefix,
        base_prefix / "DLLs",
        system_root_path / "System32",
    )
    return {
        "PATH": os.pathsep.join(str(path) for path in path_entries),
        "SYSTEMROOT": str(system_root_path),
        "WINDIR": str(system_root_path),
        "TEMP": str(temp_directory.resolve()),
        "TMP": str(temp_directory.resolve()),
        "PYTHONNOUSERSITE": "1",
        "S1A_P_TEST_DATABASE_URL": database_url,
        "S1A_P_GATE_B_RUN_ID": run_id,
    }


def _run_pytest(run_id: str, run_dir: Path, files: dict[str, Path], password: str) -> int:
    relative_tmp = (run_dir / "pytest-tmp").relative_to(ROOT).as_posix()
    relative_from_backend = Path("..") / Path(relative_tmp)
    basetemp_argument = f"--basetemp={str(relative_from_backend).replace('/', chr(92))}"
    command = (
        f".venv\\Scripts\\python.exe -m pytest {TEST_REL.as_posix()} "
        f"-p no:cacheprovider {basetemp_argument}"
    )
    _write_reserved(
        files["pytest.command.txt"],
        (
            "GATE=GATE_B\nCWD=backend\n"
            "COMMAND=.venv/Scripts/python.exe -m pytest "
            f"{TEST_REL.as_posix()} -p no:cacheprovider --basetemp=<unique-log-folder>/pytest-tmp\n"
            "DATABASE_VALUE=CHILD_ENV_ONLY;REDACTED\n"
            f"RUN_ID={run_id}\nTIMEOUT_SECONDS={GATE_B_TIMEOUT_SECONDS}\n"
        ).encode(),
    )
    database_url = URL.create(
        "postgresql+psycopg",
        username=EXPECTED_USER,
        password=password,
        host=EXPECTED_HOST,
        port=EXPECTED_PORT,
        database=EXPECTED_DATABASE,
    ).render_as_string(hide_password=False)
    metadata = (
        f"GATE=GATE_B\nRUN_ID={run_id}\nCWD=backend\nCOMMAND={command}\n"
        f"TIMEOUT_SECONDS={GATE_B_TIMEOUT_SECONDS}\nDATABASE_VALUE=CHILD_ENV_ONLY;REDACTED\n"
        "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n"
    )
    _write_reserved(files["runner-metadata.txt"], metadata.encode("utf-8"))
    process: subprocess.Popen[bytes] | None = None
    child_env: dict[str, str] = {}
    try:
        child_env = _pytest_child_environment(
            database_url, run_id, run_dir / "pytest-tmp"
        )
        process = subprocess.Popen(
            [
                str(BACKEND / ".venv" / "Scripts" / "python.exe"),
                "-m",
                "pytest",
                TEST_REL.as_posix(),
                "-p",
                "no:cacheprovider",
                basetemp_argument,
            ],
            cwd=BACKEND,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        try:
            stdout_bytes, stderr_bytes = process.communicate(
                timeout=GATE_B_TIMEOUT_SECONDS
            )
            if process.poll() is None:
                raise SafeStop("PYTEST_ROOT_EXIT_UNCONFIRMED")
            exit_code = process.returncode
            if exit_code is None:
                raise SafeStop("PYTEST_ROOT_EXIT_UNCONFIRMED")
            _store_pytest_output(files, stdout_bytes, stderr_bytes)
        except subprocess.TimeoutExpired:
            _terminate_process(process)
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
            _store_pytest_output(files, stdout_bytes, stderr_bytes)
            _write_reserved(files["pytest.exit.txt"], b"TIMEOUT\n")
            raise SafeStop("PYTEST_TIMEOUT") from None
        except KeyboardInterrupt:
            _terminate_process(process)
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
            _store_pytest_output(files, stdout_bytes, stderr_bytes)
            _write_reserved(files["pytest.exit.txt"], b"INTERRUPTED\n")
            raise SafeStop("PYTEST_INTERRUPTED") from None
    except SafeStop:
        raise
    except OSError:
        _write_reserved(files["pytest.exit.txt"], b"NOT_STARTED\n")
        raise SafeStop("PYTEST_LAUNCH_FAILED") from None
    finally:
        child_env.clear()
    _write_reserved(files["pytest.exit.txt"], f"{exit_code}\n".encode("ascii"))
    return exit_code


def _finalize_stop(
    files: dict[str, Path], stop_code: str, safety_status: str
) -> str:
    if stop_code == "GATE_B_LOG_WRITE_FAILED":
        safety_status = "FAILED_OUTPUT_WRITE"
    if not files:
        return safety_status
    if safety_status == "NOT_RUN" and stop_code != "GATE_B_LOG_WRITE_FAILED":
        if stop_code == "OUTPUT_SAFETY_FINDING":
            safety_status = "FINDING"
        elif stop_code in {
            "PROCESS_TERMINATION_UNCONFIRMED",
            "PYTEST_ROOT_EXIT_UNCONFIRMED",
        }:
            safety_status = "NOT_COMPLETE_PROCESS_TERMINATION_UNCONFIRMED"
        else:
            try:
                _scan_safety(files)
                safety_status = "PASS"
            except SafeStop as scan_stop:
                safety_status = (
                    "FINDING"
                    if scan_stop.code == "OUTPUT_SAFETY_FINDING"
                    else f"FAILED_{scan_stop.code}"
                )
    status_to_write = safety_status
    safety_status = (
        status_to_write if status_to_write != "PASS" else "STATUS_WRITE_INCOMPLETE"
    )
    status_path = files["runner-status.txt"]
    try:
        _write_json(
            status_path,
            {
                "GATE_B": "STOPPED",
                "CODE": stop_code,
                "SAFETY_SCAN": safety_status,
                "PROCESS_TREE_CHILD_ENUMERATION": "NOT_VERIFIED",
            },
        )
        if status_to_write == "PASS":
            _write_json(
                status_path,
                {
                    "GATE_B": "STOPPED",
                    "CODE": stop_code,
                    "SAFETY_SCAN": status_to_write,
                    "PROCESS_TREE_CHILD_ENUMERATION": "NOT_VERIFIED",
                },
            )
    except (SafeStop, OSError):
        safety_status = "FAILED_OUTPUT_WRITE"
        try:
            _write_json(
                status_path,
                {
                    "GATE_B": "STOPPED",
                    "CODE": stop_code,
                    "SAFETY_SCAN": safety_status,
                    "PROCESS_TREE_CHILD_ENUMERATION": "NOT_VERIFIED",
                },
            )
        except (SafeStop, OSError):
            pass
        print(
            "GATE_B_LOG_WRITE_FAILED: runner-status.txt could not be written; "
            "SAFETY_SCAN=FAILED_OUTPUT_WRITE",
            file=sys.stderr,
        )
    else:
        safety_status = status_to_write
    return safety_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-gate-b", action="store_true")
    args = parser.parse_args()
    if not args.run_gate_b:
        print("NOT LAUNCHED: Gate B requires its separately reviewed approval addendum.")
        return 2

    run_id = ""
    run_dir: Path | None = None
    files: dict[str, Path] = {}
    password = ""
    safety_status = "NOT_RUN"
    try:
        _require_clean_database_environment()
        baseline, approved_head = _verify_approval()
        _verify_repository()
        if _git("rev-parse", "HEAD").strip().lower() != approved_head.lower():
            raise SafeStop("HEAD_MISMATCH")
        run_id, run_dir, files = _reserve_outputs()
        _write_json(
            files["runner-status.txt"],
            {"GATE_B": "PREPARING", "PROCESS_TREE_CHILD_ENUMERATION": "NOT_VERIFIED"},
        )
        password = getpass.getpass(
            "PostgreSQL password (hidden; target sketch2life_m2_s1a only): "
        )
        if not password:
            raise SafeStop("EMPTY_PASSWORD")
        source_run_id = str(baseline["source_marker_run_id"])
        pre = _inventory(password, run_id, source_run_id)
        _write_json(files["pre-inventory.json"], pre)
        _check_gate_a_baseline(pre, baseline)
        pytest_exit = _run_pytest(run_id, run_dir, files, password)
        official_summary = _pytest_summary(files["pytest.stdout.txt"])
        _scan_safety(files)
        safety_status = "PASS"
        post = _inventory(password, run_id, source_run_id)
        # A post-inventory mismatch must not leave the earlier scan marked as
        # covering artifacts that were written after that scan.
        safety_status = "NOT_RUN"
        _write_json(files["post-inventory.json"], post)
        _check_gate_b_post_inventory(post, pre, run_id)
        safety = _scan_safety(files)
        safety_status = "PASS"
        if pytest_exit != 0:
            raise SafeStop("PYTEST_EXIT_NONZERO")
        if not official_summary:
            raise SafeStop("PYTEST_OFFICIAL_SUMMARY_MISSING")
        _write_json(
            files["runner-status.txt"],
            {
                "GATE_B": "PASS",
                "PRE_INVENTORY": "MATCHED_ACCEPTED_GATE_A_POST_INVENTORY",
                "PYTEST": "EXIT_0; OFFICIAL_SUMMARY=1_PASSED",
                "POST_INVENTORY": "PASS",
                "SAFETY_MATCHES": safety["unverified_or_uri_matches"],
                "PROCESS_TREE_CHILD_ENUMERATION": "NOT_VERIFIED",
            },
        )
        print(f"RUN_ID={run_id}")
        print(f"LOG_DIR={(GATE_B_LOG_ROOT / run_dir.name).as_posix()}")
        print(f"POST_INVENTORY_SHA256={_sha256_file(files['post-inventory.json'])}")
        print("PYTEST_SUMMARY=1 passed")
        return 0
    except SafeStop as stop:
        _finalize_stop(files, stop.code, safety_status)
        print(f"STOPPED_SAFELY: {stop.code}")
        if run_id and files and run_dir is not None:
            print(f"RUN_ID={run_id}")
            print(f"LOG_DIR={run_dir.relative_to(ROOT).as_posix()}")
        return 2
    except KeyboardInterrupt:
        stop_code = "OWNER_INTERRUPTED"
        _finalize_stop(files, stop_code, safety_status)
        print(f"STOPPED_SAFELY: {stop_code}")
        if run_id and files and run_dir is not None:
            print(f"RUN_ID={run_id}")
            print(f"LOG_DIR={run_dir.relative_to(ROOT).as_posix()}")
        return 130
    finally:
        password = ""


if __name__ == "__main__":
    raise SystemExit(main())
