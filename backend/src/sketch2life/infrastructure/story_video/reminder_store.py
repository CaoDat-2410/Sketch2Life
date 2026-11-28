"""Locked Parent reminder scan and transactional T-8a inbox composition (T-1d2).

The listing is bounded and read-only. Each candidate is reselected with ``FOR UPDATE SKIP LOCKED``;
the Parent owner, state, revision, effective wait marker, transcript, job and open generation are
rechecked under that lock. The current owner is taken only from the locked run row. A global inbox
trigger lookup includes read and expired rows because T-8a's uniqueness is recipient-scoped.

This store is not composed into the HTTP app or a production scheduler. Until the client registers
``RUN_WAIT_REMINDER`` version 1, use it only with synthetic fixtures. OPEN before production
enablement:
Teacher-run reminders (separate task or this one?), a scheduler and lateness objective, inbox
retention and alternate writers, an integrated owner-transfer/activity lock-order proof (NOT
VERIFIED), and whether distinct waits can reuse the same microsecond timestamp (then a durable wait
generation is required). The named audit-retention migration contains no inbox deletion, which does
not establish that external deletion is impossible. T-1d1 closeout remains independently runnable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, exists, func, literal, or_, select, tuple_
from sqlalchemy.orm import Session

from sketch2life.application.ports.notifications import NotificationProducerPort
from sketch2life.application.ports.story_run_reminder import (
    ReminderCandidate,
    ReminderCandidatePage,
    ReminderOutcome,
    ReminderScanCursor,
)
from sketch2life.application.services.story_run_reminder import ReminderSweep, reminder_command
from sketch2life.domain.story_run_closeout import (
    ACTIVE_JOB_STATES,
    ADULT_WAIT_STATES,
    DRAFT_LIKE_STATE,
    idle_since,
)
from sketch2life.domain.story_run_reminder import (
    REMINDER_DELAY,
    normalize_utc,
    reminder_due,
    require_aware_utc,
)
from sketch2life.domain.story_video.model import OPEN_STATES
from sketch2life.infrastructure.notifications.inbox_repository import SqlNotificationProducer
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_PARENT_SCOPE = "PARENT_ACCOUNT"
_RUNS = story_tables.story_runs
_TRANSCRIPTS = story_tables.transcript_revisions
_VIDEO_GENERATIONS = story_tables.video_generations
_ADULT_WAIT_VALUES = tuple(sorted(ADULT_WAIT_STATES))
_ACTIVE_JOB_VALUES = tuple(sorted(ACTIVE_JOB_STATES))
_OPEN_GENERATION_VALUES = tuple(sorted(str(state) for state in OPEN_STATES))


def _pending_transcript(run_id_column: Any) -> Any:
    return exists().where(
        _TRANSCRIPTS.c.run_id == run_id_column,
        _TRANSCRIPTS.c.state == "PENDING",
    )


def _open_generation(run_id_column: Any) -> Any:
    return exists().where(
        _VIDEO_GENERATIONS.c.story_run_id == run_id_column,
        _VIDEO_GENERATIONS.c.state.in_(_OPEN_GENERATION_VALUES),
    )


def _effective_wait_since() -> Any:
    return func.greatest(
        _RUNS.c.updated_at,
        _RUNS.c.adult_wait_started_at,
        _RUNS.c.last_meaningful_activity_at,
    )


def _waiting_predicate() -> Any:
    no_active_job = or_(
        _RUNS.c.job_state.is_(None),
        _RUNS.c.job_state.not_in(_ACTIVE_JOB_VALUES),
    )
    return or_(
        and_(_RUNS.c.run_state != DRAFT_LIKE_STATE, no_active_job),
        and_(
            _RUNS.c.run_state == DRAFT_LIKE_STATE,
            _RUNS.c.job_state.is_(None),
            ~_pending_transcript(_RUNS.c.run_id),
        ),
    )


class SqlStoryRunReminderStore:
    """SQLAlchemy adapter for a read-only keyset page and one locked reminder transaction."""

    def __init__(
        self,
        session: Session,
        *,
        producer: NotificationProducerPort | None = None,
    ) -> None:
        self._session = session
        self._producer_override = producer

    def scan_candidates(
        self,
        now: datetime,
        limit: int,
        cursor: ReminderScanCursor | None,
    ) -> ReminderCandidatePage:
        instant = require_aware_utc(now, field="now")
        wait_since = _effective_wait_since()
        statement = select(
            _RUNS.c.run_id,
            _RUNS.c.run_state,
            _RUNS.c.revision,
            _RUNS.c.active_owner_parent_account_id,
            wait_since.label("wait_since"),
        ).where(
            _RUNS.c.actor_scope_kind == _PARENT_SCOPE,
            _RUNS.c.run_state.in_(_ADULT_WAIT_VALUES),
            _waiting_predicate(),
            _RUNS.c.updated_at <= instant - REMINDER_DELAY,
            wait_since <= instant - REMINDER_DELAY,
            ~_open_generation(_RUNS.c.run_id),
        )
        if cursor is not None:
            statement = statement.where(
                tuple_(wait_since, _RUNS.c.run_id)
                > tuple_(literal(cursor.wait_since), literal(cursor.run_id))
            )
        statement = statement.order_by(wait_since, _RUNS.c.run_id).limit(limit + 1)
        try:
            rows = self._session.execute(statement).mappings().all()
        finally:
            self._session.rollback()  # listings never hold a transaction or row lock

        has_more = len(rows) > limit
        candidates = tuple(
            ReminderCandidate(
                run_id=str(row["run_id"]),
                run_state=str(row["run_state"]),
                revision=int(row["revision"]),
                owner_account_id=(
                    None
                    if row["active_owner_parent_account_id"] is None
                    else str(row["active_owner_parent_account_id"])
                ),
                wait_since=normalize_utc(row["wait_since"], field="wait_since"),
            )
            for row in rows[:limit]
        )
        return ReminderCandidatePage(candidates=candidates, has_more=has_more)

    def enqueue_if_due(self, candidate: ReminderCandidate, now: datetime) -> ReminderOutcome:
        instant = require_aware_utc(now, field="now")
        try:
            run = (
                self._session.execute(
                    select(_RUNS)
                    .where(_RUNS.c.run_id == candidate.run_id)
                    .with_for_update(skip_locked=True)
                )
                .mappings()
                .one_or_none()
            )
            if run is None:
                self._session.rollback()
                return ReminderOutcome.STALE

            state = str(run["run_state"])
            job_state = None if run["job_state"] is None else str(run["job_state"])
            owner = (
                None
                if run["active_owner_parent_account_id"] is None
                else str(run["active_owner_parent_account_id"])
            )
            since = normalize_utc(
                idle_since(
                    run["updated_at"],
                    run["adult_wait_started_at"],
                    run["last_meaningful_activity_at"],
                ),
                field="wait_since",
            )
            transcript_pending = bool(
                self._session.scalar(select(_pending_transcript(candidate.run_id)))
            )
            generation_open = bool(self._session.scalar(select(_open_generation(candidate.run_id))))

            if (
                run["actor_scope_kind"] != _PARENT_SCOPE
                or owner is None
                or owner != candidate.owner_account_id
                or state != candidate.run_state
                or int(run["revision"]) != candidate.revision
                or since != candidate.wait_since
                or not reminder_due(
                    state,
                    job_state,
                    since,
                    instant,
                    transcript_pending=transcript_pending,
                    open_generation=generation_open,
                )
            ):
                self._session.rollback()
                return ReminderOutcome.STALE

            command = reminder_command(
                recipient_account_id=owner,
                run_id=str(run["run_id"]),
                run_state=state,
                wait_since=since,
            )
            present = self._session.scalar(
                select(exists().where(INBOX_ITEMS.c.trigger_id == command.trigger_id))
            )
            if present:
                self._session.commit()
                return ReminderOutcome.ALREADY_PRESENT

            producer = self._producer_override or SqlNotificationProducer(
                self._session,
                clock=lambda: instant,
            )
            result = producer.enqueue(command)
            self._session.commit()
            return ReminderOutcome.CREATED if result.created else ReminderOutcome.ALREADY_PRESENT
        except BaseException:
            self._session.rollback()
            raise


def build_story_run_reminder(
    session: Session,
    *,
    producer: NotificationProducerPort | None = None,
) -> ReminderSweep:
    """Build the internal service only; no app route or scheduler invokes it by default."""

    store = SqlStoryRunReminderStore(session, producer=producer)
    return ReminderSweep(store, store)


__all__ = ["SqlStoryRunReminderStore", "build_story_run_reminder"]
