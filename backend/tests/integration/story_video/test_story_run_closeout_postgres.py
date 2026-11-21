"""FEAT-066 T-1d1: the adult-wait closeout and the generation deadline on PostgreSQL.

SRS l.394 (the adult-wait states, what starts the clock), l.395 (the six-hour deadline from
``accepted_at``, a refused admission returns the run to ``SCRIPT_REVIEW`` with a new timer), l.503
FR-C-11 (+168 hours: ``VIDEO_READY`` becomes ``COMPLETED``, every other wait ``ABANDONED``; the lock
is released and the content kept), FR-C-08 (the closed run can be deleted; no purge here) and, for
the deadline outcome of T-1d1-fix, l.2119-2120, BR-11 l.255, FR-AI-07 l.573 (a failed accepted
request still counts toward the cap; the run returns to script review, or ends ``FAILED`` when the
cap is spent). Runs only against a disposable database whose name contains ``be1_acceptance`` and
``frc08_v3_t1d1``.
The clock is the ``now`` argument of the sweep, so no test sleeps. The two admission ports are the
local/test pair; no provider is called.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine, func, select, text, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_closeout import CloseoutOutcome
from sketch2life.application.ports.story_run_lifecycle import (
    DELETE_ELIGIBLE_STATES,
    PURGE_STATES,
)
from sketch2life.application.ports.story_video import (
    ProgressEvent,
    QuotaStatus,
    ReservationStatus,
)
from sketch2life.application.services.story_run_closeout import StoryRunCloseoutService
from sketch2life.application.services.story_run_video import (
    StoryVideoAdmissionService,
    StoryVideoProgressService,
)
from sketch2life.domain.story_run_closeout import ACTIVE_JOB_STATES, idle_target
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.closeout_store import (
    SqlStoryRunCloseoutStore,
    build_story_run_closeout,
)
from sketch2life.infrastructure.story_video.local_adapters import (
    LocalVideoComputeReservation,
    LocalVideoQuotaAdmission,
    VideoAdmissionScript,
    build_local_video_adapters,
)
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from tests.integration.story_video.test_video_commands_postgres import (
    ISSUER,
    ScriptRun,
    new_script_run,
    principal_of,
)

RUNS = story_tables.story_runs
VG = story_tables.video_generations
NOW = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)
HOURS_168 = timedelta(hours=168)
# The values ``ck_story_run_state`` stores (DRAFT and STORY_GENERATING: SRS names no code writes).
STORED_STATES = (
    "INPUT_PROCESSING",
    "INPUT_REVIEW",
    "SUBJECT_REVIEW",
    "PREPARATION_REVIEW",
    "SCRIPT_GENERATING",
    "SCRIPT_GENERATION_UNKNOWN",
    "SCRIPT_REVIEW",
    "VIDEO_ADMISSION_PENDING",
    "DELETE_PENDING",
    "FAILED",
    "COMPLETED",
    "DELETED",
    "VIDEO_QUEUED",
    "VIDEO_GENERATING",
    "VIDEO_SAFETY_VALIDATING",
    "VIDEO_READY",
    "SAFETY_BLOCKED",
    "ABANDONED",
)
JOB_STATES: tuple[str | None, ...] = (
    None,
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "AWAITING_RECONCILIATION",
)
WAIT_STATES = (
    "INPUT_REVIEW",
    "SUBJECT_REVIEW",
    "PREPARATION_REVIEW",
    "SCRIPT_REVIEW",
    "SAFETY_BLOCKED",
    "VIDEO_READY",
)


@dataclass
class Db:
    engine: Engine
    factory: sessionmaker[Session]

    def sessions(self) -> sessionmaker[Session]:  # the shape ``new_script_run`` reads
        return self.factory

    parent: str = ""


@pytest.fixture(scope="module")
def db() -> Iterator[Db]:
    url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    name = url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in name or "frc08_v3_t1d1" not in name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t1d1*be1_acceptance db")
    engine = create_engine(url)
    yield Db(engine, sessionmaker(engine, expire_on_commit=False))
    engine.dispose()


def service(db: Db, adapters: Any = None) -> tuple[StoryRunCloseoutService, Session]:
    session = db.factory()
    return build_story_run_closeout(session, adapters), session


def sweep(db: Db, now: datetime = NOW, *, batch: int = 500, adapters: Any = None) -> Any:
    closeout, session = service(db, adapters)
    try:
        return closeout.run_once(now, batch_size=batch)
    finally:
        session.close()


def seed_run(
    db: Db,
    state: str = "SCRIPT_REVIEW",
    *,
    job_state: str | None = "SUCCEEDED",
    idle: timedelta = HOURS_168,
    wait_started: datetime | None = None,
    last_activity: datetime | None = None,
    kind: str = "PARENT_ACCOUNT",
    locked: bool | None = None,
    error_code: str | None = None,
) -> str:
    """One run row whose ``updated_at`` is ``idle`` before ``NOW`` (the Parent clock)."""

    run_id = str(uuid4())
    if locked is None:
        locked = state not in {"COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"}
    with db.factory.begin() as session:
        session.execute(
            RUNS.insert().values(
                run_id=run_id,
                actor_scope_kind=kind,
                actor_scope_ref=uuid4().hex,
                profile_ref=str(uuid4()),
                run_state=state,
                revision=5,
                version=5,
                job_state=job_state,
                error_code=error_code,
                retryable=job_state == "FAILED",
                active_owner_parent_account_id=uuid4().hex if locked else None,
                adult_wait_started_at=wait_started,
                last_meaningful_activity_at=last_activity,
                created_at=NOW - timedelta(days=60),
                updated_at=NOW - idle,
            )
        )
    return run_id


def run_row(db: Db, run_id: str) -> Any:
    with db.factory() as session:
        return session.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()


def generation_row(db: Db, generation_id: str) -> Any:
    with db.factory() as session:
        return (
            session.execute(select(VG).where(VG.c.video_generation_id == generation_id))
            .mappings()
            .one()
        )


def count_rows(db: Db, table: Any, column: Any, run_id: str) -> int:
    with db.factory() as session:
        return int(
            session.scalar(select(func.count()).select_from(table).where(column == run_id)) or 0
        )


# ------------------------------------------------------------------------------ the idle closeout
def test_every_stored_state_and_job_state_closes_as_the_domain_says(db: Db) -> None:
    seeded = {
        (state, job): seed_run(db, state, job_state=job, error_code="SOME_FAILURE")
        for state in STORED_STATES
        for job in JOB_STATES
    }
    before = {key: run_row(db, run_id) for key, run_id in seeded.items()}
    report = sweep(db)
    expected_closed = 0
    for (state, job), run_id in seeded.items():
        after = run_row(db, run_id)
        target = idle_target(state, job)
        if target is None:
            assert after["run_state"] == state and after["revision"] == 5, (state, job)
            assert (
                after["active_owner_parent_account_id"]
                == before[(state, job)]["active_owner_parent_account_id"]
            )
        else:
            expected_closed += 1
            assert after["run_state"] == target, (state, job)
            assert after["revision"] == 6 and after["version"] == 6
            assert after["active_owner_parent_account_id"] is None
            assert after["finished_at"] == NOW
            assert after["adult_wait_started_at"] is None
            assert after["retryable"] is False
            # the closed run shows no failure of a job that no longer matters (T-1d1-fix-DEC-5)
            assert after["error_code"] is None
            assert after["job_state"] == (None if target == "ABANDONED" else job)
    assert report.completed + report.abandoned >= expected_closed
    assert report.errors == 0
    # an in-flight job is never closed, whatever the state and however old the row
    for state in STORED_STATES:
        for job in JOB_STATES:  # RETRY_WAIT is not a stored run-level value: domain-only case
            if job in ACTIVE_JOB_STATES:
                assert run_row(db, seeded[(state, job)])["run_state"] == state


@pytest.mark.parametrize("state", WAIT_STATES)
def test_the_boundary_is_exactly_168_hours(db: Db, state: str) -> None:
    job = "FAILED" if state == "SAFETY_BLOCKED" else "SUCCEEDED"
    run_id = seed_run(db, state, job_state=job, idle=HOURS_168 - timedelta(seconds=1))
    sweep(db)
    assert run_row(db, run_id)["run_state"] == state
    # the same row, one second later: the clock is the injected instant
    sweep(db, NOW + timedelta(seconds=1))
    assert run_row(db, run_id)["run_state"] == (
        "COMPLETED" if state == "VIDEO_READY" else "ABANDONED"
    )


def test_video_ready_completes_and_every_other_wait_abandons(db: Db) -> None:
    ready = seed_run(db, "VIDEO_READY")
    others = [seed_run(db, state) for state in WAIT_STATES if state != "VIDEO_READY"]
    report = sweep(db)
    assert run_row(db, ready)["run_state"] == "COMPLETED"
    assert {run_row(db, run_id)["run_state"] for run_id in others} == {"ABANDONED"}
    assert report.completed >= 1 and report.abandoned >= len(others)


def test_the_wait_markers_move_the_clock_and_the_latest_one_wins(db: Db) -> None:
    fresh = NOW - timedelta(hours=2)
    # the earlier steps carry only ``updated_at`` (Parent repository); the video path the others
    only_updated = seed_run(db, "SUBJECT_REVIEW", idle=HOURS_168)
    recent_wait = seed_run(db, "SCRIPT_REVIEW", idle=HOURS_168 * 2, wait_started=fresh)
    recent_activity = seed_run(db, "VIDEO_READY", idle=HOURS_168 * 2, last_activity=fresh)
    old_markers = seed_run(
        db,
        "VIDEO_READY",
        idle=HOURS_168 * 2,
        wait_started=NOW - HOURS_168 - timedelta(hours=1),
        last_activity=NOW - HOURS_168,
    )
    sweep(db)
    assert run_row(db, only_updated)["run_state"] == "ABANDONED"
    assert run_row(db, recent_wait)["run_state"] == "SCRIPT_REVIEW"
    assert run_row(db, recent_activity)["run_state"] == "VIDEO_READY"
    assert run_row(db, old_markers)["run_state"] == "COMPLETED"


def test_closing_releases_the_lock_and_keeps_everything_else(db: Db) -> None:
    owner = f"synthetic-t1d1-{uuid4().hex[:8]}"
    with db.factory.begin() as session:
        session.add(
            AdultIdentityModel(subject=owner, issuer=ISSUER, state="active", account_role="parent")
        )
    run = new_script_run(db, owner)  # type: ignore[arg-type]
    with db.factory.begin() as session:
        session.execute(
            update(RUNS).where(RUNS.c.run_id == run.run_id).values(updated_at=NOW - HOURS_168)
        )
        held = session.scalar(
            select(RUNS.c.active_owner_parent_account_id).where(RUNS.c.run_id == run.run_id)
        )
    assert held is not None
    tables = (
        (story_tables.run_inputs, story_tables.run_inputs.c.run_id),
        (story_tables.story_revisions, story_tables.story_revisions.c.run_id),
        (story_tables.story_revision_reviews, story_tables.story_revision_reviews.c.run_id),
        (story_tables.review_decisions, story_tables.review_decisions.c.run_id),
        (
            story_tables.story_command_receipts,
            story_tables.story_command_receipts.c.idempotency_scope_ref,
        ),
    )
    counts = [count_rows(db, table, column, run.run_id) for table, column in tables]
    assert all(counts)
    before = run_row(db, run.run_id)
    assert sweep(db).abandoned >= 1
    after = run_row(db, run.run_id)
    assert after["run_state"] == "ABANDONED"
    assert after["active_owner_parent_account_id"] is None
    for column in (
        "actor_scope_ref",
        "profile_ref",
        "subject_label",
        "current_input_revision",
        "created_at",
    ):
        assert after[column] == before[column]
    assert [count_rows(db, table, column, run.run_id) for table, column in tables] == counts
    # the lock is free: the same account can start another run at once
    with db.factory.begin() as session:
        session.execute(
            RUNS.insert().values(
                run_id=str(uuid4()),
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=uuid4().hex,
                run_state="INPUT_PROCESSING",
                revision=1,
                version=1,
                active_owner_parent_account_id=held,
            )
        )
    assert "ABANDONED" in DELETE_ELIGIBLE_STATES and "COMPLETED" in DELETE_ELIGIBLE_STATES


def test_a_second_pass_changes_nothing(db: Db) -> None:
    run_id = seed_run(db, "SUBJECT_REVIEW")
    first = sweep(db)
    assert first.abandoned >= 1
    row = run_row(db, run_id)
    second = sweep(db)  # the same instant again: nothing is left to close
    assert second.completed == second.abandoned == second.deadline_failed == 0
    assert run_row(db, run_id) == row


def test_the_batch_is_bounded_and_oldest_first(db: Db) -> None:
    # far older than any other row of this module, so these five head the listing
    ages = (2001, 2005, 2003, 2009, 2007)
    ids = {hours: seed_run(db, "SCRIPT_REVIEW", idle=timedelta(hours=hours)) for hours in ages}
    session = db.factory()
    try:
        listed = [c.run_id for c in SqlStoryRunCloseoutStore(session).idle_candidates(NOW, 3)]
    finally:
        session.close()
    assert listed == [ids[2009], ids[2007], ids[2005]]
    report = sweep(db, batch=3)
    assert report.abandoned == 3
    states = {hours: run_row(db, run_id)["run_state"] for hours, run_id in ids.items()}
    assert states == {
        2009: "ABANDONED",
        2007: "ABANDONED",
        2005: "ABANDONED",
        2003: "SCRIPT_REVIEW",
        2001: "SCRIPT_REVIEW",
    }
    sweep(db, batch=3)  # the next pass takes the next oldest
    assert run_row(db, ids[2003])["run_state"] == "ABANDONED"


def test_input_processing_closes_only_when_nothing_was_ever_attached(db: Db) -> None:
    draft = seed_run(db, "INPUT_PROCESSING", job_state=None)
    attached = seed_run(db, "INPUT_PROCESSING", job_state="SUCCEEDED")
    running = seed_run(db, "INPUT_PROCESSING", job_state="RUNNING")
    voice = seed_run(db, "INPUT_PROCESSING", job_state=None)
    input_id = str(uuid4())
    transcript_id = str(uuid4())
    with db.factory.begin() as session:
        session.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=input_id, run_id=voice, input_revision=1, created_at=NOW
            )
        )
        session.execute(
            story_tables.transcript_revisions.insert().values(
                transcript_revision_id=transcript_id,
                run_id=voice,
                run_input_id=input_id,
                source_asset_ref=f"synthetic/{voice}/voice",
                revision_no=1,
                origin="ASR",
                state="PENDING",
                created_at=NOW,
            )
        )
    sweep(db)
    assert run_row(db, draft)["run_state"] == "ABANDONED"
    assert run_row(db, attached)["run_state"] == "INPUT_PROCESSING"
    assert run_row(db, running)["run_state"] == "INPUT_PROCESSING"
    assert run_row(db, voice)["run_state"] == "INPUT_PROCESSING"  # the ASR job is still working
    with db.factory.begin() as session:
        session.execute(
            update(story_tables.transcript_revisions)
            .where(story_tables.transcript_revisions.c.transcript_revision_id == transcript_id)
            .values(state="FAILED", error_code="ASR_FAILED")
        )
    sweep(db)
    assert run_row(db, voice)["run_state"] == "ABANDONED"


def test_a_run_of_another_owner_kind_is_not_touched(db: Db) -> None:
    run_id = seed_run(db, "SCRIPT_REVIEW", kind="ORGANIZATION", locked=False)
    sweep(db)
    assert run_row(db, run_id)["run_state"] == "SCRIPT_REVIEW"
    session = db.factory()
    try:
        assert SqlStoryRunCloseoutStore(session).close_idle(run_id, NOW) is CloseoutOutcome.SKIPPED
    finally:
        session.close()


def test_purge_states_are_never_touched(db: Db) -> None:
    ids = {state: seed_run(db, state, job_state=None) for state in PURGE_STATES}
    sweep(db)
    for state, run_id in ids.items():
        assert run_row(db, run_id)["run_state"] == state


# ------------------------------------------------------------------------------ concurrency
def test_a_row_held_by_a_live_command_is_skipped_then_a_cancel_wins(db: Db) -> None:
    owner = f"synthetic-t1d1-{uuid4().hex[:8]}"
    with db.factory.begin() as session:
        session.add(
            AdultIdentityModel(subject=owner, issuer=ISSUER, state="active", account_role="parent")
        )
    run = new_script_run(db, owner)  # type: ignore[arg-type]
    with db.factory.begin() as session:
        session.execute(
            update(RUNS).where(RUNS.c.run_id == run.run_id).values(updated_at=NOW - HOURS_168)
        )
    holder = db.factory()
    try:
        holder.execute(select(RUNS.c.run_id).where(RUNS.c.run_id == run.run_id).with_for_update())
        closeout, session = service(db)
        try:
            store = SqlStoryRunCloseoutStore(session)
            assert store.close_idle(run.run_id, NOW) is CloseoutOutcome.SKIPPED  # no waiting
            assert closeout.run_once(NOW).errors == 0
        finally:
            session.close()
        assert run_row(db, run.run_id)["run_state"] == "SCRIPT_REVIEW"
    finally:
        holder.rollback()
        holder.close()
    # the cancel (a real Parent command) commits first; the next sweep leaves DELETE_PENDING alone
    with db.factory() as repo_session:
        record = SqlParentStoryRunRepository(repo_session).cancel_run(
            principal=principal_of(owner),
            run_id=run.run_id,
            expected_revision=int(run_row(db, run.run_id)["revision"]),
            idempotency_key=uuid4().hex,
        )
    assert record.run_state == "DELETE_PENDING"
    sweep(db, NOW + timedelta(days=30))
    assert run_row(db, run.run_id)["run_state"] == "DELETE_PENDING"


def test_a_command_that_lands_after_the_listing_makes_the_close_skip(db: Db) -> None:
    run_id = seed_run(db, "SCRIPT_REVIEW")
    session = db.factory()
    try:
        store = SqlStoryRunCloseoutStore(session)
        assert [c.run_id for c in store.idle_candidates(NOW, 500) if c.run_id == run_id]
        with db.factory.begin() as other:  # the adult acts between the listing and the close
            other.execute(
                update(RUNS).where(RUNS.c.run_id == run_id).values(updated_at=NOW, revision=6)
            )
        assert store.close_idle(run_id, NOW) is CloseoutOutcome.SKIPPED
    finally:
        session.close()
    assert run_row(db, run_id)["run_state"] == "SCRIPT_REVIEW"


def test_closed_runs_refuse_cancel_and_accept_delete(db: Db) -> None:
    owner = f"synthetic-t1d1-{uuid4().hex[:8]}"
    with db.factory.begin() as session:
        session.add(
            AdultIdentityModel(subject=owner, issuer=ISSUER, state="active", account_role="parent")
        )
    run = new_script_run(db, owner)  # type: ignore[arg-type]
    with db.factory.begin() as session:
        session.execute(
            update(RUNS).where(RUNS.c.run_id == run.run_id).values(updated_at=NOW - HOURS_168)
        )
    sweep(db)
    row = run_row(db, run.run_id)
    assert row["run_state"] == "ABANDONED"
    principal = principal_of(owner)
    with db.factory() as session, pytest.raises(ParentStoryRunError) as refused:
        SqlParentStoryRunRepository(session).cancel_run(
            principal=principal,
            run_id=run.run_id,
            expected_revision=int(row["revision"]),
            idempotency_key=uuid4().hex,
        )
    assert refused.value.status_code == 409
    with db.factory() as session:
        deleted = SqlParentStoryRunRepository(session).delete_run(
            principal=principal, run_id=run.run_id, idempotency_key=uuid4().hex
        )
    assert deleted.run_state == "DELETE_PENDING"


def test_two_workers_close_each_run_exactly_once(db: Db) -> None:
    ids = [seed_run(db, "SUBJECT_REVIEW" if index % 2 else "VIDEO_READY") for index in range(24)]
    barrier = Barrier(2)

    def worker() -> Any:
        closeout, session = service(db)
        try:
            barrier.wait(timeout=30)
            return closeout.run_once(NOW, batch_size=500)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = [future.result() for future in [pool.submit(worker), pool.submit(worker)]]
    assert all(report.errors == 0 for report in reports)
    for run_id in ids:
        row = run_row(db, run_id)
        assert row["run_state"] in {"COMPLETED", "ABANDONED"}
        assert row["revision"] == 6  # closed once, never twice
    closed_by_workers = sum(report.completed + report.abandoned for report in reports)
    assert closed_by_workers >= len(ids)


# --------------------------------------------------------------------- admission and deadline
@dataclass
class Video:
    run: ScriptRun
    owner: str
    adapters: Any
    script: VideoAdmissionScript

    def request(self, session: Session, reason: str | None = None) -> Any:
        return StoryVideoAdmissionService(SqlStoryVideoRepository(session), self.adapters).request(
            principal=principal_of(self.owner),
            run_id=self.run.run_id,
            expected_revision=int(run_row_static(session, self.run.run_id)["revision"]),
            story_sha256=self.run.story_sha256,
            quality_reason_code=reason,
            idempotency_key=uuid4().hex,
        )


def run_row_static(session: Session, run_id: str) -> Any:
    return session.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()


def new_video(db: Db, *, prior: int = 0) -> Video:
    owner = f"synthetic-t1d1-{uuid4().hex[:8]}"
    with db.factory.begin() as session:
        session.add(
            AdultIdentityModel(subject=owner, issuer=ISSUER, state="active", account_role="parent")
        )
    run = new_script_run(db, owner, prior=prior)  # type: ignore[arg-type]
    script = VideoAdmissionScript()
    adapters = build_local_video_adapters(env="test", script=script)
    return Video(run, owner, adapters, script)


def test_a_refused_admission_starts_a_new_wait(db: Db) -> None:
    video = new_video(db)
    with db.factory.begin() as session:  # the script review was reached 300 hours ago
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == video.run.run_id)
            .values(
                updated_at=NOW - timedelta(hours=300),
                adult_wait_started_at=NOW - timedelta(hours=300),
            )
        )
    video.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    with db.factory() as session, pytest.raises(ParentStoryRunError) as refused:
        video.request(session)
    assert refused.value.code == "VIDEO_QUOTA_EXCEEDED"
    row = run_row(db, video.run.run_id)
    assert row["run_state"] == "SCRIPT_REVIEW"
    started = row["adult_wait_started_at"]
    assert started is not None and started > NOW - timedelta(hours=300)
    # 168 h after the refusal, not 168 h after the earlier wait
    sweep(db, started + HOURS_168 - timedelta(seconds=1))
    assert run_row(db, video.run.run_id)["run_state"] == "SCRIPT_REVIEW"
    sweep(db, started + HOURS_168)
    after = run_row(db, video.run.run_id)
    assert after["run_state"] == "ABANDONED"
    assert after["active_owner_parent_account_id"] is None


PATHS = {
    "ACCEPTED": [],
    "QUEUED": ["QUEUED"],
    "GENERATING": ["QUEUED", "GENERATING"],
    "TECHNICAL_VALIDATING": ["QUEUED", "GENERATING", "TECHNICAL_VALIDATING"],
    "SAFETY_VALIDATING": ["QUEUED", "GENERATING", "TECHNICAL_VALIDATING", "SAFETY_VALIDATING"],
}


@pytest.mark.parametrize("stage", list(PATHS))
def test_the_generation_deadline_runs_from_accepted_at_through_every_stage(
    db: Db, stage: str
) -> None:
    video = new_video(db)
    with db.factory() as session:
        accepted = video.request(session)
    assert accepted.record is not None and accepted.record.state == "ACCEPTED"
    generation_id = accepted.record.generation_id
    with db.factory() as session:
        progress = StoryVideoProgressService(SqlStoryVideoRepository(session), video.adapters)
        previous = "ACCEPTED"
        for step in PATHS[stage]:
            assert progress.apply(generation_id, ProgressEvent(previous, step)).applied
            previous = step
    row = generation_row(db, generation_id)
    start = row["accepted_at"]
    assert row["state"] == stage and start is not None
    # six hours minus a second: nothing happens
    early = sweep(db, start + timedelta(hours=6) - timedelta(seconds=1), adapters=video.adapters)
    assert early.deadline_failed == 0
    assert generation_row(db, generation_id)["state"] == stage
    calls_before = len(video.adapters.reservation.calls)
    late = sweep(db, start + timedelta(hours=6), adapters=video.adapters)
    assert late.deadline_failed >= 1
    failed = generation_row(db, generation_id)
    assert failed["state"] == "FAILED" and failed["safe_failure_code"] == "VIDEO_DEADLINE_EXCEEDED"
    assert failed["compute_released_at"] is not None
    assert failed["billing_quota_usage_ref"] is not None  # a consumed unit is not refunded
    calls = video.adapters.reservation.calls[calls_before:]
    assert len(calls) == 1  # one release or one settle, never both
    started = stage not in {"ACCEPTED", "QUEUED"}
    assert calls[0][0].startswith("settle") if started else calls[0][0] == "release"
    # the failed request still counts toward the cap, so the run returns to the script review
    # with a new adult wait and keeps its owner lock (SRS l.2120, BR-11 l.255, FR-C-11 l.503)
    run = run_row(db, video.run.run_id)
    assert run["run_state"] == "SCRIPT_REVIEW" and run["active_owner_parent_account_id"] is not None
    assert run["finished_at"] is None and run["retryable"] is False
    assert run["job_state"] == "FAILED" and run["error_code"] == "VIDEO_DEADLINE_EXCEEDED"
    assert run["adult_wait_started_at"] is not None
    assert run["adult_wait_started_at"] >= failed["completed_at"] - timedelta(seconds=5)
    again = sweep(db, start + timedelta(days=2), adapters=video.adapters)
    assert again.deadline_failed == 0
    assert len(video.adapters.reservation.calls) == calls_before + 1


def test_an_admission_pending_intent_is_outside_the_deadline_and_the_idle_clock(db: Db) -> None:
    video = new_video(db)
    video.script.reservations.append(ReservationStatus.UNAVAILABLE)
    with db.factory() as session:
        pending = video.request(session)
    assert pending.record is not None and pending.record.state == "ADMISSION_PENDING"
    assert run_row(db, video.run.run_id)["run_state"] == "VIDEO_ADMISSION_PENDING"
    report = sweep(db, NOW + timedelta(days=365), adapters=video.adapters)
    assert report.errors == 0
    assert run_row(db, video.run.run_id)["run_state"] == "VIDEO_ADMISSION_PENDING"
    assert generation_row(db, pending.record.generation_id)["state"] == "ADMISSION_PENDING"


def test_the_deadline_leaves_a_settled_generation_and_a_finished_run_alone(db: Db) -> None:
    video = new_video(db)
    with db.factory() as session:
        accepted = video.request(session)
    assert accepted.record is not None
    with db.factory() as session:
        progress = StoryVideoProgressService(SqlStoryVideoRepository(session), video.adapters)
        assert progress.apply(
            accepted.record.generation_id,
            ProgressEvent("ACCEPTED", "FAILED", safe_failure_code="OTHER"),
        ).applied
    run_before = run_row(db, video.run.run_id)
    start = generation_row(db, accepted.record.generation_id)["accepted_at"]
    report = sweep(db, start + timedelta(days=3), adapters=video.adapters)
    assert report.deadline_failed == 0
    assert run_row(db, video.run.run_id)["revision"] == run_before["revision"]


def test_the_factory_works_without_adapters_and_the_run_still_settles(db: Db) -> None:
    video = new_video(db)
    with db.factory() as session:
        accepted = video.request(session)
    assert accepted.record is not None
    start = generation_row(db, accepted.record.generation_id)["accepted_at"]
    report = sweep(db, start + timedelta(hours=6), adapters=None)
    assert report.deadline_failed >= 1
    assert run_row(db, video.run.run_id)["run_state"] == "SCRIPT_REVIEW"
    # no port was reachable: the reservation stays open for the reconciler
    assert generation_row(db, accepted.record.generation_id)["compute_released_at"] is None


def test_the_local_adapters_used_here_are_the_test_pair(db: Db) -> None:
    video = new_video(db)
    assert isinstance(video.adapters.reservation, LocalVideoComputeReservation)
    assert isinstance(video.adapters.quota, LocalVideoQuotaAdmission)


# ------------------------------------------------------------- T-1d1-fix: the deadline outcome
def accept_and_age(db: Db, video: Video, reason: str | None = None) -> tuple[str, datetime]:
    """One accepted request left at ``ACCEPTED``; returns its id and the deadline instant."""

    with db.factory() as session:
        accepted = video.request(session, reason)
    assert accepted.record is not None and accepted.record.state == "ACCEPTED"
    generation_id = accepted.record.generation_id
    return generation_id, generation_row(db, generation_id)["accepted_at"] + timedelta(hours=6)


def new_run_with_lock(db: Db, held: Any) -> None:
    """The same account starts another run at once: its lock column is free (SRS l.383)."""

    with db.factory.begin() as session:
        session.execute(
            RUNS.insert().values(
                run_id=str(uuid4()),
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=uuid4().hex,
                run_state="INPUT_PROCESSING",
                revision=1,
                version=1,
                active_owner_parent_account_id=held,
            )
        )


def test_the_deadline_never_refunds_or_releases_the_quota_unit(db: Db) -> None:
    video = new_video(db)
    generation_id, due = accept_and_age(db, video)
    before = generation_row(db, generation_id)
    quota_calls = list(video.adapters.quota.calls)
    # the quota port has no refund or release method at all: nothing here could give a unit back
    assert not [name for name in dir(video.adapters.quota) if "refund" in name or "release" in name]
    sweep(db, due, adapters=video.adapters)
    after = generation_row(db, generation_id)
    assert after["state"] == "FAILED" and after["safe_failure_code"] == "VIDEO_DEADLINE_EXCEEDED"
    assert after["billing_quota_usage_ref"] == before["billing_quota_usage_ref"] is not None
    assert after["generation_no"] == before["generation_no"] == 1  # still one of the three slots
    assert video.adapters.quota.calls == quota_calls
    assert [name for name, _ in video.adapters.reservation.calls].count("release") == 1


# The whole way back after a deadline (rewrite, confirmation, a new request, the cap) is proved
# through the real routes in ``test_story_deadline_routes_postgres.py``.


def test_the_returned_run_has_a_new_168_hour_wait_and_then_closes_abandoned(db: Db) -> None:
    video = new_video(db)
    generation_id, due = accept_and_age(db, video)
    sweep(db, due, adapters=video.adapters)
    run = run_row(db, video.run.run_id)
    started = run["adult_wait_started_at"]
    assert started is not None and run["job_state"] == "FAILED"
    # a refused admission uses the same path (FR-C-11): 168 h from the failure, not from before
    since = max(run["updated_at"], started)
    sweep(db, since + HOURS_168 - timedelta(seconds=1), adapters=video.adapters, batch=200)
    assert run_row(db, video.run.run_id)["run_state"] == "SCRIPT_REVIEW"
    sweep(db, since + HOURS_168, adapters=video.adapters, batch=200)
    closed = run_row(db, video.run.run_id)
    assert closed["run_state"] == "ABANDONED" and closed["active_owner_parent_account_id"] is None
    assert closed["error_code"] is None and closed["job_state"] is None
    assert generation_row(db, generation_id)["state"] == "FAILED"  # the attempt stays on its row


def test_when_the_cap_is_spent_the_deadline_ends_the_run_failed_and_frees_the_lock(
    db: Db,
) -> None:
    video = new_video(db, prior=2)  # two spent requests, then the third (last) one
    _generation_id, due = accept_and_age(db, video, "QUALITY_LOW")
    with db.factory() as session:
        held = run_row_static(session, video.run.run_id)["active_owner_parent_account_id"]
    assert held is not None
    sweep(db, due, adapters=video.adapters)
    run = run_row(db, video.run.run_id)
    assert run["run_state"] == "FAILED" and run["active_owner_parent_account_id"] is None
    assert run["finished_at"] is not None and run["adult_wait_started_at"] is None
    assert run["error_code"] == "VIDEO_DEADLINE_EXCEEDED" and run["job_state"] == "FAILED"
    new_run_with_lock(db, held)


def test_a_safety_blocked_run_closes_abandoned_168_hours_after_the_block(db: Db) -> None:
    video = new_video(db)
    generation_id, _due = accept_and_age(db, video)
    path = ["QUEUED", "GENERATING", "TECHNICAL_VALIDATING", "SAFETY_VALIDATING"]
    with db.factory() as session:
        progress = StoryVideoProgressService(SqlStoryVideoRepository(session), video.adapters)
        previous = "ACCEPTED"
        for step in path:
            assert progress.apply(generation_id, ProgressEvent(previous, step)).applied
            previous = step
        blocked = progress.apply(
            generation_id,
            ProgressEvent(
                "SAFETY_VALIDATING",
                "SAFETY_BLOCKED",
                safe_failure_code="SAFETY_BLOCKED",
                safety_finding_codes=("UNSAFE_CONTENT",),
            ),
        )
        assert blocked.applied
    before = run_row(db, video.run.run_id)
    assert before["run_state"] == "SAFETY_BLOCKED" and before["job_state"] == "FAILED"
    started = before["adult_wait_started_at"]
    assert started is not None and before["active_owner_parent_account_id"] is not None
    generation_before = generation_row(db, generation_id)
    since = max(before["updated_at"], started)
    sweep(db, since + HOURS_168 - timedelta(seconds=1), adapters=video.adapters, batch=200)
    assert run_row(db, video.run.run_id)["run_state"] == "SAFETY_BLOCKED"
    sweep(db, since + HOURS_168, adapters=video.adapters, batch=200)
    after = run_row(db, video.run.run_id)
    assert after["run_state"] == "ABANDONED" and after["active_owner_parent_account_id"] is None
    assert after["job_state"] is None and after["error_code"] is None
    generation_after = generation_row(db, generation_id)
    for column in ("state", "billing_quota_usage_ref", "safe_failure_code", "generation_no"):
        assert generation_after[column] == generation_before[column]  # the unit stays spent
    assert generation_after["safety_validation_state"] == "FAILED"
    new_run_with_lock(db, before["active_owner_parent_account_id"])


# ------------------------------------------------------------- T-1d1-fix: head-of-line and plan
def overdue_ids(db: Db, now: datetime) -> list[str]:
    session = db.factory()
    try:
        return [
            item.generation_id
            for item in SqlStoryRunCloseoutStore(session).overdue_generations(now, 500)
        ]
    finally:
        session.close()


def test_a_stale_generation_does_not_take_a_slot_of_the_deadline_batch(db: Db) -> None:
    video = new_video(db)
    generation_id, due = accept_and_age(db, video)
    assert generation_id in overdue_ids(db, due)
    with db.factory.begin() as session:  # a live command moved the run: advance would say STALE
        session.execute(
            update(RUNS).where(RUNS.c.run_id == video.run.run_id).values(run_state="SCRIPT_REVIEW")
        )
    assert generation_id not in overdue_ids(db, due)
    with db.factory.begin() as session:
        session.execute(
            update(RUNS).where(RUNS.c.run_id == video.run.run_id).values(run_state="VIDEO_QUEUED")
        )
    assert generation_id in overdue_ids(db, due)


def test_runs_with_an_open_generation_never_head_the_idle_batch(db: Db) -> None:
    video = new_video(db)
    generation_id, _due = accept_and_age(db, video)
    with db.factory.begin() as session:  # the oldest run of all, but it has an open generation
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == video.run.run_id)
            .values(
                updated_at=NOW - timedelta(hours=9000), run_state="SCRIPT_REVIEW", job_state=None
            )
        )
    plain = seed_run(db, "SCRIPT_REVIEW", idle=timedelta(hours=8000))
    session = db.factory()
    try:
        listed = [c.run_id for c in SqlStoryRunCloseoutStore(session).idle_candidates(NOW, 1)]
    finally:
        session.close()
    assert listed == [plain]  # a batch of one is not wasted on the always-skip row
    assert generation_row(db, generation_id)["state"] == "ACCEPTED"


def test_the_idle_listing_plan_is_recorded_over_20000_synthetic_runs(db: Db) -> None:
    """Information, not an assertion: ``EXPLAIN (ANALYZE)`` of the idle listing, rolled back.

    No index serves the listing and none is approved by T-1d1-fix. The text goes to the file named
    by ``T1D1FIX_EXPLAIN_OUT`` when set, for the evidence note."""

    with db.factory() as session:
        session.execute(
            text(
                "INSERT INTO story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, "
                "run_state, revision, version, job_state, retryable, created_at, updated_at) "
                "SELECT gen_random_uuid()::text, 'PARENT_ACCOUNT', md5(g::text), "
                "gen_random_uuid()::text, (ARRAY['SCRIPT_REVIEW','SUBJECT_REVIEW','VIDEO_READY',"
                "'INPUT_REVIEW'])[1 + g % 4], 5, 5, 'SUCCEEDED', false, now(), "
                "now() - make_interval(hours => 100 + g % 400) FROM generate_series(1, 20000) g"
            )
        )
        statement = SqlStoryRunCloseoutStore(session).idle_statement(datetime.now(UTC), 50)
        dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
        sql = str(statement.compile(dialect=dialect, compile_kwargs={"literal_binds": True}))
        plan = [row[0] for row in session.execute(text("EXPLAIN (ANALYZE) " + sql))]
        session.rollback()  # the 20,000 rows never stay
    assert plan
    out = os.environ.get("T1D1FIX_EXPLAIN_OUT")
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(plan) + "\n")
