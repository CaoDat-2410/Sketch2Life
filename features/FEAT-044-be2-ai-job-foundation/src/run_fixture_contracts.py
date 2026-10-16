"""Standalone offline runner for BE2-01 Phase A fixture contracts (A-01..A-20).

Usage (from any cwd):
    python features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py [--report PATH]
        [--write-fixtures] [--with-http]

Needs only Python 3.12 + pydantic (contracts). No BE1/app/DB/broker/provider SDK/credential.
``--with-http`` additionally drives CMD-44 through the isolated fixture app (needs FastAPI).
Every result is fake/contract semantics only: not durable, not real inference/deletion.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import platform
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
from pathlib import Path
from typing import Any

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
FIXTURES = FEATURE / "fixtures"
sys.path.insert(0, str(BACKEND_SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture_catalog  # noqa: E402
import sketch2life  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from sketch2life.application.ports.ai_jobs import CancellationNotice  # noqa: E402
from sketch2life.application.services.ai_jobs import (  # noqa: E402
    FIXTURE_RETRY_POLICY,
    AiJobError,
    CancelJobCommand,
)
from sketch2life.contracts.schemas.ai_contract_candidates import (  # noqa: E402
    SHAPE_SPECS,
    ExactContentReviewCommandV1,
    ProviderCopyLifecycleReportV1,
    check_shape,
)
from sketch2life.contracts.schemas.ai_jobs import (  # noqa: E402
    AsyncJobChildViewV1,
    AsyncJobViewV1,
)
from sketch2life.domain.ai_jobs.completion import (  # noqa: E402
    CompletionClaim,
    Moderation,
    OutputRef,
)
from sketch2life.domain.ai_jobs.model import (  # noqa: E402
    InvalidProgress,
    JobProgress,
    JobState,
    ProgressKind,
)
from sketch2life.domain.ai_jobs.provider_copy import CopyKind, ProviderCopy  # noqa: E402
from sketch2life.infrastructure.ai_jobs.fakes import FakeProvider  # noqa: E402
from sketch2life.infrastructure.ai_jobs.harness import (  # noqa: E402
    DEVICE,
    ORG,
    OUTSIDER,
    TEACHER,
    TEACHER_2,
    UNGRANTED,
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)

FORBIDDEN_RUNTIME_MODULES = ("sqlalchemy", "psycopg", "redis", "rq", "boto3", "httpx",
                             "torch", "fastapi")


@dataclass
class Result:
    criterion: str
    title: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    not_run: list[str] = field(default_factory=list)
    status: str = "PASS"

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            self.status = "FAIL"


def _error_code(fn: Callable[[], object]) -> str | None:
    try:
        fn()
    except AiJobError as exc:
        return exc.code
    return None


def _state(h: FixtureHarness, job_id: str) -> Any:
    with h.store.transaction() as tx:
        return tx.get_job(job_id)


def a02_data25(r: Result) -> None:
    problems = fixture_catalog.verify_fixtures(FIXTURES)
    r.check("fixture files match deterministic regeneration + manifest", not problems,
            "; ".join(problems))
    for group, model in (("data25", AsyncJobViewV1), ("data25_child", AsyncJobChildViewV1)):
        for path in sorted((FIXTURES / group / "positive").glob("*.json")):
            try:
                model.model_validate_json(path.read_bytes(), strict=True)
                r.check(f"{group} positive {path.stem}", True)
            except ValidationError as exc:
                r.check(f"{group} positive {path.stem}", False, str(exc.errors()[0]["msg"]))
        for path in sorted((FIXTURES / group / "negative").glob("*.json")):
            try:
                model.model_validate_json(path.read_bytes(), strict=True)
                r.check(f"{group} negative {path.stem} rejected", False, "accepted")
            except ValidationError:
                r.check(f"{group} negative {path.stem} rejected", True)


def a03_semantic_duplicate(r: Result) -> None:
    h = build_fixture_harness()
    provider = FakeProvider(lambda m: h.success_claim(m))
    first = h.service.create_job(h.create(key="k1"))
    replay = h.service.create_job(h.create(key="k1"))
    dedup = h.service.create_job(h.create(key="k2"))
    other = h.service.create_job(h.create(TEACHER_2, key="k1"))
    h.service.dispatch_outbox()
    while h.worker(provider).run_once() is not None:
        pass
    snap = h.store.snapshot()
    r.check("same key + same payload replays original receipt", replay.replayed
            and replay.job_id == first.job_id and replay.job_revision == first.job_revision)
    r.check("new key + same semantic request resolves to the same job",
            dedup.job_id == first.job_id and dedup.outcome == "deduplicated")
    r.check("other principal same key text = own scope, deduplicated, not replayed",
            other.job_id == first.job_id and not other.replayed)
    r.check("one job, one attempt", len(snap.jobs) == 1
            and len(snap.jobs[first.job_id].attempts) == 1)
    r.check("three immutable command receipts (k1, k2, teacher_2:k1)",
            len(snap.command_receipts) == 3)
    r.check("semantic cost charged once (provider calls)", dict(provider.calls) ==
            {first.job_id: 1})
    h2 = build_fixture_harness()
    base = h2.service.create_job(h2.create(key="s1")).job_id
    for label, kwargs in {"target": {"target": "target_fx_other"},
                          "session": {"session_id": "session_fx_other"},
                          "subjects": {"subjects": ("child_fx_other",)}}.items():
        other_scope = h2.service.create_job(h2.create(key=f"s_{label}", **kwargs))
        r.check(f"R02 same request, different {label} -> separate job (no scope merge)",
                other_scope.job_id != base and other_scope.outcome == "created")


def a04_key_conflict(r: Result) -> None:
    h = build_fixture_harness()
    first = h.service.create_job(h.create(key="k1"))
    code = _error_code(lambda: h.service.create_job(h.create(key="k1", ref=request_ref("req_x"))))
    r.check("same key different payload -> IDEMPOTENCY_PAYLOAD_MISMATCH",
            code == "IDEMPOTENCY_PAYLOAD_MISMATCH", str(code))
    job = _state(h, first.job_id)
    r.check("original job unchanged", job.job_revision == 1 and job.request_ref.request_id ==
            "req_fx_001")
    foreign = h.service.create_job(h.create(OUTSIDER, key="k1"))
    r.check("other organization same key/request -> separate job in its own org",
            foreign.job_id != first.job_id
            and _state(h, foreign.job_id).organization_id == OUTSIDER.organization_id)
    code = _error_code(lambda: h.service.create_job(h.create(UNGRANTED, key="k1")))
    r.check("ungranted principal cannot use key to reach job", code == "FORBIDDEN_SCOPE", str(code))


def a05_redelivery(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    again = h.service.start_attempt(cap, job_id, message.attempt_id)
    r.check("queue redelivery does not start another attempt",
            not again.started and again.reason_code == "DUPLICATE_DELIVERY")
    claim = h.success_claim(message)
    first = h.service.accept_completion(cap, claim)
    revision = _state(h, job_id).job_revision
    second = h.service.accept_completion(cap, claim)
    r.check("duplicate completion returns prior receipt", first == second)
    r.check("one effect: revision and attempts unchanged",
            _state(h, job_id).job_revision == revision and len(_state(h, job_id).attempts) == 1)


def a06_cas(r: Result) -> None:
    h = build_fixture_harness()
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
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    r.check("one winner, one COMPLETION_CONFLICT", sorted(outcomes) ==
            ["COMPLETION_CONFLICT", "accepted"], str(sorted(outcomes)))
    r.check("conflict recorded as incident",
            any(e.event_type == "job.completion_conflict" for e in h.audit.events))
    from sketch2life.infrastructure.ai_jobs.fakes import JobRevisionConflict

    job = _state(h, job_id)
    try:
        with h.store.transaction() as tx:
            tx.cas_job(expected_revision=job.job_revision - 1, job=job)
        r.check("stale CAS rejected", False)
    except JobRevisionConflict:
        r.check("stale CAS rejected", True)
    h.store.fail_next_commit = True
    with contextlib.suppress(RuntimeError):
        h.service.create_job(h.create(key="k_fail", ref=request_ref("req_fail")))
    r.check("failed commit leaves no partial job/receipt/outbox",
            len(h.store.snapshot().jobs) == 1 and len(h.store.snapshot().command_receipts) == 1)


def a07_bounded_retry(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    provider = FakeProvider(lambda m: h.failure_claim(m, code="PROVIDER_TIMEOUT"))
    worker = h.worker(provider)
    loops = 0
    while loops < 20:
        loops += 1
        h.service.dispatch_outbox()
        if worker.run_once() is None:
            h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
            if not h.service.run_due_retries():
                break
    job = _state(h, job_id)
    r.check("ends failed_exhausted", job.state is JobState.FAILED_EXHAUSTED, str(job.state))
    r.check("attempts bounded by named policy",
            len(job.attempts) == FIXTURE_RETRY_POLICY.max_attempts, str(len(job.attempts)))
    r.check("no infinite loop", loops < 20, str(loops))
    h2 = build_fixture_harness()
    jid = h2.service.create_job(h2.create()).job_id
    h2.start_next()
    h2.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    expired = h2.service.expire_overdue_attempts()
    j2 = _state(h2, jid)
    r.check("attempt timeout -> failed_retryable PROVIDER_TIMEOUT with backoff",
            expired == (jid,) and j2.state is JobState.FAILED_RETRYABLE
            and j2.failure.code == "PROVIDER_TIMEOUT" and j2.retry_not_before is not None)


def a08_progress(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    view = h.service.get_job_status(TEACHER, job_id).view or {}
    r.check("unknown progress has value null", view["progress"] ==
            {"kind": "unknown", "value": None, "stage_label": None})
    cap = h.capability(job_id)
    h.service.report_progress(cap, job_id, message.attempt_id,
                              JobProgress(ProgressKind.PERCENTAGE, 37.5))
    view = h.service.get_job_status(TEACHER, job_id).view or {}
    r.check("truthful percentage preserved", view["progress"]["value"] == 37.5)  # type: ignore[index]
    for label, kwargs in {
        "unknown with 0": {"kind": ProgressKind.UNKNOWN, "value": 0.0},
        "percentage 101": {"kind": ProgressKind.PERCENTAGE, "value": 101.0},
        "percentage nan": {"kind": ProgressKind.PERCENTAGE, "value": float("nan")},
        "stages without label": {"kind": ProgressKind.STAGES},
    }.items():
        try:
            JobProgress(**kwargs)  # type: ignore[arg-type]
            r.check(f"reject {label}", False)
        except InvalidProgress:
            r.check(f"reject {label}", True)


def a09_scope(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    for name, principal in (("other org", OUTSIDER), ("ungranted teacher", UNGRANTED)):
        code = _error_code(lambda p=principal: h.service.get_job_status(p, job_id))
        r.check(f"{name} -> RESOURCE_NOT_FOUND (existence concealed)",
                code == "RESOURCE_NOT_FOUND", str(code))
    missing = _error_code(lambda: h.service.get_job_status(TEACHER, "job_fx9999"))
    r.check("missing and forbidden look identical", missing == "RESOURCE_NOT_FOUND")
    h.authorization.revoke(DEVICE.principal_id)
    code = _error_code(lambda: h.service.get_job_status(DEVICE, job_id))
    r.check("revoked device grant denied", code == "RESOURCE_NOT_FOUND", str(code))


def a10_cache_after_revoke(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(job_id), h.success_claim(message))
    first = h.service.get_job_status(TEACHER, job_id)
    cached = h.service.get_job_status(TEACHER, job_id, first.etag)
    r.check("authorized unchanged poll -> 304", cached.not_modified)
    h.eligibility.revoked_subjects.add("child_fx_001")
    after = h.service.get_job_status(TEACHER, job_id, first.etag)
    r.check("consent revoke changes ETag; no 304 with old refs",
            not after.not_modified and after.etag != first.etag)
    r.check("refs withheld after revoke", (after.view or {}).get("result_refs") == [])
    h.authorization.revoke(TEACHER.principal_id)
    code = _error_code(lambda: h.service.get_job_status(TEACHER, job_id, first.etag))
    r.check("revoked grant gets 404 before cache/304", code == "RESOURCE_NOT_FOUND", str(code))
    h2 = build_fixture_harness()
    queued = h2.service.create_job(h2.create()).job_id
    early = h2.service.get_job_status(TEACHER, queued)
    h2.clock.advance(seconds=60)
    late = h2.service.get_job_status(TEACHER, queued, early.etag)
    r.check("R10 changed backoff hint is not hidden behind 304",
            not late.not_modified and (late.view or {}).get("poll_after_ms") == 10000
            and (early.view or {}).get("poll_after_ms") == 2000)


def a11_stale_completion(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    first = h.start_next()
    cap = h.capability(job_id)
    late_claim = h.success_claim(first)
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    h.service.expire_overdue_attempts()
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
    h.service.run_due_retries()
    second = h.start_next()
    receipt = h.service.accept_completion(cap, late_claim)
    job = _state(h, job_id)
    r.check("superseded attempt-1 success -> stale ATTEMPT_SUPERSEDED",
            str(receipt.disposition) == "stale" and receipt.reason_code == "ATTEMPT_SUPERSEDED")
    r.check("attempt 2 still running, not overwritten",
            job.state is JobState.RUNNING and job.active_attempt.attempt_id == second.attempt_id)
    tampered = replace(h.success_claim(second), input_hash="0" * 64)
    receipt = h.service.accept_completion(cap, tampered)
    r.check("wrong input hash -> rejected INPUT_MISMATCH",
            str(receipt.disposition) == "rejected" and receipt.reason_code == "INPUT_MISMATCH")
    r.check("mismatch audited as incident",
            any(e.event_type == "job.completion_input_mismatch" for e in h.audit.events))
    r.check("job still running after mismatch", _state(h, job_id).state is JobState.RUNNING)
    corrected = h.service.accept_completion(cap, h.success_claim(second))
    r.check("R03 rejected mismatch does not block corrected completion",
            corrected.disposition.value == "accepted" and corrected.authoritative)
    h2 = build_fixture_harness()
    jid = h2.service.create_job(h2.create()).job_id
    msg = h2.next_message()
    cap2 = h2.capability(jid)
    claim = h2.success_claim(msg)
    early = h2.service.accept_completion(cap2, claim)
    h2.service.start_attempt(cap2, jid, msg.attempt_id)
    later = h2.service.accept_completion(cap2, claim)
    r.check("R03 completion before start is non-authoritative; same claim lands after start",
            early.reason_code == "INVALID_STATE" and not early.authoritative
            and later.disposition.value == "accepted")
    refs = [x["artifact_ref"] for x in  # type: ignore[union-attr]
            (h2.service.get_job_status(TEACHER, jid).view or {})["result_refs"]]
    r.check("R03a accepted refs after temporary rejection are not quarantined",
            refs == [claim.outputs[0].artifact_ref] and not h2.artifacts.quarantined)
    try:
        h2.service.accept_completion(cap2, h2.success_claim(msg, body=b"other-output"))
        r.check("R03 genuine conflict after accepted completion still raised", False)
    except AiJobError as exc:
        r.check("R03 genuine conflict after accepted completion still raised",
                exc.code == "COMPLETION_CONFLICT")


def a12_context_change(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.eligibility.context_revisions["req_fx_001"] = 2
    receipt = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
    job = _state(h, job_id)
    view = h.service.get_job_status(TEACHER, job_id).view or {}
    r.check("result disposition stale STALE_CONTEXT", receipt.reason_code == "STALE_CONTEXT"
            and job.result_disposition is not None and job.result_disposition.value == "stale")
    r.check("source lineage kept (pinned context 1)",
            job.request_ref.context_revision == 1 and "superseded by 2" in (job.lineage_note or ""))
    r.check("stale result not projected", view.get("result_refs") == [])


def a13_cancel(r: Result) -> None:
    for state in ("queued", "running", "failed_retryable"):
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        message = None
        failure = None
        if state != "queued":
            message = h.start_next()
        if state == "failed_retryable":
            assert message is not None
            failure = h.failure_claim(message)
            h.service.accept_completion(h.capability(job_id), failure)
        before = _state(h, job_id)
        h.service.cancel_job(CancelJobCommand(TEACHER, "cancel_1", job_id, before.job_revision))
        job = _state(h, job_id)
        r.check(f"cancel from {state}", job.state is JobState.CANCELLED
                and job.retry_not_before is None)
        h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
        r.check(f"{state}: scheduled retry invalidated", h.service.run_due_retries() == ()
                and not h.service.retry_job(job_id, before.active_attempt.attempt_number))
        if message is not None:
            late = failure or h.success_claim(message)
            receipt = h.service.accept_completion(h.capability(job_id), late)
            expected = "PROVIDER_UNAVAILABLE" if failure else "JOB_CANCELLED"
            r.check(f"{state}: late/duplicate completion cannot resurrect",
                    receipt.reason_code == expected
                    and _state(h, job_id).state is JobState.CANCELLED
                    and len(_state(h, job_id).attempts) == len(before.attempts))
        r.check(f"{state}: outbox has no new dispatch", h.service.dispatch_outbox() == 0)
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    code = _error_code(lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c", job_id, None)))
    r.check("cancel without If-Match -> PRECONDITION_REQUIRED", code == "PRECONDITION_REQUIRED")
    code = _error_code(lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c2", job_id, 9)))
    r.check("cancel with stale revision -> STALE_AGGREGATE", code == "STALE_AGGREGATE")


def a14_eligibility(r: Result) -> None:
    cases = {
        "consent revoke": lambda h: h.eligibility.revoked_subjects.add("child_fx_001"),
        "session end": lambda h: h.eligibility.ended_sessions.add("session_fx_001"),
        "content recall": lambda h: h.eligibility.recalled_requests.add("req_fx_001"),
        "source expiry": lambda h: h.eligibility.expired_requests.add("req_fx_001"),
        "kill switch": lambda h: h.eligibility.killed_job_types.add("sketch_assistance"),
    }
    for name, apply in cases.items():
        h = build_fixture_harness()
        apply(h)
        code = _error_code(lambda h=h: h.service.create_job(h.create()))
        r.check(f"{name}: create denied without reserving receipt",
                code is not None and not h.store.snapshot().command_receipts, str(code))
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        h.service.dispatch_outbox()
        envelope = h.queue.receive()
        assert envelope is not None
        message = envelope.message
        apply(h)
        started = h.service.start_attempt(h.capability(job_id), job_id, message.attempt_id)
        r.check(f"{name}: dispatch/start denied, job cancelled, no provider call",
                not started.started and _state(h, job_id).state is JobState.CANCELLED)
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        apply(h)
        receipt = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
        r.check(f"{name}: completion rejected and quarantined",
                str(receipt.disposition) == "rejected"
                and _state(h, job_id).state is JobState.CANCELLED
                and bool(h.artifacts.quarantined))
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        h.service.accept_completion(h.capability(job_id), h.failure_claim(message))
        apply(h)
        h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
        r.check(f"{name}: retry denied -> cancelled", h.service.run_due_retries() == ()
                and _state(h, job_id).state is JobState.CANCELLED)
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    notice = CancellationNotice("notice_1", ORG, "KILL_SWITCH", job_type="sketch_assistance")
    r.check("kill-switch notice cancels pending work",
            h.service.apply_cancellation_notice(notice) == (job_id,))
    r.check("notice replay is a no-op", h.service.apply_cancellation_notice(notice) == ())
    for name, apply in cases.items():
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        apply(h)
        sent = h.service.dispatch_outbox()
        r.check(f"R09 {name}: dispatch rechecks eligibility, nothing enqueued",
                sent == 0 and not h.queue.messages
                and _state(h, job_id).state is JobState.CANCELLED
                and not h.store.snapshot().outbox)


def a15_unsafe_malformed(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    receipt = h.service.accept_completion(
        h.capability(job_id), h.success_claim(message, moderation=Moderation.UNSAFE)
    )
    view = h.service.get_job_status(TEACHER, job_id).view or {}
    r.check("unsafe -> blocked_unsafe, rejected, quarantined",
            view["state"] == "blocked_unsafe" and receipt.reason_code == "UNSAFE_CONTENT"
            and bool(h.artifacts.quarantined) and view["result_refs"] == [])
    secret = "provider said: token=sk-fixture-secret at https://provider.invalid/raw"
    for label in ("no outputs", "unknown ref", "hash mismatch", "provider failure diagnostic"):
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        good = h.success_claim(message)
        out = good.outputs[0]
        claim = {
            "no outputs": replace(good, outputs=()),
            "unknown ref": replace(good, outputs=(OutputRef("artifact_missing", out.sha256),)),
            "hash mismatch": replace(good, outputs=(OutputRef(out.artifact_ref, "f" * 64),)),
            "provider failure diagnostic": h.failure_claim(
                message, code="PROVIDER_ERROR", retryable=False, diagnostic=secret
            ),
        }[label]
        receipt = h.service.accept_completion(h.capability(job_id), claim)
        job = _state(h, job_id)
        dumped = json.dumps(h.service.get_job_status(TEACHER, job_id).view, default=str)
        audit = json.dumps([asdict(e) for e in h.audit.events], default=str)
        if label == "provider failure diagnostic":
            r.check("diagnostic redacted from view and audit",
                    "sk-fixture-secret" not in dumped and "provider.invalid" not in dumped
                    and "sk-fixture-secret" not in audit and "provider.invalid" not in audit)
        else:
            r.check(f"malformed ({label}) -> failed_exhausted OUTPUT_MALFORMED, no exposure",
                    job.state is JobState.FAILED_EXHAUSTED
                    and receipt.reason_code == "OUTPUT_MALFORMED" and job.result_refs == ())


    from sketch2life.infrastructure.ai_jobs.harness import OTHER_ORG

    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    foreign = h.artifacts.put(OTHER_ORG, b"foreign")
    sibling = h.artifacts.put(ORG, b"same-org-no-lineage")
    for label, claim in {
        "input mismatch": replace(h.success_claim(message), input_hash="0" * 64,
                                  outputs=(foreign, sibling)),
        "malformed output": replace(h.success_claim(message), outputs=(foreign, sibling)),
    }.items():
        h.service.accept_completion(h.capability(job_id), claim)
        r.check(f"R01 {label}: foreign/unowned artifacts never quarantined",
                foreign.artifact_ref not in h.artifacts.quarantined
                and sibling.artifact_ref not in h.artifacts.quarantined)
    for bad_code in ([], {}, ["token=sk-fixture-secret"]):
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        receipt = h.service.accept_completion(
            h.capability(job_id),
            replace(h.failure_claim(message, retryable=False), failure_code=bad_code),
        )
        later = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
        r.check(f"R04a non-string code {type(bad_code).__name__} -> MALFORMED_CLAIM, "
                "later valid completion accepted",
                receipt.reason_code == "MALFORMED_CLAIM" and not receipt.authoritative
                and later.disposition.value == "accepted"
                and "sk-fixture-secret" not in json.dumps([asdict(e) for e in h.audit.events]))
    for code in ("http 503 from provider", "SOME_VENDOR_CODE", None):
        h = build_fixture_harness()
        job_id = h.service.create_job(h.create()).job_id
        message = h.start_next()
        h.service.accept_completion(h.capability(job_id),
                                    replace(h.failure_claim(message, retryable=False),
                                            failure_code=code))
        view = h.service.get_job_status(TEACHER, job_id).view or {}
        AsyncJobViewV1.model_validate(view, strict=False)
        r.check(f"R04 provider code {code!r} mapped to PROVIDER_ERROR, poll view valid",
                (view.get("failure") or {}).get("code") == "PROVIDER_ERROR")  # type: ignore[union-attr]


def a16_success_semantics(r: Result) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    claim = h.success_claim(message)
    h.service.accept_completion(h.capability(job_id), claim)
    teacher = h.service.get_job_status(TEACHER, job_id).view or {}
    device = h.service.get_job_status(DEVICE, job_id).view or {}
    r.check("teacher sees exact refs + hash", teacher["result_refs"] ==
            [{"artifact_ref": claim.outputs[0].artifact_ref, "sha256": claim.outputs[0].sha256}])
    r.check("no approval/playback/session-complete fields in DATA-25 view",
            not {"approved", "review_state", "playback_state", "session_complete"} & set(teacher))
    r.check("device projection has no refs/request/disposition",
            not {"result_refs", "request_ref", "result_disposition", "attempt_id"} & set(device))
    AsyncJobChildViewV1.model_validate(device, strict=False)
    r.check("device projection validates against child candidate schema", True)


def a17_worker_capability(r: Result, with_http: bool) -> None:
    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    other = h.service.create_job(h.create(key="k2", ref=request_ref("req_2"))).job_id
    message = h.start_next()
    claim = h.success_claim(message)
    for label, cap in (("missing", ""), ("forged", "wcap_fx_forged"),
                       ("other job", h.capability(other))):
        code = _error_code(lambda c=cap: h.service.accept_completion(c, claim))
        r.check(f"{label} capability denied", code == "WORKER_CAPABILITY_INVALID", str(code))
    if not with_http:
        r.not_run.append("HTTP route surface: NOT_RUN here; run with --with-http (needs FastAPI)")
        return
    from fastapi.testclient import TestClient
    from sketch2life.interfaces.http.ai_jobs_fixture_app import (
        create_ai_jobs_fixture_app,
        route_surface,
    )

    app = create_ai_jobs_fixture_app(h.service, {"teacher": TEACHER})
    surface = route_surface(app.routes)
    r.check("fixture app exposes exactly GET CMD-44",
            surface == {("/api/collaboration/v1/jobs/{job_id}", "GET")}, str(sorted(surface)))
    client = TestClient(app)
    path = f"/api/collaboration/v1/jobs/{job_id}"
    ok = client.get(path, headers={"Authorization": "Fixture teacher"})
    r.check("authorized GET returns DATA-25 envelope", ok.status_code == 200
            and ok.json()["contract_name"] == "AsyncJobView", str(ok.status_code))
    for suffix in ("", "/completion"):
        posted = client.post(path + suffix, headers={"Authorization": "Fixture teacher"}, json={})
        r.check(f"POST {suffix or '/'} rejected (no completion route)",
                posted.status_code in {404, 405}, str(posted.status_code))


def a18_provider_copy(r: Result) -> None:
    h = build_fixture_harness()
    scope = "job_fx_scope"
    for i, profile in enumerate(["fixture-deletes", "fixture-pending", "fixture-unsupported",
                                 "fixture-exception", "fixture-unverified"]):
        h.copy_service.register_copy(ProviderCopy(f"c{i}", ORG, scope, CopyKind.OUTPUT, profile))
    first = h.copy_service.purge_scope(ORG, scope, "purge_1")
    again = h.copy_service.purge_scope(ORG, scope, "purge_1")
    labels = {o.copy_id: o.report_label for o in first}
    r.check("duplicate purge returns same receipts, no new provider request",
            first == again and len(h.copy_adapter.purge_requests) == 5)
    r.check("fixture delete labelled not actual", labels["c0"] == "fixture_deleted_not_actual")
    r.check("pending/unsupported/exception/unverified never deleted",
            [labels[c] for c in ("c1", "c2", "c3", "c4")] ==
            ["pending", "unsupported", "exception", "pending"])
    r.check("no copy claims actual deletion", not any(o.actual_deletion_proven for o in first))
    late = h.copy_service.register_copy(ProviderCopy("late", ORG, scope, CopyKind.OUTPUT,
                                                     "fixture-pending"))
    r.check("late copy in purging scope cannot resurrect", late.status.value == "purge_requested")
    r.check("other organization scope isolated", h.copy_service.discover("org_fx_other", scope)
            == ())
    h = build_fixture_harness()
    h.copy_service.register_copy(ProviderCopy("cc", ORG, "s_conc", CopyKind.OUTPUT,
                                              "fixture-deletes"))
    original = h.copy_adapter.request_purge

    def slow(copy: ProviderCopy) -> Any:
        time.sleep(0.2)
        return original(copy)

    h.copy_adapter.request_purge = slow  # type: ignore[method-assign]
    receipts: list[str | None] = []
    threads = [threading.Thread(target=lambda: receipts.append(
        h.copy_service.purge_scope(ORG, "s_conc", "same")[0].receipt_id)) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    stored = h.copy_registry.get("cc")
    r.check("R05 concurrent same-key purge: one dispatch, one consistent receipt",
            len(h.copy_adapter.purge_requests) == 1 and len(set(receipts)) == 1
            and stored is not None and stored.receipt_id == receipts[0])
    h = build_fixture_harness()
    h.copy_service.register_copy(ProviderCopy("cr", ORG, "s_rep", CopyKind.OUTPUT,
                                              "fixture-pending"))
    first_p = h.copy_service.purge_scope(ORG, "s_rep", "p1")[0]
    current = h.copy_registry.get("cr")
    assert current is not None
    h.copy_registry.save(replace(current, provider_profile="fixture-deletes"))
    h.copy_service.purge_scope(ORG, "s_rep", "p2")
    replay = h.copy_service.purge_scope(ORG, "s_rep", "p1")[0]
    after = h.copy_registry.get("cr")
    h_a = build_fixture_harness()
    h_a.copy_service.register_copy(ProviderCopy("ca", ORG, "s_a", CopyKind.OUTPUT,
                                                "fixture-deletes"))
    entered, release = threading.Event(), threading.Event()
    cancel_original = h_a.copy_adapter.request_cancel

    def paused_cancel(copy: ProviderCopy) -> None:
        entered.set()
        release.wait(5)
        cancel_original(copy)

    h_a.copy_adapter.request_cancel = paused_cancel  # type: ignore[method-assign]
    purged: list[str | None] = []
    canceller = threading.Thread(target=lambda: h_a.copy_service.cancel_scope(ORG, "s_a"))
    purger = threading.Thread(target=lambda: purged.append(
        h_a.copy_service.purge_scope(ORG, "s_a", "p1")[0].receipt_id))
    canceller.start()
    entered.wait(5)
    purger.start()
    purger.join(0.3)
    waited = purger.is_alive()
    release.set()
    canceller.join(5)
    purger.join(5)
    final = h_a.copy_registry.get("ca")
    r.check("A18a paused cancel cannot overwrite purge result/receipt",
            waited and final is not None and final.status.value == "deleted"
            and final.receipt_id == purged[0] is not None)
    r.check("R06 old-key replay returns its own result, keeps newer deleted state",
            replay == first_p and after is not None and after.status.value == "deleted"
            and len(h.copy_adapter.purge_requests) == 2)


def a19_candidates(r: Result) -> None:
    for name in ("session_sketch_approve", "library_request_changes"):
        ExactContentReviewCommandV1.model_validate_json(
            (FIXTURES / "data24" / "positive" / f"{name}.json").read_bytes(), strict=True)
        r.check(f"DATA-24 {name} validates", True)
    for path in sorted((FIXTURES / "data24" / "negative").glob("*.json")):
        try:
            ExactContentReviewCommandV1.model_validate_json(path.read_bytes(), strict=True)
            r.check(f"DATA-24 negative {path.stem} rejected", False)
        except ValidationError:
            r.check(f"DATA-24 negative {path.stem} rejected", True)
    report = ProviderCopyLifecycleReportV1.model_validate_json(
        (FIXTURES / "provider_copy" / "positive" / "fixture_scope_purge.json").read_bytes(),
        strict=True)
    r.check("ProviderCopyLifecycle owner BE2-14 / fake BE2-01 / fixture-marked",
            report.contract_owner == "BE2-14" and report.fake_support_owner == "BE2-01"
            and report.fixture_marker)
    for path in sorted((FIXTURES / "provider_copy" / "negative").glob("*.json")):
        try:
            ProviderCopyLifecycleReportV1.model_validate_json(path.read_bytes(), strict=True)
            r.check(f"provider-copy negative {path.stem} rejected", False)
        except ValidationError:
            r.check(f"provider-copy negative {path.stem} rejected", True)
    for data_id, spec in sorted(SHAPE_SPECS.items()):
        positive = json.loads((FIXTURES / "shapes" / "positive" / f"{data_id}.json").read_bytes())
        negative = json.loads((FIXTURES / "shapes" / "negative" / f"{data_id}.json").read_bytes())
        r.check(f"{data_id} ({spec.owner_card}) positive shape", check_shape(data_id, positive)
                == [])
        r.check(f"{data_id} negative shape rejected ({negative['reason']})",
                check_shape(data_id, negative["payload"]) != [])
    for path in sorted((FIXTURES / "shapes" / "negative_types").glob("*.json")):
        case = json.loads(path.read_bytes())
        try:
            errors = check_shape(case["data_id"], case["payload"])
            r.check(f"R07 {path.stem} returns validation errors", errors != [], str(errors))
        except Exception as exc:  # noqa: BLE001
            r.check(f"R07 {path.stem} returns validation errors", False, type(exc).__name__)


def a20_handoff(r: Result) -> None:
    required = [
        FEATURE / "evidence" / "notes" / "PHASE_A_HANDOFF.md",
        FIXTURES / "consumer_examples" / "p1_job_poll_sequence.json",
        FIXTURES / "error_catalogue.json",
        FIXTURES / "MANIFEST.json",
        FEATURE / "plan" / "PHASE_A_CANDIDATE_SPEC.md",
    ]
    for path in required:
        r.check(f"present: {path.relative_to(FEATURE).as_posix()}", path.exists())


def a01_standalone(r: Result, report_core: dict[str, Any], rerun_core: dict[str, Any]) -> None:
    origin = Path(sketch2life.__file__).resolve()
    r.check("sketch2life imported from this tree", origin.is_relative_to(BACKEND_SRC.resolve()),
            origin.as_posix().split("/backend/")[-1])
    loaded = sorted(m for m in FORBIDDEN_RUNTIME_MODULES if m in sys.modules)
    r.check("no DB/broker/provider SDK/HTTP client/FastAPI loaded", not loaded, ",".join(loaded))
    r.check("deterministic: two runs give identical results",
            _digest(report_core) == _digest(rerun_core))


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


SCENARIOS: list[tuple[str, str, Callable[[Result], None]]] = [
    ("A-02", "DATA-25 round-trip/invalid fixtures", a02_data25),
    ("A-03", "Duplicate semantic request", a03_semantic_duplicate),
    ("A-04", "Same key changed payload/scope", a04_key_conflict),
    ("A-05", "Queue redelivery/duplicate completion", a05_redelivery),
    ("A-06", "Fake concurrent CAS / changed output", a06_cas),
    ("A-07", "Timeout/retry to policy limit", a07_bounded_retry),
    ("A-08", "Unknown/stage/percentage progress", a08_progress),
    ("A-09", "Poll outside organization/audience/grant", a09_scope),
    ("A-10", "ETag/cache poll after revoke", a10_cache_after_revoke),
    ("A-11", "Wrong attempt/request/revision/hash completion", a11_stale_completion),
    ("A-12", "Source/context change while running", a12_context_change),
    ("A-13", "Cancel queued/running/backoff/before completion", a13_cancel),
    ("A-14", "Consent/session/recall/expiry/kill-switch", a14_eligibility),
    ("A-15", "Unsafe/malformed output", a15_unsafe_malformed),
    ("A-16", "Success pending review", a16_success_semantics),
    ("A-18", "Fake provider copy discover/cancel/purge", a18_provider_copy),
    ("A-19", "DATA-24/ProviderCopyLifecycle/shape candidates", a19_candidates),
    ("A-20", "Handoff P1/P2/P4 artefacts", a20_handoff),
]


def run_core(with_http: bool) -> list[Result]:
    results: list[Result] = []
    for criterion, title, fn in SCENARIOS:
        result = Result(criterion, title)
        try:
            fn(result)
        except Exception as exc:  # noqa: BLE001 - runner records unexpected failures
            result.check("scenario raised", False, f"{type(exc).__name__}: {exc}")
        results.append(result)
    a17 = Result("A-17", "Worker capability / no client completion")
    try:
        a17_worker_capability(a17, with_http=False)
    except Exception as exc:  # noqa: BLE001
        a17.check("scenario raised", False, f"{type(exc).__name__}: {exc}")
    results.insert(15, a17)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--write-fixtures", action="store_true")
    parser.add_argument("--with-http", action="store_true")
    args = parser.parse_args()
    if args.write_fixtures:
        written = fixture_catalog.write_fixtures(FIXTURES)
        print(f"FIXTURES_WRITTEN {len(written)} files -> {FIXTURES.relative_to(ROOT).as_posix()}")
    core = run_core(with_http=False)
    rerun = run_core(with_http=False)
    core_json = [r.__dict__ for r in core]
    a01 = Result("A-01", "Standalone deterministic runner")
    a01_standalone(a01, core_json, [r.__dict__ for r in rerun])
    results = [a01, *core]
    if args.with_http:
        http = Result("A-17-http", "CMD-44 fixture app route surface")
        a17_worker_capability(http, with_http=True)
        results.append(http)
    summary = {
        "PASS": sum(r.status == "PASS" for r in results),
        "FAIL": sum(r.status == "FAIL" for r in results),
        "checks": sum(len(r.checks) for r in results),
        "checks_failed": sum(not c["ok"] for r in results for c in r.checks),
        "not_run": sum(len(r.not_run) for r in results),
    }
    manifest = FIXTURES / "MANIFEST.json"
    report = {
        "runner": "BE2-01 Phase A fixture contracts",
        "scope": "fake/contract semantics only; not durable, not real inference/deletion",
        "fixture_manifest_sha256": (sha256(manifest.read_bytes()).hexdigest()
                                    if manifest.exists() else None),
        "results_sha256": _digest(core_json),
        "environment": {"python": platform.python_version(), "platform": sys.platform,
                        "with_http": args.with_http},
        "summary": summary,
        "results": [r.__dict__ for r in results],
    }
    text = json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(text.encode())
    for r in results:
        failed = [c["name"] for c in r.checks if not c["ok"]]
        print(f"{r.criterion:10} {r.status:5} {len(r.checks):3} checks  {r.title}"
              + (f"  FAILED: {failed}" if failed else "")
              + (f"  NOT_RUN: {r.not_run}" if r.not_run else ""))
    print(f"SUMMARY {json.dumps(summary)} results_sha256={report['results_sha256']}")
    return 0 if summary["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
