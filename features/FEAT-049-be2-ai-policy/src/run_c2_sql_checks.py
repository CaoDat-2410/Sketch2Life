"""Source-pinned BE2-14 PostgreSQL lifecycle pack; never starts/downloads a server."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUITE = "tests/integration/ai_policy/test_policy_sql.py"
EXPECTED = {
    "test_module_upgrade_downgrade_isolated": 1,
    "test_child_process_restart_reads_committed_policy_and_scoped_outbox": 1,
    "test_transaction_failure_rolls_back_lifecycle_receipt_event_outbox": 1,
    "test_concurrent_writers_have_one_record_cas_winner": 1,
    "test_duplicate_receipt_rolls_back_second_command": 1,
    "test_raw_sql_cannot_rewrite_version_or_history": 6,
    "test_replacing_review_dimension_roundtrips_order_and_preserves_all_proofs": 1,
    "test_review_history_survives_resubmission": 1,
    "test_old_published_version_recall_does_not_replace_new_head": 1,
    "test_repository_rejects_rewritten_body_and_rolls_back": 1,
}
ACTIVATION_SUITE = "tests/integration/ai_policy/test_activation_sql.py"
ACTIVATION_EXPECTED = {
    "test_actual_commands_publish_disable_and_restart_effective_pin": 1,
    "test_actual_scope_and_lifecycle_rollback_if_receipt_insert_fails": 1,
    "test_concurrent_publications_serialize_to_one_effective_pin": 1,
    "test_recall_of_old_pin_racing_replacement_does_not_disable_new_pin": 1,
    "test_emergency_stop_before_publication_is_durable_and_idempotent": 1,
    "test_emergency_stop_sql_failure_rolls_back_scope_and_intent": 1,
    "test_old_epoch_emergency_stop_cannot_disable_racing_replacement": 1,
    "test_current_use_sql_keeps_prior_pin_across_ordinary_replacement": 1,
    "test_current_use_sql_stop_history_cannot_be_bypassed_after_reactivation": 1,
    "test_current_use_sql_scope_share_fence_blocks_stop_until_lease_exit": 1,
}
ACCOUNTING_SUITE = "tests/integration/ai_policy/test_accounting_sql.py"
ACCOUNTING_EXPECTED = {
    "test_ledger_commit_reconnect_preserves_original_terms_and_terminal_proof": 1,
    "test_ledger_exception_rolls_back_counters_reservation_receipt_and_audit": 1,
    "test_ledger_duplicate_receipt_rolls_back_entire_second_reservation": 1,
    "test_ledger_concurrent_reserves_have_exactly_one_capacity_winner": 2,
    "test_ledger_new_window_does_not_reset_global_slots": 1,
    "test_ledger_same_attempt_cannot_reserve_again_in_another_window": 1,
    "test_ledger_live_and_terminal_replay_have_no_counter_or_audit_delta": 1,
    "test_ledger_verified_release_frees_original_bucket_and_slot": 1,
    "test_ledger_failed_settlement_audit_rolls_back_terminal_state_and_counters": 1,
    "test_ledger_verified_overrun_recorded_truthfully_then_blocks_new_reserve": 1,
    "test_ledger_raw_sql_cannot_rewrite_terminal_or_provenance": 5,
    "test_ledger_wrong_scope_cannot_read_or_settle_other_reservation": 1,
    "test_guarded_accounting_service_actual_sql_reserve_and_settle": 1,
    "test_guarded_accounting_sql_stop_blocks_reserve_but_allows_verified_reconcile": 1,
}
COPIES_SUITE = "tests/integration/ai_policy/test_copy_registry_sql.py"
COPIES_EXPECTED = {
    "test_inventory_empty_read_is_unknown_and_does_not_create_scope": 1,
    "test_inventory_registration_reconnect_preserves_exact_original_profile": 1,
    "test_inventory_duplicate_cannot_replace_original_provenance": 3,
    "test_inventory_failure_rolls_back_registration_scope_and_event": 1,
    "test_inventory_keyset_pages_stable_revision_and_reject_intervening_registration": 1,
    "test_inventory_coverage_report_invalidated_by_new_registration": 1,
    "test_inventory_stale_coverage_cas_has_no_partial_audit": 1,
    "test_inventory_other_scope_coverage_cannot_be_reused_at_same_revision": 1,
    "test_inventory_registration_racing_purge_is_fenced_and_later_copy_quarantined": 1,
    "test_inventory_concurrent_duplicate_register_has_one_audit_event": 1,
    "test_inventory_raw_sql_cannot_rewrite_originals_or_unpurge_scope": 5,
    "test_inventory_scope_isolation_and_read_only_mutation_denial": 1,
    "test_inventory_missing_scope_reader_does_not_mix_later_insert_into_revision_zero": 1,
    "test_guarded_inventory_service_sql_source_coverage_and_late_fence": 1,
    "test_guarded_inventory_service_sql_revocation_before_commit_rolls_back": 1,
    "test_inventory_evidence_reconnect_and_retry_preserve_original_proof": 1,
    "test_inventory_evidence_is_immutable_even_through_raw_sql": 2,
    "test_inventory_evidence_insert_failure_rolls_back_registration_and_event": 1,
    "test_inventory_evidence_forward_branch_roundtrip_preserves_inventory": 1,
    "test_copy_operation_reconnect_replay_and_scope_isolation": 1,
    "test_copy_operation_raw_sql_history_is_immutable": 4,
    "test_copy_operation_authority_insert_failure_rolls_back_intent_fence_and_event": 1,
    "test_copy_operation_concurrent_duplicate_has_one_intent_and_queued_event": 1,
    "test_copy_operation_final_owner_denial_rolls_back_all_new_writes": 1,
}


def source_hashes() -> dict[str, str]:
    paths = set((ROOT / "backend/src").rglob("*.py"))
    paths.update((ROOT / "backend/alembic").rglob("*.py"))
    paths.update((ROOT / "backend/tests/integration/ai_policy").rglob("*.py"))
    paths.update(ROOT / name for name in (
        "backend/tests/conftest.py", "backend/tests/unit/test_ai_policy_domain.py",
        "backend/tests/ai_policy_accounting_fixtures.py",
        "backend/tests/ai_policy_copy_inventory_fixtures.py",
        "backend/tests/ai_policy_copy_operation_fixtures.py",
        "backend/tests/ai_policy_fixtures.py", "backend/tests/unit/test_ai_policy_compatibility.py",
        "backend/tests/contract/test_ai_policy_contracts.py",
        "backend/tests/unit/test_ai_policy_use.py",
        "backend/pyproject.toml", "backend/alembic.ini",
        "features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py"))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def inventory(output: str, suite: str = SUITE) -> tuple[str, ...]:
    return tuple(line.strip() for line in output.splitlines()
                 if line.strip().startswith(suite + "::"))


def valid_inventory(nodes: tuple[str, ...], expected: dict[str, int] | None = None) -> bool:
    return (len(nodes) == len(set(nodes))
            and Counter(node.split("::", 1)[1].split("[", 1)[0] for node in nodes)
            == (EXPECTED if expected is None else expected))


def classify(nodes: tuple[str, ...], junit: Path, process_exit: int) -> tuple[str, int]:
    if process_exit:
        return "FAIL", 1
    if not junit.is_file():
        return "NOT_RUN", 2
    try:
        tree = ET.parse(junit)
    except (ET.ParseError, OSError):
        return "FAIL", 1
    if list(tree.iter("failure")) or list(tree.iter("error")):
        return "FAIL", 1
    names = tuple(case.get("classname", "").replace(".", "/") + ".py::"
                  + case.get("name", "") for case in tree.iter("testcase"))
    if len(names) != len(set(names)) or set(names) - set(nodes):
        return "FAIL", 1
    if list(tree.iter("skipped")) or set(names) != set(nodes):
        return "NOT_RUN", 2
    return "PASS", 0


def run(args: list[str], out: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=ROOT / "backend", text=True,
                            capture_output=True, check=False)
    out.write_text(result.stdout + result.stderr, encoding="utf-8")
    return result


def main(*, activation: bool = False, accounting: bool = False, copies: bool = False) -> int:
    if sum((activation, accounting, copies)) > 1:
        raise ValueError("select exactly one SQL pack")
    if os.environ.get("AP_TEST_ALLOW_CREATE") != "1" or not os.environ.get("AP_TEST_PG_HOST"):
        print("NOT_RUN: explicit authorized BE2-14 disposable PostgreSQL profile required")
        return 2
    out = ROOT / ".runtime/ai-policy-c2" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    suite = ACTIVATION_SUITE if activation else SUITE
    expected = ACTIVATION_EXPECTED if activation else EXPECTED
    if accounting:
        suite, expected = ACCOUNTING_SUITE, ACCOUNTING_EXPECTED
    if copies:
        suite, expected = COPIES_SUITE, COPIES_EXPECTED
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", suite]
    collected = run([*command, "--collect-only", "-q"], out / "collection.log")
    nodes = inventory(collected.stdout, suite)
    status, exit_code = "FAIL", 1
    if collected.returncode == 0 and valid_inventory(nodes, expected):
        junit = out / "junit.xml"
        tested = run([*command, "-q", "--tb=short", f"--junitxml={junit}"], out / "pytest.log")
        status, exit_code = classify(nodes, junit, tested.returncode)
    unchanged = before == source_hashes()
    if not unchanged:
        status, exit_code = "FAIL", 1
    summary = dict(scope="BE2_14_C3B_ACTIVATION_SQL" if activation else "BE2_14_OWNED_C2_SQL_ONLY",
                   status=status, expected_cases=sum(expected.values()), cases=len(nodes),
                   source_sha256=before, source_unchanged=unchanged,
                   real_owner_integration="NOT_RUN", full_goal_complete=False)
    if accounting:
        summary["scope"] = "BE2_14_C3C3B_LEDGER_SQL_ONLY"
    if copies:
        summary["scope"] = "BE2_14_C4B1_COPY_INVENTORY_SQL_ONLY"
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{status}: {out}")
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--activation", action="store_true")
    group.add_argument("--accounting", action="store_true")
    group.add_argument("--copies", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(activation=args.activation, accounting=args.accounting, copies=args.copies))
