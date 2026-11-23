"""FEAT-066 T-1d1-fix: the periodic story sweep on PostgreSQL (SRS l.394-395, l.503, l.615, l.1799).

One pass composes the lost-task reaper (T-2d-fix), the admission reconciler (T-1a) and the
adult-wait closeout and deadline (T-1d1) under a PostgreSQL advisory lock. Runs only against a
disposable database whose name contains ``be1_acceptance`` and ``frc08_v3_t1d1`` (the fixture and
the builders are the closeout module's). Every pass takes an injected ``now`` in 2020, far before
any real timestamp, so a row another test left behind is never due and a row aged to the injected
clock is; the reconciler reads no clock, so what it hands back carries a real timestamp. No
provider, no object storage, no sleep: the loop's wait is a fake.
"""

# ruff: noqa: F811  (the imported ``db`` fixture is used as a test argument)

from __future__ import annotations

import itertools
import threading
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text, update

from sketch2life.application.services.story_sweep_runner import (
    SweepReport,
    SweepStep,
    run_sweepers_once,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.sweep_worker import (
    LOCK_NAME,
    build_sweep_steps,
    run_loop,
    run_pass_locked,
)
from tests.integration.story_video.test_story_run_closeout_postgres import (  # noqa: F401
    HOURS_168,
    RUNS,
    VG,
    Db,
    Video,
    accept_and_age,
    db,
    generation_row,
    new_video,
    run_row,
    seed_run,
)
from tests.integration.story_video.test_video_commands_postgres import principal_of

LEASE = timedelta(hours=1)
SECOND = timedelta(seconds=1)
# The closeout module seeds relative to its own constant (2026-12-01); ``seed_run`` ages a row to
# ``NOW - idle``, so a row due at ``base`` is seeded with ``idle = HOURS_168 + (NOW - base)``.
CLOSEOUT_MODULE_NOW = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)
_bases = (datetime(2020 + n // 12, n % 12 + 1, 1, 12, 0, tzinfo=UTC) for n in itertools.count())
FAR_PAST = datetime(2040, 1, 1, tzinfo=UTC)  # every injected instant is earlier; real time is not


@pytest.fixture
def base() -> datetime:
    """A pass instant of its own per test (one month apart from 2020-01): no two tests share due
    rows, however many tests the module grows to."""

    return next(_bases)


@pytest.fixture(autouse=True)
def _forget_aged_rows(db: Db) -> Iterator[None]:
    yield
    cutoff = FAR_PAST
    with db.factory.begin() as session:
        session.execute(
            update(RUNS).where(RUNS.c.updated_at < cutoff).values(updated_at=datetime.now(UTC))
        )
        session.execute(
            update(VG).where(VG.c.accepted_at < cutoff).values(accepted_at=datetime.now(UTC))
        )


def idle_run(
    db: Db,
    base: datetime,
    state: str = "SCRIPT_REVIEW",
    *,
    extra: timedelta = timedelta(0),
    **kw: Any,
) -> str:
    """A run that is exactly ``168 h + extra`` idle at ``base``."""

    return seed_run(db, state, idle=HOURS_168 + extra + (CLOSEOUT_MODULE_NOW - base), **kw)


def lost_drawing_run(db: Db, base: datetime, *, idle: timedelta) -> str:
    """An analysis of the drawing that never reported: INPUT_PROCESSING with a RUNNING job."""

    run_id = seed_run(
        db, "INPUT_PROCESSING", job_state="RUNNING", idle=CLOSEOUT_MODULE_NOW - base + idle
    )
    with db.factory.begin() as session:
        session.execute(
            update(RUNS).where(RUNS.c.run_id == run_id).values(current_input_revision=1)
        )
        session.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                created_at=base - idle,
            )
        )
    return run_id


def steps_for(db: Db, video: Video | None = None, *, adapters: Any = None) -> tuple[SweepStep, ...]:
    return build_sweep_steps(
        db.factory,
        adapters if adapters is not None else (video.adapters if video else None),
        lease=LEASE,
    )


def effects(report: SweepReport) -> dict[str, dict[str, int]]:
    return {name: dict(counts) for name, counts in report.steps}


def age_accepted(db: Db, generation_id: str, accepted_at: datetime) -> None:
    with db.factory.begin() as session:
        session.execute(
            update(VG)
            .where(VG.c.video_generation_id == generation_id)
            .values(accepted_at=accepted_at)
        )


def cancel(db: Db, video: Video) -> None:
    """The adult cancels; the hook that would fail the in-flight generation never runs."""

    revision = int(run_row(db, video.run.run_id)["revision"])
    with db.factory() as session:
        record = SqlParentStoryRunRepository(session).cancel_run(
            principal=principal_of(video.owner),
            run_id=video.run.run_id,
            expected_revision=revision,
            idempotency_key=uuid4().hex,
        )
    assert record.run_state == "DELETE_PENDING"


# --------------------------------------------------------------------------------- one pass
def test_one_pass_runs_the_three_sweepers_once_each_and_a_second_pass_changes_nothing(
    db: Db, base: datetime
) -> None:
    lost = lost_drawing_run(db, base, idle=timedelta(hours=200))  # idle even longer than 168 h
    idle = idle_run(db, base)
    overdue = new_video(db)
    overdue_id, _ = accept_and_age(db, overdue)
    age_accepted(db, overdue_id, base - timedelta(hours=6))
    orphan = new_video(db)
    orphan_id, _ = accept_and_age(db, orphan)
    cancel(db, orphan)
    adapters = overdue.adapters

    report = run_sweepers_once(base, steps=steps_for(db, adapters=adapters), batch_size=200)
    got = effects(report)
    assert report.errors == 0 and list(got) == ["reaper", "reconciler", "closeout"]
    assert got["reaper"]["drawing_timed_out"] == 1
    assert got["reconciler"]["cancelled_settled"] == 1
    assert got["closeout"]["abandoned"] == 1 and got["closeout"]["deadline_failed"] == 1
    assert got["closeout"]["errors"] == 0 and got["reconciler"]["mismatched"] == 0

    # the lost analysis ends FAILED and its run gets a fresh wait: the idle pass that runs after the
    # reaper in the same pass does not close it although it was idle for 200 hours before
    lost_row = run_row(db, lost)
    assert lost_row["job_state"] == "FAILED" and lost_row["updated_at"] == base
    assert lost_row["run_state"] != "ABANDONED"
    assert run_row(db, idle)["run_state"] == "ABANDONED"
    assert generation_row(db, overdue_id)["state"] == "FAILED"
    assert run_row(db, overdue.run.run_id)["run_state"] == "SCRIPT_REVIEW"
    assert generation_row(db, orphan_id)["state"] == "FAILED"
    assert generation_row(db, orphan_id)["safe_failure_code"] == "RUN_CANCELLED"

    snapshot = {
        key: run_row(db, key) for key in (lost, idle, overdue.run.run_id, orphan.run.run_id)
    }
    second = run_sweepers_once(base, steps=steps_for(db, adapters=adapters), batch_size=200)
    again = effects(second)
    assert again["reaper"]["drawing_timed_out"] == 0 and again["reaper"]["rewrite_recovered"] == 0
    assert again["reconciler"]["cancelled_settled"] == 0 and again["reconciler"]["resolved"] == 0
    assert again["closeout"]["abandoned"] == 0 and again["closeout"]["deadline_failed"] == 0
    for key, row in snapshot.items():
        assert run_row(db, key) == row  # a second pass writes nothing


def test_without_adapters_the_pass_settles_the_run_and_a_later_pass_closes_the_reservation(
    db: Db, base: datetime
) -> None:
    video = new_video(db)
    generation_id, _ = accept_and_age(db, video)
    age_accepted(db, generation_id, base - timedelta(hours=6))
    first = run_sweepers_once(base, steps=steps_for(db), batch_size=200)  # no adapters composed
    assert effects(first)["closeout"]["deadline_failed"] == 1 and first.errors == 0
    assert run_row(db, video.run.run_id)["run_state"] == "SCRIPT_REVIEW"
    assert generation_row(db, generation_id)["compute_released_at"] is None  # no port was reachable
    later = run_sweepers_once(base, steps=steps_for(db, video), batch_size=200)
    assert effects(later)["reconciler"]["compute_closed"] >= 1
    assert generation_row(db, generation_id)["compute_released_at"] is not None
    assert [name for name, _ in video.adapters.reservation.calls].count("release") == 1


# --------------------------------------------------------------------------------- the lock
def hold_lock(db: Db) -> Any:
    connection = db.engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    acquired = connection.scalar(
        text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"), {"name": LOCK_NAME}
    )
    assert acquired is True
    return connection


def test_a_lock_held_by_another_connection_gives_lock_busy_and_no_change_then_runs_after(
    db: Db, base: datetime
) -> None:
    idle = idle_run(db, base)
    before = run_row(db, idle)
    holder = hold_lock(db)
    try:
        busy = run_pass_locked(db.engine, steps_for(db), now=base, batch_size=200)
        assert busy.lock_busy is True and busy.steps == () and busy.errors == 0
        assert run_row(db, idle) == before
    finally:
        holder.scalar(
            text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"), {"name": LOCK_NAME}
        )
        holder.close()
    done = run_pass_locked(db.engine, steps_for(db), now=base, batch_size=200)
    assert done.lock_busy is False and effects(done)["closeout"]["abandoned"] == 1
    assert run_row(db, idle)["run_state"] == "ABANDONED"
    # the pass released its lock: another connection can take it at once
    holder = hold_lock(db)
    holder.scalar(
        text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"), {"name": LOCK_NAME}
    )
    holder.close()


def test_a_failing_step_does_not_stop_the_others_and_the_lock_is_still_released(
    db: Db, base: datetime
) -> None:
    idle = idle_run(db, base)

    def boom(_now: datetime, _batch: int) -> Mapping[str, int]:
        raise RuntimeError("synthetic failure")

    steps = (SweepStep("boom", boom), *steps_for(db))
    report = run_pass_locked(db.engine, steps, now=base, batch_size=200)
    assert report.failures == (("boom", "RuntimeError"),)
    assert run_row(db, idle)["run_state"] == "ABANDONED"
    holder = hold_lock(db)  # released
    holder.scalar(
        text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"), {"name": LOCK_NAME}
    )
    holder.close()


# --------------------------------------------------------------------------------- batches
def test_the_batch_bound_leaves_the_rest_for_the_next_pass(db: Db, base: datetime) -> None:
    ids = [idle_run(db, base, extra=timedelta(hours=index)) for index in range(8)]  # batch + 5
    states: list[int] = []
    for _ in range(3):
        report = run_sweepers_once(base, steps=steps_for(db), batch_size=3)
        states.append(effects(report)["closeout"]["abandoned"])
    assert states == [3, 3, 2]
    assert {run_row(db, run_id)["run_state"] for run_id in ids} == {"ABANDONED"}
    assert [run_row(db, run_id)["revision"] for run_id in ids] == [6] * 8


def test_two_concurrent_passes_close_each_run_exactly_once(db: Db, base: datetime) -> None:
    ids = [
        idle_run(db, base, "SUBJECT_REVIEW" if index % 2 else "VIDEO_READY") for index in range(24)
    ]
    barrier = threading.Barrier(2)

    def one_pass(_index: int) -> SweepReport:
        steps = steps_for(db)
        barrier.wait(timeout=30)
        return run_sweepers_once(base, steps=steps, batch_size=200)

    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(one_pass, range(2)))
    assert all(report.errors == 0 for report in reports)
    for run_id in ids:
        row = run_row(db, run_id)
        assert row["run_state"] in {"COMPLETED", "ABANDONED"} and row["revision"] == 6  # once
    closed = sum(
        counts["abandoned"] + counts["completed"]
        for report in reports
        for name, counts in report.steps
        if name == "closeout"
    )
    assert closed == len(ids)  # between them each run was closed once (a skip is not a close)


# --------------------------------------------------------------------------------- the loop
def test_the_loop_runs_real_passes_with_a_fake_wait(db: Db, base: datetime) -> None:
    idle = idle_run(db, base)
    waits: list[float] = []
    reports: list[SweepReport] = []

    def run_pass() -> SweepReport:
        report = run_pass_locked(db.engine, steps_for(db), now=base, batch_size=200)
        reports.append(report)
        return report

    def wait(seconds: float) -> bool:
        waits.append(seconds)
        return len(waits) >= 2

    assert run_loop(run_pass, interval_seconds=300, wait=wait) == 2
    assert waits == [300, 300]
    assert [effects(report)["closeout"]["abandoned"] for report in reports] == [1, 0]
    assert run_row(db, idle)["run_state"] == "ABANDONED"
