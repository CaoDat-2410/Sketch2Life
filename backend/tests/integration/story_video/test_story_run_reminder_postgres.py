"""Synthetic PostgreSQL contract for the T-1d2 locked reminder producer.

Tests require an already migrated disposable database named with both
``frc08_v3_t1d1`` and ``be1_acceptance``. They never create a schema or run migrations.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, create_engine, func, select, text, update
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.notifications import (
    EnqueueResult,
    NotificationCommandV1,
    NotificationDedupeConflict,
    NotificationProducerPort,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_closeout import CloseoutOutcome
from sketch2life.application.ports.story_run_reminder import (
    ReminderCandidate,
    ReminderOutcome,
)
from sketch2life.application.ports.story_video import QuotaStatus
from sketch2life.application.services.story_run_reminder import reminder_command
from sketch2life.domain.story_run_reminder import REMINDER_DELAY, reminder_trigger_id
from sketch2life.infrastructure.notifications.inbox_repository import SqlNotificationProducer
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.closeout_store import SqlStoryRunCloseoutStore
from sketch2life.infrastructure.story_video.reminder_store import (
    SqlStoryRunReminderStore,
    build_story_run_reminder,
)
from tests.integration.story_video.test_story_run_closeout_postgres import new_video

RUNS = story_tables.story_runs
RUN_INPUTS = story_tables.run_inputs
TRANSCRIPTS = story_tables.transcript_revisions
NOW = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)


@dataclass
class Db:
    engine: Engine
    factory: sessionmaker[Session]
    parent: str = ""

    def sessions(self) -> sessionmaker[Session]:
        return self.factory


@pytest.fixture(scope="module")
def db() -> Iterator[Db]:
    url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "set BE1_TEST_DATABASE_URL to an already migrated disposable PostgreSQL database"
        )
    name = url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in name or "frc08_v3_t1d1" not in name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t1d1*be1_acceptance db")
    engine = create_engine(url)
    yield Db(engine, sessionmaker(engine, expire_on_commit=False))
    engine.dispose()


def seed_run(
    db: Db,
    *,
    state: str = "SCRIPT_REVIEW",
    job_state: str | None = "SUCCEEDED",
    idle: timedelta = REMINDER_DELAY,
    wait_started: datetime | None = None,
    last_activity: datetime | None = None,
    owner: str | None = None,
    run_id: str | None = None,
) -> tuple[str, str]:
    run_id = run_id or str(uuid4())
    owner = owner or str(uuid4())
    with db.factory.begin() as session:
        session.execute(
            RUNS.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=str(uuid4()),
                profile_ref=str(uuid4()),
                run_state=state,
                revision=5,
                version=5,
                job_state=job_state,
                retryable=job_state == "FAILED",
                active_owner_parent_account_id=owner,
                adult_wait_started_at=wait_started,
                last_meaningful_activity_at=last_activity,
                created_at=NOW - timedelta(days=60),
                updated_at=NOW - idle,
            )
        )
    return run_id, owner


def candidate_for(db: Db, run_id: str, now: datetime = NOW) -> ReminderCandidate | None:
    with db.factory() as session:
        store = SqlStoryRunReminderStore(session)
        cursor = None
        while True:
            page = store.scan_candidates(now, 500, cursor)
            for candidate in page.candidates:
                if candidate.run_id == run_id:
                    return candidate
            if not page.has_more or not page.candidates:
                return None
            cursor = page.candidates[-1].cursor


def inbox_rows(db: Db, trigger_id: str | None = None) -> list[Any]:
    with db.factory() as session:
        statement = select(INBOX_ITEMS)
        if trigger_id is not None:
            statement = statement.where(INBOX_ITEMS.c.trigger_id == trigger_id)
        return session.execute(statement).mappings().all()


def inbox_count(db: Db, trigger_id: str) -> int:
    with db.factory() as session:
        return int(
            session.scalar(
                select(func.count()).select_from(INBOX_ITEMS).where(
                    INBOX_ITEMS.c.trigger_id == trigger_id
                )
            )
            or 0
        )


def process_candidate(
    db: Db,
    candidate: ReminderCandidate,
    now: datetime = NOW,
    *,
    producer: NotificationProducerPort | None = None,
) -> ReminderOutcome:
    with db.factory() as session:
        return SqlStoryRunReminderStore(session, producer=producer).enqueue_if_due(candidate, now)


def test_due_parent_wait_creates_one_safe_inbox_item_at_144_hours(db: Db) -> None:
    run_id, owner = seed_run(db, idle=REMINDER_DELAY)
    assert candidate_for(db, run_id, NOW - timedelta(seconds=1)) is None
    current = candidate_for(db, run_id)
    assert current is not None
    assert process_candidate(db, current) is ReminderOutcome.CREATED
    expected_trigger = reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - REMINDER_DELAY)
    rows = inbox_rows(db, expected_trigger)
    assert len(rows) == 1
    row = rows[0]
    assert row["recipient_account_id"] == owner
    assert row["recipient_role"] == "parent"
    assert row["notification_type"] == "RUN_WAIT_REMINDER"
    assert row["template_version"] == 1
    assert row["trigger_id"] == row["trigger_dedupe_key"] == expected_trigger
    assert row["safe_parameters"] == {}
    assert row["expires_at"] is None
    assert process_candidate(db, current) is ReminderOutcome.ALREADY_PRESENT
    assert inbox_count(db, expected_trigger) == 1


def test_activity_after_listing_skips_the_stale_candidate(db: Db) -> None:
    run_id, _ = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    with db.factory.begin() as session:
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(
                last_meaningful_activity_at=NOW,
                revision=6,
                version=6,
                updated_at=NOW,
            )
        )
    with db.factory() as session:
        outcome = SqlStoryRunReminderStore(session).enqueue_if_due(candidate, NOW)
    assert outcome is ReminderOutcome.STALE
    assert not inbox_rows(
        db, reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - REMINDER_DELAY)
    )


def test_owner_transfer_before_lock_rescans_to_new_owner(db: Db) -> None:
    run_id, old_owner = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    new_owner = str(uuid4())
    with db.factory.begin() as session:
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(active_owner_parent_account_id=new_owner, revision=6, version=6)
        )
    with db.factory() as session:
        stale = SqlStoryRunReminderStore(session).enqueue_if_due(candidate, NOW)
    assert stale is ReminderOutcome.STALE
    trigger = reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - REMINDER_DELAY)
    assert not inbox_rows(db, trigger)

    updated_candidate = candidate_for(db, run_id)
    assert updated_candidate is not None
    assert process_candidate(db, updated_candidate) is ReminderOutcome.CREATED
    rows = inbox_rows(db, trigger)
    assert len(rows) == 1 and rows[0]["recipient_account_id"] == new_owner
    assert rows[0]["recipient_account_id"] != old_owner


def test_owner_transfer_after_commit_does_not_notify_a_second_recipient(db: Db) -> None:
    run_id, first_owner = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    assert process_candidate(db, candidate) is ReminderOutcome.CREATED
    trigger = reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - REMINDER_DELAY)
    second_owner = str(uuid4())
    with db.factory.begin() as session:
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(active_owner_parent_account_id=second_owner, revision=6, version=6)
        )
    transferred_candidate = candidate_for(db, run_id)
    assert transferred_candidate is not None
    assert process_candidate(db, transferred_candidate) is ReminderOutcome.ALREADY_PRESENT
    rows = inbox_rows(db, trigger)
    assert len(rows) == 1 and rows[0]["recipient_account_id"] == first_owner
    assert rows[0]["recipient_account_id"] != second_owner


def test_existing_trigger_on_another_recipient_is_global_dedupe(db: Db) -> None:
    run_id, current_owner = seed_run(db)
    since = NOW - REMINDER_DELAY
    other_owner = str(uuid4())
    command = reminder_command(
        recipient_account_id=other_owner,
        run_id=run_id,
        run_state="SCRIPT_REVIEW",
        wait_since=since,
    )
    with db.factory.begin() as session:
        SqlNotificationProducer(session, clock=lambda: NOW).enqueue(command)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    assert process_candidate(db, candidate) is ReminderOutcome.ALREADY_PRESENT
    rows = inbox_rows(db, command.trigger_id)
    assert len(rows) == 1
    assert rows[0]["recipient_account_id"] == other_owner
    assert rows[0]["recipient_account_id"] != current_owner


def test_enqueue_failure_rolls_back_and_closeout_remains_independent(db: Db) -> None:
    run_id, _ = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None

    class FailingProducer:
        def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
            raise RuntimeError("synthetic enqueue failure")

    with pytest.raises(RuntimeError, match="synthetic enqueue failure"):
        process_candidate(db, candidate, producer=FailingProducer())
    trigger = reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - REMINDER_DELAY)
    with db.factory() as session:
        row = session.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()
        assert row["run_state"] == "SCRIPT_REVIEW"
        assert row["revision"] == 5

    with db.factory() as session:
        outcome = SqlStoryRunCloseoutStore(session).close_idle(
            run_id, NOW + timedelta(hours=24)
        )
    assert outcome is CloseoutOutcome.ABANDONED
    assert not inbox_rows(db, trigger)


def test_closeout_wins_before_reminder_lock_and_closed_run_gets_no_notice(db: Db) -> None:
    run_id, _ = seed_run(db, idle=timedelta(hours=168))
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    with db.factory() as session:
        outcome = SqlStoryRunCloseoutStore(session).close_idle(run_id, NOW)
    assert outcome is CloseoutOutcome.ABANDONED
    with db.factory() as session:
        reminder_outcome = SqlStoryRunReminderStore(session).enqueue_if_due(candidate, NOW)
    assert reminder_outcome is ReminderOutcome.STALE
    assert not inbox_rows(
        db, reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - timedelta(hours=168))
    )


def test_new_wait_deadline_creates_a_new_notice_identity(db: Db) -> None:
    run_id, _ = seed_run(db, idle=timedelta(hours=200))
    first_candidate = candidate_for(db, run_id)
    assert first_candidate is not None
    assert process_candidate(db, first_candidate) is ReminderOutcome.CREATED
    first_trigger = reminder_trigger_id(
        run_id, "SCRIPT_REVIEW", NOW - timedelta(hours=200)
    )
    new_wait = NOW - REMINDER_DELAY
    with db.factory.begin() as session:
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(
                adult_wait_started_at=new_wait,
                revision=6,
                version=6,
            )
        )
    second_candidate = candidate_for(db, run_id)
    assert second_candidate is not None
    assert process_candidate(db, second_candidate) is ReminderOutcome.CREATED
    second_trigger = reminder_trigger_id(run_id, "SCRIPT_REVIEW", new_wait)
    triggers = {row["trigger_id"] for row in inbox_rows(db, first_trigger)}
    triggers.update(row["trigger_id"] for row in inbox_rows(db, second_trigger))
    assert len(triggers) == 2 and first_trigger in triggers


def test_transcript_and_active_job_candidates_are_excluded(db: Db) -> None:
    active_run, _ = seed_run(db, job_state="RUNNING")
    voice_run, _ = seed_run(db, state="INPUT_PROCESSING", job_state=None)
    run_input_id = str(uuid4())
    transcript_id = str(uuid4())
    with db.factory.begin() as session:
        session.execute(
            RUN_INPUTS.insert().values(
                run_input_id=run_input_id,
                run_id=voice_run,
                input_revision=1,
                created_at=NOW - REMINDER_DELAY,
            )
        )
        session.execute(
            TRANSCRIPTS.insert().values(
                transcript_revision_id=transcript_id,
                run_id=voice_run,
                run_input_id=run_input_id,
                source_asset_ref=f"synthetic/{voice_run}/voice",
                revision_no=1,
                origin="ASR",
                state="PENDING",
                created_at=NOW - REMINDER_DELAY,
            )
        )
    with db.factory() as session:
        store = SqlStoryRunReminderStore(session)
        candidate_ids: set[str] = set()
        cursor = None
        while True:
            page = store.scan_candidates(NOW, 500, cursor)
            candidate_ids.update(candidate.run_id for candidate in page.candidates)
            if not page.has_more or not page.candidates:
                break
            cursor = page.candidates[-1].cursor
    assert active_run not in candidate_ids
    assert voice_run not in candidate_ids


def test_open_generation_excludes_a_synthetic_wait_candidate(db: Db) -> None:
    # The helper uses only local fake quota/compute adapters and synthetic data.
    video = new_video(db)
    with db.factory() as session:
        accepted = video.request(session)
    assert accepted.record is not None
    run_id = video.run.run_id
    with db.factory.begin() as session:
        current = session.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(
                run_state="SCRIPT_REVIEW",
                job_state="SUCCEEDED",
                adult_wait_started_at=NOW - REMINDER_DELAY,
                updated_at=NOW - REMINDER_DELAY,
                revision=int(current["revision"]) + 1,
                version=int(current["version"]) + 1,
            )
        )
    with db.factory() as session:
        store = SqlStoryRunReminderStore(session)
        candidate_ids: set[str] = set()
        cursor = None
        while True:
            page = store.scan_candidates(NOW, 500, cursor)
            candidate_ids.update(candidate.run_id for candidate in page.candidates)
            if not page.has_more or not page.candidates:
                break
            cursor = page.candidates[-1].cursor
    assert run_id not in candidate_ids


def test_keyset_pages_advance_past_already_notified_oldest_rows(db: Db) -> None:
    base_run_id = uuid4().int & ((1 << 96) - 100)
    seeded = [
        seed_run(
            db,
            idle=timedelta(days=3000),
            run_id=str(UUID(int=base_run_id + index + 1)),
        )
        for index in range(5)
    ]
    for run_id, owner in seeded[:2]:
        command = reminder_command(
            recipient_account_id=owner,
            run_id=run_id,
            run_state="SCRIPT_REVIEW",
            wait_since=NOW - timedelta(days=3000),
        )
        with db.factory.begin() as session:
            SqlNotificationProducer(session, clock=lambda: NOW).enqueue(command)

    target_ids = {run_id for run_id, _ in seeded}
    target_outcomes: dict[str, ReminderOutcome] = {}
    all_triggers = {
        reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - timedelta(days=3000))
        for run_id, _ in seeded
    }
    with db.factory() as session:
        store = SqlStoryRunReminderStore(session)
        cursor = None
        while len(target_outcomes) < len(target_ids):
            page = store.scan_candidates(NOW, 2, cursor)
            for candidate in page.candidates:
                if candidate.run_id in target_ids:
                    target_outcomes[candidate.run_id] = store.enqueue_if_due(candidate, NOW)
            assert page.candidates
            cursor = page.candidates[-1].cursor
            assert page.has_more or len(target_outcomes) == len(target_ids)
    assert sum(value is ReminderOutcome.CREATED for value in target_outcomes.values()) == 3
    assert sum(value is ReminderOutcome.ALREADY_PRESENT for value in target_outcomes.values()) == 2
    assert sum(len(inbox_rows(db, trigger)) for trigger in all_triggers) == 5


def test_two_workers_create_one_global_notice_for_the_same_wait(db: Db) -> None:
    run_id, _ = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    barrier = Barrier(2)

    def worker() -> ReminderOutcome:
        barrier.wait(timeout=20)
        with db.factory() as session:
            return SqlStoryRunReminderStore(session).enqueue_if_due(candidate, NOW)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result() for future in (pool.submit(worker), pool.submit(worker))]
    trigger = reminder_trigger_id(run_id, "SCRIPT_REVIEW", NOW - REMINDER_DELAY)
    assert outcomes.count(ReminderOutcome.CREATED) == 1
    assert len(outcomes) == 2
    assert set(outcomes) <= {
        ReminderOutcome.ALREADY_PRESENT,
        ReminderOutcome.STALE,
        ReminderOutcome.CREATED,
    }
    assert inbox_count(db, trigger) == 1


def trigger_of(run_id: str, since: datetime = NOW - REMINDER_DELAY) -> str:
    return reminder_trigger_id(run_id, "SCRIPT_REVIEW", since)


class _InsertThenCrash:
    def __init__(self, session: Session) -> None:
        self._real = SqlNotificationProducer(session, clock=lambda: NOW)

    def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
        self._real.enqueue(command)
        raise RuntimeError("synthetic crash")


def test_non_utc_session_timezone_does_not_fail_candidates(db: Db) -> None:
    run_id, owner = seed_run(db)
    tz_engine = create_engine(
        os.environ["BE1_TEST_DATABASE_URL"],
        connect_args={"options": "-c TimeZone=Asia/Ho_Chi_Minh"},
    )
    try:
        factory = sessionmaker(tz_engine, expire_on_commit=False)
        with factory() as session:
            assert session.scalar(text("show timezone")) == "Asia/Ho_Chi_Minh"
            store = SqlStoryRunReminderStore(session)
            found: ReminderCandidate | None = None
            cursor = None
            while found is None:
                page = store.scan_candidates(NOW, 500, cursor)
                found = next((c for c in page.candidates if c.run_id == run_id), None)
                if not page.has_more or not page.candidates:
                    break
                cursor = page.candidates[-1].cursor
            assert found is not None
            assert found.wait_since.utcoffset() == timedelta(0)
            assert store.enqueue_if_due(found, NOW) is ReminderOutcome.CREATED
        rows = inbox_rows(db, trigger_of(run_id))
        assert len(rows) == 1 and rows[0]["recipient_account_id"] == owner
    finally:
        tz_engine.dispose()


def test_a_run_locked_by_another_session_is_skipped_then_processed_after_release(
    db: Db,
) -> None:
    run_id, _ = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    with db.factory() as holder:
        holder.execute(select(RUNS).where(RUNS.c.run_id == run_id).with_for_update())
        assert process_candidate(db, candidate) is ReminderOutcome.STALE
        assert not inbox_rows(db, trigger_of(run_id))
        holder.rollback()
    assert process_candidate(db, candidate) is ReminderOutcome.CREATED
    assert inbox_count(db, trigger_of(run_id)) == 1


def test_owner_transfer_interleaved_with_the_lock_notifies_only_the_new_owner(db: Db) -> None:
    run_id, old_owner = seed_run(db)
    old_candidate = candidate_for(db, run_id)
    assert old_candidate is not None
    new_owner = str(uuid4())
    with db.factory() as transferor:
        transferor.execute(select(RUNS).where(RUNS.c.run_id == run_id).with_for_update())
        # the reminder cannot read the half-transferred row: it skips the locked run
        assert process_candidate(db, old_candidate) is ReminderOutcome.STALE
        transferor.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(active_owner_parent_account_id=new_owner, revision=6, version=6)
        )
        transferor.commit()
    assert process_candidate(db, old_candidate) is ReminderOutcome.STALE
    fresh = candidate_for(db, run_id)
    assert fresh is not None and fresh.owner_account_id == new_owner
    assert process_candidate(db, fresh) is ReminderOutcome.CREATED
    rows = inbox_rows(db, trigger_of(run_id))
    assert [row["recipient_account_id"] for row in rows] == [new_owner]
    assert old_owner != new_owner


def test_crash_before_commit_leaves_nothing_and_after_commit_does_not_duplicate(db: Db) -> None:
    run_id, _ = seed_run(db)
    candidate = candidate_for(db, run_id)
    assert candidate is not None
    with db.factory() as session:
        store = SqlStoryRunReminderStore(session, producer=_InsertThenCrash(session))
        with pytest.raises(RuntimeError, match="synthetic crash"):
            store.enqueue_if_due(candidate, NOW)
    assert inbox_count(db, trigger_of(run_id)) == 0  # the insert rolled back with the failure
    assert process_candidate(db, candidate) is ReminderOutcome.CREATED
    # crash after commit: the result is lost, the retry finds the committed item
    assert process_candidate(db, candidate) is ReminderOutcome.ALREADY_PRESENT
    assert inbox_count(db, trigger_of(run_id)) == 1


def test_teacher_run_is_never_a_candidate(db: Db) -> None:
    run_id = str(uuid4())
    with db.factory.begin() as session:
        session.execute(
            RUNS.insert().values(
                run_id=run_id,
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref=str(uuid4()),
                profile_ref=str(uuid4()),
                run_state="SCRIPT_REVIEW",
                revision=5,
                version=5,
                job_state="SUCCEEDED",
                retryable=False,
                active_owner_parent_account_id=None,
                active_owner_teacher_id=str(uuid4()),
                occurrence_ref=str(uuid4()),
                created_by_actor_ref=str(uuid4()),
                created_at=NOW - timedelta(days=60),
                updated_at=NOW - timedelta(days=30),
            )
        )
    assert candidate_for(db, run_id) is None
    forged = ReminderCandidate(
        run_id=run_id,
        run_state="SCRIPT_REVIEW",
        revision=5,
        owner_account_id=str(uuid4()),
        wait_since=NOW - timedelta(days=30),
    )
    assert process_candidate(db, forged) is ReminderOutcome.STALE
    assert not inbox_rows(db, trigger_of(run_id, NOW - timedelta(days=30)))


def test_real_store_sweep_creates_inbox_items_isolates_failures_and_logs_no_content(
    db: Db, caplog: pytest.LogCaptureFixture
) -> None:
    good_run, good_owner = seed_run(db, idle=timedelta(days=4000))
    bad_run, bad_owner = seed_run(db, idle=timedelta(days=4000))

    class FailsForOneRecipient:
        def __init__(self, session: Session) -> None:
            self._real = SqlNotificationProducer(session, clock=lambda: NOW)

        def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
            if command.recipient_account_id == bad_owner:
                raise RuntimeError(f"synthetic failure for {bad_owner}")
            return self._real.enqueue(command)

    caplog.set_level(logging.DEBUG)
    created = failed = 0
    with db.factory() as session:
        sweep = build_story_run_reminder(session, producer=FailsForOneRecipient(session))
        cursor: str | None = None
        while True:
            result = sweep.run_once(NOW, 50, cursor)
            created += result.created
            failed += result.failed
            cursor = result.next_cursor
            if cursor is None:
                break
    assert failed >= 1 and created >= 1
    good_trigger = trigger_of(good_run, NOW - timedelta(days=4000))
    bad_trigger = trigger_of(bad_run, NOW - timedelta(days=4000))
    rows = inbox_rows(db, good_trigger)
    assert len(rows) == 1 and rows[0]["recipient_account_id"] == good_owner
    assert not inbox_rows(db, bad_trigger)  # failed run left no partial item; retried next pass
    row = rows[0]
    assert row["safe_parameters"] == {} and row["organization_ref"] is None
    assert row["recipient_role"] == "parent" and row["notification_type"] == "RUN_WAIT_REMINDER"
    visible = " ".join(str(row[key]) for key in row if key != "recipient_account_id")
    assert good_run not in visible
    logged = " ".join(record.getMessage() for record in caplog.records)
    for secret in (good_run, bad_run, good_owner, bad_owner):
        assert secret not in logged


def test_refused_admission_restarts_the_144_hour_reminder_wait(db: Db) -> None:
    video = new_video(db)
    run_id = video.run.run_id
    with db.factory.begin() as session:
        session.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(
                updated_at=NOW - timedelta(hours=300),
                adult_wait_started_at=NOW - timedelta(hours=300),
            )
        )
    assert candidate_for(db, run_id) is not None  # overdue before the refusal
    video.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    with db.factory() as session, pytest.raises(ParentStoryRunError) as refused:
        video.request(session)
    assert refused.value.code == "VIDEO_QUOTA_EXCEEDED"
    with db.factory() as session:
        started = session.scalar(
            select(RUNS.c.adult_wait_started_at).where(RUNS.c.run_id == run_id)
        )
    assert started is not None and started > NOW - timedelta(hours=300)
    due_at = started.astimezone(UTC) + REMINDER_DELAY
    assert candidate_for(db, run_id, due_at - timedelta(seconds=1)) is None
    assert candidate_for(db, run_id, due_at) is not None


def test_same_trigger_with_a_different_payload_is_a_conflict_not_a_second_item(db: Db) -> None:
    run_id, owner = seed_run(db)
    command = reminder_command(
        recipient_account_id=owner,
        run_id=run_id,
        run_state="SCRIPT_REVIEW",
        wait_since=NOW - REMINDER_DELAY,
    )
    with db.factory.begin() as session:
        SqlNotificationProducer(session, clock=lambda: NOW).enqueue(command)
    changed = replace(command, template_version=2)
    with db.factory() as session, pytest.raises(NotificationDedupeConflict):
        SqlNotificationProducer(session, clock=lambda: NOW).enqueue(changed)
    assert inbox_count(db, command.trigger_id) == 1
