"""Owner-only Gate A: preview and apply the isolated Parent revision once."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import ipaddress
import json
import os
import re
import subprocess
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
    "M2_S1A_P_GATE_A_LAUNCH_INSTRUCTION_DRAFT1_20261109.md"
)
APPROVAL_REL = Path("features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md")
DECISIONS_REL = Path("features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md")
PROGRESS_REL = Path("features/FEAT-063-system-architecture-rearchitecture/plan/M2_PROGRESS_REPORT_FOR_CODEX_20261109.md")
BASELINE_REL = Path(
    ".claude/handoff/logs/M2_S1A_T_20261107/"
    "f7fe88273c7f4dd89b3913efeac6f8fb/inventory.post.json"
)
LOG_ROOT_REL = Path(".claude/handoff/logs/M2_S1A_P_20261109")
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
EXPECTED_BRANCH = "feature/feat063-m2-parent-teacher-foundation"
EXPECTED_HEAD = "4b7f07cc283721f01f64e41ff2d81f135f63ad29"
EXPECTED_DATABASE = "sketch2life_m2_s1a"
EXPECTED_HOST = "127.0.0.1"
EXPECTED_PORT = 5433
EXPECTED_USER = "postgres"
EXPECTED_PG_MAJOR = 17
PARENT_REVISION = "20261109_m2_parent_profiles"
BASELINE_SHA256 = "710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E"
GATE_A_TIMEOUT_SECONDS = 1800
PREVIEW_TIMEOUT_SECONDS = 600
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
PARENT_TABLES = (
    "parent.child_profiles",
    "parent.profile_revisions",
    "parent.command_receipts",
)
FILE_NAMES = (
    "preview.sql",
    "preview.stderr.txt",
    "preview.exit.txt",
    "preview-command.txt",
    "preview-safety-scan.json",
    "pre-inventory.json",
    "upgrade.stdout.txt",
    "upgrade.stderr.txt",
    "upgrade.exit.txt",
    "post-inventory.json",
    "runner-status.txt",
    "runner-metadata.txt",
    "final-safety-scan.json",
)


class SafeStop(Exception):
    """A fixed safe-stop code that contains no credential or database URL."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, check=False,
    )
    if result.returncode != 0:
        raise SafeStop("GIT_PREFLIGHT_FAILED")
    return result.stdout.strip()


def _git_bytes(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SafeStop("GIT_PREFLIGHT_FAILED")
    return result.stdout


def _approval_section(text: str, prefix: str) -> str:
    lines = text.splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.startswith("## ") and line[3:].startswith(prefix)
    ]
    if not starts:
        return ""
    start = starts[-1]
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _approval_field(section: str, label: str) -> str:
    matches = re.findall(
        rf"^- \*\*{re.escape(label)}:\*\* `([^`]+)`$",
        section,
        re.MULTILINE,
    )
    if len(matches) != 1:
        raise SafeStop("APPROVAL_FIELD_INVALID")
    return matches[0]


def _approval_status(section: str) -> str:
    matches = re.findall(r"^- \*\*Status:\*\* (.+)$", section, re.MULTILINE)
    if len(matches) != 1:
        raise SafeStop("APPROVAL_FIELD_INVALID")
    value = matches[0].strip()
    if value.startswith("`"):
        if not value.endswith("`"):
            raise SafeStop("APPROVAL_FIELD_INVALID")
        value = value[1:-1]
    else:
        value = value.split(". ", maxsplit=1)[0].rstrip(".")
    return value


def _approval_table_rows(section: str, marker: str) -> list[list[str]]:
    lines = section.splitlines()
    try:
        marker_index = next(index for index, line in enumerate(lines) if marker in line)
    except StopIteration:
        raise SafeStop("REMEDIATION_MANIFEST_MISSING") from None
    rows: list[list[str]] = []
    for line in lines[marker_index + 1 :]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if cells and cells[0].lower() == "path":
            continue
        rows.append(cells)
    return rows


def _approval_artifact_pins(section: str) -> dict[str, tuple[str, str]]:
    marker = "### Required artifact pin table"
    if section.count(marker) != 1:
        raise SafeStop("GATE_A_ARTIFACT_PIN_TABLE_INVALID")
    rows = _approval_table_rows(section, marker)
    result: dict[str, tuple[str, str]] = {}
    header_count = 0
    for cells in rows:
        if cells == ["Artifact", "Repository-relative path", "SHA-256"]:
            header_count += 1
            continue
        if len(cells) != 3:
            raise SafeStop("GATE_A_ARTIFACT_PIN_TABLE_INVALID")
        name, relative, digest = cells
        relative = relative.replace("\\", "/")
        if (
            name in result
            or not re.fullmatch(r"[A-F0-9]{64}", digest.upper())
        ):
            raise SafeStop("GATE_A_ARTIFACT_PIN_TABLE_INVALID")
        result[name] = (relative, digest.upper())
    if not result or header_count != 1:
        raise SafeStop("GATE_A_ARTIFACT_PIN_TABLE_INVALID")
    return result


def _verify_gate_a_approval_entry(
    section: str,
    expected_pins: dict[str, tuple[str, str]],
) -> None:
    expected_fields = {
        "Status": "APPROVED / NOT LAUNCHED",
        "Approved branch": EXPECTED_BRANCH,
        "Approved HEAD": EXPECTED_HEAD,
        "OWNER_MODAL_CALL_APPROVED": "NO",
    }
    try:
        actual_fields = {
            label: _approval_field(section, label) for label in expected_fields
        }
    except SafeStop:
        raise SafeStop("GATE_A_ADDENDUM_MISSING_OR_STALE") from None
    if actual_fields != expected_fields:
        raise SafeStop("GATE_A_ADDENDUM_MISSING_OR_STALE")
    if _approval_artifact_pins(section) != expected_pins:
        raise SafeStop("GATE_A_ADDENDUM_MISSING_OR_STALE")


def _approved_remediation_section(approval_text: str) -> str:
    section = _approval_section(
        approval_text, "M2 S1a-P Remediation Addendum —"
    )
    if (
        "**Status:** APPROVED / NOT LAUNCHED" not in section
        or "**Owner decision record:** D-184" not in section
    ):
        raise SafeStop("REMEDIATION_ADDENDUM_MISSING_OR_STALE")
    return section


def _approved_append_only_supersessions(
    approval_text: str,
) -> dict[str, tuple[str, str]]:
    section = _approved_remediation_section(approval_text)
    rows = _approval_table_rows(section, "**Pinned append-only supersessions:**")
    result: dict[str, tuple[str, str]] = {}
    for cells in rows:
        if len(cells) != 3:
            raise SafeStop("REMEDIATION_PIN_TABLE_INVALID")
        relative, prefix_hash, current_hash = cells
        relative = relative.replace("\\", "/")
        if (
            relative in result
            or relative not in {DECISIONS_REL.as_posix(), PROGRESS_REL.as_posix()}
            or not re.fullmatch(r"[A-F0-9]{64}", prefix_hash.upper())
            or not re.fullmatch(r"[A-F0-9]{64}", current_hash.upper())
        ):
            raise SafeStop("REMEDIATION_PIN_TABLE_INVALID")
        result[relative] = (prefix_hash.upper(), current_hash.upper())
    if set(result) != {DECISIONS_REL.as_posix(), PROGRESS_REL.as_posix()}:
        raise SafeStop("REMEDIATION_PIN_TABLE_INVALID")
    return result


def _approved_untracked_document_hashes(approval_text: str) -> dict[str, str]:
    section = _approval_section(approval_text, "M2 S1a-P Gate A Approval")
    if _approval_field(section, "Status") != "APPROVED / NOT LAUNCHED":
        raise SafeStop("GATE_A_ADDENDUM_MISSING_OR_STALE")
    rows = _approval_table_rows(
        section, "**Exact current untracked Markdown manifest:**"
    )
    result: dict[str, str] = {}
    allowed_roots = (
        "features/FEAT-063-system-architecture-rearchitecture/evidence/",
        "features/FEAT-063-system-architecture-rearchitecture/plan/",
    )
    for cells in rows:
        if len(cells) != 2:
            raise SafeStop("UNTRACKED_DOCUMENT_MANIFEST_INVALID")
        relative, expected = cells
        relative = relative.replace("\\", "/")
        relative_parts = relative.split("/")
        if (
            relative in result
            or not relative.endswith(".md")
            or not relative.startswith(allowed_roots)
            or any(part in {"", ".", ".."} for part in relative_parts)
            or not re.fullmatch(r"[A-F0-9]{64}", expected.upper())
        ):
            raise SafeStop("UNTRACKED_DOCUMENT_MANIFEST_INVALID")
        path = (ROOT / Path(*relative_parts)).resolve()
        allowed_paths = tuple(
            (ROOT / root.rstrip("/")).resolve() for root in allowed_roots
        )
        if (
            ROOT.resolve() not in path.parents
            or not any(root in path.parents for root in allowed_paths)
            or not path.is_file()
        ):
            raise SafeStop("UNTRACKED_DOCUMENT_MANIFEST_INVALID")
        result[relative] = expected.upper()
    if not result:
        raise SafeStop("UNTRACKED_DOCUMENT_MANIFEST_INVALID")
    for relative, expected in result.items():
        path = (ROOT / Path(*relative.split("/"))).resolve()
        if sha256_file(path) != expected:
            raise SafeStop("UNTRACKED_DOCUMENT_HASH_MISMATCH")
    return result


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
    spec_text: str, gate_a_section: str, launch_text: str
) -> None:
    marker = "**Mode E/R/E/N backend source SHA-256:**"
    approval_hashes = _source_hashes(gate_a_section, marker)
    launch_hashes = _source_hashes(launch_text, marker)
    expected_paths = _mode_backend_paths(spec_text)
    if (
        set(approval_hashes) != expected_paths
        or set(launch_hashes) != expected_paths
        or approval_hashes != launch_hashes
    ):
        raise SafeStop("SOURCE_HASH_MANIFEST_MISMATCH")
    for relative, expected in approval_hashes.items():
        path = (ROOT / Path(relative)).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SafeStop("PINNED_SOURCE_FILE_MISSING")
        if sha256_file(path) != expected:
            raise SafeStop("PINNED_SOURCE_HASH_MISMATCH")


def _has_line_boundary_prefix(data: bytes, expected_hash: str) -> bool:
    digest = hashlib.sha256()
    for byte in data:
        digest.update(bytes((byte,)))
        if byte == 10 and digest.hexdigest().upper() == expected_hash:
            return True
    return False


def _verify_pinned_read_only_inputs(spec_text: str, approval_text: str) -> None:
    found = 0
    supersessions = _approved_append_only_supersessions(approval_text)
    for relative, (prefix_hash, current_hash) in supersessions.items():
        path = ROOT / Path(relative)
        if not path.is_file():
            raise SafeStop("PINNED_APPEND_ONLY_INPUT_MISMATCH")
        data = path.read_bytes()
        if (
            sha256_file(path) != current_hash
            or not _has_line_boundary_prefix(data, prefix_hash)
        ):
            raise SafeStop("PINNED_APPEND_ONLY_INPUT_MISMATCH")
    for line in spec_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0] not in {"R", "H"}:
            continue
        relative = cells[1].strip("`").replace("\\", "/")
        expected = cells[2].strip("`").upper()
        path = (ROOT / Path(relative)).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SafeStop("PINNED_INPUT_MISSING")
        if not re.fullmatch(r"[A-F0-9]{64}", expected):
            raise SafeStop("PINNED_INPUT_HASH_MISMATCH")
        current_hash = sha256_file(path)
        if current_hash != expected:
            if relative in supersessions:
                prefix_hash, approved_hash = supersessions[relative]
                if (
                    expected != prefix_hash
                    or current_hash != approved_hash
                    or not _has_line_boundary_prefix(path.read_bytes(), expected)
                ):
                    raise SafeStop("PINNED_APPEND_ONLY_INPUT_MISMATCH")
            elif relative == "features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md":
                committed = _git_bytes("show", f"HEAD:{relative}")
                if hashlib.sha256(committed).hexdigest().upper() != expected or not path.read_bytes().startswith(committed):
                    raise SafeStop("PINNED_APPEND_ONLY_INPUT_MISMATCH")
            else:
                raise SafeStop("PINNED_INPUT_HASH_MISMATCH")
        found += 1
    if found == 0:
        raise SafeStop("PINNED_INPUT_TABLE_MISSING")


def _verify_allowlisted_changes(spec_text: str, approval_text: str) -> None:
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

    untracked_paths = {
        path.replace("\\", "/")
        for path in _git("ls-files", "--others", "--exclude-standard").splitlines()
    }
    approved_untracked_docs = _approved_untracked_document_hashes(approval_text)
    unexpected_untracked = untracked_paths - new_paths - set(approved_untracked_docs)
    if unexpected_untracked:
        raise SafeStop("UNTRACKED_PATH_OUTSIDE_APPROVED_ALLOWLIST")


def _verify_approval_pins() -> None:
    spec = ROOT / SPEC_REL
    launch = ROOT / LAUNCH_REL
    approval = ROOT / APPROVAL_REL
    decisions = ROOT / DECISIONS_REL
    if not all(path.is_file() for path in (spec, launch, approval, decisions, ROOT / BASELINE_REL)):
        raise SafeStop("APPROVAL_ARTIFACT_MISSING")
    spec_text = spec.read_text(encoding="utf-8")
    launch_text = launch.read_text(encoding="utf-8")
    approval_bytes = approval.read_bytes()
    try:
        approval_text = approval_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise SafeStop("APPROVAL_UNREADABLE") from None
    spec_hash = sha256_file(spec)
    launch_hash = sha256_file(launch)
    script_hash = sha256_file(Path(__file__).resolve())
    decisions_hash = sha256_file(decisions)
    baseline_hash = sha256_file(ROOT / BASELINE_REL)
    initial = _approval_section(approval_text, "M2 S1a-P Approval —")
    gate_a = _approval_section(approval_text, "M2 S1a-P Gate A Approval")
    try:
        initial_status = _approval_status(initial)
    except SafeStop:
        raise SafeStop("S1AP_APPROVAL_MISSING_OR_STALE") from None
    if initial_status != "APPROVED / NOT LAUNCHED" or spec_hash not in initial:
        raise SafeStop("S1AP_APPROVAL_MISSING_OR_STALE")
    if not gate_a:
        raise SafeStop("GATE_A_ADDENDUM_MISSING_OR_STALE")
    expected_gate_pins = {
        "S1a-P specification": (SPEC_REL.as_posix(), spec_hash),
        "Gate A launch instruction": (LAUNCH_REL.as_posix(), launch_hash),
        "Gate A runner": (
            Path(__file__).resolve().relative_to(ROOT.resolve()).as_posix(),
            script_hash,
        ),
        "DECISIONS.md": (DECISIONS_REL.as_posix(), decisions_hash),
        "S1a-T pre-migration inventory": (BASELINE_REL.as_posix(), baseline_hash),
    }
    _verify_gate_a_approval_entry(gate_a, expected_gate_pins)
    gate_a_heading = next(
        line
        for line in approval_text.splitlines()
        if line.startswith("## ") and line[3:].startswith("M2 S1a-P Gate A Approval")
    )
    heading_offset = approval_bytes.find(gate_a_heading.encode("utf-8"))
    if (
        heading_offset < 0
        or hashlib.sha256(approval_bytes[:heading_offset]).hexdigest().upper()
        != _approval_field(gate_a, "Approval prefix SHA-256").upper()
    ):
        raise SafeStop("APPROVAL_PREFIX_MISMATCH")
    if "DO NOT LAUNCH" not in launch_text or "OWNER_MODAL_CALL_APPROVED=NO" not in launch_text:
        raise SafeStop("GATE_A_LAUNCH_GUARD_MISSING")
    if spec_hash not in launch_text or script_hash not in launch_text:
        raise SafeStop("GATE_A_LAUNCH_PIN_MISMATCH")
    _verify_mode_backend_source_hashes(spec_text, gate_a, launch_text)
    _verify_pinned_read_only_inputs(spec_text, approval_text)
    _verify_allowlisted_changes(spec_text, approval_text)


def _verify_repo_and_environment() -> None:
    if _git("branch", "--show-current") != EXPECTED_BRANCH:
        raise SafeStop("BRANCH_MISMATCH")
    if _git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise SafeStop("HEAD_MISMATCH")
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode != 0:
        raise SafeStop("INDEX_NOT_EMPTY")
    if any(os.environ.get(name) for name in PARENT_DB_ENV):
        raise SafeStop("DATABASE_ENVIRONMENT_NOT_CLEAN")
    if not PYTHON.is_file():
        raise SafeStop("APPROVED_PYTHON_MISSING")


def _reserve_outputs() -> tuple[str, Path, dict[str, Path]]:
    base = ROOT / LOG_ROOT_REL
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", (LOG_ROOT_REL / "probe").as_posix()],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if ignored.returncode != 0:
        raise SafeStop("LOG_ROOT_NOT_IGNORED")
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}_gate_a_{uuid.uuid4().hex[:12]}"
    run_dir = base / run_id
    run_dir.mkdir(exist_ok=False)
    files = {name: run_dir / name for name in FILE_NAMES}
    for path in files.values():
        with path.open("xb"):
            pass
    (run_dir / "pytest-temp").mkdir(exist_ok=False)
    return run_id, run_dir, files


def _write_reserved(path: Path, data: bytes) -> None:
    if not path.is_file() or path.stat().st_size != 0:
        raise SafeStop("OUTPUT_FILE_NOT_EMPTY")
    with path.open("r+b") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _write_text(path: Path, value: str) -> None:
    _write_reserved(path, value.encode("utf-8"))


def _safe_preview_environment() -> dict[str, str]:
    child = {
        name: value for name, value in os.environ.items()
        if not name.startswith("SKETCH2LIFE_") and not name.startswith("PG")
        and name not in PARENT_DB_ENV
    }
    placeholder = URL.create(
        "postgresql+psycopg", username=EXPECTED_USER,
        host=EXPECTED_HOST, port=EXPECTED_PORT, database=EXPECTED_DATABASE,
    ).render_as_string(hide_password=False)
    child["S1A_P_ALEMBIC_DATABASE_URL"] = placeholder
    return child


def _run_preview(files: dict[str, Path]) -> None:
    command = [
        str(PYTHON), "-m", "alembic", "-c", "backend/alembic.ini",
        "upgrade", "parent@head", "--sql",
    ]
    _write_text(
        files["preview-command.txt"],
        "GATE=GATE_A\nCWD=.\nPREVIEW=ONE_OFFLINE_SQL_PREVIEW\n"
        "COMMAND=backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini "
        "upgrade parent@head --sql\nDATABASE_VALUE=CHILD_ENV_ONLY;REDACTED\n",
    )
    try:
        with files["preview.sql"].open("r+b") as stdout, files["preview.stderr.txt"].open("r+b") as stderr:
            result = subprocess.run(
                command, cwd=ROOT, env=_safe_preview_environment(), stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, check=False, timeout=PREVIEW_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired:
        _write_text(files["preview.exit.txt"], "TIMEOUT\n")
        raise SafeStop("OFFLINE_PREVIEW_TIMEOUT") from None
    except OSError:
        _write_text(files["preview.exit.txt"], "NOT_STARTED\n")
        raise SafeStop("OFFLINE_PREVIEW_NOT_STARTED") from None
    _write_text(files["preview.exit.txt"], f"{result.returncode}\n")
    if result.returncode != 0 or files["preview.sql"].stat().st_size == 0:
        raise SafeStop("OFFLINE_PREVIEW_FAILED")
    preview = files["preview.sql"].read_text(encoding="utf-8", errors="replace")
    required = (
        "CREATE SCHEMA parent",
        "child_profiles",
        "profile_revisions",
        "command_receipts",
        "fk_parent_child_profiles_current_revision",
        "trg_parent_profile_revisions_immutable",
        PARENT_REVISION,
    )
    if not all(item in preview for item in required):
        raise SafeStop("OFFLINE_PREVIEW_CONTENT_INCOMPLETE")
    _scan_safety(files, output_name="preview-safety-scan.json")


def _scan_safety(files: dict[str, Path], *, output_name: str) -> dict[str, int]:
    counts = {name: 0 for name in SENSITIVE_PATTERNS}
    counts["scheme_url"] = 0
    for path in files.values():
        if path.name.endswith("-safety-scan.json"):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            raise SafeStop("OUTPUT_SCAN_FAILED") from None
        counts["scheme_url"] += len(URI_RE.findall(content))
        for name, pattern in SENSITIVE_PATTERNS.items():
            counts[name] += len(pattern.findall(content))
    counts["unverified_or_uri_matches"] = counts["scheme_url"] + sum(
        counts[name] for name in SENSITIVE_PATTERNS
    )
    scan_path = files[output_name]
    _write_reserved(
        scan_path,
        (json.dumps(counts, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )
    if counts["unverified_or_uri_matches"]:
        raise SafeStop("OUTPUT_SAFETY_FINDING")
    return counts


def _accept_preview(files: dict[str, Path]) -> None:
    print("OFFLINE_SQL_PREVIEW_READY; review the full preview.sql locally before continuing.")
    print("The preview is evidence only. Do not apply it directly.")
    if input("Type APPLY_PARENT_ONLY_PREVIEW to continue to the owner password prompt: ") != "APPLY_PARENT_ONLY_PREVIEW":
        raise SafeStop("OFFLINE_PREVIEW_NOT_ACCEPTED")


def _connect_kwargs(password: str) -> dict[str, object]:
    return {
        "dbname": EXPECTED_DATABASE,
        "host": EXPECTED_HOST,
        "port": EXPECTED_PORT,
        "user": EXPECTED_USER,
        "password": password,
        "connect_timeout": 5,
        "options": "-c default_transaction_read_only=on",
        "autocommit": True,
    }


def _verify_identity(cursor: Any) -> dict[str, object]:
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
            database != EXPECTED_DATABASE or user != EXPECTED_USER
            or int(port) != EXPECTED_PORT or not ipaddress.ip_address(str(host_text)).is_loopback
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


def _marker_counts(cursor: Any, source_run_id: str) -> dict[str, int]:
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
    result: dict[str, int] = {}
    for qualified, column, marker, exact in specs:
        schema, table = qualified.split(".", 1)
        comparator = sql.SQL("{} = %s") if exact else sql.SQL("left({}::text, %s) = %s")
        predicate = comparator.format(sql.Identifier(column))
        params: tuple[object, ...] = (marker,) if exact else (len(marker), marker)
        cursor.execute(
            sql.SQL("SELECT count(*) FROM {}.{} WHERE ").format(
                sql.Identifier(schema), sql.Identifier(table)
            ) + predicate,
            params,
        )
        result[qualified] = int(cursor.fetchone()[0])
    cursor.execute(
        "SELECT count(*) FROM public.be1_enrollments e "
        "JOIN public.be1_managed_profiles p ON p.child_id = e.child_id "
        "WHERE left(p.display_name, %s) = %s",
        (len(f"Synthetic S1AT {source_run_id} "), f"Synthetic S1AT {source_run_id} "),
    )
    result["public.be1_enrollments"] = int(cursor.fetchone()[0])
    return dict(sorted(result.items()))


def _inventory(password: str, gate_run_id: str, marker_run_id: str) -> dict[str, Any]:
    try:
        import psycopg
    except ImportError:
        raise SafeStop("PSYCOPG_UNAVAILABLE") from None
    connection = None
    try:
        connection = psycopg.connect(**_connect_kwargs(password))
        with connection.cursor() as cursor:
            cursor.execute("BEGIN READ ONLY")
            identity = _verify_identity(cursor)
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata "
                "WHERE schema_name = 'parent')"
            )
            parent_schema_exists = bool(cursor.fetchone()[0])
            cursor.execute(
                "SELECT n.nspname, c.relname FROM pg_catalog.pg_class c "
                "JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace "
                "WHERE c.relkind IN ('r','p') "
                "AND n.nspname NOT IN ('pg_catalog','information_schema') "
                "AND n.nspname NOT LIKE 'pg_toast%' "
                "AND n.nspname NOT LIKE 'pg_temp_%' ORDER BY n.nspname,c.relname"
            )
            relations = [(str(schema), str(table)) for schema, table in cursor.fetchall()]
            from psycopg import sql
            counts: dict[str, int] = {}
            for schema, table in relations:
                cursor.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier(schema), sql.Identifier(table)
                    )
                )
                counts[f"{schema}.{table}"] = int(cursor.fetchone()[0])
            versions: list[str] = []
            if "public.alembic_version" in counts:
                cursor.execute("SELECT version_num FROM public.alembic_version ORDER BY version_num")
                versions = [str(row[0]) for row in cursor.fetchall()]
            markers = _marker_counts(cursor, marker_run_id)
            read_only = True
        connection.rollback()
    except SafeStop:
        raise
    except Exception:  # noqa: BLE001 - fail closed without exposing driver errors.
        raise SafeStop("READ_ONLY_INVENTORY_FAILED") from None
    finally:
        if connection is not None:
            with suppress(Exception):
                connection.rollback()
            with suppress(Exception):
                connection.close()

    total_rows = sum(counts.values())
    marker_total = sum(markers.values())
    known_control = {"public.alembic_version": 1} if versions == [PARENT_REVISION] else {}
    unmatched = {
        table: count - markers.get(table, 0) - known_control.get(table, 0)
        for table, count in counts.items()
        if count != markers.get(table, 0) + known_control.get(table, 0)
    }
    status = "MARKER_COUNTS_MATCH" if not unmatched and total_rows == marker_total + sum(known_control.values()) else "UNKNOWN_ROWS_FOUND"
    return {
        "run_id": gate_run_id,
        "source_marker_run_id": marker_run_id,
        "read_only": read_only,
        "identity": identity,
        "parent_schema_exists": parent_schema_exists,
        "table_rows": dict(sorted(counts.items())),
        "total_rows": total_rows,
        "marker_rows": markers,
        "marker_total": marker_total,
        "known_control_rows": known_control,
        "unmatched_tables": dict(sorted(unmatched.items())),
        "alembic_versions": versions,
        "status": status,
    }


def _write_json(path: Path, value: object) -> None:
    _write_reserved(path, (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _baseline_projection(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value[key] for key in (
        "read_only", "table_rows", "marker_rows", "marker_total", "total_rows", "unmatched_tables"
    )}


def _load_t_baseline() -> dict[str, Any]:
    path = ROOT / BASELINE_REL
    if sha256_file(path) != BASELINE_SHA256:
        raise SafeStop("S1AT_INVENTORY_PIN_MISMATCH")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise SafeStop("S1AT_INVENTORY_INVALID") from None
    if (
        value.get("read_only") is not True or value.get("status") != "MARKER_COUNTS_MATCH"
        or len(value.get("table_rows", {})) != 117 or value.get("total_rows") != 29
        or value.get("marker_total") != 29 or value.get("unmatched_tables") != {}
        or sum(value.get("marker_rows", {}).values()) != 29
    ):
        raise SafeStop("S1AT_INVENTORY_CONTENT_MISMATCH")
    return value


def _preflight_checks(pre: dict[str, Any], baseline: dict[str, Any]) -> None:
    if _baseline_projection(pre) != _baseline_projection(baseline):
        raise SafeStop("PRE_MIGRATION_INVENTORY_MISMATCH")
    if pre.get("status") != "MARKER_COUNTS_MATCH":
        raise SafeStop("PRE_MIGRATION_MARKERS_NOT_CONFIRMED")
    counts = pre["table_rows"]
    if (
        len(counts) != 117 or sum(counts.values()) != 29
        or counts.get("public.alembic_version") != 0
        or any(table in counts for table in PARENT_TABLES)
        or pre.get("parent_schema_exists") is not False
        or "parent" in {name.split(".", 1)[0] for name in counts}
    ):
        raise SafeStop("PRE_MIGRATION_STATE_UNEXPECTED")


def _run_upgrade(run_dir: Path, files: dict[str, Path], password: str) -> None:
    database_url = URL.create(
        "postgresql+psycopg", username=EXPECTED_USER, password=password,
        host=EXPECTED_HOST, port=EXPECTED_PORT, database=EXPECTED_DATABASE,
    ).render_as_string(hide_password=False)
    child_env = {
        name: value for name, value in os.environ.items()
        if not name.startswith("SKETCH2LIFE_") and not name.startswith("PG")
        and name not in PARENT_DB_ENV
    }
    child_env["S1A_P_ALEMBIC_DATABASE_URL"] = database_url
    command = ".venv\\Scripts\\python.exe -m alembic -c alembic.ini upgrade parent@head"
    _write_reserved(
        files["runner-metadata.txt"],
        (
            f"GATE=GATE_A\nRUN_ID={run_dir.name}\nCWD=backend\nCOMMAND={command}\n"
            f"TIMEOUT_SECONDS={GATE_A_TIMEOUT_SECONDS}\nDATABASE_VALUE=CHILD_ENV_ONLY;REDACTED\n"
        ).encode(),
    )
    stdout = files["upgrade.stdout.txt"].open("r+b")
    stderr = files["upgrade.stderr.txt"].open("r+b")
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            ["cmd.exe", "/d", "/c", command], cwd=BACKEND, env=child_env,
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        try:
            exit_code = process.wait(timeout=GATE_A_TIMEOUT_SECONDS)
            if process.poll() is None:
                raise SafeStop("ALEMBIC_ROOT_EXIT_UNCONFIRMED")
        except subprocess.TimeoutExpired:
            _terminate_process(process)
            raise SafeStop("ALEMBIC_TIMEOUT") from None
        except KeyboardInterrupt:
            _terminate_process(process)
            raise SafeStop("ALEMBIC_INTERRUPTED") from None
    except SafeStop:
        raise
    except OSError:
        raise SafeStop("ALEMBIC_LAUNCH_FAILED") from None
    finally:
        stdout.close()
        stderr.close()
    _write_text(files["upgrade.exit.txt"], f"{exit_code}\n")
    if exit_code != 0:
        raise SafeStop("ALEMBIC_EXIT_NONZERO")


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")
    try:
        result = subprocess.run(
            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=20,
        )
    except KeyboardInterrupt:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    except (OSError, subprocess.TimeoutExpired):
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    if result.returncode != 0:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")
    try:
        process.wait(timeout=20)
    except KeyboardInterrupt:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    except subprocess.TimeoutExpired:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED") from None
    if process.poll() is None:
        raise SafeStop("PROCESS_TERMINATION_UNCONFIRMED")


def _postflight_checks(post: dict[str, Any], pre: dict[str, Any]) -> None:
    before = pre["table_rows"]
    expected = dict(before)
    expected["public.alembic_version"] = 1
    expected.update({table: 0 for table in PARENT_TABLES})
    if (
        post["table_rows"] != dict(sorted(expected.items()))
        or len(post["table_rows"]) != 120 or post["total_rows"] != 30
        or post["alembic_versions"] != [PARENT_REVISION]
        or post["marker_rows"] != pre["marker_rows"]
        or post["marker_total"] != 29
        or post["known_control_rows"] != {"public.alembic_version": 1}
        or post["unmatched_tables"] != {}
        or post["status"] != "MARKER_COUNTS_MATCH"
    ):
        raise SafeStop("POST_MIGRATION_INVENTORY_MISMATCH")


def _finalize_stop(
    files: dict[str, Path], stop_code: str, safety_status: str
) -> str:
    if not files:
        return safety_status
    if safety_status == "NOT_RUN":
        if stop_code in {
            "PROCESS_TERMINATION_UNCONFIRMED",
            "ALEMBIC_ROOT_EXIT_UNCONFIRMED",
        }:
            safety_status = "NOT_COMPLETE_PROCESS_TERMINATION_UNCONFIRMED"
        else:
            try:
                _scan_safety(files, output_name="final-safety-scan.json")
                safety_status = "PASS"
            except SafeStop as scan_stop:
                safety_status = (
                    "FINDING"
                    if scan_stop.code == "OUTPUT_SAFETY_FINDING"
                    else f"FAILED_{scan_stop.code}"
                )
    try:
        _write_reserved(
            files["runner-status.txt"],
            (
                f"GATE_A=STOPPED; CODE={stop_code}\n"
                "PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n"
                f"SAFETY_SCAN={safety_status}\n"
            ).encode("ascii"),
        )
    except (SafeStop, OSError):
        pass
    return safety_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-gate-a", action="store_true")
    args = parser.parse_args()
    if not args.run_gate_a:
        print("NOT LAUNCHED: pass --run-gate-a only after the separate reviewed Gate A addendum.")
        return 2

    run_id = ""
    files: dict[str, Path] = {}
    password = ""
    safety_status = "NOT_RUN"
    try:
        _verify_repo_and_environment()
        _verify_approval_pins()
        baseline = _load_t_baseline()
        run_id, run_dir, files = _reserve_outputs()
        _run_preview(files)
        _accept_preview(files)

        password = getpass.getpass(
            "PostgreSQL password (hidden; target sketch2life_m2_s1a only): "
        )
        if not password:
            raise SafeStop("EMPTY_PASSWORD")
        source_run_id = str(baseline["run_id"])
        pre = _inventory(password, run_id, source_run_id)
        _write_json(files["pre-inventory.json"], pre)
        _preflight_checks(pre, baseline)
        _run_upgrade(run_dir, files, password)
        post = _inventory(password, run_id, source_run_id)
        _write_json(files["post-inventory.json"], post)
        try:
            safety = _scan_safety(files, output_name="final-safety-scan.json")
            safety_status = "PASS"
        except SafeStop as scan_stop:
            safety_status = (
                "FINDING"
                if scan_stop.code == "OUTPUT_SAFETY_FINDING"
                else f"FAILED_{scan_stop.code}"
            )
            raise
        _postflight_checks(post, pre)
        _write_text(
            files["runner-status.txt"],
            "GATE_A=PASS\nPRE_INVENTORY=PASS\nALEMBIC=EXIT_0\n"
            "POST_INVENTORY=PASS\nPROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED\n",
        )
        print(f"RUN_ID={run_id}")
        print(f"LOG_DIR={(LOG_ROOT_REL / run_id).as_posix()}")
        print(f"POST_INVENTORY_SHA256={sha256_file(files['post-inventory.json'])}")
        print(f"SAFETY_MATCHES={safety['unverified_or_uri_matches']}")
        return 0
    except SafeStop as stop:
        _finalize_stop(files, stop.code, safety_status)
        print(f"STOPPED_SAFELY: {stop.code}")
        if run_id:
            print(f"RUN_ID={run_id}")
            print(f"LOG_DIR={(LOG_ROOT_REL / run_id).as_posix()}")
        return 2
    except KeyboardInterrupt:
        stop_code = "OWNER_INTERRUPTED"
        _finalize_stop(files, stop_code, safety_status)
        print(f"STOPPED_SAFELY: {stop_code}")
        if run_id:
            print(f"RUN_ID={run_id}")
            print(f"LOG_DIR={(LOG_ROOT_REL / run_id).as_posix()}")
        return 130
    finally:
        password = ""


if __name__ == "__main__":
    raise SystemExit(main())
