"""BE2-01 Phase B batch B6: durable conformance runner (plan revision 3 §4/§7/§7.1/§8).

Usage (inside the synthetic Studio runner container, from the repository root):
    python features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py \
        --report PATH --manifest SOURCE_MANIFEST --manifest-sha256 HEX \
        --junit B2_B6.xml --phase-a-junit PHASE_A.xml --fixture-report PHASE_A_RUNNER.json

What it proves, and what it does not:

* Phase A scenarios A-01..A-20 are mapped one by one. Each scenario with durable meaning runs
  on the real SQL adapter (PostgreSQL 17, a fresh disposable database per harness cloned from a
  migrated template), real Redis/RQ transport, real HMAC worker capabilities, the fake provider
  and the ASSUMED_CONTRACT owner-fence fixture (decisions, fences, audit/artifact sinks).
  Contract-only scenarios are not re-labelled as durable; they stay owned by the Phase A
  fixture runner. Durable provider-copy lifecycle is DEFERRED (BE2-14).
* B-01..B-12 and the §7.1 crash-window matrix are resolved from the JUnit results of the same
  source-bound run (pytest B2–B6 and Phase A), the Phase A fixture report and this run.
  B-12 is a handoff list, never PASS: real owner/provider/live-route integration is not proven.
* The runner is a self-sufficient gate (B6-CR01): G-01/G-02 aggregate every JUnit case of the
  B2–B6 and Phase A suites against the test ids pytest collects from the running tree,
  parameter ids included (any failure FAILs; a missing or skipped case is NOT_RUN; a case
  outside the inventory FAILs), G-03 needs
  the complete Phase A fixture report and G-04 needs a pinned, non-empty source manifest that
  matches the tree and lists every Phase B surface file.

Exit codes: 0 = every required item PASS; 1 = any FAIL; 2 = no FAIL but a required item
NOT_RUN (missing service, missing JUnit/report, skipped test). Nothing falls back to fakes.
Configuration uses the integration-test variables (BE2_TEST_PG_HOST/PORT/USER/MAINTENANCE_DB/
PASSWORD_FILE, BE2_TEST_REDIS_HOST/PORT). Secrets, tokens and keys are never printed.
"""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import functools
import hashlib
import json
import logging
import os
import platform
import re
import subprocess
import sys
import threading
import uuid
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from typing import Any

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
BACKEND = ROOT / "backend"
BACKEND_SRC = BACKEND / "src"
sys.path.insert(0, str(BACKEND_SRC))

import sketch2life  # noqa: E402
from sketch2life.application.ports.ai_jobs import (  # noqa: E402
    AuthorizationAction,
    CancellationNotice,
    JobRevisionConflict,
    Principal,
)
from sketch2life.application.services.ai_jobs import (  # noqa: E402
    FIXTURE_RETRY_POLICY,
    AiJobDependencies,
    AiJobError,
    AiJobService,
    CancelJobCommand,
    CreateJobCommand,
)
from sketch2life.domain.ai_jobs.completion import (  # noqa: E402
    CompletionClaim,
    Moderation,
    OutcomeKind,
    OutputRef,
)
from sketch2life.domain.ai_jobs.model import (  # noqa: E402
    AiJob,
    InvalidProgress,
    JobProgress,
    JobState,
    ProgressKind,
    RequestRef,
)
from sketch2life.infrastructure.ai_jobs.fakes import FakeClock, FakeProvider  # noqa: E402
from sketch2life.infrastructure.ai_jobs.harness import (  # noqa: E402
    ADMIN,
    DEVICE,
    FIXTURE_START,
    JOB_TYPE,
    ORG,
    OTHER_ORG,
    OUTSIDER,
    SESSION,
    SUBJECT,
    TARGET,
    TEACHER,
    TEACHER_2,
    UNGRANTED,
    request_ref,
)

RUNNER = "BE2-01 Phase B B6 durable conformance"
RUNNER_VERSION = "b6.2"
PLAN = ("plan/PHASE_B_PLAN.md revision 3 (sha256 bb20d5be...) B1-B6, "
        "approvals/PHASE_B_TASK_APPROVAL.md")
OWNER_FENCE_LABEL = "ASSUMED_CONTRACT OwnerFenceV1/0.1-candidate (owner_fence_fixture)"
ALL_ACTIONS = [str(action) for action in AuthorizationAction]

REQUIRED = "required"
OPTIONAL = "optional"
CONTRACT_ONLY = "contract_only"
DEFERRED = "deferred"
HANDOFF = "handoff"

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"
NOT_APPLICABLE, DEFERRED_STATUS, HANDOFF_STATUS = "NOT_APPLICABLE", "DEFERRED", "HANDOFF"


# ================================================================== results and decisions
@dataclass
class Result:
    item: str
    title: str
    kind: str
    status: str = PASS
    checks: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""
    evidence: list[str] = field(default_factory=list)

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            self.status = FAIL

    def mark(self, status: str, reason: str) -> Result:
        self.status, self.reason = status, reason
        return self


def exit_code(results: list[Result]) -> int:
    """1 if anything failed; 2 if a required item did not run; else 0."""

    if any(r.status == FAIL for r in results):
        return 1
    if any(r.kind == REQUIRED and r.status != PASS for r in results):
        return 2
    return 0


def summarise(results: list[Result]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return {
        "items": len(results),
        "by_status": dict(sorted(counts.items())),
        "required": sum(r.kind == REQUIRED for r in results),
        "required_pass": sum(r.kind == REQUIRED and r.status == PASS for r in results),
        "required_not_run": sorted(r.item for r in results
                                   if r.kind == REQUIRED and r.status == NOT_RUN),
        "failed": sorted(r.item for r in results if r.status == FAIL),
        "checks": sum(len(r.checks) for r in results),
        "checks_failed": sum(not c["ok"] for r in results for c in r.checks),
    }


# ======================================================================= JUnit evidence
@dataclass(frozen=True)
class CaseOutcome:
    module: str  # test file relative to the pytest rootdir (backend/): tests/unit/test_x.py
    name: str  # test id within the file: class parts and parameter id included
    status: str  # PASS | FAIL | NOT_RUN

    @property
    def file(self) -> str:
        return self.module.rsplit("/", 1)[-1]


def nodeid_key(nodeid: str) -> tuple[str, str] | None:
    """``(file path, test id)`` of a pytest node id such as ``tests/a/test_x.py::C::t[1]``."""

    path, sep, rest = nodeid.strip().partition("::")
    if not sep or not rest or not path.endswith(".py"):
        return None
    return path.replace("\\", "/"), rest


def junit_key(classname: str, name: str) -> tuple[str, str]:
    """The same identity from a pytest JUnit ``testcase``: ``classname`` is the dotted file
    path (plus class names), ``name`` the function name with its parameter id."""

    parts = classname.split(".") if classname else []
    module_at = max((i for i, part in enumerate(parts) if part.startswith("test_")), default=None)
    if module_at is None:
        return classname, name
    return ("/".join(parts[: module_at + 1]) + ".py",
            "::".join([*parts[module_at + 1:], name]))


# The suites the package runs; their test inventory is collected by pytest from the running
# (manifest-verified) tree, never taken from the JUnit under evaluation.
SUITE_B2_B6: tuple[str, ...] = (
    "backend/tests/integration/ai_jobs/test_*.py",
    "backend/tests/unit/test_ai_job_b3_fences.py",
    "backend/tests/unit/test_ai_job_b4_dispatch.py",
    "backend/tests/unit/test_ai_job_b5_capability.py",
    "backend/tests/unit/test_ai_job_b5_effects.py",
    "backend/tests/unit/test_ai_job_b6_conformance.py",
)
SUITE_PHASE_A: tuple[str, ...] = (
    "backend/tests/unit/test_ai_job_q00_followups.py",
    "backend/tests/unit/test_ai_job_review_regressions.py",
    "backend/tests/unit/test_ai_job_lifecycle.py",
    "backend/tests/unit/test_ai_job_application.py",
    "backend/tests/contract/test_ai_job_contracts.py",
    "backend/tests/contract/test_ai_job_polling.py",
)
# Every file of the Phase B surface present in the tree must be listed in the source manifest.
PHASE_B_SURFACE: tuple[str, ...] = (
    "backend/alembic/versions/20261015_ai_*.py",
    "backend/src/sketch2life/infrastructure/ai_jobs/sql/*.py",
    "backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py",
    "backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py",
    "backend/src/sketch2life/infrastructure/ai_jobs/rq_queue.py",
    "backend/src/sketch2life/infrastructure/ai_jobs/worker.py",
    "backend/src/sketch2life/infrastructure/ai_jobs/worker_capability.py",
    "backend/tests/integration/ai_jobs/*.py",
    "backend/tests/unit/test_ai_job_b[3-6]_*.py",
    "features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py",
)
FIXTURE_ITEMS: tuple[str, ...] = tuple(f"A-{n:02d}" for n in range(1, 21))


Inventory = dict[str, frozenset[str]]


@functools.cache
def suite_inventory(globs: tuple[str, ...], root: Path = ROOT) -> tuple[Inventory, str]:
    """``({tests/.../test_x.py: {collected test ids}}, detail)`` from ``pytest --collect-only``
    over the suite files of the running tree, so every parameter variant is expected.
    All or nothing: a collection error, a count that differs from pytest's own total, a case
    outside the suite files or a suite file without cases gives an empty inventory, which can
    never pass a gate."""

    backend = root / "backend"
    files = sorted({p for pattern in globs for p in root.glob(pattern) if p.is_file()})
    if not files:
        return {}, "no suite files in the running tree"
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", str(backend / "pyproject.toml"),
         "--collect-only", "-q", "-o", "addopts=", "-p", "no:cacheprovider",
         *(str(p) for p in files)],
        cwd=root, capture_output=True, text=True, timeout=900, check=False,
    )
    if done.returncode != 0:
        tail = (done.stdout + done.stderr).strip().splitlines()[-1:] or [""]
        return {}, f"pytest collection exit {done.returncode}: {tail[0][:160]}"
    keys = [key for key in map(nodeid_key, done.stdout.splitlines()) if key is not None]
    totals = [int(m.group(1)) for m in re.finditer(r"^(\d+) tests? collected", done.stdout, re.M)]
    if len(totals) != 1 or totals[0] != len(keys) or len(set(keys)) != len(keys):
        return {}, f"collection incomplete: pytest total {totals}, parsed {len(keys)} node ids"
    expected_files = {p.relative_to(backend).as_posix() for p in files}
    found: dict[str, set[str]] = {}
    for module, name in keys:
        found.setdefault(module, set()).add(name)
    if set(found) - expected_files:
        return {}, f"cases outside the suite files: {sorted(set(found) - expected_files)[:3]}"
    if expected_files - set(found):
        return {}, f"no case collected from {sorted(expected_files - set(found))[:3]}"
    return ({module: frozenset(names) for module, names in found.items()},
            f"pytest collected {len(keys)} cases in {len(found)} files")



def read_junit(paths: list[Path]) -> tuple[list[CaseOutcome], list[str]]:
    """All test cases of the given JUnit files; missing or unreadable files are reported,
    never guessed."""

    outcomes: list[CaseOutcome] = []
    missing: list[str] = []
    for path in paths:
        if not path.is_file():
            missing.append(path.name)
            continue
        try:
            root = ElementTree.parse(path).getroot()
        except ElementTree.ParseError:
            missing.append(f"{path.name} (unreadable)")
            continue
        for case in root.iter("testcase"):
            module, name = junit_key(case.get("classname") or "", case.get("name") or "")
            status = PASS
            if case.find("failure") is not None or case.find("error") is not None:
                status = FAIL
            elif case.find("skipped") is not None:
                status = NOT_RUN
            outcomes.append(CaseOutcome(module, name, status))
    return outcomes, missing


def resolve_tests(
    outcomes: list[CaseOutcome],
    patterns: list[str],
    inventory: Inventory | None = None,
) -> tuple[str, list[str]]:
    """Status of the tests matching ``file.py::name`` patterns (fnmatch on the name).
    Every pattern must match at least one executed case and, given an inventory, every
    collected case (each parameter variant) of the functions it names must have executed; any
    FAIL fails, any skip or missing case is NOT_RUN."""

    detail: list[str] = []
    status = PASS
    for pattern in patterns:
        module, _, name = pattern.partition("::")
        matched = [o for o in outcomes if o.file == module and fnmatch.fnmatchcase(o.name, name)]
        base = name.split("[", 1)[0]
        expected = {(path, t) for path, names in (inventory or {}).items()
                    if path.rsplit("/", 1)[-1] == module for t in names
                    if fnmatch.fnmatchcase(t.split("[", 1)[0], base)}
        absent = sorted(f"{t}" for _, t in expected - {(o.module, o.name) for o in outcomes})
        if not matched:
            detail.append(f"{pattern}: no executed case")
            status = FAIL if status == FAIL else NOT_RUN
            continue
        states = {o.status for o in matched}
        if FAIL in states:
            status = FAIL
            detail.append(f"{pattern}: FAIL ({sum(o.status == FAIL for o in matched)})")
        elif NOT_RUN in states or absent:
            status = FAIL if status == FAIL else NOT_RUN
            detail.append(f"{pattern}: skipped {sum(o.status == NOT_RUN for o in matched)}, "
                          f"not executed {len(absent)} {absent[:3]}")
        else:
            detail.append(f"{pattern}: PASS ({len(matched)})")
    return status, detail


def suite_gate(item: str, title: str, outcomes: list[CaseOutcome], have: bool,
               collected: tuple[Inventory, str], source: str) -> Result:
    """Every JUnit case of one suite against the collected inventory: a failure FAILs, a case
    outside the inventory FAILs, a missing (also a single parameter variant) or skipped case
    is NOT_RUN."""

    inventory, detail = collected
    r = Result(item, title, REQUIRED, evidence=[f"inventory ({source}): {detail}"])
    if not inventory:
        r.check("suite inventory collected from the running tree", False, detail)
        return r
    if not have:
        return r.mark(NOT_RUN, "JUnit of this suite not supplied or unreadable")
    expected = {(module, name) for module, names in inventory.items() for name in names}
    executed = {(o.module, o.name) for o in outcomes}
    failed = sorted(f"{o.module}::{o.name}" for o in outcomes if o.status == FAIL)
    foreign = sorted(f"{m}::{n}" for m, n in executed - expected)
    skipped = sorted(f"{o.module}::{o.name}" for o in outcomes if o.status == NOT_RUN)
    absent = sorted(f"{m}::{n}" for m, n in expected - executed)
    r.evidence.append(f"junit: {len(outcomes)} cases, {len(failed)} failed, {len(skipped)} "
                      f"skipped, {len(absent)} collected cases not executed, {len(foreign)} "
                      "outside the inventory")
    r.check("no failed or errored case", not failed, ", ".join(failed[:5]))
    r.check("no case outside the suite inventory", not foreign, ", ".join(foreign[:5]))
    if r.status == PASS and (skipped or absent):
        return r.mark(NOT_RUN, f"skipped {skipped[:3]}; not executed {absent[:3]}")
    return r


# =============================================== §7.1 crash windows and §8 acceptance map
@dataclass(frozen=True)
class CrashWindow:
    window_id: str
    window: str
    recovery: str
    tests: tuple[str, ...]
    bounded: str = ""


CRASH_WINDOWS: tuple[CrashWindow, ...] = (
    CrashWindow("W01", "Crash before create commit",
                "Nothing durable; the caller retries the same key",
                ("test_restart_recovery.py::test_crash_before_create_commit_leaves_nothing_*",
                 "test_sql_repository.py::test_failure_at_each_create_boundary_leaves_nothing*")),
    CrashWindow("W02", "Create committed, process killed before publish",
                "Rows survive restart unchanged; a restarted dispatcher publishes the "
                "pending outbox",
                ("test_restart_recovery.py::test_kill_after_commit_keeps_rows_*",
                 "test_migrations.py::test_committed_rows_are_read_back_by_a_new_connection")),
    CrashWindow("W03", "Enqueued, crash before fenced mark",
                "Lease expiry; new holder (generation+1) republishes the same attempt; stale "
                "mark/release no-op; start deduplicates",
                ("test_dispatch_recovery.py::test_enqueue_then_crash_before_mark_*",
                 "test_dispatch_recovery.py::test_stale_lease_holder_mark_and_release_*")),
    CrashWindow("W04", "Broker down",
                "Enqueue fails, row stays pending, job stays queued, no extra attempt",
                ("test_outbox_dispatch.py::test_broker_outage_keeps_sql_pending_*",)),
    CrashWindow("W05", "Worker received, died before durable start",
                "Same-attempt republish within the bound, then dispatch loss -> backoff/policy",
                ("test_capability.py::test_worker_dies_after_receive_*",
                 "test_dispatch_recovery.py::test_lost_receive_is_republished_*",
                 "test_dispatch_recovery.py::test_publish_bound_then_dispatch_loss_*",
                 "test_dispatch_recovery.py::test_final_attempt_dispatch_loss_*",
                 "test_dispatch_recovery.py::test_dispatch_loss_and_start_have_exactly_one_winner*")),
    CrashWindow("W06", "Started, died before provider result",
                "Overdue sweep -> failed_retryable PROVIDER_TIMEOUT -> policy retry (new attempt)",
                ("test_restart_recovery.py::test_worker_dies_after_start_before_provider_*",
                 "test_dispatch_recovery.py::test_overdue_running_and_due_retry_sweeps_*")),
    CrashWindow("W07", "Provider returned, died before completion commit",
                "Attempt times out -> policy retry; a late claim of the old attempt is "
                "ATTEMPT_SUPERSEDED and its owned output quarantined",
                ("test_capability.py::test_provider_output_without_completion_*",
                 "test_completion_recovery.py::test_uncommitted_provider_output_*"),
                bounded="No same-claim recovery: no durable claim journal, no invented "
                        "fingerprint, provider may have executed twice (plan 7.1)"),
    CrashWindow("W08", "Completion committed, crash before audit/quarantine delivery",
                "Intents stay in the outbox; a restarted process delivers them, dedup by event_id",
                ("test_audit_durability.py::test_crash_before_delivery_is_redelivered_*",
                 "test_restart_recovery.py::test_kill_after_commit_keeps_rows_*")),
    CrashWindow("W09", "Quarantine effect applied, crash before delivery mark",
                "Redelivery sends the same stored event_id; sink no-op; artifact changed once",
                ("test_audit_durability.py::test_crash_after_sink_effect_before_mark_*",)),
    CrashWindow("W10", "Rejection/conflict, crash or failure before incident commit",
                "No answer returned (503); the retry recomputes the same event_id; committed once",
                ("test_audit_durability.py::test_incident_commit_failure_is_a_retryable_503",
                 "test_audit_durability.py::test_repeated_incident_is_stored_and_applied_once",
                 "test_audit_durability.py::test_concurrent_identical_conflict_incidents_*")),
    CrashWindow("W11", "Failure at any completion write boundary (rollback, B-08a)",
                "Whole transaction rolls back: no partial job/receipt/intent, no sink effect",
                ("test_completion_recovery.py::test_failure_at_each_completion_boundary_*",)),
    CrashWindow("W12", "Crash mid-notice (B-09g)",
                "Rollback, no COMPLETE marker; redelivery cancels every match; nothing reopened",
                ("test_notice_coverage.py::test_crash_mid_notice_rolls_back_*",)),
)


@dataclass(frozen=True)
class Acceptance:
    item: str
    title: str
    tests: tuple[str, ...] = ()
    batches: str = ""


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance("B-01", "Restart after commit keeps revisions, receipts/fingerprints, outbox",
               ("test_migrations.py::test_committed_rows_are_read_back_by_a_new_connection",
                "test_restart_recovery.py::test_*"), "B2 schema level + B6 kill/restart"),
    Acceptance("B-02", "Broker down loses nothing; replay creates no semantic attempt",
               ("test_outbox_dispatch.py::test_broker_outage_keeps_sql_pending_*",
                "test_outbox_dispatch.py::test_dispatch_publishes_through_rq_*"), "B4"),
    Acceptance("B-03", "Create races: one job, per-key receipts, mismatch, null session, order",
               ("test_create_races.py::test_b03*",), "B3"),
    Acceptance("B-04", "Receive-before-start republish, dispatch loss, lease fencing",
               ("test_dispatch_recovery.py::test_*",), "B4"),
    Acceptance("B-05", "One authoritative completion; attempt-bound capability; token-free",
               ("test_completion_recovery.py::test_concurrent_completions_*",
                "test_capability.py::test_*"), "B5"),
    Acceptance("B-06", "Crash matrix plan 7.1 (a-d)", (), "B4/B5 + B6 matrix (resolved below)"),
    Acceptance("B-07", "Semantic scope isolation durable",
               ("test_sql_repository.py::test_semantic_scope_isolation_is_durable*",
                "test_create_races.py::test_b03d*", "test_create_races.py::test_b03e*"), "B3"),
    Acceptance("B-08", "Rollback leaves nothing partial; audit-only failure 503",
               ("test_sql_repository.py::test_failure_at_each_create_boundary_leaves_nothing*",
                "test_sql_repository.py::test_cancel_commits_state_receipt_and_audit_*",
                "test_completion_recovery.py::test_failure_at_each_completion_boundary_*",
                "test_audit_durability.py::test_incident_commit_failure_is_a_retryable_503"),
               "B3/B5"),
    Acceptance("B-09", "Owner fences (a-d) and atomic notices (e-g)",
               ("test_owner_fence.py::test_*", "test_notice_coverage.py::test_*"), "B3/B5"),
    Acceptance("B-10", "Durable outbox/receipt/CAS/rollback and capability on the real adapter",
               ("test_capability.py::test_hmac_capability_reaches_the_worker_only_through_rq_*",),
               "B6 runner (A-scenarios on SQL) + B5 capability"),
    Acceptance("B-11", "Migration/conformance report; Phase A suites still pass on fakes",
               ("test_migrations.py::test_*",), "B2 migrations + Phase A + this report"),
)

B12_HANDOFF: tuple[dict[str, str], ...] = (
    {"item": "Real owner fence (OwnerFenceV1) adapter, fence rows/function, notice transport",
     "owner": "P2 / BE1 (Q2/Q3/Q8)", "status": "DEFERRED: component proof uses ASSUMED_CONTRACT "
     "owner_fence_fixture only"},
    {"item": "Production audit storage and artifact quarantine adapter (sinks)",
     "owner": "BE1 (audit/artifact owners, Q4/Q5)",
     "status": "DEFERRED: FixtureAuditSink/FixtureArtifacts component sinks only"},
    {"item": "Worker capability key provisioning, key_id rotation, process wiring",
     "owner": "P4 / INTG-02 (Q6)", "status": "DEFERRED: per-run ephemeral test key only"},
    {"item": "Live router/namespace and HTTP surface beyond the CMD-44 fixture app",
     "owner": "P4 / INTG-02, BE2 later cards", "status": "DEFERRED: not wired into the live app"},
    {"item": "Provider inference, real provider adapters, exactly-once execution",
     "owner": "BE2-04/BE2-08 (provider cards)", "status": "DEFERRED: fake provider only; no "
     "claim journal by design (plan 7.1)"},
    {"item": "Durable ProviderCopyLifecycle and actual provider-copy deletion",
     "owner": "BE2-14", "status": "DEFERRED: Phase A fake (A-18) only"},
    {"item": "Production policy values (retry, dispatch, TTL, notice bound) and deployment",
     "owner": "Project owner / INTG-02", "status": "DEFERRED: fixture.durable_jobs.v0 PROPOSED"},
    {"item": "P1/P2/P4 role sign-off, registry and production adoption",
     "owner": "P1/P2/P4", "status": "DEFERRED: PROJECT_OWNER_DIRECTIVE is not role sign-off"},
)


def resolve_matrix(outcomes: list[CaseOutcome], have_junit: bool,
                   inventory: Inventory | None = None) -> list[Result]:
    rows = []
    for window in CRASH_WINDOWS:
        r = Result(window.window_id, window.window, REQUIRED,
                   evidence=[f"recovery: {window.recovery}"]
                   + ([f"bounded: {window.bounded}"] if window.bounded else []))
        if not have_junit:
            rows.append(r.mark(NOT_RUN, "no JUnit result of the B2-B6 suite supplied"))
            continue
        status, detail = resolve_tests(outcomes, list(window.tests), inventory)
        r.evidence.extend(detail)
        r.status = status
        if status != PASS:
            r.reason = "mapped tests did not all pass in this run"
        rows.append(r)
    return rows


def resolve_acceptance(
    outcomes: list[CaseOutcome],
    have_junit: bool,
    matrix: list[Result],
    scenarios: list[Result],
    phase_a: tuple[str, str],
    fixture: tuple[str, str],
    inventory: Inventory | None = None,
) -> list[Result]:
    rows: list[Result] = []
    for acc in ACCEPTANCE:
        r = Result(acc.item, acc.title, REQUIRED, evidence=[f"batches: {acc.batches}"])
        parts: list[str] = []
        if acc.tests:
            if not have_junit:
                parts.append(NOT_RUN)
                r.evidence.append("no JUnit result of the B2-B6 suite supplied")
            else:
                status, detail = resolve_tests(outcomes, list(acc.tests), inventory)
                parts.append(status)
                r.evidence.extend(detail)
        if acc.item == "B-06":
            statuses = {row.status for row in matrix}
            parts.append(FAIL if FAIL in statuses else NOT_RUN if NOT_RUN in statuses else PASS)
            r.evidence.append("crash windows: " + ", ".join(f"{m.item}={m.status}" for m in matrix))
        if acc.item == "B-10":
            durable = [s for s in scenarios if s.kind == REQUIRED]
            statuses = {s.status for s in durable}
            parts.append(FAIL if FAIL in statuses else NOT_RUN if NOT_RUN in statuses else PASS)
            r.evidence.append("durable scenarios: "
                              + ", ".join(f"{s.item}={s.status}" for s in durable))
        if acc.item == "B-11":
            for label, (status, info) in (("Phase A pytest", phase_a),
                                          ("Phase A fixture runner", fixture)):
                parts.append(status)
                r.evidence.append(f"{label}: {status} ({info})")
        r.status = FAIL if FAIL in parts else NOT_RUN if NOT_RUN in parts else PASS
        if r.status != PASS:
            r.reason = "required evidence missing or not passing in this run"
        rows.append(r)
    b12 = Result("B-12", "Not proven here: real integrations (handoff)", HANDOFF,
                 evidence=[f"{h['item']} -> {h['owner']}: {h['status']}" for h in B12_HANDOFF])
    rows.append(b12.mark(HANDOFF_STATUS, "explicit handoff boundary; never reported as PASS"))
    return rows


def fixture_gate(path: Path | None) -> Result:
    """G-03: the complete Phase A fixture runner report (every A-01..A-20 PASS, checks > 0)."""

    r = Result("G-03", "Phase A fixture runner report complete", REQUIRED)
    if path is None or not path.is_file():
        return r.mark(NOT_RUN, "no Phase A fixture runner report supplied")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        summary = dict(report["summary"])
        results = {str(item["criterion"]): str(item["status"]) for item in report["results"]}
    except (ValueError, KeyError, TypeError) as exc:
        r.check("report is a readable fixture runner report", False, type(exc).__name__)
        return r
    digest = str(report.get("results_sha256", ""))
    r.evidence.append(f"PASS {summary.get('PASS')}, FAIL {summary.get('FAIL')}, checks "
                      f"{summary.get('checks')}, results_sha256 {digest[:8]}")
    checks = summary.get("checks")
    r.check("checks executed (> 0) and none failed",
            isinstance(checks, int) and checks > 0 and summary.get("checks_failed") == 0
            and summary.get("FAIL") == 0, f"checks={checks}")
    r.check("exactly A-01..A-20, every one PASS",
            sorted(results) == list(FIXTURE_ITEMS) and set(results.values()) == {PASS}
            and summary.get("PASS") == len(FIXTURE_ITEMS),
            ", ".join(f"{k}={v}" for k, v in sorted(results.items()) if v != PASS))
    r.check("results digest present", bool(re.fullmatch(r"[0-9a-f]{64}", digest)), digest[:16])
    return r


def manifest_gate(manifest: Path | None, pinned: str | None, root: Path = ROOT) -> Result:
    """G-04: the source manifest is pinned, well formed, non-empty, matches the running tree
    and lists every Phase B surface file present in it."""

    r = Result("G-04", "Source manifest pinned, complete and matching the tree", REQUIRED)
    if manifest is None or not manifest.is_file():
        return r.mark(NOT_RUN, "no source manifest supplied")
    data = manifest.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    r.evidence.append(f"manifest sha256 {actual}")
    r.check("manifest hash pinned and equal (--manifest-sha256)",
            bool(pinned) and pinned == actual, f"pinned={str(pinned)[:12]} actual={actual[:12]}")
    entries: dict[str, str] = {}
    malformed: list[str] = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (\S.*)", line)
        rel = match.group(2) if match else ""
        if (match is None or rel in entries or rel.startswith("/") or "\\" in rel
                or ".." in Path(rel).parts):
            malformed.append(line[:80])
            continue
        entries[rel] = match.group(1)
    r.check("manifest well formed: '<sha256>  <relative path>', no duplicates", not malformed,
            "; ".join(malformed[:3]))
    r.check("manifest lists at least one file", bool(entries), f"{len(entries)} files")
    bad = [rel for rel, digest in entries.items()
           if not (root / rel).is_file()
           or hashlib.sha256((root / rel).read_bytes()).hexdigest() != digest]
    r.check("every listed file exists and matches its hash", not bad, ", ".join(bad[:5]))
    surface = sorted({p.relative_to(root).as_posix() for pattern in PHASE_B_SURFACE
                      for p in root.glob(pattern) if p.is_file()})
    unlisted = [rel for rel in surface if rel not in entries]
    r.check("every Phase B surface file present in the tree is listed", bool(surface)
            and not unlisted, ", ".join(unlisted[:5]) or f"{len(surface)} surface files")
    return r


# =========================================================================== services
@dataclass(frozen=True)
class Services:
    pg_host: str
    pg_port: int
    pg_user: str
    pg_maintenance_db: str
    pg_password: str = field(repr=False)
    redis_host: str
    redis_port: int


def services_from_env(environ: dict[str, str] | None = None) -> tuple[Services | None, list[str]]:
    env = os.environ if environ is None else environ
    missing = []
    if not env.get("BE2_TEST_PG_HOST"):
        missing.append("BE2_TEST_PG_HOST not set: PostgreSQL NOT_RUN")
    secret_path = env.get("BE2_TEST_PG_PASSWORD_FILE")
    if not secret_path or not Path(secret_path).is_file():
        missing.append("BE2_TEST_PG_PASSWORD_FILE missing or unreadable: PostgreSQL NOT_RUN")
    if not env.get("BE2_TEST_REDIS_HOST"):
        missing.append("BE2_TEST_REDIS_HOST not set: Redis/RQ NOT_RUN")
    if missing:
        return None, missing
    return Services(
        pg_host=env["BE2_TEST_PG_HOST"],
        pg_port=int(env.get("BE2_TEST_PG_PORT", "5432")),
        pg_user=env.get("BE2_TEST_PG_USER", "be2_test"),
        pg_maintenance_db=env.get("BE2_TEST_PG_MAINTENANCE_DB", "postgres"),
        pg_password=Path(secret_path or "").read_text(encoding="utf-8").strip(),
        redis_host=env["BE2_TEST_REDIS_HOST"],
        redis_port=int(env.get("BE2_TEST_REDIS_PORT", "6379")),
    ), []


class UuidIds:
    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"


class DurableEnvironment:
    """Disposable PostgreSQL databases (one migrated template, one clone per harness) and
    isolated RQ queues; everything created is dropped/deleted on exit."""

    def __init__(self, services: Services) -> None:
        import psycopg
        from redis import Redis
        from sketch2life.infrastructure.ai_jobs.worker_capability import CapabilityKey

        self.services = services
        self._psycopg = psycopg
        self.redis = Redis(host=services.redis_host, port=services.redis_port,
                           socket_connect_timeout=2, socket_timeout=5)
        self.key = CapabilityKey("b6_run", os.urandom(32))  # one ephemeral key per run
        self.template: str | None = None
        self.databases: list[str] = []
        self.versions: dict[str, str] = {}

    def _admin(self) -> Any:
        s = self.services
        return self._psycopg.connect(host=s.pg_host, port=s.pg_port, user=s.pg_user,
                                     password=s.pg_password, dbname=s.pg_maintenance_db,
                                     connect_timeout=10, autocommit=True)

    def url(self, database: str) -> Any:
        from sqlalchemy.engine import URL

        s = self.services
        return URL.create("postgresql+psycopg", username=s.pg_user, password=s.pg_password,
                          host=s.pg_host, port=s.pg_port, database=database)

    def prepare(self) -> None:
        with self._admin() as admin:
            row = admin.execute("SHOW server_version").fetchone()
        if row is None:
            raise OSError("PostgreSQL did not report a server version")
        version = str(row[0])
        self.versions["postgresql_server"] = version
        if not version.startswith("17."):
            raise OSError(f"PostgreSQL 17 required, server reports {version}")
        server: Any = self.redis.info("server")
        self.versions["redis_server"] = str(server["redis_version"])
        self.template = self._create()
        self._migrate(self.template)
        with self._admin() as admin:  # alembic uses NullPool; make cloning safe regardless
            admin.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                          "WHERE datname = %s AND pid <> pg_backend_pid()", (self.template,))

    def _create(self, template: str | None = None) -> str:
        name = f"be2_b2_{uuid.uuid4().hex[:16]}"  # owner-fixture DDL accepts only this shape
        with self._admin() as admin:
            suffix = f' TEMPLATE "{template}"' if template else ""
            admin.execute(f'CREATE DATABASE "{name}"{suffix}')
        self.databases.append(name)
        return name

    def _migrate(self, database: str) -> None:
        from alembic import command
        from alembic.config import Config
        from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
        from sketch2life.infrastructure.config.settings import get_core_database_settings
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        url = self.url(database)
        previous = os.environ.get("SKETCH2LIFE_DATABASE_URL")
        os.environ["SKETCH2LIFE_DATABASE_URL"] = url.render_as_string(hide_password=False)
        get_core_database_settings.cache_clear()
        try:
            cfg = Config(str(BACKEND / "alembic.ini"))
            cfg.set_main_option("script_location", str(BACKEND / "alembic"))
            command.upgrade(cfg, "ai_jobs@head")
        finally:
            if previous is None:
                os.environ.pop("SKETCH2LIFE_DATABASE_URL", None)
            else:
                os.environ["SKETCH2LIFE_DATABASE_URL"] = previous
            get_core_database_settings.cache_clear()
            _reenable_loggers()
        engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
        try:
            with engine.begin() as connection:
                fx.create_fixture_schema(connection)
            owner = fx.OwnerFixture(engine)
            for principal in (TEACHER, TEACHER_2, ADMIN, OUTSIDER):
                owner.set(fx.grant_scope(principal.organization_id, principal.principal_id),
                          {"actions": ALL_ACTIONS})
            owner.set(fx.grant_scope(DEVICE.organization_id, DEVICE.principal_id),
                      {"actions": [str(AuthorizationAction.READ_JOB)]})
        finally:
            engine.dispose()

    @contextlib.contextmanager
    def harness(self) -> Iterator[DurableHarness]:
        assert self.template is not None
        database = self._create(self.template)
        h: DurableHarness | None = None
        try:
            h = DurableHarness(self, database)
            yield h
        finally:
            if h is not None:
                h.close()
            self._drop(database)

    def _drop(self, database: str) -> None:
        with contextlib.suppress(Exception), self._admin() as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
        if database in self.databases:
            self.databases.remove(database)

    def close(self) -> None:
        for database in list(self.databases):
            self._drop(database)
        with contextlib.suppress(Exception):
            self.redis.close()


def _reenable_loggers() -> None:
    """Alembic's fileConfig disables existing loggers; keep the runner's records flowing."""

    for logger in logging.root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.disabled = False


# ============================================================================ harness
class DurableHarness:
    """One disposable database + one isolated RQ queue; the Phase A harness surface on the
    real SQL adapter with HMAC capabilities and the ASSUMED_CONTRACT owner fixture."""

    def __init__(self, env: DurableEnvironment, database: str) -> None:
        from sketch2life.infrastructure.ai_jobs.rq_queue import RqDispatchQueue
        from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
        from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository
        from sketch2life.infrastructure.ai_jobs.worker_capability import (
            HmacCapabilityIssuer,
            HmacCapabilityVerifier,
        )
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        self.fx = fx
        self.env = env
        self.engine = create_engine(env.url(database), poolclass=NullPool, hide_parameters=True)
        self.owner = fx.OwnerFixture(self.engine)
        self.clock = FakeClock(FIXTURE_START)
        self.queue = RqDispatchQueue(env.redis, f"be2_b6_{uuid.uuid4().hex[:16]}")
        self.audit = fx.FixtureAuditSink(self.engine)
        self.issuer = HmacCapabilityIssuer(env.key)
        self.repository = SqlAiJobRepository(self.engine, lambda c: fx.FixtureFenceHold(c))
        self.deps = AiJobDependencies(
            repository=self.repository,
            authorization=fx.FixtureAuthorization(self.owner),
            eligibility=fx.FixtureEligibility(self.owner),
            worker_capability=HmacCapabilityVerifier(env.key, self.clock),
            clock=self.clock,
            ids=UuidIds(),
            artifacts=fx.FixtureArtifacts(self.owner),
            audit=self.audit,
            queue=self.queue,
            capability_issuer=self.issuer,
        )
        self.service = AiJobService(self.deps)
        self.last_envelope: Any = None
        self.provider_runs: dict[str, int] = {}

    def with_ports(self, **changes: Any) -> AiJobService:
        values = {name: getattr(self.deps, name) for name in self.deps.__dataclass_fields__}
        values.update(changes)
        return AiJobService(AiJobDependencies(**values))

    # owner state -----------------------------------------------------------------------
    def set_eligibility(self, request_id: str, *, eligible: bool = True,
                        reason: str | None = None, context: int | None = None,
                        organization_id: str = ORG) -> None:
        payload: dict[str, Any] = {"eligible": eligible}
        if reason is not None:
            payload["reason_code"] = reason
        if context is not None:
            payload["context_revision"] = context
        self.owner.change(self.fx.eligibility_scope(organization_id, request_id), payload,
                          notice_id=None)

    def revoke_grant(self, principal: Principal) -> None:
        self.owner.change(self.fx.grant_scope(principal.organization_id, principal.principal_id),
                          {"actions": []}, notice_id=None)

    def _ensure_eligible(self, organization_id: str, request_id: str) -> None:
        scope = self.fx.eligibility_scope(organization_id, request_id)
        if self.owner.read(scope) is None:
            self.owner.set(scope, {"eligible": True})

    # commands --------------------------------------------------------------------------
    def create(
        self,
        principal: Principal = TEACHER,
        *,
        key: str = "idem_fx_001",
        ref: RequestRef | None = None,
        target: str = TARGET,
        session_id: str | None = SESSION,
        subjects: tuple[str, ...] = (SUBJECT,),
    ) -> CreateJobCommand:
        ref = ref or request_ref()
        self._ensure_eligible(principal.organization_id, ref.request_id)
        return CreateJobCommand(principal, key, JOB_TYPE, target, "purpose_fx_ai_assistance",
                                session_id, subjects, ref, "corr_fx_001")

    def next_message(self) -> Any:
        from sketch2life.infrastructure.ai_jobs.rq_queue import pop_envelope

        self.service.dispatch_outbox()
        envelope = pop_envelope(self.queue.queue)  # fixture receiver over real Redis
        if envelope is None:
            raise AssertionError("no dispatch message available")
        self.last_envelope = envelope
        return envelope.message

    def drain(self) -> list[Any]:
        from sketch2life.infrastructure.ai_jobs.rq_queue import pop_envelope

        found = []
        while (envelope := pop_envelope(self.queue.queue)) is not None:
            found.append(envelope)
        return found

    def start_next(self) -> Any:
        message = self.next_message()
        started = self.service.start_attempt(self.last_envelope.capability, message.job_id,
                                             message.attempt_id)
        if not started.started:
            raise AssertionError(f"attempt did not start: {started.reason_code}")
        return message

    def capability(self, job_id: str, attempt_id: str | None = None) -> str:
        if attempt_id is None:
            attempt_id = self.job(job_id).active_attempt.attempt_id
        return self.issuer.issue(job_id, attempt_id, self.clock.now())

    # artifacts/claims ------------------------------------------------------------------
    def put_artifact(self, organization_id: str, body: bytes, *, job_id: str | None = None,
                     attempt_id: str | None = None) -> OutputRef:
        digest = hashlib.sha256(body).hexdigest()
        ref = f"artifact_b6_{uuid.uuid4().hex[:20]}"
        payload: dict[str, Any] = {"sha256": digest, "organization_id": organization_id}
        if job_id is not None:
            payload |= {"producer_job_id": job_id, "producer_attempt_id": attempt_id}
        self.owner.set(self.fx.artifact_scope(ref), payload)
        return OutputRef(ref, digest)

    def success_claim(self, message: Any, *, body: bytes = b"synthetic-output",
                      moderation: Moderation = Moderation.PASSED) -> CompletionClaim:
        output = self.put_artifact(ORG, body + message.attempt_id.encode(),
                                   job_id=message.job_id, attempt_id=message.attempt_id)
        pinned = message.request_ref
        return CompletionClaim(message.job_id, message.attempt_id, pinned.request_revision,
                               pinned.input_hash, pinned.context_revision, OutcomeKind.SUCCESS,
                               outputs=(output,), moderation=moderation)

    def failure_claim(self, message: Any, *, code: Any = "PROVIDER_UNAVAILABLE",
                      retryable: bool = True, diagnostic: str | None = None) -> CompletionClaim:
        pinned = message.request_ref
        return CompletionClaim(message.job_id, message.attempt_id, pinned.request_revision,
                               pinned.input_hash, pinned.context_revision, OutcomeKind.FAILURE,
                               failure_code=code, retryable=retryable, diagnostic=diagnostic)

    # durable readback --------------------------------------------------------------------
    def job(self, job_id: str) -> AiJob:
        with self.repository.transaction() as tx:
            found = tx.get_job(job_id)
        assert found is not None
        return found

    def quarantined(self, artifact_ref: str) -> str | None:
        found = self.owner.read(self.fx.artifact_scope(artifact_ref))
        return None if found is None else found[0].get("quarantine_reason")

    def counts(self) -> dict[str, int]:
        from sketch2life.infrastructure.ai_jobs.sql import tables as t
        from sqlalchemy import func, select

        with self.engine.connect() as connection:
            result = {
                name: int(connection.execute(select(func.count()).select_from(table)).scalar_one())
                for name, table in (("job", t.job), ("attempt", t.attempt),
                                    ("semantic_request", t.semantic_request),
                                    ("command_receipt", t.command_receipt),
                                    ("completion_receipt", t.completion_receipt))
            }
            result["pending_dispatch"] = int(connection.execute(
                select(func.count()).select_from(t.outbox).where(
                    t.outbox.c.kind == "dispatch", t.outbox.c.delivered_at.is_(None))
            ).scalar_one())
        return result

    def audit_intents(self) -> list[str]:
        """Event types of the durable audit intents (outbox), in no particular order."""

        from sketch2life.infrastructure.ai_jobs.sql import tables as t
        from sqlalchemy import select

        with self.engine.connect() as connection:
            rows = connection.execute(
                select(t.outbox.c.payload).where(t.outbox.c.kind == "audit")).scalars()
            return [row["event_type"] for row in rows]

    def stored_text(self) -> str:
        from sketch2life.infrastructure.ai_jobs.sql import tables as t
        from sqlalchemy import select

        tables = [*t.AI_JOBS_METADATA.sorted_tables, self.fx.audit_applied,
                  self.fx.quarantine_applied, self.fx.decision]
        with self.engine.connect() as connection:
            return "\n".join(repr(row) for table in tables
                             for row in connection.execute(select(table)).all())

    def close(self) -> None:
        from rq.job import Job

        with contextlib.suppress(Exception):
            rq = self.queue.queue
            for registry in (rq.started_job_registry, rq.failed_job_registry,
                             rq.finished_job_registry):
                for job_id in registry.get_job_ids():
                    with contextlib.suppress(Exception):
                        Job.fetch(job_id, connection=rq.connection).delete()
            rq.delete(delete_jobs=True)
            for key in rq.connection.scan_iter(match=f"*{rq.name}*"):
                rq.connection.delete(key)
        self.engine.dispose()


def _code(fn: Callable[[], object]) -> str | None:
    try:
        fn()
    except AiJobError as exc:
        return exc.code
    return None


# ======================================================================= A-scenarios
Scenario = Callable[[DurableEnvironment, Result], None]


def a01_provenance(env: DurableEnvironment, r: Result, manifest: Result) -> None:
    origin = Path(sketch2life.__file__).resolve()
    r.check("sketch2life imported from this tree (no editable install elsewhere)",
            origin.is_relative_to(BACKEND_SRC.resolve()), origin.as_posix().split("/backend/")[-1])
    r.check("PostgreSQL 17 disposable databases",
            env.versions.get("postgresql_server", "").startswith("17."),
            env.versions.get("postgresql_server", ""))
    r.check("real Redis server reachable", bool(env.versions.get("redis_server")),
            env.versions.get("redis_server", ""))
    from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx

    with env.harness() as h:
        with h.repository.transaction() as tx:
            fence = tx._owner_fences
        r.check("owner fence port is the labelled ASSUMED_CONTRACT fixture",
                isinstance(fence, fx.FixtureFenceHold) and fence.label == fx.ASSUMED_CONTRACT,
                OWNER_FENCE_LABEL)
    r.check("source manifest gate G-04 PASS (pinned, complete, matching the tree)",
            manifest.status == PASS, manifest.reason or manifest.status)


def a03_semantic_duplicate(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        provider = FakeProvider(lambda m: h.success_claim(m))
        first = h.service.create_job(h.create(key="k1"))
        replay = h.service.create_job(h.create(key="k1"))
        dedup = h.service.create_job(h.create(key="k2"))
        other = h.service.create_job(h.create(TEACHER_2, key="k1"))
        from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker

        h.service.dispatch_outbox()
        for envelope in h.drain():
            DispatchWorker(h.service, provider).handle(envelope)
        counts = h.counts()
        r.check("same key + same payload replays original receipt", replay.replayed
                and replay.job_id == first.job_id and replay.job_revision == first.job_revision)
        r.check("new key + same semantic request resolves to the same job",
                dedup.job_id == first.job_id and dedup.outcome == "deduplicated")
        r.check("other principal same key text = own scope, deduplicated, not replayed",
                other.job_id == first.job_id and not other.replayed)
        r.check("one job, one attempt, one semantic row (SQL)",
                (counts["job"], counts["attempt"], counts["semantic_request"]) == (1, 1, 1),
                str(counts))
        r.check("three immutable command receipts", counts["command_receipt"] == 3)
        r.check("semantic cost charged once (provider calls)",
                dict(provider.calls) == {first.job_id: 1}, str(dict(provider.calls)))
        r.check("job settled through the real queue", h.job(first.job_id).state
                is JobState.SUCCEEDED)
    with env.harness() as h:
        base = h.service.create_job(h.create(key="s1")).job_id
        for label, kwargs in {"target": {"target": "target_fx_other"},
                              "session": {"session_id": "session_fx_other"},
                              "subjects": {"subjects": ("child_fx_other",)}}.items():
            scoped = h.service.create_job(h.create(key=f"s_{label}", **kwargs))  # type: ignore[arg-type]
            r.check(f"R02 same request, different {label} -> separate job",
                    scoped.job_id != base and scoped.outcome == "created")


def a04_key_conflict(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        first = h.service.create_job(h.create(key="k1"))
        code = _code(lambda: h.service.create_job(h.create(key="k1", ref=request_ref("req_x"))))
        r.check("same key different payload -> IDEMPOTENCY_PAYLOAD_MISMATCH",
                code == "IDEMPOTENCY_PAYLOAD_MISMATCH", str(code))
        job = h.job(first.job_id)
        r.check("original job unchanged", job.job_revision == 1
                and job.request_ref.request_id == "req_fx_001")
        foreign = h.service.create_job(h.create(OUTSIDER, key="k1"))
        r.check("other organization same key/request -> separate job in its own org",
                foreign.job_id != first.job_id
                and h.job(foreign.job_id).organization_id == OTHER_ORG)
        code = _code(lambda: h.service.create_job(h.create(UNGRANTED, key="k1")))
        r.check("ungranted principal cannot use key to reach job", code == "FORBIDDEN_SCOPE",
                str(code))


def a05_redelivery(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        cap = h.capability(job_id)
        again = h.service.start_attempt(cap, job_id, message.attempt_id)
        r.check("queue redelivery does not start another attempt",
                not again.started and again.reason_code == "DUPLICATE_DELIVERY")
        claim = h.success_claim(message)
        first = h.service.accept_completion(cap, claim)
        revision = h.job(job_id).job_revision
        second = h.service.accept_completion(cap, claim)
        r.check("duplicate completion returns the stored receipt",
                first.receipt_id == second.receipt_id and first.fingerprint == second.fingerprint)
        r.check("one effect: revision, attempts and receipts unchanged",
                h.job(job_id).job_revision == revision and len(h.job(job_id).attempts) == 1
                and h.counts()["completion_receipt"] == 1)


def a06_cas(env: DurableEnvironment, r: Result) -> None:
    from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository

    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        cap = h.capability(job_id)
        claims = [h.success_claim(message, body=b"out-a"), h.success_claim(message, body=b"out-b")]
        outcomes: list[str] = []
        barrier = threading.Barrier(2)

        def run(claim: CompletionClaim) -> None:
            barrier.wait()
            try:
                outcomes.append(str(h.service.accept_completion(cap, claim).disposition))
            except AiJobError as exc:
                outcomes.append(exc.code)

        threads = [threading.Thread(target=run, args=(c,)) for c in claims]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        r.check("row-locked concurrency: one winner, one COMPLETION_CONFLICT",
                sorted(outcomes) == ["COMPLETION_CONFLICT", "accepted"], str(sorted(outcomes)))
        r.check("conflict recorded as a durable incident intent",
                "job.completion_conflict" in h.audit_intents())
        job = h.job(job_id)
        try:
            with h.repository.transaction() as tx:
                tx.cas_job(expected_revision=job.job_revision - 1, job=job)
            r.check("stale CAS rejected", False)
        except JobRevisionConflict:
            r.check("stale CAS rejected", True)

        def fail(uow: Any) -> None:
            if uow.writes:
                raise RuntimeError("injected commit failure")

        failing = h.with_ports(repository=SqlAiJobRepository(
            h.engine, lambda c: h.fx.FixtureFenceHold(c), before_commit=fail))
        before = h.counts()
        with contextlib.suppress(RuntimeError):
            failing.create_job(h.create(key="k_fail", ref=request_ref("req_fail")))
        r.check("failed commit leaves no partial job/receipt/outbox", h.counts() == before,
                str(h.counts()))


def a07_bounded_retry(env: DurableEnvironment, r: Result) -> None:
    from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker

    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        provider = FakeProvider(lambda m: h.failure_claim(m, code="PROVIDER_TIMEOUT"))
        loops = 0
        while loops < 20:
            loops += 1
            h.service.dispatch_outbox()
            envelopes = h.drain()
            for envelope in envelopes:
                DispatchWorker(h.service, provider).handle(envelope)
            if not envelopes:
                h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
                if not h.service.run_due_retries():
                    break
        job = h.job(job_id)
        r.check("ends failed_exhausted", job.state is JobState.FAILED_EXHAUSTED, str(job.state))
        r.check("attempts bounded by named policy",
                len(job.attempts) == FIXTURE_RETRY_POLICY.max_attempts, str(len(job.attempts)))
        r.check("no infinite loop", loops < 20, str(loops))
    with env.harness() as h:
        jid = h.service.create_job(h.create()).job_id
        h.start_next()
        h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
        expired = h.service.expire_overdue_attempts()
        job = h.job(jid)
        r.check("attempt timeout -> failed_retryable PROVIDER_TIMEOUT with backoff",
                expired == (jid,) and job.state is JobState.FAILED_RETRYABLE
                and job.failure is not None and job.failure.code == "PROVIDER_TIMEOUT"
                and job.retry_not_before is not None)


def a08_progress(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        view = h.service.get_job_status(TEACHER, job_id).view or {}
        r.check("unknown progress has value null",
                view["progress"] == {"kind": "unknown", "value": None, "stage_label": None})
        h.service.report_progress(h.capability(job_id), job_id, message.attempt_id,
                                  JobProgress(ProgressKind.PERCENTAGE, 37.5))
        view = h.service.get_job_status(TEACHER, job_id).view or {}
        r.check("truthful percentage persisted and projected",
                view["progress"]["value"] == 37.5)  # type: ignore[index]
    for label, kwargs in {
        "unknown with 0": {"kind": ProgressKind.UNKNOWN, "value": 0.0},
        "percentage 101": {"kind": ProgressKind.PERCENTAGE, "value": 101.0},
        "percentage nan": {"kind": ProgressKind.PERCENTAGE, "value": float("nan")},
        "stages without label": {"kind": ProgressKind.STAGES},
    }.items():
        try:
            JobProgress(**kwargs)  # type: ignore[arg-type]
            r.check(f"reject {label} (domain invariant)", False)
        except InvalidProgress:
            r.check(f"reject {label} (domain invariant)", True)


def a09_scope(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        for name, principal in (("other org", OUTSIDER), ("ungranted teacher", UNGRANTED)):
            code = _code(partial(h.service.get_job_status, principal, job_id))
            r.check(f"{name} -> RESOURCE_NOT_FOUND (existence concealed)",
                    code == "RESOURCE_NOT_FOUND", str(code))
        missing = _code(lambda: h.service.get_job_status(TEACHER, "job_b6_missing"))
        r.check("missing and forbidden look identical", missing == "RESOURCE_NOT_FOUND")
        r.check("device grant reads its projection", h.service.get_job_status(DEVICE, job_id)
                .view is not None)
        h.revoke_grant(DEVICE)
        code = _code(lambda: h.service.get_job_status(DEVICE, job_id))
        r.check("revoked device grant denied", code == "RESOURCE_NOT_FOUND", str(code))


def a10_cache_after_revoke(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        h.service.accept_completion(h.capability(job_id), h.success_claim(message))
        first = h.service.get_job_status(TEACHER, job_id)
        cached = h.service.get_job_status(TEACHER, job_id, first.etag)
        r.check("authorized unchanged poll -> 304", cached.not_modified)
        h.set_eligibility("req_fx_001", eligible=False, reason="CONSENT_REVOKED")
        after = h.service.get_job_status(TEACHER, job_id, first.etag)
        r.check("consent revoke changes ETag; no 304 with old refs",
                not after.not_modified and after.etag != first.etag)
        r.check("refs withheld after revoke", (after.view or {}).get("result_refs") == [])
        h.revoke_grant(TEACHER)
        code = _code(lambda: h.service.get_job_status(TEACHER, job_id, first.etag))
        r.check("revoked grant gets 404 before cache/304", code == "RESOURCE_NOT_FOUND", str(code))
    with env.harness() as h:
        queued = h.service.create_job(h.create()).job_id
        early = h.service.get_job_status(TEACHER, queued)
        h.clock.advance(seconds=60)
        late = h.service.get_job_status(TEACHER, queued, early.etag)
        r.check("R10 changed backoff hint is not hidden behind 304",
                not late.not_modified and (late.view or {}).get("poll_after_ms") == 10000
                and (early.view or {}).get("poll_after_ms") == 2000)


def a11_stale_completion(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        first = h.start_next()
        cap = h.capability(job_id)
        late_claim = h.success_claim(first)
        h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
        h.service.expire_overdue_attempts()
        h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
        h.service.run_due_retries()
        second = h.start_next()
        receipt = h.service.accept_completion(cap, late_claim)
        job = h.job(job_id)
        r.check("superseded attempt-1 success -> stale ATTEMPT_SUPERSEDED",
                str(receipt.disposition) == "stale" and receipt.reason_code == "ATTEMPT_SUPERSEDED")
        r.check("attempt 2 still running, not overwritten",
                job.state is JobState.RUNNING
                and job.active_attempt.attempt_id == second.attempt_id)
        r.check("superseded output quarantined (owned lineage)",
                h.quarantined(late_claim.outputs[0].artifact_ref) == "ATTEMPT_SUPERSEDED")
        cap = h.capability(job_id)
        tampered = replace(h.success_claim(second), input_hash="0" * 64)
        receipt = h.service.accept_completion(cap, tampered)
        r.check("wrong input hash -> rejected INPUT_MISMATCH",
                str(receipt.disposition) == "rejected" and receipt.reason_code == "INPUT_MISMATCH")
        r.check("mismatch durable as an incident intent",
                "job.completion_input_mismatch" in h.audit_intents())
        r.check("job still running after mismatch", h.job(job_id).state is JobState.RUNNING)
        corrected = h.service.accept_completion(cap, h.success_claim(second))
        r.check("R03 rejected mismatch does not block corrected completion",
                corrected.disposition.value == "accepted" and corrected.authoritative)
    with env.harness() as h:
        jid = h.service.create_job(h.create()).job_id
        msg = h.next_message()
        cap = h.capability(jid)
        claim = h.success_claim(msg)
        early = h.service.accept_completion(cap, claim)
        h.service.start_attempt(cap, jid, msg.attempt_id)
        later = h.service.accept_completion(cap, claim)
        r.check("R03 completion before start is non-authoritative; same claim lands after start",
                early.reason_code == "INVALID_STATE" and not early.authoritative
                and later.disposition.value == "accepted")
        r.check("R03a accepted refs after temporary rejection are not quarantined",
                h.quarantined(claim.outputs[0].artifact_ref) is None)
        code = _code(lambda: h.service.accept_completion(
            cap, h.success_claim(msg, body=b"other-output")))
        r.check("genuine conflict after accepted completion still raised",
                code == "COMPLETION_CONFLICT", str(code))


def a12_context_change(env: DurableEnvironment, r: Result) -> None:
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        h.set_eligibility("req_fx_001", context=2)
        receipt = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
        job = h.job(job_id)
        view = h.service.get_job_status(TEACHER, job_id).view or {}
        r.check("result disposition stale STALE_CONTEXT", receipt.reason_code == "STALE_CONTEXT"
                and job.result_disposition is not None and job.result_disposition.value == "stale")
        r.check("source lineage kept (pinned context 1)",
                job.request_ref.context_revision == 1
                and "superseded by 2" in (job.lineage_note or ""))
        r.check("stale result not projected", view.get("result_refs") == [])


def a13_cancel(env: DurableEnvironment, r: Result) -> None:
    for state in ("queued", "running", "failed_retryable"):
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            message = None
            failure = None
            if state != "queued":
                message = h.start_next()
            if state == "failed_retryable":
                assert message is not None
                failure = h.failure_claim(message)
                h.service.accept_completion(h.capability(job_id), failure)
            before = h.job(job_id)
            h.service.cancel_job(CancelJobCommand(TEACHER, "cancel_1", job_id, before.job_revision))
            job = h.job(job_id)
            r.check(f"cancel from {state}", job.state is JobState.CANCELLED
                    and job.retry_not_before is None)
            h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
            r.check(f"{state}: scheduled retry invalidated", h.service.run_due_retries() == ()
                    and not h.service.retry_job(job_id, before.active_attempt.attempt_number))
            if message is not None:
                late = failure or h.success_claim(message)
                receipt = h.service.accept_completion(h.capability(job_id), late)
                expected = "PROVIDER_UNAVAILABLE" if failure else "JOB_CANCELLED"
                job = h.job(job_id)
                r.check(f"{state}: late/duplicate completion cannot resurrect",
                        receipt.reason_code == expected and job.state is JobState.CANCELLED
                        and len(job.attempts) == len(before.attempts))
            r.check(f"{state}: outbox has no new dispatch", h.service.dispatch_outbox() == 0)
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        code = _code(lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c", job_id, None)))
        r.check("cancel without If-Match -> PRECONDITION_REQUIRED", code == "PRECONDITION_REQUIRED")
        code = _code(lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c2", job_id, 9)))
        r.check("cancel with stale revision -> STALE_AGGREGATE", code == "STALE_AGGREGATE")


ELIGIBILITY_CASES = {
    "consent revoke": "CONSENT_REVOKED",
    "session end": "SESSION_ENDED",
    "content recall": "CONTENT_RECALLED",
    "source expiry": "SOURCE_EXPIRED",
    "kill switch": "KILL_SWITCH",
}


def a14_eligibility(env: DurableEnvironment, r: Result) -> None:
    for name, reason in ELIGIBILITY_CASES.items():
        with env.harness() as h:
            h.set_eligibility("req_fx_001", eligible=False, reason=reason)
            code = _code(partial(h.service.create_job, h.create()))
            r.check(f"{name}: create denied without reserving a receipt",
                    code is not None and h.counts()["command_receipt"] == 0, str(code))
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            h.service.dispatch_outbox()
            envelope = h.drain()[0]
            h.set_eligibility("req_fx_001", eligible=False, reason=reason)
            started = h.service.start_attempt(envelope.capability, job_id,
                                              envelope.message.attempt_id)
            r.check(f"{name}: start denied, job cancelled, no provider call",
                    not started.started and h.job(job_id).state is JobState.CANCELLED)
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            message = h.start_next()
            h.set_eligibility("req_fx_001", eligible=False, reason=reason)
            claim = h.success_claim(message)
            receipt = h.service.accept_completion(h.capability(job_id), claim)
            r.check(f"{name}: completion rejected and owned output quarantined",
                    str(receipt.disposition) == "rejected"
                    and h.job(job_id).state is JobState.CANCELLED
                    and h.quarantined(claim.outputs[0].artifact_ref) == reason)
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            message = h.start_next()
            h.service.accept_completion(h.capability(job_id), h.failure_claim(message))
            h.set_eligibility("req_fx_001", eligible=False, reason=reason)
            h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
            r.check(f"{name}: retry denied -> cancelled", h.service.run_due_retries() == ()
                    and h.job(job_id).state is JobState.CANCELLED)
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        notice = CancellationNotice("notice_1", ORG, "KILL_SWITCH", job_type=JOB_TYPE)
        r.check("kill-switch notice cancels pending work",
                h.service.apply_cancellation_notice(notice) == (job_id,))
        r.check("notice replay is a no-op", h.service.apply_cancellation_notice(notice) == ())
    for name, reason in ELIGIBILITY_CASES.items():
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            h.set_eligibility("req_fx_001", eligible=False, reason=reason)
            sent = h.service.dispatch_outbox()
            r.check(f"R09 {name}: dispatch rechecks eligibility, nothing enqueued",
                    sent == 0 and not h.drain() and h.job(job_id).state is JobState.CANCELLED
                    and h.counts()["pending_dispatch"] == 0)


def a15_unsafe_malformed(env: DurableEnvironment, r: Result) -> None:
    from sketch2life.contracts.schemas.ai_jobs import AsyncJobViewV1

    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        claim = h.success_claim(message, moderation=Moderation.UNSAFE)
        receipt = h.service.accept_completion(h.capability(job_id), claim)
        view = h.service.get_job_status(TEACHER, job_id).view or {}
        r.check("unsafe -> blocked_unsafe, rejected, quarantined",
                view["state"] == "blocked_unsafe" and receipt.reason_code == "UNSAFE_CONTENT"
                and h.quarantined(claim.outputs[0].artifact_ref) == "UNSAFE_CONTENT"
                and view["result_refs"] == [])
    leak = "provider said: token=sk-fixture-secret at https://provider.invalid/raw"
    for label in ("no outputs", "unknown ref", "hash mismatch", "provider failure diagnostic"):
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            message = h.start_next()
            good = h.success_claim(message)
            out = good.outputs[0]
            claim = {
                "no outputs": replace(good, outputs=()),
                "unknown ref": replace(good, outputs=(OutputRef("artifact_missing", out.sha256),)),
                "hash mismatch": replace(good, outputs=(OutputRef(out.artifact_ref, "f" * 64),)),
                "provider failure diagnostic": h.failure_claim(
                    message, code="PROVIDER_ERROR", retryable=False, diagnostic=leak),
            }[label]
            receipt = h.service.accept_completion(h.capability(job_id), claim)
            job = h.job(job_id)
            if label == "provider failure diagnostic":
                dumped = json.dumps(h.service.get_job_status(TEACHER, job_id).view, default=str)
                stored = h.stored_text()
                r.check("diagnostic absent from view, durable rows and sinks",
                        "sk-fixture-secret" not in dumped + stored
                        and "provider.invalid" not in dumped + stored)
            else:
                r.check(f"malformed ({label}) -> failed_exhausted OUTPUT_MALFORMED, no exposure",
                        job.state is JobState.FAILED_EXHAUSTED
                        and receipt.reason_code == "OUTPUT_MALFORMED" and job.result_refs == ())
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        foreign = h.put_artifact(OTHER_ORG, b"foreign")
        sibling = h.put_artifact(ORG, b"same-org-no-lineage")
        for label, claim in {
            "input mismatch": replace(h.success_claim(message), input_hash="0" * 64,
                                      outputs=(foreign, sibling)),
            "malformed output": replace(h.success_claim(message), outputs=(foreign, sibling)),
        }.items():
            h.service.accept_completion(h.capability(job_id), claim)
            r.check(f"R01 {label}: foreign/unowned artifacts never quarantined",
                    h.quarantined(foreign.artifact_ref) is None
                    and h.quarantined(sibling.artifact_ref) is None)
    bad_codes: list[Any] = [[], {}, ["token=sk-fixture-secret"]]
    for bad_code in bad_codes:
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            message = h.start_next()
            receipt = h.service.accept_completion(
                h.capability(job_id),
                h.failure_claim(message, code=bad_code, retryable=False))
            later = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
            r.check(f"R04a non-string code {type(bad_code).__name__} -> MALFORMED_CLAIM, "
                    "later valid completion accepted",
                    receipt.reason_code == "MALFORMED_CLAIM" and not receipt.authoritative
                    and later.disposition.value == "accepted"
                    and "sk-fixture-secret" not in h.stored_text())
    for code in ("http 503 from provider", "SOME_VENDOR_CODE", None):
        with env.harness() as h:
            job_id = h.service.create_job(h.create()).job_id
            message = h.start_next()
            h.service.accept_completion(h.capability(job_id),
                                        replace(h.failure_claim(message, retryable=False),
                                                failure_code=code))
            view = h.service.get_job_status(TEACHER, job_id).view or {}
            AsyncJobViewV1.model_validate(view, strict=False)
            failure = view.get("failure")
            r.check(f"R04 provider code {code!r} mapped to PROVIDER_ERROR, poll view valid",
                    isinstance(failure, dict) and failure.get("code") == "PROVIDER_ERROR")


def a16_success_semantics(env: DurableEnvironment, r: Result) -> None:
    from sketch2life.contracts.schemas.ai_jobs import AsyncJobChildViewV1

    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        claim = h.success_claim(message)
        h.service.accept_completion(h.capability(job_id), claim)
        teacher = h.service.get_job_status(TEACHER, job_id).view or {}
        device = h.service.get_job_status(DEVICE, job_id).view or {}
        expected = [{"artifact_ref": claim.outputs[0].artifact_ref,
                     "sha256": claim.outputs[0].sha256}]
        r.check("teacher sees exact refs + hash read back from SQL",
                teacher["result_refs"] == expected)
        r.check("no approval/playback/session-complete fields in DATA-25 view",
                not {"approved", "review_state", "playback_state", "session_complete"}
                & set(teacher))
        r.check("device projection has no refs/request/disposition",
                not {"result_refs", "request_ref", "result_disposition", "attempt_id"}
                & set(device))
        AsyncJobChildViewV1.model_validate(device, strict=False)
        r.check("device projection validates against the child candidate schema", True)


def a17_worker_capability(env: DurableEnvironment, r: Result) -> None:
    from sketch2life.infrastructure.ai_jobs.rq_queue import RedactingSimpleWorker
    from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker, install_worker
    from sketch2life.infrastructure.ai_jobs.worker_capability import (
        CapabilityKey,
        HmacCapabilityIssuer,
    )

    with env.harness() as h:
        # C-R2-A17-01: the outbox dispatches in (available_at, message_id) order, and under one
        # fixed clock a UUID message_id does not follow creation order. The target job is
        # therefore created AND dispatched before the control job exists: the claim can only
        # belong to the target, whatever the message ids are.
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        r.check("dispatched message belongs to the target job", message.job_id == job_id,
                "" if message.job_id == job_id else f"{message.job_id} != {job_id}")
        other = h.service.create_job(h.create(key="k2", ref=request_ref("req_2"))).job_id
        other_capability = h.capability(other)
        r.check("control capability is bound to another job and attempt than the claim",
                other != message.job_id
                and h.job(other).active_attempt.attempt_id != message.attempt_id)
        claim = h.success_claim(message)
        foreign_key = HmacCapabilityIssuer(CapabilityKey("b6_foreign", os.urandom(32)))
        for label, cap in (("missing", ""), ("forged", "wcap.v1.b6_run.e30.AAAA"),
                           ("other job", other_capability),
                           ("other key", foreign_key.issue(job_id, message.attempt_id,
                                                           h.clock.now()))):
            code = _code(partial(h.service.accept_completion, cap, claim))
            r.check(f"{label} capability denied", code == "WORKER_CAPABILITY_INVALID", str(code))
    with env.harness() as h:  # B-10c: real Redis/RQ carrier end to end, token-free state/logs
        job_id = h.service.create_job(h.create()).job_id
        records: list[logging.LogRecord] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        capture = Capture(level=logging.DEBUG)
        logging.root.addHandler(capture)
        previous = logging.root.level
        logging.root.setLevel(logging.DEBUG)
        _reenable_loggers()
        try:
            assert h.service.dispatch_outbox() == 1
            from rq.job import Job

            (rq_job_id,) = h.queue.queue.job_ids
            token = Job.fetch(rq_job_id, connection=h.queue.queue.connection).args[1]
            install_worker(DispatchWorker(h.service, FakeProvider(lambda m: h.success_claim(m))))
            RedactingSimpleWorker([h.queue.queue], connection=h.queue.queue.connection).work(
                burst=True)
        finally:
            install_worker(None)
            logging.root.removeHandler(capture)
            logging.root.setLevel(previous)
        r.check("job completed through RQ worker with the broker-carried capability",
                h.job(job_id).state is JobState.SUCCEEDED)
        r.check("capability absent from SQL rows, receipts, intents and sinks",
                token not in h.stored_text())
        r.check("capability absent from every captured log record field",
                records != [] and all(
                    token not in " ".join(str(v) for v in (rec.getMessage(), vars(rec)))
                    for rec in records))


def a17_http_surface(env: DurableEnvironment, r: Result) -> None:
    try:
        from fastapi.testclient import TestClient
        from sketch2life.interfaces.http.ai_jobs_fixture_app import (
            create_ai_jobs_fixture_app,
            route_surface,
        )
    except Exception as exc:  # noqa: BLE001 - optional dependency boundary
        r.mark(NOT_RUN, f"optional HTTP surface: {type(exc).__name__} importing FastAPI/app")
        return
    with env.harness() as h:
        job_id = h.service.create_job(h.create()).job_id
        app = create_ai_jobs_fixture_app(h.service, {"teacher": TEACHER})
        surface = route_surface(app.routes)
        r.check("fixture app exposes exactly GET CMD-44",
                surface == {("/api/collaboration/v1/jobs/{job_id}", "GET")}, str(sorted(surface)))
        client = TestClient(app)
        path = f"/api/collaboration/v1/jobs/{job_id}"
        ok = client.get(path, headers={"Authorization": "Fixture teacher"})
        r.check("authorized GET on the SQL-backed service returns DATA-25 envelope",
                ok.status_code == 200 and ok.json()["contract_name"] == "AsyncJobView",
                str(ok.status_code))
        for suffix in ("", "/completion"):
            posted = client.post(path + suffix, headers={"Authorization": "Fixture teacher"},
                                 json={})
            r.check(f"POST {suffix or '/'} rejected (no completion route)",
                    posted.status_code in {404, 405}, str(posted.status_code))


DURABLE_SCENARIOS: tuple[tuple[str, str, Scenario], ...] = (
    ("A-03", "Duplicate semantic request", a03_semantic_duplicate),
    ("A-04", "Same key changed payload/scope", a04_key_conflict),
    ("A-05", "Queue redelivery/duplicate completion", a05_redelivery),
    ("A-06", "Concurrent completion CAS / rollback on SQL", a06_cas),
    ("A-07", "Timeout/retry to policy limit", a07_bounded_retry),
    ("A-08", "Progress persisted and projected", a08_progress),
    ("A-09", "Poll outside organization/audience/grant", a09_scope),
    ("A-10", "ETag/cache poll after revoke", a10_cache_after_revoke),
    ("A-11", "Wrong attempt/request/revision/hash completion", a11_stale_completion),
    ("A-12", "Source/context change while running", a12_context_change),
    ("A-13", "Cancel queued/running/backoff/before completion", a13_cancel),
    ("A-14", "Consent/session/recall/expiry/kill-switch", a14_eligibility),
    ("A-15", "Unsafe/malformed output", a15_unsafe_malformed),
    ("A-16", "Success pending review projections", a16_success_semantics),
    ("A-17", "Worker capability on real Redis/RQ (B-10c)", a17_worker_capability),
)

NON_DURABLE: tuple[Result, ...] = (
    Result("A-02", "DATA-25 round-trip/invalid fixtures", CONTRACT_ONLY, NOT_APPLICABLE,
           reason="contract fixtures, no storage semantics; owned by the Phase A fixture runner "
                  "(consumed by B-11)"),
    Result("A-18", "Provider copy discover/cancel/purge", DEFERRED, DEFERRED_STATUS,
           reason="durable ProviderCopyLifecycle belongs to BE2-14; Phase A fake proof only "
                  "(see B-12)"),
    Result("A-19", "DATA-24/ProviderCopyLifecycle/shape candidates", CONTRACT_ONLY,
           NOT_APPLICABLE,
           reason="contract shapes only; owned by the Phase A fixture runner (consumed by B-11)"),
    Result("A-20", "Handoff P1/P2/P4 artefacts", CONTRACT_ONLY, NOT_APPLICABLE,
           reason="documentation handoff; Phase A artefacts in the fixture runner, Phase B "
                  "handoff in B-12 and evidence/notes/PHASE_B_B6_*"),
)


def run_scenarios(env: DurableEnvironment | None, missing: list[str],
                  manifest: Result) -> list[Result]:
    results: list[Result] = []
    a01 = Result("A-01", "Durable runner provenance (source, services, owner-fence label)",
                 REQUIRED)
    if env is None:
        results.append(a01.mark(NOT_RUN, "; ".join(missing)))
    else:
        try:
            a01_provenance(env, a01, manifest)
        except Exception as exc:  # noqa: BLE001 - recorded, never hidden
            a01.check("scenario raised", False, type(exc).__name__)
        results.append(a01)
    results.extend(replace(r, checks=[], evidence=list(r.evidence)) for r in NON_DURABLE)
    for item, title, fn in DURABLE_SCENARIOS:
        r = Result(item, title, REQUIRED)
        if env is None:
            results.append(r.mark(NOT_RUN, "; ".join(missing)))
            continue
        try:
            fn(env, r)
        except Exception as exc:  # noqa: BLE001 - recorded, never hidden
            r.check("scenario raised", False, f"{type(exc).__name__}: {str(exc)[:200]}")
        results.append(r)
    http = Result("A-17-http", "CMD-44 fixture app over the SQL-backed service", OPTIONAL)
    if env is None:
        results.append(http.mark(NOT_RUN, "; ".join(missing)))
    else:
        try:
            a17_http_surface(env, http)
        except Exception as exc:  # noqa: BLE001
            http.check("scenario raised", False, type(exc).__name__)
        results.append(http)
    order = {f"A-{n:02d}": n for n in range(1, 21)}
    return sorted(results, key=lambda r: (order.get(r.item[:4], 99), r.item))


# =============================================================================== main
def _sha(path: Path | None) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None


def _versions() -> dict[str, str]:
    from importlib import metadata

    found = {"python": platform.python_version()}
    for name in ("sqlalchemy", "alembic", "psycopg", "redis", "rq", "pydantic"):
        with contextlib.suppress(metadata.PackageNotFoundError):
            found[name] = metadata.version(name)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--manifest-sha256", help="pinned SHA-256 of the --manifest file")
    parser.add_argument("--junit", type=Path, action="append", default=[],
                        help="JUnit of the B2-B6 pytest run")
    parser.add_argument("--phase-a-junit", type=Path)
    parser.add_argument("--fixture-report", type=Path)
    args = parser.parse_args(argv)

    services, missing = services_from_env()
    env: DurableEnvironment | None = None
    if services is not None:
        try:
            env = DurableEnvironment(services)
            env.prepare()
        except Exception as exc:  # noqa: BLE001 - environment failure is NOT_RUN, not PASS
            missing = [f"durable environment unavailable: {type(exc).__name__}: "
                       f"{str(exc)[:160]}"]
            if env is not None:
                env.close()
            env = None
    manifest = manifest_gate(args.manifest, args.manifest_sha256)
    try:
        scenarios = run_scenarios(env, missing, manifest)
        versions = dict(env.versions) if env else {}
    finally:
        if env is not None:
            env.close()

    outcomes, junit_missing = read_junit(args.junit)
    have_junit = bool(args.junit) and not junit_missing
    phase_a_outcomes, phase_a_missing = read_junit(
        [args.phase_a_junit] if args.phase_a_junit else [])
    b2_b6_collected = suite_inventory(SUITE_B2_B6)
    b2_b6_inventory = b2_b6_collected[0]
    gates = [
        suite_gate("G-01", "B2-B6 JUnit complete: every collected case ran and passed",
                   outcomes, have_junit, b2_b6_collected, "SUITE_B2_B6"),
        suite_gate("G-02", "Phase A JUnit complete: every collected case ran and passed",
                   phase_a_outcomes, bool(args.phase_a_junit) and not phase_a_missing,
                   suite_inventory(SUITE_PHASE_A), "SUITE_PHASE_A"),
        fixture_gate(args.fixture_report),
        manifest,
    ]
    matrix = resolve_matrix(outcomes, have_junit, b2_b6_inventory)
    acceptance = resolve_acceptance(
        outcomes, have_junit, matrix, scenarios,
        (gates[1].status, "; ".join(gates[1].evidence[-1:]) or gates[1].reason),
        (gates[2].status, "; ".join(gates[2].evidence[-1:]) or gates[2].reason),
        b2_b6_inventory,
    )
    everything = [*scenarios, *gates, *matrix, *acceptance]
    code = exit_code(everything)
    report: dict[str, Any] = {
        "runner": RUNNER,
        "runner_version": RUNNER_VERSION,
        "authority": PLAN,
        "owner_fence": OWNER_FENCE_LABEL,
        "source_manifest_sha256": _sha(args.manifest),
        "source_manifest_pinned": args.manifest_sha256,
        "inputs": {
            "junit": [{"name": p.name, "sha256": _sha(p)} for p in args.junit],
            "phase_a_junit": _sha(args.phase_a_junit),
            "fixture_report": _sha(args.fixture_report),
            "junit_cases": len(outcomes),
        },
        "environment": {**_versions(), **versions, "platform": sys.platform},
        "not_run_reasons": missing,
        "summary": {
            "scenarios": summarise(scenarios),
            "gates": summarise(gates),
            "crash_matrix": summarise(matrix),
            "acceptance": summarise(acceptance),
            "overall": summarise(everything),
            "exit_code": code,
        },
        "scenarios": [r.__dict__ for r in scenarios],
        "gates": [r.__dict__ for r in gates],
        "crash_matrix": [r.__dict__ for r in matrix],
        "acceptance": [r.__dict__ for r in acceptance],
        "b12_handoff": list(B12_HANDOFF),
        "limits": [
            "Fake provider only; no claim journal or exactly-once provider execution (plan 7.1).",
            "OwnerFence, audit and artifact sinks are ASSUMED_CONTRACT component fixtures.",
            "Contract-only Phase A items are owned by the Phase A fixture runner.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes((json.dumps(report, indent=2, ensure_ascii=False, default=str)
                             + "\n").encode("utf-8"))
    for r in everything:
        failed = [c["name"] for c in r.checks if not c["ok"]]
        print(f"{r.item:10} {r.status:14} {r.kind:13} {len(r.checks):3} checks  {r.title}"
              + (f"  FAILED: {failed}" if failed else "")
              + (f"  ({r.reason})" if r.reason and r.status != PASS else ""))
    print("DURABLE_SUMMARY " + json.dumps(report["summary"]["overall"])
          + f" exit_code={code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
