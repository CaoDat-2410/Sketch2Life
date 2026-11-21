"""Story-owned PostgreSQL adapter for the FR-C-08 StoryRun purge (DTR Draft 6).

It implements the Story lifecycle port and ``RunAssetReferencePort`` of
``application.ports.story_run_lifecycle``: the step-4 plan and purge of run-owned Story
content, the ``DELETED`` finalization of step 5, the run state read and the cross-run asset
reference answer. It also holds the one-time reconciliation of pre-existing ``DELETE_PENDING``
runs (DTR §6.4). Every statement is scoped to one run; no content is ever logged. A run is a
Parent run (``PARENT_ACCOUNT``, no organization column) or, since FEAT-066 T-13a, a Teacher run
(``ORGANIZATION``, ``organization_id`` = the scope ref): the run row names its own kind and the
aggregate, audit and event rows copy it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import Table, and_, delete, exists, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.core_foundation import (
    ORGANIZATION_SCOPE_KIND,
    PARENT_SCOPE_KIND,
    LifecycleScope,
    validate_run_ref,
)
from sketch2life.application.ports.story_run_lifecycle import (
    AUDIT_COMPLETED,
    AUDIT_RESOURCE_TYPE,
    CANCEL_EVENT_TYPE,
    LIFECYCLE_WORKER_ACTOR,
    PURGE_STATES,
    StoryLifecycleError,
    StoryPurgePlan,
    is_projection_body,
    lifecycle_audit_id,
    lifecycle_event_id,
    lifecycle_projection_body,
    lifecycle_request_id,
    sha256_hex,
)
from sketch2life.domain.story_video.model import OPEN_STATES as OPEN_VIDEO_STATES
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_RUNS = story_tables.story_runs
_RECEIPTS = story_tables.story_command_receipts
_AGGREGATES = cast(Table, CoreAggregateRevisionModel.__table__)
_OUTBOX = cast(Table, CoreOutboxEventModel.__table__)
_AUDIT = cast(Table, CoreAuditEntryModel.__table__)
_PURGE_STATE_VALUES = tuple(sorted(PURGE_STATES))
_LIFECYCLE_SCOPE_KINDS = (PARENT_SCOPE_KIND, ORGANIZATION_SCOPE_KIND)

# DTR S10: the run-owned private columns of ``story.runs`` that step 4 sets to NULL. Identity,
# scope, state, revision and version are kept.
S10_RUN_COLUMNS: tuple[str, ...] = (
    "asset_ref",
    "derived_asset_ref",
    "subject_label",
    "confidence",
    "result_sha256",
    "raw_body_sha256",
    "child_age_months",
    "profile_ref",
    "provider_job_id",
    "provider_attempt_id",
    "understanding_revision",
    "error_code",
    "current_input_revision",
    # T-1a: the pointer to the current video generation; the generation rows go in step 4 too.
    "current_video_generation_id",
)
# The two receipt operations whose fingerprints hold only the run id (and, for cancel, the
# expected revision) and are never tombstoned (DTR step 4, S12).
_LIFECYCLE_OPERATIONS = frozenset({"CANCEL_RUN", "DELETE_RUN"})


def tombstone_fingerprint(receipt_id: str) -> str:
    """``SHA-256('tombstone:' || receipt_id)`` (DTR Draft 6 step 4)."""

    return sha256_hex("tombstone:" + receipt_id)


@dataclass(frozen=True, slots=True)
class StoryRunSnapshot:
    """The facts of one run that decide its Story purge plan (no content values)."""

    run_id: str
    run_state: str
    revision: int
    version: int
    s10_present: bool
    child_ids: tuple[str, ...]
    receipts: tuple[tuple[str, str, str, Any], ...]  # (receipt_id, operation, fingerprint, body)
    # T-1a: video requests that a worker or the reconciler still owns (an intent or in flight).
    unsettled_generations: int = 0
    # T-13a: the owner scope kind of the run row (``PARENT_ACCOUNT`` or ``ORGANIZATION``).
    scope_kind: str = PARENT_SCOPE_KIND


def _require_settled_video(snapshot: StoryRunSnapshot) -> None:
    """T-1a (D4): a purge never deletes a request that the saga or a worker still owns.

    The error is retryable: the lifecycle consumer fails the attempt and tries again once the
    cancel hook or the reconciler has settled the generation.
    """

    if snapshot.unsettled_generations:
        raise StoryLifecycleError("VIDEO_GENERATION_UNSETTLED")


def story_plan_ids(snapshot: StoryRunSnapshot) -> tuple[str, ...]:
    """DTR T2 ``story`` identifiers: child rows, untombstoned receipts and ``run:<id>``."""

    ids: list[str] = list(snapshot.child_ids)
    for receipt_id, operation, fingerprint, body in snapshot.receipts:
        if operation == "CANCEL_RUN":
            pending = not is_projection_body(body)
        else:
            pending = operation not in _LIFECYCLE_OPERATIONS and fingerprint != (
                tombstone_fingerprint(receipt_id)
            )
        if pending:
            ids.append("receipt:" + receipt_id)
    if snapshot.s10_present:
        ids.append("run:" + snapshot.run_id)
    return tuple(sorted(ids))


class SqlStoryLifecycleStore:
    """Story lifecycle port and ``RunAssetReferencePort`` over the Story schema."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    # ---------------------------------------------------------------- reads
    def lifecycle_state(self, run_ref: str) -> str | None:
        run_id = validate_run_ref(run_ref)
        with self._sessions() as session:
            state = session.scalar(
                select(_RUNS.c.run_state).where(
                    _RUNS.c.run_id == run_id,
                    _RUNS.c.actor_scope_kind.in_(_LIFECYCLE_SCOPE_KINDS),
                )
            )
            return None if state is None else str(state)

    def plan_story_purge(self, run_ref: str) -> StoryPurgePlan:
        run_id = validate_run_ref(run_ref)
        with self._sessions() as session:
            snapshot = self._snapshot(session, run_id, lock=False)
        _require_settled_video(snapshot)
        return StoryPurgePlan(run_ref=run_id, ids=story_plan_ids(snapshot))

    def assets_referenced_by_other_runs(
        self, scope: LifecycleScope, run_ref: str, asset_refs: frozenset[str]
    ) -> frozenset[str]:
        """The subset of ``asset_refs`` that any other run or run input references (§5.2)."""

        run_id = validate_run_ref(run_ref)
        del scope  # the answer covers every other run, in any scope
        refs = sorted(asset_refs)
        if not refs:
            return frozenset()
        inputs = story_tables.run_inputs
        found: set[str] = set()
        with self._sessions() as session:
            for column in (_RUNS.c.asset_ref, _RUNS.c.derived_asset_ref):
                found.update(
                    str(value)
                    for value in session.scalars(
                        select(column).where(_RUNS.c.run_id != run_id, column.in_(refs))
                    )
                )
            for column in (
                inputs.c.original_asset_ref,
                inputs.c.derived_asset_ref,
                inputs.c.voice_asset_ref,
            ):
                found.update(
                    str(value)
                    for value in session.scalars(
                        select(column).where(inputs.c.run_id != run_id, column.in_(refs))
                    )
                )
        return frozenset(found & set(refs))

    # ---------------------------------------------------------------- writes
    def purge_story_content(self, plan: StoryPurgePlan) -> None:
        """DTR step 4 in one Story transaction; the plan is re-derived under the run lock."""

        run_id = validate_run_ref(plan.run_ref)
        with self._sessions.begin() as session:
            snapshot = self._snapshot(session, run_id, lock=True)
            if snapshot.run_state not in PURGE_STATES:
                raise StoryLifecycleError("RUN_NOT_PURGEABLE")
            _require_settled_video(snapshot)
            current = story_plan_ids(snapshot)
            if current != plan.ids:
                raise StoryLifecycleError("PLAN_CHANGED")
            if not current:
                return
            self._delete_children(session, run_id)
            session.execute(
                update(_RUNS)
                .where(_RUNS.c.run_id == run_id, _RUNS.c.run_state.in_(_PURGE_STATE_VALUES))
                .values({name: None for name in S10_RUN_COLUMNS})
            )
            projection = lifecycle_projection_body(
                run_id=run_id,
                run_state=snapshot.run_state,
                revision=snapshot.revision,
                version=snapshot.version,
            )
            for receipt_id, operation, fingerprint, body in snapshot.receipts:
                if operation == "CANCEL_RUN":
                    if not is_projection_body(body):
                        session.execute(
                            update(_RECEIPTS)
                            .where(_RECEIPTS.c.receipt_id == receipt_id)
                            .values(
                                response_body=projection,
                                state_version=_RECEIPTS.c.state_version + 1,
                            )
                        )
                elif operation not in _LIFECYCLE_OPERATIONS:
                    tombstone = tombstone_fingerprint(receipt_id)
                    if fingerprint != tombstone:
                        session.execute(
                            update(_RECEIPTS)
                            .where(_RECEIPTS.c.receipt_id == receipt_id)
                            .values(
                                request_fingerprint_sha256=tombstone,
                                state_version=_RECEIPTS.c.state_version + 1,
                            )
                        )

    def finalize_deleted(self, run_ref: str, request_id: str) -> bool:
        """DTR step 5: ``DELETED``, revision/version +1, aggregate row, ``lifecycle.completed``."""

        run_id = validate_run_ref(run_ref)
        if request_id != lifecycle_request_id(run_id):
            raise StoryLifecycleError("REQUEST_ID_MISMATCH")
        with self._sessions.begin() as session:
            snapshot = self._snapshot(session, run_id, lock=True)
            if snapshot.run_state == "DELETED":
                return False
            if snapshot.run_state != "DELETE_PENDING":
                raise StoryLifecycleError("RUN_NOT_PURGEABLE")
            if story_plan_ids(snapshot):
                raise StoryLifecycleError("STORY_CONTENT_NOT_PURGED")
            scope_ref = self._scope_ref(session, run_id)
            now = datetime.now(UTC)
            new_revision = snapshot.revision + 1
            changed = cast(
                CursorResult[Any],
                session.execute(
                    update(_RUNS)
                    .where(_RUNS.c.run_id == run_id, _RUNS.c.run_state == "DELETE_PENDING")
                    .values(
                        run_state="DELETED",
                        revision=new_revision,
                        version=snapshot.version + 1,
                        updated_at=now,
                    )
                ),
            )
            if changed.rowcount != 1:
                raise StoryLifecycleError("RUN_NOT_PURGEABLE")
            scope_kind = snapshot.scope_kind
            _upsert_aggregate(
                session,
                run_id=run_id,
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                revision=new_revision,
            )
            session.execute(
                pg_insert(_AUDIT)
                .values(
                    audit_id=lifecycle_audit_id(request_id, AUDIT_COMPLETED),
                    organization_id=_organization_column(scope_kind, scope_ref),
                    owner_scope_kind=scope_kind,
                    owner_scope_ref=scope_ref,
                    actor_ref=LIFECYCLE_WORKER_ACTOR,
                    action=AUDIT_COMPLETED,
                    resource_type=AUDIT_RESOURCE_TYPE,
                    resource_id=run_id,
                    decision="completed:" + request_id,
                    created_at=now,
                )
                .on_conflict_do_nothing(index_elements=["audit_id"])
            )
            return True

    # ---------------------------------------------------------------- DTR §6.4
    def delete_pending_runs_without_event(self, *, limit: int = 500) -> tuple[str, ...]:
        """``DELETE_PENDING`` runs (Parent or Teacher) with no outbox event for their aggregate."""

        if not 1 <= limit <= 5000:
            raise ValueError("reconciliation page size is outside the allowed bounds")
        with self._sessions() as session:
            rows = session.scalars(
                select(_RUNS.c.run_id)
                .where(
                    _RUNS.c.actor_scope_kind.in_(_LIFECYCLE_SCOPE_KINDS),
                    _RUNS.c.run_state == "DELETE_PENDING",
                    ~exists().where(_OUTBOX.c.aggregate_id == _RUNS.c.run_id),
                )
                .order_by(_RUNS.c.run_id)
                .limit(limit)
            )
            return tuple(str(value) for value in rows)

    def insert_reconciliation_event(self, run_ref: str) -> bool:
        """Insert ``StoryRunCancellationRequestedV1`` and the aggregate row, if absent.

        Returns ``True`` only when this call inserted the event. A run that is no longer
        ``DELETE_PENDING`` or already has an event for its aggregate is left unchanged.
        """

        run_id = validate_run_ref(run_ref)
        with self._sessions.begin() as session:
            run = session.execute(
                select(
                    _RUNS.c.run_state,
                    _RUNS.c.revision,
                    _RUNS.c.actor_scope_ref,
                    _RUNS.c.actor_scope_kind,
                )
                .where(
                    _RUNS.c.run_id == run_id,
                    _RUNS.c.actor_scope_kind.in_(_LIFECYCLE_SCOPE_KINDS),
                )
                .with_for_update()
            ).one_or_none()
            if run is None or run.run_state != "DELETE_PENDING":
                return False
            if session.scalar(select(exists().where(_OUTBOX.c.aggregate_id == run_id))):
                return False
            scope_ref = str(run.actor_scope_ref)
            scope_kind = str(run.actor_scope_kind)
            revision = int(run.revision)
            _upsert_aggregate(
                session,
                run_id=run_id,
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                revision=revision,
            )
            now = datetime.now(UTC)
            # The insert is judged by RETURNING, not by rowcount: SQLAlchemy only guarantees
            # rowcount for UPDATE and DELETE (owner run 20261119-103216 saw an inserted=0 here).
            inserted = session.execute(
                reconciliation_event_statement(
                    run_id=run_id,
                    scope_ref=scope_ref,
                    revision=revision,
                    now=now,
                    scope_kind=scope_kind,
                )
            ).scalar_one_or_none()
            return inserted is not None

    # ---------------------------------------------------------------- helpers
    def _snapshot(self, session: Session, run_id: str, *, lock: bool) -> StoryRunSnapshot:
        query = select(_RUNS).where(
            _RUNS.c.run_id == run_id, _RUNS.c.actor_scope_kind.in_(_LIFECYCLE_SCOPE_KINDS)
        )
        if lock:
            query = query.with_for_update()
        run = session.execute(query).mappings().one_or_none()
        if run is None:
            raise StoryLifecycleError("RUN_NOT_FOUND")
        receipts = session.execute(
            select(
                _RECEIPTS.c.receipt_id,
                _RECEIPTS.c.operation,
                _RECEIPTS.c.request_fingerprint_sha256,
                _RECEIPTS.c.response_body,
            )
            .where(_RECEIPTS.c.resource_ref == run_id)
            .order_by(_RECEIPTS.c.receipt_id)
        ).all()
        return StoryRunSnapshot(
            run_id=run_id,
            run_state=str(run["run_state"]),
            revision=int(run["revision"]),
            version=int(run["version"]),
            s10_present=_s10_present(run),
            child_ids=tuple(self._child_ids(session, run_id)),
            receipts=tuple(
                (str(row[0]), str(row[1]), str(row[2]), row[3]) for row in receipts
            ),
            scope_kind=str(run["actor_scope_kind"]),
            unsettled_generations=int(
                session.scalar(
                    select(func.count())
                    .select_from(story_tables.video_generations)
                    .where(
                        story_tables.video_generations.c.story_run_id == run_id,
                        story_tables.video_generations.c.state.in_(
                            sorted(str(state) for state in OPEN_VIDEO_STATES)
                        ),
                    )
                )
                or 0
            ),
        )

    @staticmethod
    def _child_ids(session: Session, run_id: str) -> Iterable[str]:
        t = story_tables
        revisions = select(t.story_revisions.c.story_revision_id).where(
            t.story_revisions.c.run_id == run_id
        )
        generations = select(t.video_generations.c.video_generation_id).where(
            t.video_generations.c.story_run_id == run_id
        )
        sources: tuple[tuple[str, Any, Any], ...] = (
            ("run_inputs", t.run_inputs.c.run_input_id, t.run_inputs.c.run_id == run_id),
            (
                "video_generation_scenes",
                t.video_generation_scenes.c.generation_scene_id,
                t.video_generation_scenes.c.video_generation_id.in_(generations),
            ),
            (
                "video_generations",
                t.video_generations.c.video_generation_id,
                t.video_generations.c.story_run_id == run_id,
            ),
            (
                "understanding_revisions",
                t.understanding_revisions.c.understanding_revision_id,
                t.understanding_revisions.c.run_id == run_id,
            ),
            (
                "transcript_revisions",
                t.transcript_revisions.c.transcript_revision_id,
                t.transcript_revisions.c.run_id == run_id,
            ),
            (
                "review_decisions",
                t.review_decisions.c.decision_id,
                t.review_decisions.c.run_id == run_id,
            ),
            (
                "story_revisions",
                t.story_revisions.c.story_revision_id,
                t.story_revisions.c.run_id == run_id,
            ),
            (
                "story_scenes",
                t.story_scenes.c.scene_id,
                t.story_scenes.c.story_revision_id.in_(revisions),
            ),
            (
                "story_revision_reviews",
                t.story_revision_reviews.c.review_id,
                t.story_revision_reviews.c.run_id == run_id,
            ),
        )
        for name, column, predicate in sources:
            for value in session.scalars(select(column).where(predicate)):
                yield f"{name}:{value}"

    @staticmethod
    def _delete_children(session: Session, run_id: str) -> None:
        t = story_tables
        revisions = select(t.story_revisions.c.story_revision_id).where(
            t.story_revisions.c.run_id == run_id
        )
        # T-1a: generations hold composite keys to the revisions and the reviews, so they go first
        # (scenes, then the run pointer, then the generations); the pointer is set NULL before the
        # row it names is deleted.
        generations = select(t.video_generations.c.video_generation_id).where(
            t.video_generations.c.story_run_id == run_id
        )
        session.execute(
            delete(t.video_generation_scenes).where(
                t.video_generation_scenes.c.video_generation_id.in_(generations)
            )
        )
        session.execute(
            update(_RUNS).where(_RUNS.c.run_id == run_id).values(current_video_generation_id=None)
        )
        session.execute(
            delete(t.video_generations).where(t.video_generations.c.story_run_id == run_id)
        )
        session.execute(
            delete(t.story_revision_reviews).where(t.story_revision_reviews.c.run_id == run_id)
        )
        session.execute(delete(t.review_decisions).where(t.review_decisions.c.run_id == run_id))
        session.execute(
            delete(t.story_scenes).where(t.story_scenes.c.story_revision_id.in_(revisions))
        )
        session.execute(delete(t.story_revisions).where(t.story_revisions.c.run_id == run_id))
        session.execute(
            delete(t.understanding_revisions).where(t.understanding_revisions.c.run_id == run_id)
        )
        # T-2c: the transcript text is deleted with the run (BR-23); rows go before run_inputs.
        session.execute(
            delete(t.transcript_revisions).where(t.transcript_revisions.c.run_id == run_id)
        )
        session.execute(delete(t.run_inputs).where(t.run_inputs.c.run_id == run_id))

    @staticmethod
    def _scope_ref(session: Session, run_id: str) -> str:
        value = session.scalar(select(_RUNS.c.actor_scope_ref).where(_RUNS.c.run_id == run_id))
        if not isinstance(value, str) or not value:
            raise StoryLifecycleError("RUN_SCOPE_INVALID")
        return value


def _organization_column(scope_kind: str, scope_ref: str) -> str | None:
    """NULL for a Parent row; the organization (= the scope ref) for an ``ORGANIZATION`` row."""

    return scope_ref if scope_kind == ORGANIZATION_SCOPE_KIND else None


def reconciliation_event_statement(
    *,
    run_id: str,
    scope_ref: str,
    revision: int,
    now: datetime,
    scope_kind: str = PARENT_SCOPE_KIND,
) -> Any:
    """DTR §6.4 insert-if-absent of the cancel event; RETURNING yields the id only if inserted."""

    request_id = lifecycle_request_id(run_id)
    return (
        pg_insert(_OUTBOX)
        .values(
            event_id=lifecycle_event_id(request_id, CANCEL_EVENT_TYPE),
            event_type=CANCEL_EVENT_TYPE,
            organization_id=_organization_column(scope_kind, scope_ref),
            owner_scope_kind=scope_kind,
            owner_scope_ref=scope_ref,
            aggregate_id=run_id,
            aggregate_revision=revision,
            payload={
                "run_ref": run_id,
                "lifecycle_request_ref": request_id,
                "actor_ref": scope_ref,
                "reason_code": "PRE_EXISTING_DELETE_PENDING",
            },
            status="pending",
            attempt_count=0,
            available_at=now,
            created_at=now,
        )
        .on_conflict_do_nothing(index_elements=["event_id"])
        .returning(_OUTBOX.c.event_id)
    )


def _s10_present(run: Mapping[str, Any] | RowMapping) -> bool:
    return any(run.get(name) is not None for name in S10_RUN_COLUMNS)


def _upsert_aggregate(
    session: Session, *, run_id: str, scope_kind: str, scope_ref: str, revision: int
) -> None:
    statement = pg_insert(_AGGREGATES).values(
        aggregate_id=run_id,
        organization_id=_organization_column(scope_kind, scope_ref),
        owner_scope_kind=scope_kind,
        owner_scope_ref=scope_ref,
        revision=revision,
        updated_at=datetime.now(UTC),
    )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[_AGGREGATES.c.aggregate_id],
            set_={
                "revision": statement.excluded.revision,
                "updated_at": statement.excluded.updated_at,
            },
            where=and_(
                _AGGREGATES.c.owner_scope_kind == scope_kind,
                _AGGREGATES.c.owner_scope_ref == scope_ref,
            ),
        )
    )


__all__ = [
    "S10_RUN_COLUMNS",
    "SqlStoryLifecycleStore",
    "StoryRunSnapshot",
    "reconciliation_event_statement",
    "story_plan_ids",
    "tombstone_fingerprint",
]
