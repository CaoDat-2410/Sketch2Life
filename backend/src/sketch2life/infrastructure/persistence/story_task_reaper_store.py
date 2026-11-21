"""PostgreSQL store of the lost-background-task reaper (FEAT-066 T-2d-fix; SRS l.394, l.615).

Five listings (one per stuck kind) and one transactional ``reap``. The listings are bounded,
ordered, read-only prefilters that select ids and clocks only (no content column). ``reap`` is one
transaction per run: ``SELECT ... FOR UPDATE SKIP LOCKED`` on the run row (a row a live adult
command or a late worker holds is skipped, never waited for), a re-check of every condition under
the lock, then compare-and-set writes on the locked revision and state. Only ``PARENT_ACCOUNT``
runs of the Parent lane are touched: the StoryRun-lite demo lane writes the same table but never
sets ``current_input_revision``, so that column is the lane marker. Every effect writes one
metadata audit row (actor, action, run id, safe code; no content, BR-34 l.278).

The clock is ``updated_at`` (every Parent run write bumps it, T-1d1 audit), so the lease is an
inactivity lease and not the SRS job deadline; the transcript clock is its own ``created_at``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import and_, func, select, update
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_lifecycle import PURGE_STATES
from sketch2life.application.ports.story_task_reaper import (
    AUDIT_TIMED_OUT_DRAWING,
    AUDIT_TIMED_OUT_STORY,
    AUDIT_TIMED_OUT_TRANSCRIPT,
    REAPER_ACTOR_REF,
    TASK_TIMEOUT_CODE,
    ReapCandidate,
    ReapKind,
    ReapOutcome,
)
from sketch2life.application.services.story_task_reaper import StoryTaskReaperService
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    write_story_task_audit,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
_RUNS = story_tables.story_runs
_TRANSCRIPTS = story_tables.transcript_revisions
_REVISIONS = story_tables.story_revisions
_RECEIPTS = story_tables.story_command_receipts
_INPUTS = story_tables.run_inputs
_PURGE_STATE_VALUES = tuple(sorted(PURGE_STATES))
_LOST_JOBS = ("QUEUED", "RUNNING")
_UNKNOWN_JOB = "AWAITING_RECONCILIATION"
_REWRITE_OPERATION = "GENERATE_STORY_REVISION"


def _parent_lane() -> Any:
    """Parent-lane runs only: the demo lane never sets ``current_input_revision``."""

    return and_(
        _RUNS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
        _RUNS.c.current_input_revision.is_not(None),
        _RUNS.c.run_state.not_in(_PURGE_STATE_VALUES),
    )


class SqlStoryTaskReaperStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------------------------------------------------------------------- listings
    def list_candidates(self, kind: ReapKind, cutoff: datetime, limit: int) -> list[ReapCandidate]:
        """Runs that look stuck at ``cutoff``; ``reap`` re-checks each one under its lock."""

        if kind is ReapKind.TRANSCRIPT_LOST:
            oldest = func.min(_TRANSCRIPTS.c.created_at)
            statement = (
                select(_RUNS.c.run_id)
                .join(_TRANSCRIPTS, _TRANSCRIPTS.c.run_id == _RUNS.c.run_id)
                .where(
                    _parent_lane(),
                    _RUNS.c.run_state == "INPUT_PROCESSING",
                    _TRANSCRIPTS.c.state == "PENDING",
                    _TRANSCRIPTS.c.created_at <= cutoff,
                )
                .group_by(_RUNS.c.run_id)
                .order_by(oldest, _RUNS.c.run_id)
                .limit(limit)
            )
        else:
            run_state, jobs = _kind_state(kind)
            conditions: list[Any] = [
                _parent_lane(),
                _RUNS.c.run_state == run_state,
                _RUNS.c.updated_at <= cutoff,
            ]
            if jobs:
                conditions.append(_RUNS.c.job_state.in_(jobs))
            statement = (
                select(_RUNS.c.run_id)
                .where(*conditions)
                .order_by(_RUNS.c.updated_at, _RUNS.c.run_id)
                .limit(limit)
            )
        try:
            rows = self._session.execute(statement).all()
        finally:
            self._session.rollback()  # a listing holds no transaction open
        return [ReapCandidate(str(row[0]), kind) for row in rows]

    # ---------------------------------------------------------------------- the reap
    def reap(self, candidate: ReapCandidate, now: datetime, cutoff: datetime) -> ReapOutcome:
        try:
            outcome = self._reap(candidate, now, cutoff)
            if outcome is ReapOutcome.SKIPPED:
                self._session.rollback()
            else:
                self._session.commit()
            return outcome
        except BaseException:
            self._session.rollback()
            raise

    def _reap(self, candidate: ReapCandidate, now: datetime, cutoff: datetime) -> ReapOutcome:
        run = (
            self._session.execute(
                select(_RUNS)
                .where(_RUNS.c.run_id == candidate.run_id)
                .with_for_update(skip_locked=True)
            )
            .mappings()
            .one_or_none()
        )
        if (
            run is None
            or run["actor_scope_kind"] != _OWNER_SCOPE_KIND
            or run["current_input_revision"] is None
            or run["run_state"] in PURGE_STATES
        ):
            return ReapOutcome.SKIPPED  # locked by a live command, gone, purged or a demo run
        if candidate.kind in (ReapKind.DRAWING_LOST, ReapKind.DRAWING_UNKNOWN):
            return self._reap_drawing(run, candidate.kind, now, cutoff)
        if candidate.kind is ReapKind.TRANSCRIPT_LOST:
            return self._reap_transcript(run, now, cutoff)
        return self._reap_story(run, candidate.kind, now, cutoff)

    def _reap_drawing(
        self, run: RowMapping, kind: ReapKind, now: datetime, cutoff: datetime
    ) -> ReapOutcome:
        run_state, jobs = _kind_state(kind)
        if (
            run["run_state"] != run_state
            or run["job_state"] not in jobs
            or run["updated_at"] > cutoff
        ):
            return ReapOutcome.SKIPPED
        changed = cast(
            CursorResult[Any],
            self._session.execute(
                update(_RUNS)
                .where(
                    _RUNS.c.run_id == run["run_id"],
                    _RUNS.c.revision == run["revision"],
                    _RUNS.c.run_state == run_state,
                    _RUNS.c.job_state == run["job_state"],
                )
                .values(
                    job_state="FAILED",
                    retryable=True,
                    error_code=TASK_TIMEOUT_CODE,
                    version=int(run["version"]) + 1,
                    revision=int(run["revision"]) + 1,
                    updated_at=now,
                )
            ),
        )
        if changed.rowcount != 1:
            return ReapOutcome.SKIPPED
        # T2C-D6: INPUT_REVIEW for a first analysis or a retake, SUBJECT_REVIEW for a lost rerun
        # (the earlier understanding of the same drawing stays), unless a transcript still waits.
        SqlParentStoryRunRepository(self._session).settle_run_state(str(run["run_id"]))
        self._audit(run, AUDIT_TIMED_OUT_DRAWING, now)
        return ReapOutcome.DRAWING_TIMED_OUT

    def _reap_transcript(self, run: RowMapping, now: datetime, cutoff: datetime) -> ReapOutcome:
        if run["run_state"] != "INPUT_PROCESSING":
            return ReapOutcome.SKIPPED
        voice_ref = self._session.scalar(
            select(_INPUTS.c.voice_asset_ref).where(
                _INPUTS.c.run_id == run["run_id"],
                _INPUTS.c.input_revision == run["current_input_revision"],
            )
        )
        if voice_ref is None:
            return ReapOutcome.SKIPPED
        # The latest non-superseded transcript of the current voice asset is the one the run waits
        # for (T2C-D4); an older one of a replaced voice asset does not block anything.
        latest = self._session.execute(
            select(
                _TRANSCRIPTS.c.transcript_revision_id,
                _TRANSCRIPTS.c.state,
                _TRANSCRIPTS.c.created_at,
            )
            .where(
                _TRANSCRIPTS.c.run_id == run["run_id"],
                _TRANSCRIPTS.c.source_asset_ref == voice_ref,
                _TRANSCRIPTS.c.state != "SUPERSEDED",
            )
            .order_by(_TRANSCRIPTS.c.revision_no.desc())
            .limit(1)
        ).one_or_none()
        if latest is None or latest[1] != "PENDING" or latest[2] > cutoff:
            return ReapOutcome.SKIPPED
        failed = cast(
            CursorResult[Any],
            self._session.execute(
                update(_TRANSCRIPTS)
                .where(
                    _TRANSCRIPTS.c.transcript_revision_id == latest[0],
                    _TRANSCRIPTS.c.state == "PENDING",
                )
                .values(state="FAILED", error_code=TASK_TIMEOUT_CODE)
            ),
        )
        if failed.rowcount != 1:
            return ReapOutcome.SKIPPED
        bumped = cast(
            CursorResult[Any],
            self._session.execute(
                update(_RUNS)
                .where(
                    _RUNS.c.run_id == run["run_id"],
                    _RUNS.c.revision == run["revision"],
                    _RUNS.c.run_state == "INPUT_PROCESSING",
                )
                .values(
                    version=int(run["version"]) + 1,
                    revision=int(run["revision"]) + 1,
                    updated_at=now,
                )
            ),
        )
        if bumped.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        SqlParentStoryRunRepository(self._session).settle_run_state(str(run["run_id"]))
        self._audit(run, AUDIT_TIMED_OUT_TRANSCRIPT, now)
        return ReapOutcome.TRANSCRIPT_TIMED_OUT

    def _reap_story(
        self, run: RowMapping, kind: ReapKind, now: datetime, cutoff: datetime
    ) -> ReapOutcome:
        run_state, jobs = _kind_state(kind)
        if (
            run["run_state"] != run_state
            or (jobs and run["job_state"] not in jobs)
            or run["updated_at"] > cutoff
        ):
            return ReapOutcome.SKIPPED
        row_status = "GENERATING" if kind is ReapKind.STORY_LOST else "AWAITING_RECONCILIATION"
        revision = self._session.execute(
            select(
                _REVISIONS.c.story_revision_id,
                _REVISIONS.c.revision_no,
                _REVISIONS.c.status,
            )
            .where(_REVISIONS.c.run_id == run["run_id"])
            .order_by(_REVISIONS.c.revision_no.desc())
            .limit(1)
        ).one_or_none()
        if revision is None or revision[2] != row_status:
            return ReapOutcome.SKIPPED
        revision_id, revision_no = str(revision[0]), int(revision[1])
        is_rewrite = revision_no >= 2 and self._is_rewrite_route(run, revision_id)
        try:
            if is_rewrite:
                SqlParentStoryRunRepository(self._session).recover_failed_rewrite(
                    run=run,
                    story_revision_id=revision_id,
                    revision_no=revision_no,
                    error_code=TASK_TIMEOUT_CODE,
                    now=now,
                    actor_ref=REAPER_ACTOR_REF,
                )
                return ReapOutcome.REWRITE_RECOVERED
            self._fail_story_terminally(run, revision_id, row_status, now)
        except ParentStoryRunError:
            return ReapOutcome.SKIPPED  # a compare-and-set missed: the caller rolls back
        self._audit(run, AUDIT_TIMED_OUT_STORY, now)
        return ReapOutcome.STORY_FAILED

    def _is_rewrite_route(self, run: RowMapping, revision_id: str) -> bool:
        """``True`` when a final 202 receipt of ``story-rewrites`` names this revision (D1)."""

        return (
            self._session.scalar(
                select(_RECEIPTS.c.receipt_id)
                .where(
                    _RECEIPTS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                    _RECEIPTS.c.actor_scope_ref == run["actor_scope_ref"],
                    _RECEIPTS.c.operation == _REWRITE_OPERATION,
                    _RECEIPTS.c.idempotency_scope_kind == "STORY_RUN",
                    _RECEIPTS.c.idempotency_scope_ref == run["run_id"],
                    _RECEIPTS.c.state == "FINAL",
                    _RECEIPTS.c.response_status == 202,
                    _RECEIPTS.c.response_body["story_revision_id"].astext == revision_id,
                )
                .limit(1)
            )
            is not None
        )

    def _fail_story_terminally(
        self, run: RowMapping, revision_id: str, row_status: str, now: datetime
    ) -> None:
        """A first story or a legacy-route story: the run ends ``FAILED`` as in D1 (l.1413)."""

        failed_row = cast(
            CursorResult[Any],
            self._session.execute(
                update(_REVISIONS)
                .where(
                    _REVISIONS.c.story_revision_id == revision_id,
                    _REVISIONS.c.run_id == run["run_id"],
                    _REVISIONS.c.status == row_status,
                )
                .values(status="FAILED")
            ),
        )
        if failed_row.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        new_version = int(run["version"]) + 1
        failed_run = cast(
            CursorResult[Any],
            self._session.execute(
                update(_RUNS)
                .where(
                    _RUNS.c.run_id == run["run_id"],
                    _RUNS.c.revision == run["revision"],
                    _RUNS.c.run_state == run["run_state"],
                )
                .values(
                    run_state="FAILED",
                    job_state="FAILED",
                    retryable=False,
                    error_code=TASK_TIMEOUT_CODE,
                    active_owner_parent_account_id=None,
                    adult_wait_started_at=None,
                    finished_at=now,
                    version=new_version,
                    revision=int(run["revision"]) + 1,
                    updated_at=now,
                )
            ),
        )
        if failed_run.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        # The legacy route's receipt is still PENDING (at most one per run and actor): finalise it
        # as the provider failure the caller would have seen; a rewrite route receipt is final.
        self._session.execute(
            update(_RECEIPTS)
            .where(
                _RECEIPTS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                _RECEIPTS.c.actor_scope_ref == run["actor_scope_ref"],
                _RECEIPTS.c.operation == _REWRITE_OPERATION,
                _RECEIPTS.c.idempotency_scope_kind == "STORY_RUN",
                _RECEIPTS.c.idempotency_scope_ref == run["run_id"],
                _RECEIPTS.c.state == "PENDING",
            )
            .values(
                state="FINAL",
                response_status=502,
                response_resource_version=new_version,
                response_body={"error_code": TASK_TIMEOUT_CODE},
                resource_version=new_version,
                state_version=_RECEIPTS.c.state_version + 1,
                finalized_at=now,
            )
        )

    def _audit(self, run: RowMapping, action: str, now: datetime) -> None:
        write_story_task_audit(
            self._session,
            owner_scope_ref=str(run["actor_scope_ref"]),
            actor_ref=REAPER_ACTOR_REF,
            action=action,
            run_id=str(run["run_id"]),
            decision=TASK_TIMEOUT_CODE,
            run_revision=int(run["revision"]) + 1,
            now=now,
        )


def _kind_state(kind: ReapKind) -> tuple[str, tuple[str, ...]]:
    """The run state and the job states a kind looks for (empty: any job state)."""

    if kind is ReapKind.DRAWING_LOST:
        return "INPUT_PROCESSING", _LOST_JOBS
    if kind is ReapKind.DRAWING_UNKNOWN:
        return "INPUT_PROCESSING", (_UNKNOWN_JOB,)
    if kind is ReapKind.STORY_LOST:
        return "SCRIPT_GENERATING", _LOST_JOBS
    if kind is ReapKind.STORY_UNKNOWN:
        return "SCRIPT_GENERATION_UNKNOWN", ()
    return "INPUT_PROCESSING", ()


def build_story_task_reaper(session: Session) -> StoryTaskReaperService:
    """The reaper over one session: the periodic runner (not built yet) calls ``run_once`` on it."""

    return StoryTaskReaperService(SqlStoryTaskReaperStore(session))


__all__ = ["SqlStoryTaskReaperStore", "build_story_task_reaper"]
