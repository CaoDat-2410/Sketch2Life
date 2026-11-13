"""Run one approved S1a-P offline command and capture immutable evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND = REPO_ROOT / "backend"
LOG_ROOT = REPO_ROOT / ".claude" / "handoff" / "logs" / "M2_S1A_P_20261109"
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"

BASELINE_TESTS = (
    "tests/unit/test_age_provenance_columns.py",
    "tests/unit/test_profile_age_invariant.py",
    "tests/unit/test_synthetic_eligibility.py",
    "tests/unit/test_be1_fact_reader.py",
    "tests/contract/test_be1_fact_reader_contract.py",
    "tests/contract/test_app_composition.py",
    "tests/contract/test_openapi_contract_catalog.py",
)

POST_TESTS = (
    "tests/unit/test_parent_profiles.py",
    "tests/unit/test_parent_profiles_service.py",
    "tests/unit/test_parent_profiles_migration.py",
    "tests/unit/test_age_provenance_columns.py",
    "tests/unit/test_profile_age_invariant.py",
    "tests/unit/test_synthetic_eligibility.py",
    "tests/unit/test_be1_fact_reader.py",
    "tests/contract/test_be1_fact_reader_contract.py",
    "tests/contract/test_parent_profiles_routes.py",
    "tests/contract/test_app_composition.py",
    "tests/contract/test_openapi_contract_catalog.py",
)

RUFF_CANDIDATES = (
    "backend/alembic/env.py",
    "backend/src/sketch2life/interfaces/http/app.py",
    "backend/src/sketch2life/interfaces/http/openapi_contract.py",
    "backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py",
    "backend/src/sketch2life/interfaces/http/openapi_srs_v22.py",
    "backend/src/sketch2life/interfaces/http/router_composition.py",
    "backend/src/sketch2life/domain/parent_profiles.py",
    "backend/src/sketch2life/application/ports/parent_profiles.py",
    "backend/src/sketch2life/application/services/parent_profiles.py",
    "backend/src/sketch2life/contracts/schemas/parent_profiles.py",
    "backend/src/sketch2life/infrastructure/persistence/parent_models.py",
    "backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py",
    "backend/src/sketch2life/interfaces/http/parent_runtime.py",
    "backend/src/sketch2life/interfaces/http/routers/parent_profiles.py",
    "backend/alembic/versions/20261109_m2_parent_profiles.py",
    "backend/tests/contract/test_app_composition.py",
    "backend/tests/contract/test_openapi_contract_catalog.py",
    "backend/tests/contract/test_parent_profiles_routes.py",
    "backend/tests/unit/test_synthetic_eligibility.py",
    "backend/tests/unit/test_parent_profiles.py",
    "backend/tests/unit/test_parent_profiles_service.py",
    "backend/tests/unit/test_parent_profiles_migration.py",
    "features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_gate_a_20261109.py",
    "features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_gate_b_20261109.py",
    "features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_offline_checks_20261109.py",
)

SENSITIVE_TEXT_PATTERNS = {
    "userinfo_at_host": re.compile(r"[^\s:/]+:[^\s@/]+@[^\s/]+"),
    "password_assignment": re.compile(r"(?i)\bpassword\s*="),
    "pgpassword": re.compile(r"(?i)\bPGPASSWORD\b"),
    "bearer_token": re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~-]{30,}"),
    "auth_key_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|"
        r"client[_-]?secret|secret(?:[_-]?key)?|credential|authorization)\s*[:=]\s*"
        r"[\"']?[A-Za-z0-9._~+/=-]{8,}"
    ),
}
URI_SCHEME_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
BENIGN_MYPY_DOC_PREFIX = "https://mypy.readthedocs.io/"


def _command_for(step: str, run_dir: Path) -> tuple[Path, list[str], Path]:
    cache_dir = run_dir / "mypy-cache"
    basetemp = run_dir / "pytest-temp"
    if step == "baseline-pytest":
        return PYTHON, ["-m", "pytest", *BASELINE_TESTS, "-p", "no:cacheprovider", f"--basetemp={basetemp}"], BACKEND
    if step == "baseline-mypy":
        return PYTHON, ["-m", "mypy", "--strict", "src/sketch2life", "tests", f"--cache-dir={cache_dir}"], BACKEND
    if step == "post-pytest":
        return PYTHON, ["-m", "pytest", *POST_TESTS, "-p", "no:cacheprovider", f"--basetemp={basetemp}"], BACKEND
    if step == "post-mypy":
        return PYTHON, ["-m", "mypy", "--strict", "src/sketch2life", "tests", f"--cache-dir={cache_dir}"], BACKEND
    if step == "ruff":
        targets = [str(REPO_ROOT / item) for item in RUFF_CANDIDATES if (REPO_ROOT / item).is_file()]
        return PYTHON, ["-m", "ruff", "check", "--no-cache", *targets], REPO_ROOT
    if step == "validate-harness":
        return Path(sys.executable), ["tools/validate_harness.py"], REPO_ROOT
    if step == "validate-security":
        return Path(sys.executable), ["tools/validate_repository_security.py"], REPO_ROOT
    if step == "validate-architecture":
        return Path(sys.executable), ["tools/validate_architecture.py"], REPO_ROOT
    if step == "validate-skeleton":
        return Path(sys.executable), ["tools/validate_skeleton.py"], REPO_ROOT
    if step == "diff-check":
        git = shutil.which("git.exe") or shutil.which("git")
        if git is None:
            raise RuntimeError("git executable is unavailable")
        return Path(git), ["diff", "--check"], REPO_ROOT
    raise ValueError(f"unapproved step: {step}")


def _new_run_dir(step: str) -> Path:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = LOG_ROOT / f"{stamp}_{step}_{uuid.uuid4().hex[:12]}"
    run_dir.mkdir(exist_ok=False)
    return run_dir


def _scan_log(path: Path) -> dict[str, int]:
    counts = {name: 0 for name in SENSITIVE_TEXT_PATTERNS}
    counts.update(
        {
            "scheme_url": 0,
            "benign_mypy_doc_uri": 0,
            "unsafe_scheme_url": 0,
        }
    )
    with path.open("rb") as stream:
        for raw_line in stream:
            line = raw_line.decode("utf-8", errors="replace")
            uri_tokens = URI_SCHEME_PATTERN.findall(line)
            counts["scheme_url"] += len(uri_tokens)
            for uri in uri_tokens:
                if uri.startswith(BENIGN_MYPY_DOC_PREFIX):
                    counts["benign_mypy_doc_uri"] += 1
                else:
                    counts["unsafe_scheme_url"] += 1
            for name, pattern in SENSITIVE_TEXT_PATTERNS.items():
                counts[name] += len(pattern.findall(line))
    return counts


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "step",
        choices=(
            "baseline-pytest",
            "baseline-mypy",
            "post-pytest",
            "post-mypy",
            "ruff",
            "validate-harness",
            "validate-security",
            "validate-architecture",
            "validate-skeleton",
            "diff-check",
        ),
    )
    args = parser.parse_args()

    if not PYTHON.is_file():
        raise RuntimeError("approved backend Python executable is missing")
    run_dir = _new_run_dir(args.step)
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    exit_path = run_dir / "exit-code.txt"
    command_path = run_dir / "command.txt"
    safety_path = run_dir / "safety-scan.json"
    executable, arguments, cwd = _command_for(args.step, run_dir)
    payload = subprocess.list2cmdline([str(executable), *arguments])
    # All approved executable and log paths are under this repository, which has no spaces.
    # Keep the /c payload unwrapped: cmd.exe treats escaped outer quotes as part of the command name.
    command_line = payload
    command_path.write_text(
        f"cmd.exe /d /c {command_line}\nCWD={cwd.relative_to(REPO_ROOT).as_posix()}\n",
        encoding="utf-8",
        newline="\n",
    )

    child_env = os.environ.copy()
    for name in (
        "BE1_TEST_DATABASE_URL",
        "S1A_P_TEST_DATABASE_URL",
        "S1A_P_ALEMBIC_DATABASE_URL",
        "SKETCH2LIFE_DATABASE_URL",
        "PGPASSWORD",
        "PGHOST",
        "PGPORT",
        "PGUSER",
        "PGSERVICE",
        "PGSERVICEFILE",
        "PGPASSFILE",
    ):
        child_env.pop(name, None)

    # Pass cmd.exe a raw /c command string so it does not wrap the complete command
    # in outer quotes, which Windows otherwise treats as part of the command name.
    exit_code: int | str
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            result = subprocess.run(
                f"cmd.exe /d /c {command_line}",
                cwd=cwd,
                env=child_env,
                stdout=stdout,
                stderr=stderr,
                check=False,
                shell=False,
            )
        exit_code = result.returncode
    except OSError:
        exit_code = "NOT_STARTED"
        if not stdout_path.exists():
            stdout_path.touch(exist_ok=False)
        if not stderr_path.exists():
            stderr_path.touch(exist_ok=False)
    exit_path.write_text(f"{exit_code}\n", encoding="ascii", newline="\n")

    scan = {
        "stdout": _scan_log(stdout_path),
        "stderr": _scan_log(stderr_path),
    }
    safety_path.write_text(
        json.dumps(scan, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    findings = sum(
        sum(
            count
            for name, count in values.items()
            if name not in {"scheme_url", "benign_mypy_doc_uri"}
        )
        for values in scan.values()
    )
    print(f"STEP={args.step}")
    print(f"RUN_DIR={run_dir.relative_to(REPO_ROOT).as_posix()}")
    print(f"EXIT={exit_code}")
    print(f"REDACTED_SAFETY_MATCHES={findings}")
    return 0 if findings == 0 and isinstance(exit_code, int) else 2


if __name__ == "__main__":
    raise SystemExit(_main())
