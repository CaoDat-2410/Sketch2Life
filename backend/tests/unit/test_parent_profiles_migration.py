"""Static checks for the isolated Parent Alembic branch; never execute DDL."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import Table

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20261109_m2_parent_profiles.py"
)
_GATE_A_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "features"
    / "FEAT-063-system-architecture-rearchitecture"
    / "evidence"
    / "scripts"
    / "m2_s1a_p_gate_a_20261109.py"
)
_GATE_B_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "features"
    / "FEAT-063-system-architecture-rearchitecture"
    / "evidence"
    / "scripts"
    / "m2_s1a_p_gate_b_20261109.py"
)


def _constants(tree: ast.Module) -> dict[str, object]:
    result: dict[str, object] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
        else:
            continue
        if isinstance(target, ast.Name) and target.id in {
            "revision",
            "down_revision",
            "branch_labels",
            "depends_on",
        }:
            value = getattr(statement, "value", None)
            if value is None:
                raise AssertionError(f"migration constant {target.id} has no value")
            result[target.id] = ast.literal_eval(value)
    return result


def _calls(function: ast.FunctionDef) -> list[tuple[str, ast.Call]]:
    calls = [
        (ast.unparse(node.func), node)
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
    ]
    return sorted(calls, key=lambda item: (item[1].lineno, item[1].col_offset))


@pytest.fixture
def migration_tree() -> ast.Module:
    return ast.parse(_MIGRATION.read_text(encoding="utf-8"))


def test_parent_migration_is_an_independent_named_root(migration_tree: ast.Module) -> None:
    constants = _constants(migration_tree)
    assert constants == {
        "revision": "20261109_m2_parent_profiles",
        "down_revision": None,
        "branch_labels": ("parent",),
        "depends_on": None,
    }


def test_upgrade_creates_only_parent_objects_in_dependency_order(
    migration_tree: ast.Module,
) -> None:
    upgrade = next(
        node
        for node in migration_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade"
    )
    calls = _calls(upgrade)
    table_calls = [
        (ast.literal_eval(call.args[0]), index)
        for index, (name, call) in enumerate(calls)
        if name == "op.create_table"
    ]
    assert [name for name, _index in table_calls] == [
        "child_profiles",
        "profile_revisions",
        "command_receipts",
    ]
    current_fk_index = next(
        index
        for index, (name, call) in enumerate(calls)
        if name == "op.create_foreign_key"
        and ast.literal_eval(call.args[0]) == "fk_parent_child_profiles_current_revision"
    )
    assert current_fk_index > max(index for _name, index in table_calls[:2])

    upgrade_text = ast.unparse(upgrade)
    assert "CREATE SCHEMA parent" in upgrade_text
    assert "CREATE TRIGGER trg_parent_profile_revisions_immutable" in upgrade_text
    assert "parent.reject_profile_revision_mutation()" in upgrade_text
    assert "ON parent.profile_revisions" in upgrade_text
    assert "IF NOT EXISTS" not in upgrade_text
    assert not any(
        marker in upgrade_text
        for marker in ("be1.", "core.", "story.", "lesson.", "ai_jobs.")
    )


def test_downgrade_removes_objects_in_reverse_dependency_order(
    migration_tree: ast.Module,
) -> None:
    downgrade = next(
        node
        for node in migration_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "downgrade"
    )
    action_labels: list[str] = []
    for name, call in _calls(downgrade):
        literals = [
            node.value
            for node in ast.walk(call)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        if name == "op.drop_index":
            action_labels.append("drop_index")
        elif name == "op.drop_table":
            action_labels.append(f"drop_table:{literals[0]}")
        elif name == "op.drop_constraint":
            action_labels.append(f"drop_constraint:{literals[0]}")
        elif name == "op.execute":
            action_labels.extend(literals)
    assert action_labels == [
        "drop_index",
        "drop_table:command_receipts",
        "DROP TRIGGER trg_parent_profile_revisions_immutable ON parent.profile_revisions",
        "DROP FUNCTION parent.reject_profile_revision_mutation()",
        "drop_constraint:fk_parent_child_profiles_current_revision",
        "drop_table:profile_revisions",
        "drop_table:child_profiles",
        "DROP SCHEMA parent",
    ]


def test_gate_a_rejects_untracked_paths_outside_allowlist_prefixes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_a_test", _GATE_A_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_a = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_a)

    def fake_git(*args: str) -> str:
        if args == ("diff", "--name-only", "HEAD"):
            return ""
        if args == ("ls-files", "--others", "--exclude-standard"):
            return "unrelated/notes.md"
        raise AssertionError(args)

    monkeypatch.setattr(gate_a, "_git", fake_git)
    monkeypatch.setattr(gate_a, "_approved_untracked_document_hashes", lambda _text: {})

    with pytest.raises(gate_a.SafeStop, match="UNTRACKED_PATH_OUTSIDE_APPROVED_ALLOWLIST"):
        gate_a._verify_allowlisted_changes(
            "| Mode | Path | SHA-256 |\n"
            "|---|---|---|\n"
            "| N | `backend/tests/unit/new_test.py` | ABSENT |\n",
            "",
        )


@pytest.mark.parametrize(
    ("script_path", "module_name", "parser_name", "expected_stop"),
    [
        (
            _GATE_A_SCRIPT,
            "m2_s1a_p_gate_a_manifest_test",
            "_approved_untracked_document_hashes",
            "UNTRACKED_DOCUMENT_MANIFEST_INVALID",
        ),
        (
            _GATE_B_SCRIPT,
            "m2_s1a_p_gate_b_manifest_test",
            "_manifest_hashes",
            "UNTRACKED_MANIFEST_INVALID",
        ),
    ],
)
def test_gate_manifest_parsers_reject_parent_traversal_before_hashing(
    script_path: Path,
    module_name: str,
    parser_name: str,
    expected_stop: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert module_spec is not None and module_spec.loader is not None
    runner = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(runner)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    hash_function = "sha256_file" if "gate_a" in module_name else "_sha256_file"
    monkeypatch.setattr(
        runner,
        hash_function,
        lambda _path: pytest.fail("unsafe manifest path reached file hashing"),
    )

    unsafe_path = (
        "features/FEAT-063-system-architecture-rearchitecture/evidence/"
        "../outside.md"
    )
    manifest = (
        "## M2 S1a-P Gate A Approval — test\n\n"
        "- **Status:** `APPROVED / NOT LAUNCHED`\n\n"
        "**Exact current untracked Markdown manifest:**\n"
        "| Path | SHA-256 |\n"
        "|---|---|\n"
        f"| `{unsafe_path}` | `{'A' * 64}` |\n"
    )
    parser = getattr(runner, parser_name)

    with pytest.raises(runner.SafeStop, match=expected_stop):
        parser(manifest)


def test_gate_a_rejects_draft_status_that_contains_approved_substring() -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_a_status_test", _GATE_A_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_a = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_a)
    section = (
        "## M2 S1a-P Gate A Approval — test\n"
        "- **Status:** `DRAFT / NOT APPROVED / NOT LAUNCHED`\n"
        "- **Approved branch:** `feature/feat063-m2-parent-teacher-foundation`\n"
        "- **Approved HEAD:** `4b7f07cc283721f01f64e41ff2d81f135f63ad29`\n"
        "- **OWNER_MODAL_CALL_APPROVED:** `NO`\n"
    )

    with pytest.raises(
        gate_a.SafeStop, match="GATE_A_ADDENDUM_MISSING_OR_STALE"
    ):
        gate_a._verify_gate_a_approval_entry(section, {})


@pytest.mark.parametrize(
    "value",
    ["APPROVED / NOT LAUNCHED", "`APPROVED / NOT LAUNCHED`"],
)
def test_gate_b_status_parser_requires_one_exact_field(value: str) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_status_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)

    assert gate_b._status_value(
        f"- **Status:** {value}", "APPROVED / NOT LAUNCHED"
    ) == (
        "APPROVED / NOT LAUNCHED"
    )
    invalid_sections = (
        "- **Status:** APPROVED / NOT LAUNCHED\n- **Status:** ACCEPTED",
        "- **Status:** DRAFT / APPROVED / NOT LAUNCHED",
        "- **Status:** APPROVED / NOT LAUNCHED extra",
    )
    for section in invalid_sections:
        with pytest.raises(
            gate_b.SafeStop, match="APPROVAL_STATUS_INVALID"
        ):
            gate_b._status_value(section, "APPROVED / NOT LAUNCHED")


def test_gate_b_child_environment_uses_only_fixed_allowlisted_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_child_environment_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)

    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setenv("PATH", "INHERITED_PATH_SENTINEL")
    monkeypatch.setenv("PYTEST_PLUGINS", "INHERITED_PLUGIN_SENTINEL")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--showlocals")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0")
    monkeypatch.setenv("PYTHONPATH", "INHERITED_PYTHONPATH_SENTINEL")
    monkeypatch.setenv("PYTHONHOME", "INHERITED_PYTHONHOME_SENTINEL")
    monkeypatch.setenv("PYTHONSTARTUP", "INHERITED_PYTHONSTARTUP_SENTINEL")

    temp_directory = tmp_path / "pytest-tmp"
    temp_directory.mkdir()
    child_env = gate_b._pytest_child_environment(
        "SYNTHETIC_DATABASE_VALUE", "a" * 32, temp_directory
    )

    assert set(child_env) == {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "PYTHONNOUSERSITE",
        "S1A_P_TEST_DATABASE_URL",
        "S1A_P_GATE_B_RUN_ID",
    }
    assert child_env["PATH"] != "INHERITED_PATH_SENTINEL"
    assert child_env["SYSTEMROOT"] == r"C:\Windows"
    assert child_env["WINDIR"] == r"C:\Windows"
    assert child_env["TEMP"] == child_env["TMP"] == str(temp_directory.resolve())
    assert child_env["PYTHONNOUSERSITE"] == "1"
    assert child_env["S1A_P_TEST_DATABASE_URL"] == "SYNTHETIC_DATABASE_VALUE"
    assert child_env["S1A_P_GATE_B_RUN_ID"] == "a" * 32
    assert not any(name.startswith("PYTEST_") for name in child_env)
    assert "PYTHONPATH" not in child_env
    assert "PYTHONHOME" not in child_env
    assert "PYTHONSTARTUP" not in child_env
    assert all("INHERITED_" not in value for value in child_env.values())


def test_gate_b_log_write_failure_cannot_be_rescanned_as_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_log_write_failure_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)

    bad_artifact = tmp_path / "artifact-is-a-directory"
    bad_artifact.mkdir()
    with pytest.raises(gate_b.SafeStop, match="GATE_B_LOG_WRITE_FAILED") as failure:
        gate_b._write_reserved(bad_artifact, b"artifact")

    status_path = tmp_path / "runner-status.txt"
    status_path.write_bytes(b"")

    def fail_if_rescanned(_: dict[str, Path]) -> dict[str, int]:
        raise AssertionError("safety rescan must not override an output-write failure")

    monkeypatch.setattr(gate_b, "_scan_safety", fail_if_rescanned)
    files = {"runner-status.txt": status_path}
    safety_status = gate_b._finalize_stop(
        files, failure.value.code, "PASS"
    )

    assert safety_status == "FAILED_OUTPUT_WRITE"
    assert gate_b.json.loads(status_path.read_text(encoding="utf-8"))["SAFETY_SCAN"] == (
        "FAILED_OUTPUT_WRITE"
    )
    assert gate_b._finalize_stop(files, "LATER_STOP", safety_status) == (
        "FAILED_OUTPUT_WRITE"
    )


def test_gate_b_runner_status_write_failure_downgrades_pass_and_reports_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_runner_status_write_failure_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)

    status_path = tmp_path / "runner-status.txt"
    status_path.write_text(
        gate_b.json.dumps({"SAFETY_SCAN": "PASS"}), encoding="utf-8"
    )
    write_json = gate_b._write_json
    write_statuses: list[str] = []

    def fail_pass_promotion(path: Path, value: object) -> None:
        assert isinstance(value, dict)
        status = value["SAFETY_SCAN"]
        write_statuses.append(str(status))
        if status == "PASS":
            raise gate_b.SafeStop("GATE_B_LOG_WRITE_FAILED")
        write_json(path, value)

    monkeypatch.setattr(gate_b, "_write_json", fail_pass_promotion)
    safety_status = gate_b._finalize_stop(
        {"runner-status.txt": status_path}, "PYTEST_EXIT_NONZERO", "PASS"
    )

    assert safety_status == "FAILED_OUTPUT_WRITE"
    assert safety_status != "PASS"
    assert write_statuses == [
        "STATUS_WRITE_INCOMPLETE",
        "PASS",
        "FAILED_OUTPUT_WRITE",
    ]
    assert gate_b.json.loads(status_path.read_text(encoding="utf-8"))["SAFETY_SCAN"] == (
        "FAILED_OUTPUT_WRITE"
    )
    captured = capsys.readouterr()
    assert "GATE_B_LOG_WRITE_FAILED" in captured.err
    assert "SAFETY_SCAN=FAILED_OUTPUT_WRITE" in captured.err


def test_gate_b_withholds_sensitive_pytest_output_before_persisting_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_output_scan_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)

    stdout_path = tmp_path / "pytest.stdout.txt"
    stderr_path = tmp_path / "pytest.stderr.txt"
    safety_path = tmp_path / "safety-scan.json"
    for path in (stdout_path, stderr_path, safety_path):
        path.write_bytes(b"")
    monkeypatch.setattr(gate_b, "URI_RE", gate_b.re.compile("LOCAL_SAFETY_MARKER"))
    files = {
        "pytest.stdout.txt": stdout_path,
        "pytest.stderr.txt": stderr_path,
        "safety-scan.json": safety_path,
    }

    with pytest.raises(gate_b.SafeStop, match="OUTPUT_SAFETY_FINDING"):
        gate_b._store_pytest_output(
            files, b"LOCAL_SAFETY_MARKER", b"ordinary stderr"
        )

    assert b"LOCAL_SAFETY_MARKER" not in stdout_path.read_bytes()
    assert b"LOCAL_SAFETY_MARKER" not in stderr_path.read_bytes()
    assert gate_b.json.loads(safety_path.read_text(encoding="utf-8")) == {
        "scheme_url": 1,
        "unverified_or_uri_matches": 1,
        "userinfo": 0,
        "password_assignment": 0,
        "pgpassword": 0,
        "bearer_token": 0,
        "credential_assignment": 0,
    }


@pytest.mark.parametrize(
    ("script_path", "module_name", "scan_artifact_name", "output_name"),
    [
        (
            _GATE_A_SCRIPT,
            "m2_s1a_p_gate_a_safety_scan_regression_test",
            "preview-safety-scan.json",
            "final-safety-scan.json",
        ),
        (
            _GATE_B_SCRIPT,
            "m2_s1a_p_gate_b_safety_scan_regression_test",
            "safety-scan.json",
            None,
        ),
    ],
)
def test_gate_safety_scanner_ignores_its_report_but_detects_sensitive_logs(
    script_path: Path,
    module_name: str,
    scan_artifact_name: str,
    output_name: str | None,
    tmp_path: Path,
) -> None:
    module_spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert module_spec is not None and module_spec.loader is not None
    runner = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(runner)

    scan_artifact = tmp_path / scan_artifact_name
    scan_artifact.write_text('{"pgpassword": 0}\n', encoding="utf-8")
    sensitive_log = tmp_path / "pytest.stderr.txt"
    sensitive_log.write_text("ordinary diagnostic\n", encoding="utf-8")
    if output_name is None:
        output_path = scan_artifact
        files = {
            scan_artifact_name: scan_artifact,
            "pytest.stderr.txt": sensitive_log,
        }
        counts = runner._scan_safety(files)
    else:
        output_path = tmp_path / output_name
        output_path.write_bytes(b"")
        files = {
            scan_artifact_name: scan_artifact,
            output_name: output_path,
            "upgrade.stderr.txt": sensitive_log,
        }
        counts = runner._scan_safety(files, output_name=output_name)

    assert counts["pgpassword"] == 0
    assert counts["unverified_or_uri_matches"] == 0

    sensitive_log.write_text("password=fixture-sensitive-value\n", encoding="utf-8")
    if output_name is not None:
        output_path.write_bytes(b"")
    with pytest.raises(runner.SafeStop, match="OUTPUT_SAFETY_FINDING"):
        if output_name is None:
            runner._scan_safety(files)
        else:
            runner._scan_safety(files, output_name=output_name)

    finding_counts = runner.json.loads(output_path.read_text(encoding="utf-8"))
    assert finding_counts["password_assignment"] == 1
    assert finding_counts["unverified_or_uri_matches"] == 1


def test_gate_b_rechecks_read_only_pins_with_append_only_prefixes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_read_only_pins_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)
    monkeypatch.setattr(gate_b, "ROOT", tmp_path)

    def write(relative: str, value: bytes) -> Path:
        path = tmp_path / Path(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    config_rel = "backend/pyproject.toml"
    decisions_rel = gate_b.DECISIONS_REL.as_posix()
    approval_rel = gate_b.APPROVAL_REL.as_posix()
    progress_rel = (
        "features/FEAT-063-system-architecture-rearchitecture/plan/"
        "M2_PROGRESS_REPORT_FOR_CODEX_20261109.md"
    )
    historical_rel = (
        "features/FEAT-063-system-architecture-rearchitecture/plan/"
        "M2_S1A_P_TASK_APPROVAL_DRAFT3_20261107.md"
    )
    config_path = write(config_rel, b"pinned config\n")
    decisions_base = b"pinned decisions prefix\n"
    decisions_current = decisions_base + b"appended decision\n"
    write(decisions_rel, decisions_current)
    approval_base = b"pinned approval prefix\n"
    approval_current = approval_base + b"## M2 S1a-P Gate B Approval -- test\n"
    write(approval_rel, approval_current)
    progress_base = b"pinned progress prefix\n"
    write(progress_rel, progress_base + b"appended progress\n")
    historical = write(historical_rel, b"historical input\n").read_bytes()

    digest = gate_b._sha256_bytes
    spec_text = "\n".join(
        (
            "### 5.1 Read-only inputs (R)",
            "",
            "| Mode | Repository-relative path | SHA-256 |",
            "|---|---|---|",
            f"| R | `{config_rel}` | {digest(config_path.read_bytes())} |",
            f"| R | `{decisions_rel}` | {digest(decisions_base)} |",
            f"| R | `{approval_rel}` | {digest(approval_base)} |",
            f"| R | `{progress_rel}` | {digest(progress_base)} |",
            f"| H | `{historical_rel}` | {digest(historical)} |",
            "",
        )
    )
    approval_section = (
        f"- **Approval prefix SHA-256:** `{digest(approval_base)}`"
    )
    decisions_pin = (decisions_rel, digest(decisions_current))
    gate_b._verify_read_only_input_hashes(
        spec_text,
        approval_section,
        approval_current,
        len(approval_base),
        decisions_pin,
    )

    config_path.write_bytes(b"changed config\n")
    with pytest.raises(gate_b.SafeStop, match="READ_ONLY_INPUT_HASH_MISMATCH"):
        gate_b._verify_read_only_input_hashes(
            spec_text,
            approval_section,
            approval_current,
            len(approval_base),
            decisions_pin,
        )


def test_gate_b_manifest_parser_stops_at_the_manifest_table_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_manifest_boundary_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)
    monkeypatch.setattr(gate_b, "ROOT", tmp_path)
    approved = (
        "features/FEAT-063-system-architecture-rearchitecture/evidence/approved.md"
    )
    approved_path = tmp_path / Path(*approved.split("/"))
    approved_path.parent.mkdir(parents=True)
    approved_path.write_text("approved", encoding="utf-8")
    monkeypatch.setattr(gate_b, "_sha256_file", lambda _path: "A" * 64)
    section = (
        "**Exact current untracked Markdown manifest:**\n"
        "| Path | SHA-256 |\n"
        "|---|---|\n"
        f"| `{approved}` | `{'A' * 64}` |\n"
        "\n"
        "| Path | SHA-256 |\n"
        "|---|---|\n"
        "| `features/FEAT-063-system-architecture-rearchitecture/plan/extra.md` "
        f"| `{'B' * 64}` |\n"
    )

    assert gate_b._manifest_hashes(section) == {approved: "A" * 64}


def test_gate_b_rejects_gate_a_inventory_path_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_inventory_path_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)
    log_root = Path(".claude/handoff/logs/M2_S1A_P_20261109")
    monkeypatch.setattr(gate_b, "ROOT", tmp_path)
    monkeypatch.setattr(gate_b, "GATE_A_LOG_ROOT", log_root)

    with pytest.raises(
        gate_b.SafeStop, match="GATE_A_INVENTORY_PATH_INVALID"
    ):
        gate_b._gate_a_inventory_path(
            f"{log_root.as_posix()}/run-id/../outside/post-inventory.json"
        )


def test_gate_b_inventory_rejects_boolean_row_counts() -> None:
    module_spec = importlib.util.spec_from_file_location(
        "m2_s1a_p_gate_b_inventory_shape_test", _GATE_B_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    gate_b = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(gate_b)
    table_rows = {f"public.table_{index}": 0 for index in range(120)}
    table_rows["public.table_0"] = True
    inventory = {
        "run_id": "run-id",
        "source_marker_run_id": "source-run-id",
        "read_only": True,
        "identity": {
            "database": "sketch2life_m2_s1a",
            "host": "127.0.0.1",
            "port": 5433,
            "user": "postgres",
            "postgres_major": 17,
        },
        "parent_schema_exists": True,
        "table_rows": table_rows,
        "total_rows": 1,
        "marker_rows": {},
        "marker_total": 0,
        "known_control_rows": {},
        "unmatched_tables": {},
        "alembic_versions": ["20261109_m2_parent_profiles"],
        "status": "MARKER_COUNTS_MATCH",
    }

    with pytest.raises(gate_b.SafeStop, match="GATE_A_INVENTORY_INVALID"):
        gate_b._validate_inventory_shape(inventory)


def test_models_keep_the_parent_current_revision_constraint_deferred() -> None:
    from sketch2life.infrastructure.persistence.parent_models import (
        ParentChildProfileModel,
        ParentCommandReceiptModel,
        ParentProfileRevisionModel,
    )

    child_table = cast(Table, ParentChildProfileModel.__table__)
    revision_table = cast(Table, ParentProfileRevisionModel.__table__)
    receipt_table = cast(Table, ParentCommandReceiptModel.__table__)
    child_constraints = {item.name: item for item in child_table.constraints}
    current_fk = child_constraints["fk_parent_child_profiles_current_revision"]
    assert current_fk.deferrable is True
    assert current_fk.initially == "DEFERRED"
    revision_constraints = {
        item.name: item for item in revision_table.constraints
    }
    assert "uq_parent_profile_revisions_parent_revision_no" in revision_constraints
    receipt_constraints = {
        item.name: item for item in receipt_table.constraints
    }
    assert "uq_parent_command_receipts_scope_key" in receipt_constraints
