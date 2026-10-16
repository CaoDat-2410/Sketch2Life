"""BE2-01 Phase B batch B3: owner-decision fence on real PostgreSQL (plan rev3 §5.1, B-09a–d).

ASSUMED_CONTRACT: the owner side is the test-only ``owner_fence_fixture`` schema implementing
the assumed OwnerFenceV1/0.1-candidate contract, not a P2 adapter (real integration is B-12).
An owner change is committed between BE2's precheck and its write transaction with the
cancellation notice withheld, so BE2's ``job_revision`` CAS alone would not notice it.
``requires_postgres``; skipped means NOT_RUN.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from dataclasses import replace
from hashlib import sha256

import b3_support as s
import pytest
from sketch2life.application.ports.ai_jobs import (
    AuthorizationAction,
    EligibilityDecision,
    OwnerFence,
)
from sketch2life.application.services.ai_jobs import AiJobError, CancelJobCommand, StartResult
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    Moderation,
    OutcomeKind,
    OutputRef,
)
from sketch2life.domain.ai_jobs.model import JobScope, JobState, RequestRef, ResultDisposition
from sketch2life.infrastructure.ai_jobs.harness import ORG, TEACHER
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres

ELIGIBILITY = fx.eligibility_scope(ORG, s.REQUESTS[0])
GRANT = fx.grant_scope(ORG, TEACHER.principal_id)


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


def _queued(rig: s.SqlRig) -> tuple[str, str]:
    created = rig.service.create_job(s.command())
    return created.job_id, rig.job(created.job_id).active_attempt.attempt_id


def _started(rig: s.SqlRig) -> tuple[str, str]:
    job_id, attempt_id = _queued(rig)
    started = rig.service.start_attempt(rig.capability(job_id), job_id, attempt_id)
    assert started.started
    return job_id, attempt_id


def _claim(
    rig: s.SqlRig, job_id: str, attempt_id: str, ref: str = "artifact_b3_1"
) -> CompletionClaim:
    digest = sha256(f"synthetic-output:{ref}".encode()).hexdigest()
    rig.owner.set(
        fx.artifact_scope(ref),
        {
            "sha256": digest,
            "organization_id": ORG,
            "producer_job_id": job_id,
            "producer_attempt_id": attempt_id,
        },
    )
    pinned = rig.job(job_id).active_attempt.request_ref
    return CompletionClaim(
        job_id=job_id,
        attempt_id=attempt_id,
        expected_request_revision=pinned.request_revision,
        input_hash=pinned.input_hash,
        context_revision=pinned.context_revision,
        kind=OutcomeKind.SUCCESS,
        outputs=(OutputRef(ref, digest),),
        moderation=Moderation.PASSED,
    )


def test_b09a_consent_revoked_before_start_write_is_not_authorised(db: URL) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id = _queued(rig)
    before = rig.job(job_id)

    def revoke(call: int) -> None:
        if call == 1:  # owner commits after BE2's precheck, notice withheld
            rig.owner.change(
                ELIGIBILITY,
                {"eligible": False, "reason_code": "CONSENT_REVOKED"},
                notice_id="notice_b09a_start",
            )

    service = rig.with_ports(
        eligibility=s.HookedEligibility(fx.FixtureEligibility(rig.owner), revoke)
    )
    rig.holds.clear()
    result = service.start_attempt(rig.capability(job_id), job_id, attempt_id)
    assert result == StartResult(False, "CONSENT_REVOKED")
    assert [hold.current for hold in rig.holds] == [False, True]  # stale, then re-decided
    after = rig.job(job_id)
    assert after.state is JobState.CANCELLED
    assert after.active_attempt.started_at is None
    assert after.job_revision == before.job_revision + 1  # only the fenced cancel
    assert rig.owner.withheld_notices() == 1


def test_b09a_repeatedly_stale_decision_returns_typed_outcome_and_writes_nothing(
    db: URL,
) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id = _queued(rig)
    before = rig.job(job_id)

    def bump(call: int) -> None:
        rig.owner.change(ELIGIBILITY, {"eligible": True}, notice_id=f"notice_b09a_{call}")

    service = rig.with_ports(
        eligibility=s.HookedEligibility(fx.FixtureEligibility(rig.owner), bump)
    )
    rig.holds.clear()
    result = service.start_attempt(rig.capability(job_id), job_id, attempt_id)
    assert result == StartResult(False, "STALE_CONTEXT")
    assert [hold.current for hold in rig.holds] == [False, False]
    assert rig.job(job_id) == before


def test_b09a_consent_revoked_before_completion_write_is_not_accepted(db: URL) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id = _started(rig)
    claim = _claim(rig, job_id, attempt_id)

    def revoke(call: int) -> None:
        if call == 1:
            rig.owner.change(
                ELIGIBILITY,
                {"eligible": False, "reason_code": "CONSENT_REVOKED"},
                notice_id="notice_b09a_completion",
            )

    service = rig.with_ports(
        eligibility=s.HookedEligibility(fx.FixtureEligibility(rig.owner), revoke)
    )
    rig.holds.clear()
    receipt = service.accept_completion(rig.capability(job_id), claim)
    assert (receipt.disposition, receipt.reason_code) == (
        ResultDisposition.REJECTED,
        "CONSENT_REVOKED",
    )
    assert [hold.current for hold in rig.holds] == [False, True]
    job = rig.job(job_id)
    assert job.state is JobState.CANCELLED and job.result_refs == ()
    descriptor = fx.FixtureArtifacts(rig.owner).describe("artifact_b3_1")
    assert descriptor is not None and descriptor.quarantine_reason == "CONSENT_REVOKED"


def test_b09b_artifact_quarantined_before_completion_write_is_not_accepted(db: URL) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id = _started(rig)
    claim = _claim(rig, job_id, attempt_id)
    changed: list[str] = []

    def quarantine(ref: str) -> None:
        if not changed:
            found = rig.owner.read(fx.artifact_scope(ref))
            assert found is not None
            rig.owner.change(
                fx.artifact_scope(ref),
                {**found[0], "quarantine_reason": "OWNER_QUARANTINE"},
                notice_id="notice_b09b",
            )
            changed.append(ref)

    service = rig.with_ports(
        artifacts=s.HookedArtifacts(fx.FixtureArtifacts(rig.owner), quarantine)
    )
    rig.holds.clear()
    receipt = service.accept_completion(rig.capability(job_id), claim)
    assert [hold.current for hold in rig.holds] == [False, True]
    assert (receipt.disposition, receipt.reason_code) == (
        ResultDisposition.REJECTED,
        "OUTPUT_MALFORMED",
    )
    job = rig.job(job_id)
    assert job.state is JobState.FAILED_EXHAUSTED and job.result_refs == ()


def test_b09c_grant_revoked_before_create_write_creates_nothing(db: URL) -> None:
    rig = s.build_rig(db)

    def revoke(action: AuthorizationAction, call: int) -> None:
        if call == 1 and action is AuthorizationAction.CREATE_JOB:
            rig.owner.change(
                GRANT, {"actions": ["read_job", "cancel_job"]}, notice_id="notice_b09c_create"
            )

    service = rig.with_ports(
        authorization=s.HookedAuthorization(fx.FixtureAuthorization(rig.owner), revoke)
    )
    rig.holds.clear()
    with pytest.raises(AiJobError) as error:
        service.create_job(s.command())
    assert (error.value.code, error.value.http_status) == ("FORBIDDEN_SCOPE", 403)
    assert [hold.current for hold in rig.holds] == [False]
    assert all(value == 0 for value in s.counts(rig.engine).values())


def test_b09c_grant_revoked_before_cancel_write_leaves_job_and_receipts(db: URL) -> None:
    rig = s.build_rig(db)
    job_id, _ = _queued(rig)
    before = rig.job(job_id)
    counts = s.counts(rig.engine)

    def revoke(action: AuthorizationAction, call: int) -> None:
        if action is AuthorizationAction.CANCEL_JOB and call <= 2:
            rig.owner.change(
                GRANT,
                {"actions": ["create_job", "read_job"]},
                notice_id=f"notice_b09c_cancel_{call}",
            )

    service = rig.with_ports(
        authorization=s.HookedAuthorization(fx.FixtureAuthorization(rig.owner), revoke)
    )
    rig.holds.clear()
    with pytest.raises(AiJobError) as error:
        service.cancel_job(CancelJobCommand(TEACHER, "idem_b09c", job_id, before.job_revision))
    assert (error.value.code, error.value.http_status) == ("FORBIDDEN_SCOPE", 403)
    assert [hold.current for hold in rig.holds] == [False]
    assert rig.job(job_id) == before
    assert s.counts(rig.engine) == counts


def test_b09d_reads_stay_current_authority_and_history_is_unchanged(db: URL) -> None:
    rig = s.build_rig(db)
    created = rig.service.create_job(s.command())
    attempt_id = rig.job(created.job_id).active_attempt.attempt_id
    capability = rig.capability(created.job_id)
    assert rig.service.start_attempt(capability, created.job_id, attempt_id).started
    claim = _claim(rig, created.job_id, attempt_id)
    receipt = rig.service.accept_completion(capability, claim)
    assert receipt.disposition is ResultDisposition.ACCEPTED
    visible = rig.service.get_job_status(TEACHER, created.job_id)
    assert visible.view is not None and visible.view["result_refs"]
    settled = rig.job(created.job_id)

    rig.owner.change(
        ELIGIBILITY, {"eligible": False, "reason_code": "CONSENT_REVOKED"}, notice_id="notice_b09d"
    )
    hidden = rig.service.get_job_status(TEACHER, created.job_id, visible.etag)
    assert not hidden.not_modified and hidden.etag != visible.etag  # no stale 304
    assert hidden.view is not None and hidden.view["result_refs"] == []
    # Historical receipts replay unchanged; nothing is rewritten by the owner change.
    assert rig.service.accept_completion(capability, claim) == receipt
    replay = rig.service.create_job(s.command())
    assert (replay.job_id, replay.replayed, replay.job_revision) == (created.job_id, True, 1)
    assert rig.job(created.job_id) == settled


def test_be2_hold_first_commits_first_and_owner_change_waits(db: URL) -> None:
    job_id, attempt_id = _queued(s.build_rig(db))
    held = threading.Event()
    release = threading.Event()

    def on_hold(result: object) -> None:
        if not held.is_set():
            held.set()
            assert release.wait(30)

    rig = s.build_rig(db, on_hold=on_hold)
    outcome: dict[str, StartResult] = {}
    start = threading.Thread(
        target=lambda: outcome.update(
            result=rig.service.start_attempt(rig.capability(job_id), job_id, attempt_id)
        )
    )
    start.start()
    assert held.wait(30)
    owner_locked = threading.Event()
    owner = threading.Thread(
        target=lambda: rig.owner.change(
            ELIGIBILITY,
            {"eligible": False, "reason_code": "CONSENT_REVOKED"},
            notice_id="notice_linearization",
            after_lock=owner_locked.set,
        )
    )
    owner.start()
    try:
        # BE2 holds the fence FOR SHARE: the owner's FOR UPDATE cannot proceed yet.
        assert not owner_locked.wait(1.5)
    finally:
        release.set()
        start.join(30)
        owner.join(30)
    assert owner_locked.is_set()
    assert outcome["result"] == StartResult(True, None)  # committed first: historically valid
    assert rig.job(job_id).state is JobState.RUNNING
    assert rig.owner.withheld_notices() == 1  # later change is handled by its notice (B5)


@pytest.mark.parametrize("fence", [None, OwnerFence("eligibility:unknown_scope", 1)])
def test_missing_or_unknown_fence_is_never_treated_as_current(
    db: URL, fence: OwnerFence | None
) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id = _queued(rig)
    before = rig.job(job_id)
    real = fx.FixtureEligibility(rig.owner)

    class Unfenced:
        def check(
            self, *, scope: JobScope, request_ref: RequestRef, job_type: str
        ) -> EligibilityDecision:
            decision = real.check(scope=scope, request_ref=request_ref, job_type=job_type)
            return replace(decision, fence=fence)

    service = rig.with_ports(eligibility=Unfenced())
    result = service.start_attempt(rig.capability(job_id), job_id, attempt_id)
    assert result == StartResult(False, "STALE_CONTEXT")
    assert rig.job(job_id) == before
