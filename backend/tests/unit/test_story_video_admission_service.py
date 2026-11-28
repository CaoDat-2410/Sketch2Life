"""FEAT-066 T-1a: the admission saga and the progress service over fake ports and a fake repository.

The SQL behaviour (locks, the CHECKs, the partial uniques, the purge) is in
``tests/integration/story_video/test_video_generations_postgres.py``. Here the order of the steps
and the meaning of each port outcome are pinned: the intent is stored first, both ports are called
with no transaction open, a refusal releases the reservation, an unreadable answer leaves the
intent pending, and no timer or error ever rejects an intent.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_video import (
    AckStatus,
    AdmissionDecision,
    GenerationRecord,
    IntentResult,
    ProgressEvent,
    ProgressResult,
    QuotaResult,
    QuotaStatus,
    ReservationResult,
    ReservationStatus,
    StoryVideoAdapters,
    VideoRequestScope,
)
from sketch2life.application.services.story_run_video import (
    StoryVideoAdmissionService,
    StoryVideoProgressService,
)

PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer="issuer-1", roles=frozenset())
RUN = "11111111-1111-4111-8111-111111111111"
GEN = "22222222-2222-4222-8222-222222222222"
HASH = "a" * 64


def _record(**changes: Any) -> GenerationRecord:
    values: dict[str, Any] = {
        "generation_id": GEN,
        "run_id": RUN,
        "scope_kind": "PARENT_ACCOUNT",
        "scope_ref": "s" * 64,
        "state": "ADMISSION_PENDING",
        "kind": "INITIAL",
        "generation_no": None,
        "job_ref": None,
        "key_hash": "k" * 64,
        "fingerprint": "f" * 64,
        "script_hash": HASH,
        "story_revision_id": "r1",
        "review_id": "rv1",
        "quality_reason_code": None,
        "compute_reservation_ref": None,
        "compute_released_at": None,
        "billing_quota_usage_ref": None,
        "safe_failure_code": None,
        "started": False,
        "generation_revision": 1,
        "run_state": "VIDEO_ADMISSION_PENDING",
        "run_revision": 6,
    }
    values.update(changes)
    return GenerationRecord(**values)


@dataclass
class FakeRepo:
    """In-memory stand-in: one generation, a log of the steps, a flag for an open transaction."""

    record: GenerationRecord = field(default_factory=_record)
    log: list[str] = field(default_factory=list)
    in_transaction: bool = False
    replay: bool = False
    available_seen: list[bool] = field(default_factory=list)
    open_rows: list[GenerationRecord] = field(default_factory=list)
    closures: list[GenerationRecord] = field(default_factory=list)
    orphans: list[GenerationRecord] = field(default_factory=list)
    cancel_applies: bool = True

    def begin_intent(self, **kwargs: Any) -> IntentResult:
        self.log.append("tx1")
        self.available_seen.append(kwargs["adapters_available"])
        return IntentResult(self.record, self.replay)

    def finish_admission(
        self, generation_id: str, decision: AdmissionDecision
    ) -> GenerationRecord | None:
        reject = f"tx2:reject:{decision.refusal_code}"
        self.log.append("tx2:accept" if decision.accepted else reject)
        if self.record.state != "ADMISSION_PENDING":
            return self.record
        if decision.accepted:
            self.record = replace(
                self.record,
                state="ACCEPTED",
                generation_no=1,
                job_ref="vjob_" + "1" * 32,
                compute_reservation_ref=decision.reservation_ref,
                billing_quota_usage_ref=decision.usage_ref,
                run_state="VIDEO_QUEUED",
                run_revision=7,
            )
        else:
            self.record = replace(
                self.record,
                state="ADMISSION_REJECTED",
                safe_failure_code=decision.refusal_code,
                compute_reservation_ref=decision.reservation_ref,
                run_state="SCRIPT_REVIEW",
                run_revision=7,
            )
        return self.record

    def mark_compute_closed(self, generation_id: str) -> None:
        self.log.append("closed")
        self.record = replace(self.record, compute_released_at="now")

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        return self.record

    def pending_intents(self, limit: int, run_id: str | None = None) -> list[GenerationRecord]:
        return [self.record] if self.record.state == "ADMISSION_PENDING" else []

    def pending_compute_closures(self, limit: int) -> list[GenerationRecord]:
        return self.closures

    def open_generations(self, run_id: str) -> list[GenerationRecord]:
        return self.open_rows

    def orphaned_in_flight(self, limit: int) -> list[GenerationRecord]:
        return self.orphans

    def advance(self, generation_id: str, event: ProgressEvent) -> ProgressResult:
        self.log.append(f"advance:{event.expected_state}>{event.target_state}")
        self.record = replace(self.record, state=event.target_state)
        return ProgressResult(True, self.record)

    def fail_for_cancelled_run(self, generation_id: str) -> ProgressResult:
        self.log.append("cancel_fail")
        if not self.cancel_applies:
            return ProgressResult(False, self.record, "STALE")
        self.record = replace(self.record, state="FAILED", safe_failure_code="RUN_CANCELLED")
        return ProgressResult(True, self.record)


@dataclass
class Ports:
    repo: FakeRepo
    reserve_results: list[Any] = field(default_factory=list)
    quota_results: list[Any] = field(default_factory=list)
    release_results: list[AckStatus] = field(default_factory=list)
    settle_results: list[AckStatus] = field(default_factory=list)
    open_during_call: list[bool] = field(default_factory=list)
    quota_scopes: list[VideoRequestScope] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    delay: float = 0.0

    def reserve(self, **kwargs: Any) -> ReservationResult:
        self.calls.append("reserve")
        self.repo.log.append("reserve")
        self.open_during_call.append(self.repo.in_transaction)
        if self.delay:
            time.sleep(self.delay)
        item = self.reserve_results.pop(0) if self.reserve_results else None
        if isinstance(item, BaseException):
            raise item
        return item or ReservationResult(ReservationStatus.RESERVED, "res-1")

    def release(self, **kwargs: Any) -> AckStatus:
        self.calls.append("release")
        self.repo.log.append("release")
        self.open_during_call.append(self.repo.in_transaction)
        return self.release_results.pop(0) if self.release_results else AckStatus.DONE

    def settle(self, **kwargs: Any) -> AckStatus:
        self.calls.append(f"settle:{kwargs['outcome']}")
        self.repo.log.append("settle")
        return self.settle_results.pop(0) if self.settle_results else AckStatus.DONE

    def admit_video_request(self, **kwargs: Any) -> QuotaResult:
        self.calls.append("admit")
        self.repo.log.append("admit")
        self.open_during_call.append(self.repo.in_transaction)
        assert kwargs["contract_version"] == "video-quota-port-v1"
        assert isinstance(kwargs["scope"], VideoRequestScope)
        self.quota_scopes.append(kwargs["scope"])
        item = self.quota_results.pop(0) if self.quota_results else None
        return item or QuotaResult(QuotaStatus.ACCEPTED, "usage-1", "grant-1")


def _service(
    repo: FakeRepo, ports: Ports | None = None, *, timeout: float = 2.0, configured: bool = True
) -> StoryVideoAdmissionService:
    adapters = (
        StoryVideoAdapters(reservation=ports, quota=ports)
        if configured and ports is not None
        else None
    )
    return StoryVideoAdmissionService(repo, adapters, call_timeout_seconds=timeout)


def _request(service: StoryVideoAdmissionService) -> Any:
    return service.request(
        principal=PRINCIPAL,
        run_id=RUN,
        expected_revision=5,
        story_sha256=HASH,
        quality_reason_code=None,
        idempotency_key="key-1",
    )


# ------------------------------------------------------------------------------- the saga
def test_both_receipts_clear_accepts_after_the_intent_and_with_no_transaction_open() -> None:
    repo = FakeRepo()
    ports = Ports(repo)
    outcome = _request(_service(repo, ports))
    assert outcome.record.state == "ACCEPTED" and outcome.record.generation_no == 1
    assert outcome.record.job_ref is not None
    # the intent is stored first, the compute reservation comes before the quota admission
    assert repo.log == ["tx1", "reserve", "admit", "tx2:accept"]
    assert ports.open_during_call == [False, False]
    assert repo.available_seen == [True]
    assert repo.record.compute_reservation_ref == "res-1"
    assert repo.record.billing_quota_usage_ref == "usage-1"
    assert ports.quota_scopes == [VideoRequestScope("PARENT_ACCOUNT", "s" * 64)]


def test_teacher_quota_scope_carries_the_active_teacher_account_id() -> None:
    repo = FakeRepo(
        record=_record(
            scope_kind="ORGANIZATION",
            scope_ref="organization-1",
            teacher_account_id="teacher-account-1",
        )
    )
    ports = Ports(repo)

    _request(_service(repo, ports))

    assert ports.quota_scopes == [
        VideoRequestScope("ORGANIZATION", "organization-1", "teacher-account-1")
    ]


@pytest.mark.parametrize(
    ("quota", "code", "status"),
    [
        (QuotaStatus.QUOTA_EXCEEDED, "VIDEO_QUOTA_EXCEEDED", 409),
        (QuotaStatus.QUOTA_ALLOCATION_NOT_FOUND, "QUOTA_ALLOCATION_NOT_FOUND", 409),
        (QuotaStatus.TEACHER_QUOTA_INSUFFICIENT, "TEACHER_QUOTA_INSUFFICIENT", 409),
        (QuotaStatus.SCHOOL_QUOTA_INSUFFICIENT, "SCHOOL_QUOTA_INSUFFICIENT", 409),
        (QuotaStatus.SUBSCRIPTION_RESTRICTED, "SUBSCRIPTION_RESTRICTED", 409),
    ],
)
def test_a_quota_refusal_rejects_the_intent_and_releases_the_reservation(
    quota: QuotaStatus, code: str, status: int
) -> None:
    repo = FakeRepo()
    ports = Ports(repo, quota_results=[QuotaResult(quota)])
    with pytest.raises(ParentStoryRunError) as raised:
        _request(_service(repo, ports))
    assert (raised.value.status_code, raised.value.code) == (status, code)
    assert repo.record.state == "ADMISSION_REJECTED"
    assert repo.record.generation_no is None and repo.record.job_ref is None
    assert repo.record.billing_quota_usage_ref is None
    assert repo.log == ["tx1", "reserve", "admit", f"tx2:reject:{code}", "release", "closed"]
    assert repo.record.compute_released_at is not None
    assert ports.open_during_call == [False, False, False]


def test_a_cost_refusal_stops_before_the_quota_and_has_no_reservation_to_release() -> None:
    repo = FakeRepo()
    ports = Ports(repo, reserve_results=[ReservationResult(ReservationStatus.COST_LIMIT_REACHED)])
    with pytest.raises(ParentStoryRunError) as raised:
        _request(_service(repo, ports))
    assert (raised.value.status_code, raised.value.code) == (503, "AI_COST_LIMIT_REACHED")
    assert "admit" not in ports.calls and "release" not in ports.calls
    assert repo.log == ["tx1", "reserve", "tx2:reject:AI_COST_LIMIT_REACHED"]
    assert repo.record.state == "ADMISSION_REJECTED"


def test_a_release_that_cannot_be_answered_keeps_the_reservation_for_the_reconciler() -> None:
    repo = FakeRepo()
    ports = Ports(
        repo,
        quota_results=[QuotaResult(QuotaStatus.QUOTA_EXCEEDED)],
        release_results=[AckStatus.UNAVAILABLE],
    )
    with pytest.raises(ParentStoryRunError):
        _request(_service(repo, ports))
    assert repo.record.compute_reservation_ref == "res-1"
    assert repo.record.compute_released_at is None  # never lost
    repo.closures = [repo.record]
    report = _service(repo, ports).reconcile_pending_admissions()
    assert report.compute_closed == 1 and repo.record.compute_released_at is not None


@pytest.mark.parametrize("stage", ["reserve", "quota"])
def test_an_unreadable_answer_leaves_the_intent_pending(stage: str) -> None:
    repo = FakeRepo()
    ports = Ports(repo)
    if stage == "reserve":
        ports.reserve_results = [ReservationResult(ReservationStatus.UNAVAILABLE)]
    else:
        ports.quota_results = [QuotaResult(QuotaStatus.UNAVAILABLE)]
    outcome = _request(_service(repo, ports))
    assert outcome.record.state == "ADMISSION_PENDING"
    assert outcome.record.job_ref is None and outcome.record.generation_no is None
    assert not any(entry.startswith("tx2") for entry in repo.log)  # no verdict, no rejection
    assert ("admit" in ports.calls) is (stage == "quota")


def test_a_port_that_raises_or_times_out_is_read_as_unavailable() -> None:
    repo = FakeRepo()
    ports = Ports(repo, reserve_results=[RuntimeError("boom")])
    assert _request(_service(repo, ports)).record.state == "ADMISSION_PENDING"
    slow_repo = FakeRepo()
    slow = Ports(slow_repo, delay=0.4)
    outcome = _request(_service(slow_repo, slow, timeout=0.05))
    assert outcome.record.state == "ADMISSION_PENDING"
    assert "admit" not in slow.calls


def test_a_changed_payload_under_one_key_stays_pending_and_is_a_key_error() -> None:
    repo = FakeRepo()
    ports = Ports(repo, quota_results=[QuotaResult(QuotaStatus.IDEMPOTENCY_MISMATCH)])
    with pytest.raises(ParentStoryRunError) as raised:
        _request(_service(repo, ports))
    assert (raised.value.status_code, raised.value.code) == (400, "INVALID_IDEMPOTENCY_KEY")
    assert repo.record.state == "ADMISSION_PENDING"
    assert not any(entry.startswith("tx2") for entry in repo.log)


def test_without_adapters_the_repository_is_told_and_nothing_is_called() -> None:
    repo = FakeRepo()
    service = _service(repo, None, configured=False)
    assert _request(service).record.state == "ADMISSION_PENDING"
    assert repo.available_seen == [False]
    assert repo.log == ["tx1"]


# ------------------------------------------------------------------------------- replays
def test_a_replay_of_a_rejected_intent_repeats_the_refusal_without_a_port_call() -> None:
    repo = FakeRepo(
        record=_record(state="ADMISSION_REJECTED", safe_failure_code="VIDEO_QUOTA_EXCEEDED"),
        replay=True,
    )
    ports = Ports(repo)
    with pytest.raises(ParentStoryRunError) as raised:
        _request(_service(repo, ports))
    assert (raised.value.status_code, raised.value.code) == (409, "VIDEO_QUOTA_EXCEEDED")
    assert ports.calls == []


def test_a_replay_of_a_cost_refusal_is_the_same_503() -> None:
    repo = FakeRepo(
        record=_record(state="ADMISSION_REJECTED", safe_failure_code="AI_COST_LIMIT_REACHED"),
        replay=True,
    )
    with pytest.raises(ParentStoryRunError) as raised:
        _request(_service(repo, Ports(repo)))
    assert (raised.value.status_code, raised.value.code) == (503, "AI_COST_LIMIT_REACHED")


def test_a_replay_of_an_accepted_request_answers_its_current_state_without_a_port_call() -> None:
    repo = FakeRepo(
        record=_record(state="GENERATING", generation_no=1, job_ref="vjob_" + "2" * 32),
        replay=True,
    )
    ports = Ports(repo)
    outcome = _request(_service(repo, ports))
    assert outcome.record.state == "GENERATING" and ports.calls == []


def test_a_replay_of_a_pending_intent_asks_the_ports_again_with_the_same_key() -> None:
    repo = FakeRepo(replay=True)
    ports = Ports(repo)
    outcome = _request(_service(repo, ports))
    assert outcome.record.state == "ACCEPTED"
    assert ports.calls == ["reserve", "admit"]


def test_a_purged_replay_returns_the_projection() -> None:
    class Purged(FakeRepo):
        def begin_intent(self, **kwargs: Any) -> IntentResult:
            return IntentResult(None, True, "projection")  # type: ignore[arg-type]

    outcome = _request(_service(Purged(), Ports(FakeRepo())))
    assert outcome.record is None and outcome.projection == "projection"


# -------------------------------------------------------------------------- reconciler
def test_the_reconciler_resolves_a_pending_intent_with_the_same_key() -> None:
    repo = FakeRepo()
    ports = Ports(
        repo,
        reserve_results=[ReservationResult(ReservationStatus.UNAVAILABLE)],
    )
    service = _service(repo, ports)
    assert _request(service).record.state == "ADMISSION_PENDING"
    report = service.reconcile_pending_admissions()
    assert (report.resolved, report.still_pending, report.mismatched) == (1, 0, 0)
    assert repo.record.state == "ACCEPTED"
    assert ports.calls == ["reserve", "reserve", "admit"]


def test_the_reconciler_counts_what_stays_pending_and_what_is_a_key_error() -> None:
    repo = FakeRepo()
    ports = Ports(repo, quota_results=[QuotaResult(QuotaStatus.UNAVAILABLE)])
    report = _service(repo, ports).reconcile_pending_admissions()
    assert (report.resolved, report.still_pending) == (0, 1)
    ports.quota_results = [QuotaResult(QuotaStatus.IDEMPOTENCY_MISMATCH)]
    report = _service(repo, ports).reconcile_pending_admissions()
    assert report.mismatched == 1 and repo.record.state == "ADMISSION_PENDING"


def test_no_timer_exists_that_rejects_an_intent() -> None:
    import sketch2life.application.services.story_run_video as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    for word in ("expires", "timeout_rejects", "ADMISSION_REJECTED_BY_TIMEOUT", "datetime"):
        assert word not in source


# ----------------------------------------------------------------- cancel and progress
def test_a_cancelled_pending_intent_is_resolved_and_an_admitted_unit_stays_consumed() -> None:
    repo = FakeRepo(record=_record(run_state="DELETE_PENDING"))
    ports = Ports(repo)
    repo.open_rows = [repo.record]
    original = repo.finish_admission

    def finish_cancelled(generation_id: str, decision: AdmissionDecision) -> GenerationRecord:
        repo.log.append("tx2:cancelled")
        repo.record = replace(
            repo.record,
            state="FAILED",
            generation_no=1,
            job_ref="vjob_" + "3" * 32,
            safe_failure_code="RUN_CANCELLED",
            compute_reservation_ref=decision.reservation_ref,
            billing_quota_usage_ref=decision.usage_ref,
        )
        return repo.record

    repo.finish_admission = finish_cancelled  # type: ignore[method-assign]
    StoryVideoProgressService(
        repo, StoryVideoAdapters(reservation=ports, quota=ports)
    ).on_run_cancelled(RUN)
    assert repo.record.state == "FAILED" and repo.record.safe_failure_code == "RUN_CANCELLED"
    assert repo.record.billing_quota_usage_ref == "usage-1"  # consumed, never refunded
    assert ports.calls == ["reserve", "admit", "release"]  # nothing started: release, not settle
    assert repo.record.compute_released_at is not None
    del original


@pytest.mark.parametrize(("started", "expected"), [(False, ["release"]), (True, ["settle:FAILED"])])
def test_a_cancelled_in_flight_generation_releases_or_settles_by_whether_it_started(
    started: bool, expected: list[str]
) -> None:
    repo = FakeRepo(
        record=_record(
            state="GENERATING" if started else "QUEUED",
            generation_no=1,
            job_ref="vjob_" + "4" * 32,
            compute_reservation_ref="res-1",
            started=started,
            run_state="DELETE_PENDING",
        )
    )
    repo.open_rows = [repo.record]
    ports = Ports(repo)
    # the repository reports the row after the step; ``started`` survives it
    original = repo.fail_for_cancelled_run

    def fail(generation_id: str) -> ProgressResult:
        result = original(generation_id)
        repo.record = replace(repo.record, started=started)
        return ProgressResult(result.applied, repo.record)

    repo.fail_for_cancelled_run = fail  # type: ignore[method-assign]
    StoryVideoProgressService(
        repo, StoryVideoAdapters(reservation=ports, quota=ports)
    ).on_run_cancelled(RUN)
    assert repo.record.state == "FAILED" and ports.calls == expected


def test_a_late_worker_result_after_cancel_is_a_no_op_that_calls_no_port() -> None:
    repo = FakeRepo(record=_record(state="QUEUED", generation_no=1, run_state="DELETE_PENDING"))
    repo.open_rows = [repo.record]
    repo.cancel_applies = False
    ports = Ports(repo)
    StoryVideoProgressService(
        repo, StoryVideoAdapters(reservation=ports, quota=ports)
    ).on_run_cancelled(RUN)
    assert ports.calls == [] and repo.record.state == "QUEUED"


@pytest.mark.parametrize(
    ("target", "started", "expected"),
    [
        ("READY", True, ["settle:COMPLETED"]),
        ("SAFETY_BLOCKED", True, ["settle:SAFETY_BLOCKED"]),
        ("FAILED", True, ["settle:FAILED"]),
        ("FAILED", False, ["release"]),
        ("GENERATING", True, []),
    ],
)
def test_progress_settles_the_compute_reservation_only_when_the_request_ends(
    target: str, started: bool, expected: list[str]
) -> None:
    repo = FakeRepo(
        record=_record(
            state="GENERATING",
            generation_no=1,
            job_ref="vjob_" + "5" * 32,
            compute_reservation_ref="res-1",
            started=started,
        )
    )
    ports = Ports(repo)
    service = StoryVideoProgressService(repo, StoryVideoAdapters(reservation=ports, quota=ports))
    result = service.apply(
        GEN, ProgressEvent(expected_state="GENERATING", target_state=target, safe_failure_code="X")
    )
    assert result.applied and ports.calls == expected


# ------------------------------------------------------------- review R1 fixes (F-01, F-02, F-03)
@pytest.mark.parametrize("stage", ["reservation", "quota"])
def test_an_accepted_answer_without_its_ref_is_an_unreadable_answer(stage: str) -> None:
    repo = FakeRepo()
    ports = Ports(repo)
    if stage == "reservation":
        ports.reserve_results = [ReservationResult(ReservationStatus.RESERVED, None)]
    else:
        ports.quota_results = [QuotaResult(QuotaStatus.ACCEPTED, None, "grant-1")]
    outcome = _request(_service(repo, ports))
    assert outcome.record.state == "ADMISSION_PENDING"
    assert not any(entry.startswith("tx2") for entry in repo.log)  # no unrecordable accept
    assert ("admit" in ports.calls) is (stage == "quota")
    # the same key asks again and a complete answer settles it
    report = _service(repo, ports).reconcile_pending_admissions()
    assert report.resolved == 1 and repo.record.state == "ACCEPTED"


def test_the_reconciler_fails_the_in_flight_rows_of_cancelled_runs_and_closes_compute() -> None:
    repo = FakeRepo(
        record=_record(
            state="GENERATING",
            generation_no=1,
            job_ref="vjob_" + "6" * 32,
            compute_reservation_ref="res-1",
            started=True,
            run_state="DELETE_PENDING",
        )
    )
    repo.orphans = [repo.record]
    ports = Ports(repo)
    original = repo.fail_for_cancelled_run

    def fail(generation_id: str) -> ProgressResult:
        result = original(generation_id)
        repo.record = replace(repo.record, started=True)
        return ProgressResult(result.applied, repo.record)

    repo.fail_for_cancelled_run = fail  # type: ignore[method-assign]
    report = _service(repo, ports).reconcile_pending_admissions()
    assert report.cancelled_settled == 1
    assert repo.record.state == "FAILED" and repo.record.safe_failure_code == "RUN_CANCELLED"
    assert ports.calls == ["settle:FAILED"] and repo.record.compute_released_at is not None


def test_a_sweep_row_that_is_already_settled_is_a_recorded_no_op() -> None:
    repo = FakeRepo(record=_record(state="QUEUED", generation_no=1, run_state="DELETE_PENDING"))
    repo.orphans = [repo.record]
    repo.cancel_applies = False
    ports = Ports(repo)
    report = _service(repo, ports).reconcile_pending_admissions()
    assert report.cancelled_settled == 0 and ports.calls == []


def test_a_cancel_fails_the_in_flight_row_before_it_waits_on_a_pending_intent() -> None:
    repo = FakeRepo(record=_record(state="QUEUED", generation_no=1, run_state="DELETE_PENDING"))
    pending = _record(generation_id="gen-pending", run_state="DELETE_PENDING")
    repo.open_rows = [pending, repo.record]
    ports = Ports(repo)
    order: list[str] = []
    service = StoryVideoProgressService(repo, StoryVideoAdapters(reservation=ports, quota=ports))
    original = repo.fail_for_cancelled_run

    def fail(generation_id: str) -> ProgressResult:
        order.append("fail")
        return original(generation_id)

    repo.fail_for_cancelled_run = fail  # type: ignore[method-assign]
    service._admission.resolve = lambda record: order.append("resolve") or record  # type: ignore[method-assign]
    service.on_run_cancelled(RUN)
    assert order == ["fail", "resolve"]


@pytest.mark.parametrize("state", ["REJECTED_BY_ADULT", "SUPERSEDED"])
def test_a_closure_of_a_choice_made_by_the_adult_settles_as_completed(state: str) -> None:
    repo = FakeRepo(
        record=_record(state=state, generation_no=1, compute_reservation_ref="res-1", started=True)
    )
    repo.closures = [repo.record]
    ports = Ports(repo)
    report = _service(repo, ports).reconcile_pending_admissions()
    assert report.compute_closed == 1 and ports.calls == ["settle:COMPLETED"]
