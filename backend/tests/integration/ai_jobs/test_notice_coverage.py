"""BE2-01 Phase B batch B5: atomic cancellation notices on PostgreSQL (B-09e–g, Δ10).

More than ``notice_atomic_max``/2 matches cancelled in one transaction (invisible until its
commit); above the bound a typed failure with nothing changed or recorded; duplicate,
concurrent duplicate and overlapping notices; crash mid-notice then redelivery; and an owner
bump with its notice withheld that blocks a concurrent stale create. ASSUMED_CONTRACT owner
fixture; synthetic data. ``requires_postgres``; without PostgreSQL: NOT_RUN, never PASS.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import b3_support as s
import b5_support as b5
import pytest
from sketch2life.application.ports.ai_jobs import CancellationNotice
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    AiJobError,
    CancelJobCommand,
)
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.harness import JOB_TYPE, ORG, SESSION, TEACHER
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sqlalchemy import func, select
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres
TIMEOUT = 60
ABOVE_HALF = FIXTURE_DISPATCH_POLICY.notice_atomic_max // 2 + 1  # 51: multi-"page" volume


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


def _notice(notice_id: str = "notice_b5", **select_by: Any) -> CancellationNotice:
    if not select_by:
        select_by = {"session_id": SESSION}
    return CancellationNotice(notice_id, ORG, "SESSION_ENDED", **select_by)


def _jobs(rig: b5.B5Rig, count: int, prefix: str = "n", **command: Any) -> list[str]:
    made = []
    for index in range(count):
        request = f"req_{prefix}_{index}"
        b5.eligible(rig, request)
        made.append(
            rig.service.create_job(s.command(key=f"{prefix}_{index}", request=request, **command))
            .job_id
        )
    return made


def _states(rig: b5.B5Rig, job_ids: list[str]) -> dict[str, tuple[JobState, int]]:
    jobs = {job_id: rig.base.job(job_id) for job_id in job_ids}
    return {job_id: (job.state, job.job_revision) for job_id, job in jobs.items()}


def _cancelled(rig: b5.B5Rig, job_ids: list[str]) -> int:
    with rig.engine.connect() as connection:
        return int(connection.execute(
            select(func.count()).select_from(t.job).where(
                t.job.c.job_id.in_(job_ids), t.job.c.state == "cancelled")
        ).scalar_one())


def _notice_rows(rig: b5.B5Rig) -> list[Any]:
    with rig.engine.connect() as connection:
        return list(connection.execute(select(t.cancellation_notice)).all())


def _notice_audits(rig: b5.B5Rig) -> list[Any]:
    return [row for row in b5.outbox_rows(rig.engine, "audit")
            if row.payload["event_type"] == "job.cancelled_by_notice"]


def _bystanders(rig: b5.B5Rig) -> list[str]:
    other_session = _jobs(rig, 1, "other", session_id="session_other",
                          subjects=("child_fx_other",), job_type="other_type")
    done = _jobs(rig, 1, "done")
    job = rig.base.job(done[0])
    rig.service.cancel_job(CancelJobCommand(TEACHER, "idem_done", job.job_id, job.job_revision))
    return other_session + done


def test_notice_cancels_every_match_in_one_invisible_until_commit_transaction(db: URL) -> None:
    hook, ready, release = b5.pause_first_write()
    armed = {"on": False}

    def before_commit(uow: Any) -> None:
        if armed["on"]:
            hook(uow)

    rig = b5.build_b5_rig(db, before_commit=before_commit)
    matches = _jobs(rig, ABOVE_HALF)
    bystanders = _bystanders(rig)
    untouched = _states(rig, bystanders)
    armed["on"] = True
    worker, box = b5.run_thread(lambda: rig.service.apply_cancellation_notice(_notice()))
    assert ready.wait(TIMEOUT)  # every match cancelled inside the open transaction
    assert _cancelled(rig, matches) == 0 and _notice_rows(rig) == []  # nothing visible yet
    release.set()
    worker.join(TIMEOUT)
    status, cancelled = box[0]
    assert status == "ok" and sorted(cancelled) == sorted(matches)
    assert _cancelled(rig, matches) == ABOVE_HALF
    (notice,) = _notice_rows(rig)
    assert (notice.status, notice.applied_count) == ("COMPLETE", ABOVE_HALF)
    assert len(_notice_audits(rig)) == ABOVE_HALF
    assert _states(rig, bystanders) == untouched


def test_notice_above_the_atomic_bound_fails_typed_with_nothing_changed(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    matches = _jobs(rig, FIXTURE_DISPATCH_POLICY.notice_atomic_max + 1)
    before = _states(rig, matches)
    with pytest.raises(AiJobError) as error:
        rig.service.apply_cancellation_notice(_notice())
    assert error.value.code == "NOTICE_ATOMIC_LIMIT"
    assert _states(rig, matches) == before
    assert _notice_rows(rig) == [] and _notice_audits(rig) == []


def test_duplicate_notice_is_a_no_op(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    matches = _jobs(rig, 3)
    assert sorted(rig.service.apply_cancellation_notice(_notice())) == sorted(matches)
    after = _states(rig, matches)
    assert rig.service.apply_cancellation_notice(_notice()) == ()
    assert _states(rig, matches) == after and len(_notice_rows(rig)) == 1


@pytest.mark.parametrize("second_selects", ["duplicate", "overlap"])
def test_concurrent_duplicate_or_overlapping_notice_cancels_each_job_once(
    db: URL, second_selects: str
) -> None:
    hook, ready, release = b5.pause_first_write()
    armed = {"on": False}

    def before_commit(uow: Any) -> None:
        if armed["on"]:
            hook(uow)

    rig = b5.build_b5_rig(db, before_commit=before_commit)
    session_jobs = _jobs(rig, 4, "s")
    # Same job type, other session: a job-type notice overlaps every session match.
    typed_jobs = _jobs(rig, 2, "t", session_id="session_typed", subjects=("child_fx_t",))
    second = _notice() if second_selects == "duplicate" else _notice(
        "notice_b5_overlap", job_type=JOB_TYPE
    )
    armed["on"] = True
    first, first_box = b5.run_thread(lambda: rig.service.apply_cancellation_notice(_notice()))
    assert ready.wait(TIMEOUT)  # first notice holds every matching job row lock
    armed["on"] = False
    other, other_box = b5.run_thread(lambda: rig.service.apply_cancellation_notice(second))
    b5.wait_for_lock_waiters(rig.engine)
    release.set()
    first.join(TIMEOUT)
    other.join(TIMEOUT)
    assert first_box[0][0] == "ok" and sorted(first_box[0][1]) == sorted(session_jobs)
    assert other_box[0][0] == "ok"
    if second_selects == "duplicate":
        assert other_box[0][1] == () and len(_notice_rows(rig)) == 1
        assert _cancelled(rig, typed_jobs) == 0
    else:  # the overlap only gets the rows the first notice did not cancel
        assert sorted(other_box[0][1]) == sorted(typed_jobs)
        assert sorted(row.applied_count for row in _notice_rows(rig)) == [2, 4]
    every = session_jobs + (typed_jobs if second_selects == "overlap" else [])
    audited = [row.job_id for row in _notice_audits(rig)]
    assert sorted(audited) == sorted(every)  # each job cancelled and audited exactly once


def test_crash_mid_notice_rolls_back_then_redelivery_cancels_all(db: URL) -> None:
    hook, _, _ = b5.pause_first_write(fail=True)
    armed = {"on": False}

    def before_commit(uow: Any) -> None:
        if armed["on"]:
            hook(uow)

    rig = b5.build_b5_rig(db, before_commit=before_commit)
    matches = _jobs(rig, 5)
    before = _states(rig, matches)
    armed["on"] = True
    with pytest.raises(RuntimeError, match="injected"):
        rig.service.apply_cancellation_notice(_notice())
    armed["on"] = False
    assert _states(rig, matches) == before and _notice_rows(rig) == []
    assert sorted(rig.service.apply_cancellation_notice(_notice())) == sorted(matches)
    settled = _states(rig, matches)
    assert all(state is JobState.CANCELLED for state, _ in settled.values())
    assert rig.service.apply_cancellation_notice(_notice()) == ()
    assert _states(rig, matches) == settled  # nothing reopened or re-cancelled


def test_owner_bump_with_withheld_notice_blocks_a_stale_create(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    existing = _jobs(rig, 1, "owner")
    scope = fx.eligibility_scope(ORG, "req_owner_0")

    def revoke(call: int) -> None:
        if call == 1:  # the owner ends the session after BE2's precheck; notice withheld
            rig.base.owner.change(scope, {"eligible": False, "reason_code": "SESSION_ENDED"},
                                  notice_id="notice_withheld_b5")

    service = rig.with_ports(
        eligibility=s.HookedEligibility(fx.FixtureEligibility(rig.base.owner), revoke)
    )
    with pytest.raises(AiJobError) as error:
        service.create_job(s.command(key="owner_late", request="req_owner_0",
                                     session_id="session_late"))
    assert error.value.code == "INVALID_STATE"  # re-decided after the stale fence
    assert rig.base.owner.withheld_notices() == 1
    with rig.engine.connect() as connection:
        assert connection.execute(select(func.count()).select_from(t.job)).scalar_one() == 1
    assert rig.service.apply_cancellation_notice(_notice("notice_withheld_b5")) == tuple(existing)
    assert rig.base.job(existing[0]).state is JobState.CANCELLED
