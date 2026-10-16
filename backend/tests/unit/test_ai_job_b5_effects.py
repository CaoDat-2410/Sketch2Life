"""BE2-01 Phase B batch B5 offline checks on fakes: completion/incident atomicity (Δ9),
quarantine intents (Δ15), leased side-effect delivery and atomic cancellation notices (Δ10).

Fakes only; PostgreSQL evidence is in tests/integration/ai_jobs/test_completion_recovery.py,
test_audit_durability.py and test_notice_coverage.py (skipped without a server = NOT_RUN).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import timedelta
from typing import Any

import pytest

from sketch2life.application.ports.ai_jobs import (
    AuditEvent,
    CancellationNotice,
    QuarantineIntent,
    UniqueConflict,
)
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    FIXTURE_RETRY_POLICY,
    AiJobDependencies,
    AiJobError,
    AiJobService,
    CancelJobCommand,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim, Moderation
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.fakes import eligibility_fence_scope
from sketch2life.infrastructure.ai_jobs.harness import (
    ORG,
    OUTSIDER,
    SESSION,
    TEACHER,
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)

LEASE_MS = FIXTURE_DISPATCH_POLICY.lease_ms
WRITES = ("insert_job", "cas_job", "put_", "add_", "record_notice")


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


# ------------------------------------------------------------------ fault-injecting store
@dataclass
class Faults:
    """Per-harness fault plan for the fake unit of work (synthetic boundaries only)."""

    fail_after: str | None = None  # raise right after this UoW method ran
    fail_commit_after_write: bool = False
    raise_before: dict[str, Exception] = field(default_factory=dict)  # one-shot
    on_raise: dict[str, Callable[[], None]] = field(default_factory=dict)  # after that round
    after_rollback: list[Callable[[], None]] = field(default_factory=list)
    enabled: bool = True


class _Proxy:
    def __init__(self, uow: Any, faults: Faults) -> None:
        self._uow, self._faults, self.wrote = uow, faults, False

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._uow, name)
        faults = self._faults
        if not callable(attr) or not faults.enabled:
            return attr

        def call(*args: Any, **kwargs: Any) -> Any:
            if name in faults.raise_before:
                if name in faults.on_raise:
                    faults.after_rollback.append(faults.on_raise.pop(name))
                raise faults.raise_before.pop(name)
            result = attr(*args, **kwargs)
            if name.startswith(WRITES):
                self.wrote = True
            if faults.fail_after == name:
                faults.fail_after = None
                raise RuntimeError(f"injected failure after {name}")
            return result

        return call


def faulty(h: FixtureHarness) -> Faults:
    faults = Faults()
    original = h.store.transaction

    @contextmanager
    def transaction() -> Iterator[Any]:
        try:
            with original() as uow:
                proxy = _Proxy(uow, faults)
                yield proxy
                if faults.enabled and faults.fail_commit_after_write and proxy.wrote:
                    faults.fail_commit_after_write = False
                    raise RuntimeError("injected commit failure")
        finally:
            pending, faults.after_rollback[:] = list(faults.after_rollback), []
            for callback in pending:  # e.g. a competitor commits once this round ended
                callback()

    h.store.transaction = transaction  # type: ignore[method-assign]
    return faults


def _state(h: FixtureHarness) -> tuple[Any, ...]:
    snap = h.store.snapshot()
    return (snap.jobs, snap.completion_receipts, snap.audit_intents, snap.quarantine_intents,
            snap.notices, snap.side_effects_delivered)


def _running(h: FixtureHarness, key: str = "idem_b5", request: str = "req_b5") -> tuple[str, Any]:
    job_id = h.service.create_job(h.create(key=key, ref=request_ref(request))).job_id
    return job_id, h.start_next()


def _token(h: FixtureHarness) -> str:
    assert h.last_envelope is not None
    return h.last_envelope.capability


def _superseded(h: FixtureHarness) -> tuple[str, str, CompletionClaim]:
    """A late claim of attempt 1 after a policy retry started attempt 2."""

    job_id, first = _running(h)
    token = _token(h)
    late = h.success_claim(first)
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert h.service.expire_overdue_attempts() == (job_id,)
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert h.service.run_due_retries() == (job_id,)
    h.start_next()
    return job_id, token, late


def _intents(h: FixtureHarness, event_type: str) -> list[AuditEvent]:
    return [e for e in h.store.snapshot().audit_intents.values() if e.event_type == event_type]


# ------------------------------------------------------- authoritative completion (B-08)
@pytest.mark.parametrize(
    "boundary",
    ["cas_job", "put_completion_receipt", "add_quarantine_intent", "add_audit_intent", "commit"],
)
def test_job_changing_completion_commits_all_effects_together_or_none(
    h: FixtureHarness, boundary: str
) -> None:
    job_id, message = _running(h)
    token = _token(h)
    claim = h.success_claim(message, moderation=Moderation.UNSAFE)
    faults = faulty(h)
    before, events_before = _state(h), list(h.audit.events)
    if boundary == "commit":
        faults.fail_commit_after_write = True
    else:
        faults.fail_after = boundary
    with pytest.raises(RuntimeError, match="injected"):
        h.service.accept_completion(token, claim)
    assert _state(h) == before  # no partial job/receipt/intent
    assert h.artifacts.quarantined == {} and h.audit.events == events_before
    receipt = h.service.accept_completion(token, claim)
    assert receipt.authoritative and receipt.reason_code == "UNSAFE_CONTENT"
    snap = h.store.snapshot()
    assert snap.jobs[job_id].state is JobState.BLOCKED_UNSAFE
    assert (job_id, message.attempt_id) in snap.completion_receipts
    (intent,) = snap.quarantine_intents.values()
    assert intent.artifact_refs == (claim.outputs[0].artifact_ref,)
    assert [e.reason_code for e in _intents(h, "job.completion")] == ["UNSAFE_CONTENT"]
    assert h.artifacts.applied_events == [intent.event_id]


def test_identical_replay_returns_the_receipt_and_conflict_never_overwrites(
    h: FixtureHarness,
) -> None:
    job_id, message = _running(h)
    token = _token(h)
    claim = h.success_claim(message)
    receipt = h.service.accept_completion(token, claim)
    assert h.service.accept_completion(token, claim) == receipt
    other = h.success_claim(message, body=b"other-output")
    with pytest.raises(AiJobError) as error:
        h.service.accept_completion(token, other)
    assert (error.value.code, error.value.http_status) == ("COMPLETION_CONFLICT", 409)
    assert h.store.snapshot().completion_receipts[(job_id, message.attempt_id)] == receipt
    (conflict,) = _intents(h, "job.completion_conflict")
    assert conflict.reason_code == "COMPLETION_CONFLICT"
    assert conflict.event_id in {e.event_id for e in h.audit.events}


# -------------------------------------------------------- audit-only incidents (B-06c, B-08b)
def test_guard_rejection_commits_an_audit_only_incident_before_answering(
    h: FixtureHarness,
) -> None:
    job_id, token, late = _superseded(h)
    job_before = h.store.snapshot().jobs[job_id]
    receipt = h.service.accept_completion(token, late)
    assert not receipt.authoritative and receipt.reason_code == "ATTEMPT_SUPERSEDED"
    snap = h.store.snapshot()
    assert snap.jobs[job_id] == job_before  # incident only: the job row is unchanged
    assert (job_id, late.attempt_id) not in snap.completion_receipts  # slot stays free
    (incident,) = _intents(h, "job.completion_rejected")
    assert incident.reason_code == "ATTEMPT_SUPERSEDED"
    (quarantine,) = snap.quarantine_intents.values()  # committed-final: owned output
    assert quarantine.artifact_refs == (late.outputs[0].artifact_ref,)
    assert quarantine.attempt_id == late.attempt_id
    assert late.outputs[0].artifact_ref in h.artifacts.quarantined


def _malformed(h: FixtureHarness) -> tuple[str, CompletionClaim]:
    _, message = _running(h)
    return _token(h), replace(h.failure_claim(message), kind="bogus")  # type: ignore[arg-type]


def _conflicting(h: FixtureHarness) -> tuple[str, CompletionClaim]:
    _, message = _running(h)
    token = _token(h)
    h.service.accept_completion(token, h.success_claim(message))
    return token, h.success_claim(message, body=b"other-output")


@pytest.mark.parametrize("case", ["superseded", "malformed", "conflict"])
def test_incident_commit_failure_is_a_retryable_503_not_a_receipt(
    h: FixtureHarness, case: str
) -> None:
    if case == "superseded":
        _, token, claim = _superseded(h)
    else:
        token, claim = _malformed(h) if case == "malformed" else _conflicting(h)
    faults = faulty(h)
    before = _state(h)
    faults.fail_commit_after_write = True
    with pytest.raises(AiJobError) as error:
        h.service.accept_completion(token, claim)
    assert (error.value.code, error.value.http_status, error.value.retryable) == (
        "DEPENDENCY_UNAVAILABLE", 503, True
    )
    assert _state(h) == before
    if case == "conflict":
        with pytest.raises(AiJobError) as again:
            h.service.accept_completion(token, claim)
        assert again.value.code == "COMPLETION_CONFLICT"
    else:
        assert not h.service.accept_completion(token, claim).authoritative
    assert len(h.store.snapshot().audit_intents) == len(before[2]) + 1


def test_repeated_incident_is_deduplicated_by_event_id(h: FixtureHarness) -> None:
    _, token, late = _superseded(h)
    first = h.service.accept_completion(token, late)
    second = h.service.accept_completion(token, late)
    assert not first.authoritative and not second.authoritative
    (incident,) = _intents(h, "job.completion_rejected")
    assert h.audit.deliveries.count(incident.event_id) == 2
    assert [e.event_id for e in h.audit.events].count(incident.event_id) == 1
    (quarantine,) = h.store.snapshot().quarantine_intents.values()
    assert h.artifacts.applied_events == [quarantine.event_id]
    assert h.artifacts.deliveries.count(quarantine.event_id) == 2


def _competing(faults: Faults, call: Callable[[], Any], box: list[Any]) -> Callable[[], None]:
    """A competitor that commits the same work right after the current round rolled back."""

    def run() -> None:
        faults.enabled = False
        try:
            box.append(call())
        finally:
            faults.enabled = True

    return run


def test_concurrent_identical_incident_rolls_back_then_deduplicates(h: FixtureHarness) -> None:
    _, token, late = _superseded(h)
    faults = faulty(h)
    competitor: list[Any] = []
    # Round 1 loses on the side-effect key: its whole transaction rolls back, the competitor's
    # identical incident commits, and round 2 finds the stored event ids instead of continuing.
    faults.raise_before["add_quarantine_intent"] = UniqueConflict("outbox")
    faults.on_raise["add_quarantine_intent"] = _competing(
        faults, lambda: h.service.accept_completion(token, late), competitor
    )
    receipt = h.service.accept_completion(token, late)
    assert competitor and not competitor[0].authoritative and not receipt.authoritative
    assert len(_intents(h, "job.completion_rejected")) == 1
    assert len(h.store.snapshot().quarantine_intents) == 1


def test_unrelated_unique_conflict_in_an_incident_is_not_swallowed(h: FixtureHarness) -> None:
    _, token, late = _superseded(h)
    faults = faulty(h)
    faults.raise_before["add_audit_intent"] = UniqueConflict("command_receipt")
    with pytest.raises(UniqueConflict) as error:
        h.service.accept_completion(token, late)
    assert error.value.kind == "command_receipt"
    assert _intents(h, "job.completion_rejected") == []


# ------------------------------------------------- leased side-effect delivery (B-06c/d)
def test_crash_after_commit_before_delivery_is_redelivered_with_stored_ids(
    h: FixtureHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    job_id, message = _running(h)
    token = _token(h)
    claim = h.success_claim(message, moderation=Moderation.UNSAFE)

    def down(*_: Any) -> None:
        raise ConnectionError("sink unavailable")

    monkeypatch.setattr(h.audit, "record", down)
    monkeypatch.setattr(h.artifacts, "quarantine", down)
    receipt = h.service.accept_completion(token, claim)
    assert receipt.authoritative  # committed: success is truthful even though delivery failed
    assert h.artifacts.quarantined == {}
    monkeypatch.undo()
    snap = h.store.snapshot()
    stored = set(snap.audit_intents) | set(snap.quarantine_intents)
    assert h.service.deliver_side_effects() == len(stored)
    assert set(h.store.snapshot().side_effects_delivered) == stored
    # every stored intent reached its sink (direct non-outbox audits such as job.start aside)
    assert stored <= {e.event_id for e in h.audit.events} | set(h.artifacts.applied_events)
    assert claim.outputs[0].artifact_ref in h.artifacts.quarantined
    assert h.service.deliver_side_effects() == 0
    assert h.store.snapshot().jobs[job_id].state is JobState.BLOCKED_UNSAFE


def test_crash_after_sink_effect_before_mark_redelivers_as_a_no_op(h: FixtureHarness) -> None:
    _, message = _running(h)
    token = _token(h)
    claim = h.success_claim(message, moderation=Moderation.UNSAFE)
    h.service.accept_completion(token, claim)  # direct delivery applied the quarantine once
    ref = claim.outputs[0].artifact_ref
    epoch = h.fences.epochs[f"artifact:{ref}"]
    with h.store.transaction() as tx:
        claimed = tx.claim_side_effects("crashing", h.clock.now(), timedelta(milliseconds=LEASE_MS),
                                        50)
    for item in claimed:  # the sink effect happens, then the holder dies before marking
        if isinstance(item.effect, QuarantineIntent):
            h.artifacts.quarantine(item.effect)
        else:
            h.audit.record(item.effect)
    h.clock.advance(milliseconds=LEASE_MS)
    assert h.service.deliver_side_effects(owner="restarted") == len(claimed)
    (intent,) = h.store.snapshot().quarantine_intents.values()
    assert h.artifacts.applied_events == [intent.event_id]
    assert h.artifacts.deliveries.count(intent.event_id) == 3  # direct, crashed, redelivered
    assert h.fences.epochs[f"artifact:{ref}"] == epoch  # artifact state changed only once


def test_stale_side_effect_holder_cannot_mark_or_release(h: FixtureHarness) -> None:
    h.service.create_job(h.create())
    lease = timedelta(milliseconds=LEASE_MS)
    with h.store.transaction() as tx:
        (old,) = tx.claim_side_effects("holder_a", h.clock.now(), lease, 10)
    h.clock.advance(milliseconds=LEASE_MS)
    with h.store.transaction() as tx:
        (new,) = tx.claim_side_effects("holder_b", h.clock.now(), lease, 10)
    assert new.lease.generation == old.lease.generation + 1
    with h.store.transaction() as tx:
        assert not tx.mark_side_effect(old.lease, h.clock.now())
        assert not tx.release_outbox(old.lease, "LATE")
        assert tx.mark_side_effect(new.lease, h.clock.now())
        assert not tx.mark_side_effect(new.lease, h.clock.now())  # repeated mark: no-op


def test_side_effect_delivery_never_touches_dispatch_bookkeeping(h: FixtureHarness) -> None:
    _, message = _running(h)
    h.service.accept_completion(_token(h), h.success_claim(message))
    before = h.store.snapshot().attempt_dispatch
    assert h.service.deliver_side_effects() > 0
    assert h.store.snapshot().attempt_dispatch == before


def test_rolled_back_round_leaves_no_intents_and_foreign_refs_stay_untouched(
    h: FixtureHarness,
) -> None:
    job_id, message = _running(h)
    token = _token(h)
    claim = h.success_claim(message, moderation=Moderation.UNSAFE)
    foreign = h.artifacts.put(ORG, b"foreign-output", job_id="job_other", attempt_id="att_other")
    claim = replace(claim, outputs=(*claim.outputs, foreign))
    bumped: list[int] = []
    port = h.service._d.eligibility

    class BumpOnce:
        def check(self, **kwargs: Any) -> Any:
            decision = port.check(**kwargs)
            if not bumped:  # owner change between the precheck and the write round
                bumped.append(h.fences.bump(eligibility_fence_scope(ORG)))
            return decision

    deps = h.service._d
    values = {name: getattr(deps, name) for name in deps.__dataclass_fields__}
    values["eligibility"] = BumpOnce()
    service = AiJobService(AiJobDependencies(**values))
    receipt = service.accept_completion(token, claim)
    assert bumped and receipt.authoritative and receipt.reason_code == "UNSAFE_CONTENT"
    (intent,) = h.store.snapshot().quarantine_intents.values()  # only the committed round's
    assert intent.artifact_refs == (claim.outputs[0].artifact_ref,)
    assert foreign.artifact_ref not in h.artifacts.quarantined
    assert h.artifacts.applied_events == [intent.event_id]
    assert h.store.snapshot().jobs[job_id].state is JobState.BLOCKED_UNSAFE


def test_create_and_cancel_deliver_each_stored_audit_intent_once(h: FixtureHarness) -> None:
    created = h.service.create_job(h.create())
    h.service.cancel_job(CancelJobCommand(TEACHER, "idem_cancel_b5", created.job_id,
                                          created.job_revision))
    stored = h.store.snapshot().audit_intents
    assert [e.event_type for e in stored.values()] == ["job.created", "job.cancelled"]
    assert [e.event_id for e in h.audit.events] == list(stored)  # direct delivery, stored ids
    assert h.service.deliver_side_effects() == 2
    assert [e.event_id for e in h.audit.events] == list(stored)  # redelivery deduplicated


# --------------------------------------------------------------------- notices (B-09e–g)
def _notice(notice_id: str = "notice_b5") -> CancellationNotice:
    return CancellationNotice(notice_id, ORG, "SESSION_ENDED", session_id=SESSION)


def _matching_jobs(h: FixtureHarness, count: int) -> list[str]:
    return [
        h.service.create_job(h.create(key=f"idem_n{index}", ref=request_ref(f"req_n{index}")))
        .job_id
        for index in range(count)
    ]


def _bystanders(h: FixtureHarness) -> dict[str, Any]:
    outsider = h.service.create_job(h.create(OUTSIDER, key="idem_out")).job_id
    other_session = h.service.create_job(
        h.create(key="idem_other_session", ref=request_ref("req_os"), session_id="session_x",
                 subjects=("child_fx_x",), job_type="other_type")
    ).job_id
    done = h.service.create_job(h.create(key="idem_done", ref=request_ref("req_done")))
    h.service.cancel_job(CancelJobCommand(TEACHER, "idem_done_c", done.job_id, done.job_revision))
    jobs = h.store.snapshot().jobs
    return {job_id: jobs[job_id] for job_id in (outsider, other_session, done.job_id)}


def test_notice_cancels_every_match_in_one_transaction_and_records_complete(
    h: FixtureHarness,
) -> None:
    matches = _matching_jobs(h, 51)
    bystanders = _bystanders(h)
    transactions: list[int] = []
    original = h.store.transaction

    @contextmanager
    def counted() -> Iterator[Any]:
        transactions.append(1)
        with original() as uow:
            yield uow

    h.store.transaction = counted  # type: ignore[method-assign]
    cancelled = h.service.apply_cancellation_notice(_notice())
    assert sorted(cancelled) == sorted(matches) and len(transactions) == 1
    snap = h.store.snapshot()
    assert all(snap.jobs[job_id].state is JobState.CANCELLED for job_id in matches)
    assert {job_id: snap.jobs[job_id] for job_id in bystanders} == bystanders
    recorded = snap.notices["notice_b5"]
    assert (recorded.applied_count, recorded.reason_code) == (51, "SESSION_ENDED")
    assert sorted(str(e.job_id) for e in _intents(h, "job.cancelled_by_notice")) == sorted(matches)


def test_notice_above_the_atomic_bound_fails_typed_without_any_change(h: FixtureHarness) -> None:
    _matching_jobs(h, FIXTURE_DISPATCH_POLICY.notice_atomic_max + 1)
    before = _state(h)
    with pytest.raises(AiJobError) as error:
        h.service.apply_cancellation_notice(_notice())
    assert error.value.code == "NOTICE_ATOMIC_LIMIT" and not error.value.retryable
    assert _state(h) == before and "notice_b5" not in h.store.snapshot().notices


def test_duplicate_notice_is_a_no_op(h: FixtureHarness) -> None:
    matches = _matching_jobs(h, 3)
    assert sorted(h.service.apply_cancellation_notice(_notice())) == sorted(matches)
    before = _state(h)
    assert h.service.apply_cancellation_notice(_notice()) == ()
    assert _state(h) == before


def test_crash_mid_notice_rolls_back_and_redelivery_cancels_all(h: FixtureHarness) -> None:
    matches = _matching_jobs(h, 5)
    faults = faulty(h)
    before = _state(h)
    faults.fail_commit_after_write = True
    with pytest.raises(RuntimeError, match="injected"):
        h.service.apply_cancellation_notice(_notice())
    assert _state(h) == before  # no partial cancellation, no COMPLETE marker
    assert sorted(h.service.apply_cancellation_notice(_notice())) == sorted(matches)
    assert h.service.apply_cancellation_notice(_notice()) == ()
    assert all(h.store.snapshot().jobs[j].state is JobState.CANCELLED for j in matches)


def test_concurrent_duplicate_notice_loses_on_the_notice_key(h: FixtureHarness) -> None:
    matches = _matching_jobs(h, 4)
    faults = faulty(h)
    winner: list[tuple[str, ...]] = []
    faults.raise_before["record_notice"] = UniqueConflict("cancellation_notice")
    faults.on_raise["record_notice"] = _competing(
        faults, lambda: h.service.apply_cancellation_notice(_notice()), winner
    )
    assert h.service.apply_cancellation_notice(_notice()) == ()  # lost, then saw it recorded
    assert winner and sorted(winner[0]) == sorted(matches)
    assert h.store.snapshot().notices["notice_b5"].applied_count == 4
    assert len(_intents(h, "job.cancelled_by_notice")) == 4  # each job cancelled once


def test_unrelated_unique_conflict_in_a_notice_is_not_swallowed(h: FixtureHarness) -> None:
    _matching_jobs(h, 2)
    faults = faulty(h)
    before = _state(h)
    faults.raise_before["add_audit_intent"] = UniqueConflict("outbox")
    with pytest.raises(UniqueConflict):
        h.service.apply_cancellation_notice(_notice())
    assert _state(h) == before


# ------------------------------------------- B5-R01 fair traversal past failing side effects
def _audit_backlog(h: FixtureHarness, count: int) -> None:
    """``count`` older undelivered audit intents (job.created), ahead of later work."""

    for index in range(count):
        h.service.create_job(h.create(key=f"idem_bl{index}", ref=request_ref(f"req_bl{index}")))


def _calls(target: Any, name: str, monkeypatch: pytest.MonkeyPatch, *, down: bool) -> list[str]:
    seen: list[str] = []
    original = getattr(target, name)

    def call(effect: Any) -> None:
        seen.append(effect.event_id)
        if down:
            raise ConnectionError("sink unavailable")
        original(effect)

    monkeypatch.setattr(target, name, call)
    return seen


def test_failing_audit_backlog_never_starves_a_healthy_quarantine(
    h: FixtureHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    limit = FIXTURE_DISPATCH_POLICY.claim_limit
    _audit_backlog(h, limit + 5)  # more failing audit rows than one claim page
    _, message = _running(h, key="idem_r01", request="req_r01")
    claim = h.success_claim(message, moderation=Moderation.UNSAFE)
    with monkeypatch.context() as down:  # both sinks down while the completion commits
        _calls(h.audit, "record", down, down=True)
        _calls(h.artifacts, "quarantine", down, down=True)
        assert h.service.accept_completion(_token(h), claim).authoritative
    assert h.artifacts.quarantined == {}
    audit_calls = _calls(h.audit, "record", monkeypatch, down=True)  # audit stays down
    quarantine_calls = _calls(h.artifacts, "quarantine", monkeypatch, down=False)
    assert h.service.deliver_side_effects() == 1  # the healthy quarantine, in the first pass
    (intent,) = h.store.snapshot().quarantine_intents.values()
    assert quarantine_calls == [intent.event_id]
    assert claim.outputs[0].artifact_ref in h.artifacts.quarantined
    snap = h.store.snapshot()
    pending_audits = [e for e in snap.audit_intents if e not in snap.side_effects_delivered]
    assert len(pending_audits) == len(snap.audit_intents)  # audit work retained, not dropped
    assert sorted(audit_calls) == sorted(pending_audits)  # each tried once in that pass
    assert h.service.deliver_side_effects() == 0
    assert quarantine_calls == [intent.event_id]  # no duplicate effect on later passes
    monkeypatch.undo()
    assert h.service.deliver_side_effects() == len(pending_audits)  # audit recovers: retried
    assert h.artifacts.applied_events == [intent.event_id]


def test_all_failing_side_effects_terminate_with_each_row_tried_once(
    h: FixtureHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    limit = FIXTURE_DISPATCH_POLICY.claim_limit
    _audit_backlog(h, 2 * limit + 3)  # several full pages, all failing
    calls = _calls(h.audit, "record", monkeypatch, down=True)
    assert h.service.deliver_side_effects() == 0
    snap = h.store.snapshot()
    assert sorted(calls) == sorted(snap.audit_intents)  # finite: every row exactly once
    assert snap.side_effect_leases == {}  # all released for the next invocation
    assert h.service.deliver_side_effects() == 0
    assert len(calls) == 2 * len(snap.audit_intents)


def test_side_effect_delivery_does_not_chase_continuously_arriving_work(
    h: FixtureHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    _audit_backlog(h, 2)
    initial = set(h.store.snapshot().audit_intents)
    policy = replace(FIXTURE_DISPATCH_POLICY, claim_limit=2)
    service = AiJobService(replace(h.service._d, dispatch_policy=policy))
    original = h.audit.record
    calls: list[str] = []

    def producer(event: AuditEvent) -> None:
        calls.append(event.event_id)
        assert len(calls) <= len(initial), "delivery chased new arrivals beyond its budget"
        original(event)
        h.clock.advance(seconds=1)
        arrived = AuditEvent("job.probe", ORG, None, None,
                             event_id=f"producer_{len(calls)}")
        with h.store.transaction() as tx:
            tx.add_audit_intent(arrived.event_id, arrived)

    monkeypatch.setattr(h.audit, "record", producer)
    assert service.deliver_side_effects() == len(initial)
    assert set(calls) == initial
    with h.store.transaction() as tx:
        assert tx.pending_side_effects_count() == len(initial)
    monkeypatch.undo()
    assert service.deliver_side_effects() == len(initial)
    assert service.deliver_side_effects() == 0
