"""PostgreSQL store of the adult-wait closeout sweep (FEAT-066 T-1d1; SRS l.394-395, l.503).

Two listings and one transactional close. The listings are bounded, ordered, read-only prefilters;
the close is one transaction per run: ``SELECT ... FOR UPDATE SKIP LOCKED`` on the run row (a row a
live adult command holds is skipped, never waited for), a re-check of every condition under the
lock with the pure rules of ``domain.story_run_closeout``, then a compare-and-set update on the
locked revision and state. Only ``PARENT_ACCOUNT`` runs are read (the Teacher owner column arrives
with DDL-B2). No content column is selected by the listings and nothing is written to the audit
log, the outbox or a notification channel: the effect is the run row alone (lock released,
``finished_at`` set, content kept until the user deletes the run, FR-C-08).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, exists, func, or_, select, update
from sqlalchemy.orm import Session

from sketch2life.application.ports.story_run_closeout import (
    CloseoutOutcome,
    IdleCandidate,
    OverdueGeneration,
)
from sketch2life.application.ports.story_run_lifecycle import PURGE_STATES
from sketch2life.application.ports.story_video import StoryVideoAdapters
from sketch2life.application.services.story_run_closeout import StoryRunCloseoutService
from sketch2life.application.services.story_run_video import (
    DEFAULT_PORT_TIMEOUT_SECONDS,
    StoryVideoProgressService,
)
from sketch2life.domain.story_run_closeout import (
    ACTIVE_JOB_STATES,
    CLOSEOUT_TRANSITIONS,
    DRAFT_LIKE_STATE,
    GENERATION_DEADLINE,
    IDLE_ABANDONED,
    IDLE_CLOSEOUT,
    idle_closeout_due,
    idle_since,
    idle_target,
)
from sketch2life.domain.story_video.model import (
    IN_FLIGHT_STATES,
    OPEN_STATES,
    RUN_STATE_FOR_GENERATION,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository

_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
_RUNS = story_tables.story_runs
_VG = story_tables.video_generations
_TRANSCRIPTS = story_tables.transcript_revisions
_PURGE_STATE_VALUES = tuple(sorted(PURGE_STATES))
_ACTIVE_JOBS = tuple(sorted(ACTIVE_JOB_STATES))
_CLOSABLE_STATES = tuple(sorted(CLOSEOUT_TRANSITIONS))
_IN_FLIGHT_VALUES = tuple(sorted(str(state) for state in IN_FLIGHT_STATES))
_OPEN_VALUES = tuple(sorted(str(state) for state in OPEN_STATES))
_EXPECTED_RUN_STATE = {str(state): RUN_STATE_FOR_GENERATION[state] for state in IN_FLIGHT_STATES}


def _pending_transcript(run_id_column: Any) -> Any:
    return exists().where(_TRANSCRIPTS.c.run_id == run_id_column, _TRANSCRIPTS.c.state == "PENDING")


def _run_matches_generation() -> Any:
    """The run is in the state ``advance`` expects for the generation (else it answers STALE)."""

    return or_(
        *(
            and_(_VG.c.state == state, _RUNS.c.run_state == run_state)
            for state, run_state in _EXPECTED_RUN_STATE.items()
        )
    )


def _open_generation() -> Any:
    return exists().where(_VG.c.story_run_id == _RUNS.c.run_id, _VG.c.state.in_(_OPEN_VALUES))


def _idle_since_column() -> Any:
    # GREATEST ignores NULL, and ``updated_at`` is never NULL: the same rule as ``idle_since``.
    return func.greatest(
        _RUNS.c.updated_at, _RUNS.c.adult_wait_started_at, _RUNS.c.last_meaningful_activity_at
    )


class SqlStoryRunCloseoutStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------------------------------------------------------------------- listings
    def overdue_generations(self, now: datetime, limit: int) -> list[OverdueGeneration]:
        """Accepted generations past ``accepted_at`` + 6 h that have not settled (SRS l.395)."""

        statement = (
            select(_VG.c.video_generation_id, _VG.c.state)
            .join(_RUNS, _RUNS.c.run_id == _VG.c.story_run_id)
            .where(
                _VG.c.state.in_(_IN_FLIGHT_VALUES),
                _VG.c.accepted_at.is_not(None),
                _VG.c.accepted_at <= now - GENERATION_DEADLINE,
                _RUNS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                _RUNS.c.run_state.not_in(_PURGE_STATE_VALUES),
                # A row whose run no longer matches the generation state (a live command moved it)
                # would answer STALE forever and hold a batch slot each pass (T-1d1 P3-8).
                _run_matches_generation(),
            )
            .order_by(_VG.c.accepted_at, _VG.c.video_generation_id)
            .limit(limit)
        )
        try:
            rows = self._session.execute(statement).all()
        finally:
            self._session.rollback()  # a listing holds no transaction open
        return [OverdueGeneration(str(row[0]), str(row[1])) for row in rows]

    def idle_statement(self, now: datetime, limit: int) -> Any:
        """The listing of ``idle_candidates`` as a statement (the evidence reads its plan)."""

        since = _idle_since_column()
        no_active_job = or_(_RUNS.c.job_state.is_(None), _RUNS.c.job_state.not_in(_ACTIVE_JOBS))
        waiting = or_(
            and_(_RUNS.c.run_state != DRAFT_LIKE_STATE, no_active_job),
            and_(
                _RUNS.c.run_state == DRAFT_LIKE_STATE,
                _RUNS.c.job_state.is_(None),
                ~_pending_transcript(_RUNS.c.run_id),
            ),
        )
        return (
            select(_RUNS.c.run_id, _RUNS.c.run_state)
            .where(
                _RUNS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                _RUNS.c.run_state.in_(_CLOSABLE_STATES),
                waiting,
                # No index serves this listing and none is approved here: the clock is the GREATEST
                # of three columns and never earlier than ``updated_at``, so this prefilter cannot
                # lose a due row. It keeps the plan cheap to filter and the batch ordered; it does
                # not avoid the sequential scan (see the T-1d1-fix evidence note).
                _RUNS.c.updated_at <= now - IDLE_CLOSEOUT,
                since <= now - IDLE_CLOSEOUT,
                # A run with an open generation is never closed: do not let always-skip rows head
                # the bounded batch (the close re-checks the same predicate under the lock).
                ~_open_generation(),
            )
            .order_by(since, _RUNS.c.run_id)
            .limit(limit)
        )

    def idle_candidates(self, now: datetime, limit: int) -> list[IdleCandidate]:
        """Runs that look idle at ``now``; the close re-checks each one under its lock."""

        statement = self.idle_statement(now, limit)
        try:
            rows = self._session.execute(statement).all()
        finally:
            self._session.rollback()
        return [IdleCandidate(str(row[0]), str(row[1])) for row in rows]

    # ---------------------------------------------------------------------- the close
    def close_idle(self, run_id: str, now: datetime) -> CloseoutOutcome:
        try:
            outcome = self._close(run_id, now)
            self._session.commit()
            return outcome
        except BaseException:
            self._session.rollback()
            raise

    def _close(self, run_id: str, now: datetime) -> CloseoutOutcome:
        run = (
            self._session.execute(
                select(_RUNS).where(_RUNS.c.run_id == run_id).with_for_update(skip_locked=True)
            )
            .mappings()
            .one_or_none()
        )
        if run is None or run["actor_scope_kind"] != _OWNER_SCOPE_KIND:
            return CloseoutOutcome.SKIPPED  # locked by a live command, gone, or not a Parent run
        state = str(run["run_state"])
        job_state = None if run["job_state"] is None else str(run["job_state"])
        pending = bool(self._session.scalar(select(_pending_transcript(run_id))))
        target = idle_target(state, job_state, transcript_pending=pending)
        if target is None or not idle_closeout_due(
            idle_since(
                run["updated_at"], run["adult_wait_started_at"], run["last_meaningful_activity_at"]
            ),
            now,
        ):
            return CloseoutOutcome.SKIPPED
        if self._session.scalar(
            select(exists().where(_VG.c.story_run_id == run_id, _VG.c.state.in_(_OPEN_VALUES)))
        ):
            return CloseoutOutcome.SKIPPED  # a generation is still open: the run is not idle
        changed = self._session.execute(
            update(_RUNS)
            .where(
                _RUNS.c.run_id == run_id,
                _RUNS.c.revision == run["revision"],
                _RUNS.c.run_state == state,
            )
            .values(
                run_state=target,
                active_owner_parent_account_id=None,
                adult_wait_started_at=None,
                finished_at=now,
                retryable=False,
                # A closed run shows no failure of a job that no longer matters; ``COMPLETED``
                # keeps ``SUCCEEDED`` (SRS is silent: T-1d1-fix-DEC-5). The failed attempt stays
                # on the generation row and in the T-1c detail.
                error_code=None,
                job_state=None if target == IDLE_ABANDONED else run["job_state"],
                revision=int(run["revision"]) + 1,
                version=int(run["version"]) + 1,
                updated_at=now,
            )
        )
        if changed.rowcount != 1:  # type: ignore[attr-defined]
            return CloseoutOutcome.SKIPPED
        return CloseoutOutcome.ABANDONED if target == IDLE_ABANDONED else CloseoutOutcome.COMPLETED


def build_story_run_closeout(
    session: Session,
    adapters: StoryVideoAdapters | None,
    *,
    call_timeout_seconds: float = DEFAULT_PORT_TIMEOUT_SECONDS,
) -> StoryRunCloseoutService:
    """The sweep over one session; the periodic runner (``sweep_worker``) calls ``run_once`` on it.

    ``adapters`` is the same pair the admission route uses; with ``None`` a deadline failure still
    ends the generation and settles the run, and the compute reservation stays for the reconciler.
    """

    progress = StoryVideoProgressService(
        SqlStoryVideoRepository(session), adapters, call_timeout_seconds=call_timeout_seconds
    )
    return StoryRunCloseoutService(SqlStoryRunCloseoutStore(session), progress)


__all__ = ["SqlStoryRunCloseoutStore", "build_story_run_closeout"]
