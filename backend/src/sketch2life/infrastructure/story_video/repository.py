"""PostgreSQL adapter of the Parent video request saga (FEAT-066 T-1a; SRS l.395, l.1670).

One class, three kinds of unit of work, none of them across a port call (BR-38 l.282):

* **Tx1** ``begin_intent``: lock the run, answer a replay, check the request, then insert the
  ``ADMISSION_PENDING`` intent, the receipt and the run move to ``VIDEO_ADMISSION_PENDING``.
* **Tx2** ``finish_admission``: ``FOR UPDATE`` on the run and the generation, compare-and-set on
  ``ADMISSION_PENDING``, then ``ACCEPTED`` (number, refs, job ref, scenes, run ``VIDEO_QUEUED``) or
  ``ADMISSION_REJECTED`` (run back to ``SCRIPT_REVIEW`` with a new adult-wait start). A run that was
  cancelled in between is never moved: an admitted unit ends ``FAILED`` with ``RUN_CANCELLED``.
* **progress** ``advance`` and ``fail_for_cancelled_run``: one generation step and its run step by
  compare-and-set; a result for a run no longer in the expected state is a recorded no-op.

Lock order is always run, then generation. Every statement is scoped to one run; no content, key or
provider text is logged and no storage key leaves this module through a record.

T-4b3b: the same repository serves the Teacher of a Teacher run.
``SqlStoryVideoRepository(session)`` is the Parent repository exactly as before; with an
``actor`` (a Teacher) and the Teacher access port the run is found by the occurrence-pin rule on
the CURRENT assignment (a run without an occurrence pin is the uniform 404), the receipts take the
command scope (``ORGANIZATION`` plus the digest of the calling principal) and a read-only class
(suspended or archived) refuses a new write AFTER the replay lookup. The generation itself
replays by ``(run, key hash)``, not by actor.

V4-A OPEN-A D8 (SRS l.386, l.2690-2699): with an optional ``plan_read`` port the repository fences a
Teacher run whose pinned plan is no longer the approved plan, with read-only checks and no write to
Lesson: ``begin_intent`` answers 409 ``STALE_REVISION`` (``current_version`` is the approved plan
revision number) and ``advance`` turns a worker-start step of a not-yet-started generation into
``FAILED`` (``PLAN_SUPERSEDED``) before anything is dispatched. A generation that is already running
finishes with its old pin (deviation DEV-4: its cancellation is not built).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, insert, null, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.approved_plan_read import ApprovedPlanReadPort
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_actor import (
    TEACHER_COMMAND_SCOPE_KIND,
    RunActor,
    TeacherRunAccess,
    TeacherRunAccessPort,
)
from sketch2life.application.ports.story_run_lifecycle import (
    PURGE_STATES,
    lifecycle_projection_body,
)
from sketch2life.application.ports.story_video import (
    AdmissionDecision,
    GenerationRecord,
    IntentResult,
    PlaybackResolution,
    PlaybackStatus,
    PlaybackTarget,
    ProgressEvent,
    ProgressResult,
    RunCommandResult,
    SampleFacts,
    port_fingerprint,
)
from sketch2life.domain.story_video.model import (
    ADMISSION_REFUSALS,
    COMPLETED_RUN_STATE,
    IN_FLIGHT_STATES,
    MAX_ACCEPTED_REQUESTS,
    OPEN_STATES,
    RUN_CANCELLED,
    RUN_JOB_STATE_FOR_GENERATION,
    RUN_STATE_FOR_GENERATION,
    VIDEO_READY_RUN_STATE,
    GenerationState,
    ValidationState,
    generation_kind_for,
    is_playable,
    require_transition,
)
from sketch2life.infrastructure.persistence.parent_models import ParentChildProfileModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref

OPERATION = "CREATE_VIDEO_GENERATION"
UNSUITABLE_OPERATION = "MARK_VIDEO_UNSUITABLE"
COMPLETE_OPERATION = "COMPLETE_RUN"
_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
# a Name, not a literal: ``ORGANIZATION`` stays a bare value of ``ScopeKind`` (T-1a scope test)
_TEACHER_SCOPE_KIND = TEACHER_COMMAND_SCOPE_KIND
_PURGE_STATE_VALUES = tuple(sorted(PURGE_STATES))
_VG = story_tables.video_generations
_VGS = story_tables.video_generation_scenes
_RUNS = story_tables.story_runs
_RECEIPTS = story_tables.story_command_receipts
_STORE_UNAVAILABLE = "PARENT_STORY_RUN_STORE_UNAVAILABLE"
# The stored safe code of a generation fenced by a plan re-approval; the client sees
# ``VIDEO_TECHNICAL_FAILURE`` (``public_failure_code``).
PLAN_SUPERSEDED = "PLAN_SUPERSEDED"
_WORKER_START_STATES = frozenset({GenerationState.ACCEPTED, GenerationState.QUEUED})
_WORKER_START_TARGETS = frozenset({GenerationState.QUEUED, GenerationState.GENERATING})
_CONFLICT_CONSTRAINTS = frozenset(
    {"uq_vg_one_open", "uq_vg_review_consumed", "uq_vg_number", "uq_vg_one_ready"}
)

_RECORD_QUERY = select(
    _VG,
    _RUNS.c.actor_scope_kind.label("owner_scope_kind"),
    _RUNS.c.actor_scope_ref.label("owner_scope_ref"),
    _RUNS.c.run_state.label("current_run_state"),
    _RUNS.c.revision.label("current_run_revision"),
).join(_RUNS, _RUNS.c.run_id == _VG.c.story_run_id)


def idempotency_key_hash(value: str) -> str:
    """SHA-256 of the stripped key; an empty or over-long key is 400 ``INVALID_IDEMPOTENCY_KEY``."""

    normalized = value.strip()
    if not normalized or len(normalized) > 256:
        raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def request_fingerprint(
    run_id: str, expected_revision: int, story_sha256: str, quality_reason_code: str | None
) -> str:
    """Fingerprint of the exact request body (replay equality, SRS l.1697)."""

    canonical = json.dumps(
        {
            "run_id": run_id,
            "expected_revision": expected_revision,
            "story_sha256": story_sha256,
            "quality_reason_code": quality_reason_code,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _command_fingerprint(**fields: Any) -> str:
    """Fingerprint of the exact body of a one-step run command (replay equality, SRS l.1697)."""

    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _to_record(row: Mapping[Any, Any]) -> GenerationRecord:
    return GenerationRecord(
        generation_id=str(row["video_generation_id"]),
        run_id=str(row["story_run_id"]),
        scope_kind=str(row["owner_scope_kind"]),
        scope_ref=str(row["owner_scope_ref"]),
        state=str(row["state"]),
        kind=str(row["generation_kind"]),
        generation_no=None if row["generation_no"] is None else int(row["generation_no"]),
        job_ref=None if row["job_ref"] is None else str(row["job_ref"]),
        key_hash=str(row["request_idempotency_key_hash"]),
        fingerprint=str(row["request_fingerprint_sha256"]),
        script_hash=str(row["target_script_hash"]),
        story_revision_id=str(row["story_revision_id"]),
        review_id=str(row["story_review_id"]),
        quality_reason_code=row["quality_reason_code"],
        compute_reservation_ref=row["compute_reservation_ref"],
        compute_released_at=row["compute_released_at"],
        billing_quota_usage_ref=row["billing_quota_usage_ref"],
        safe_failure_code=row["safe_failure_code"],
        started=row["started_at"] is not None,
        generation_revision=int(row["generation_revision"]),
        run_state=str(row["current_run_state"]),
        run_revision=int(row["current_run_revision"]),
    )


def _live_run(run_id: str) -> Any:
    return (_RUNS.c.run_id == run_id) & _RUNS.c.run_state.not_in(_PURGE_STATE_VALUES)


class SqlStoryVideoRepository:
    def __init__(
        self,
        session: Session,
        actor: RunActor | None = None,
        teacher_access: TeacherRunAccessPort | None = None,
        plan_read: ApprovedPlanReadPort | None = None,
    ) -> None:
        self._session = session
        self._actor = actor
        self._teacher_access = teacher_access
        self._plan_read = plan_read

    @property
    def _is_teacher(self) -> bool:
        return self._actor is not None and self._actor.is_teacher

    def _superseded_plan_no(self, run: Mapping[Any, Any]) -> int | None:
        """The approved plan revision number when this Teacher run is pinned to another plan
        (V4-A OPEN-A D8), else ``None``. No port, a Parent run, a run without an occurrence pin, a
        pin without a plan revision id and an occurrence without an approved plan are all "not
        superseded" (no fence)."""

        reader = self._plan_read
        if (
            reader is None
            or run["actor_scope_kind"] != _TEACHER_SCOPE_KIND
            or run["occurrence_ref"] is None
        ):
            return None
        inputs = story_tables.run_inputs
        pin = self._session.scalar(
            select(inputs.c.lesson_pin_snapshot).where(
                inputs.c.run_id == run["run_id"],
                inputs.c.input_revision == run["current_input_revision"],
            )
        )
        pinned = pin.get("plan_revision_id") if isinstance(pin, dict) else None
        if not isinstance(pinned, str) or not pinned:
            return None
        approved = reader.approved_plan(str(run["occurrence_ref"]))
        if approved is None or approved.plan_revision_id == pinned:
            return None
        return approved.revision_no

    def _command_scope(self, principal: VerifiedPrincipal) -> tuple[str, str]:
        """Kind and reference of a receipt: who gave the command (the Parent's own scope, or
        ``ORGANIZATION`` plus the digest of the calling Teacher), never the run's owner pair."""

        kind = self._actor.command_scope_kind if self._actor is not None else _OWNER_SCOPE_KIND
        return kind, parent_scope_ref(principal)

    # ---------------------------------------------------------------------- unit of work
    @contextmanager
    def _unit(self) -> Iterator[None]:
        """Commit on success; roll back and map a database failure to the Story error."""

        try:
            yield
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except IntegrityError as exc:
            self._session.rollback()
            name = _constraint_name(exc)
            if name in _CONFLICT_CONSTRAINTS:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None
            if name == "uq_vg_run_key":
                raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY") from None
            raise ParentStoryRunError(503, _STORE_UNAVAILABLE) from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, _STORE_UNAVAILABLE) from None
        except Exception:
            self._session.rollback()
            raise

    # ---------------------------------------------------------------------- Tx1
    def begin_intent(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        story_sha256: str,
        quality_reason_code: str | None,
        idempotency_key: str,
        adapters_available: bool,
    ) -> IntentResult:
        command_kind, scope_ref = self._command_scope(principal)
        key_hash = idempotency_key_hash(idempotency_key)
        fingerprint = request_fingerprint(
            run_id, expected_revision, story_sha256, quality_reason_code
        )
        result: IntentResult | None = None
        with self._unit():
            # 404 first: a foreign actor learns nothing
            run, access = self._owned_run(principal, run_id)
            if run["run_state"] in PURGE_STATES:
                result = self._purged_replay(command_kind, scope_ref, run, key_hash)
            else:
                existing = self._by_key(run_id, key_hash)
                if existing is not None:
                    if not hmac.compare_digest(
                        str(existing["request_fingerprint_sha256"]), fingerprint
                    ):
                        raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
                    result = IntentResult(_to_record(existing), True)
                else:
                    # a suspended or archived class is read-only: after the replay (l.1697)
                    self._refuse_read_only_class(access)
                    result = self._insert_intent(
                        run=run,
                        command_kind=command_kind,
                        scope_ref=scope_ref,
                        key_hash=key_hash,
                        fingerprint=fingerprint,
                        expected_revision=expected_revision,
                        story_sha256=story_sha256,
                        quality_reason_code=quality_reason_code,
                        adapters_available=adapters_available,
                    )
        assert result is not None
        return result

    def _owned_run(
        self, principal: VerifiedPrincipal, run_id: str
    ) -> tuple[RowMapping, TeacherRunAccess | None]:
        """The run row under the run lock and, for a Teacher, what the current assignment granted.

        Parent: the run of the caller's own scope. Teacher: a PINNED ``ORGANIZATION`` run, found
        by the occurrence-pin rule on the CURRENT assignment (the assignment and class rows are
        held ``FOR SHARE``, after the run row: the T-4a1 lock order); a run without an occurrence
        pin, an unassigned Teacher and an unknown id are the same 404.
        """

        if self._is_teacher:
            return self._teacher_run(principal, run_id)
        row = (
            self._session.execute(
                select(_RUNS)
                .where(
                    _RUNS.c.run_id == run_id,
                    _RUNS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                    _RUNS.c.actor_scope_ref == parent_scope_ref(principal),
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        return row, None

    def _teacher_run(
        self, principal: VerifiedPrincipal, run_id: str
    ) -> tuple[RowMapping, TeacherRunAccess]:
        row = (
            self._session.execute(
                select(_RUNS)
                .where(
                    _RUNS.c.run_id == run_id,
                    _RUNS.c.actor_scope_kind == _TEACHER_SCOPE_KIND,
                    _RUNS.c.occurrence_ref.is_not(None),
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None or self._teacher_access is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        access = self._teacher_access.resolve(
            principal=principal,
            organization_id=str(row["actor_scope_ref"]),
            child_id=None if row["profile_ref"] is None else str(row["profile_ref"]),
            lock=True,
            occurrence_ref=None if row["occurrence_ref"] is None else str(row["occurrence_ref"]),
        )
        if access is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        return row, access

    @staticmethod
    def _refuse_read_only_class(access: TeacherRunAccess | None) -> None:
        """A Teacher write in a suspended or archived class is 409 (SRS l.364, l.593, l.1425),
        asked AFTER the replay lookup so an earlier success is still replayed (SRS l.1697)."""

        if access is not None and not access.writable:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def _purged_replay(
        self, command_kind: str, scope_ref: str, run: RowMapping, key_hash: str
    ) -> IntentResult:
        """A replay on a run in the purge states is the content-free projection (DTR §6.5)."""

        receipt = self._session.scalar(
            select(_RECEIPTS.c.receipt_id).where(
                _RECEIPTS.c.actor_scope_kind == command_kind,
                _RECEIPTS.c.actor_scope_ref == scope_ref,
                _RECEIPTS.c.operation == OPERATION,
                _RECEIPTS.c.idempotency_scope_kind == "STORY_RUN",
                _RECEIPTS.c.idempotency_scope_ref == str(run["run_id"]),
                _RECEIPTS.c.idempotency_key_sha256 == key_hash,
            )
        )
        if receipt is None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        projection = ParentStoryLifecycleRecord.from_body(
            lifecycle_projection_body(
                run_id=str(run["run_id"]),
                run_state=str(run["run_state"]),
                revision=int(run["revision"]),
                version=int(run["version"]),
            )
        )
        return IntentResult(None, True, projection)

    def _by_key(self, run_id: str, key_hash: str) -> RowMapping | None:
        return (
            self._session.execute(
                _RECORD_QUERY.where(
                    _VG.c.story_run_id == run_id, _VG.c.request_idempotency_key_hash == key_hash
                )
            )
            .mappings()
            .one_or_none()
        )

    def _insert_intent(
        self,
        *,
        run: RowMapping,
        command_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
        expected_revision: int,
        story_sha256: str,
        quality_reason_code: str | None,
        adapters_available: bool,
    ) -> IntentResult:
        run_id = str(run["run_id"])
        if run["run_state"] != "SCRIPT_REVIEW":
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        revision = (
            self._session.execute(
                select(story_tables.story_revisions)
                .where(story_tables.story_revisions.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        if revision is None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        current_revision = int(run["revision"])
        if current_revision != expected_revision or not hmac.compare_digest(
            str(revision["story_sha256"] or ""), story_sha256
        ):
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=current_revision)
        if revision["status"] != "CONFIRMED":
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        # V4-A T-1b-fix D4: a confirmation may be repeated after a spent request, so the request
        # consumes the review with the highest epoch of the latest revision.
        review_id = self._session.scalar(
            select(story_tables.story_revision_reviews.c.review_id)
            .where(
                story_tables.story_revision_reviews.c.run_id == run_id,
                story_tables.story_revision_reviews.c.story_revision_id
                == revision["story_revision_id"],
            )
            .order_by(story_tables.story_revision_reviews.c.review_epoch.desc())
            .limit(1)
        )
        if review_id is None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        consumed = self._session.scalar(
            select(func.count())
            .select_from(_VG)
            .where(_VG.c.story_review_id == review_id, _VG.c.state != "ADMISSION_REJECTED")
        )
        if consumed:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        self._require_confirmed_inputs(run, revision)
        superseded_by = self._superseded_plan_no(run)
        if superseded_by is not None:
            # D8(1): the run was pinned to a plan that has since been replaced; the number is the
            # approved plan revision, not a run revision.
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=superseded_by)
        accepted = int(
            self._session.scalar(
                select(func.count())
                .select_from(_VG)
                .where(_VG.c.story_run_id == run_id, _VG.c.generation_no.is_not(None))
            )
            or 0
        )
        if accepted >= MAX_ACCEPTED_REQUESTS:
            raise ParentStoryRunError(409, "VIDEO_REGENERATION_LIMIT_REACHED")
        if accepted == 0 and quality_reason_code is not None:
            raise _field_error("quality_reason_code", "NOT_ALLOWED")
        if accepted > 0 and quality_reason_code is None:
            raise _field_error("quality_reason_code", "REQUIRED")
        if not adapters_available:
            # After every 404/409/400 above: a foreign actor never sees 503 first (review F-10).
            raise ParentStoryRunError(503, "PROVIDER_UNAVAILABLE")

        now = datetime.now(UTC)
        generation_id = str(uuid4())
        new_revision = current_revision + 1
        new_version = int(run["version"]) + 1
        self._session.execute(
            insert(_VG).values(
                video_generation_id=generation_id,
                story_run_id=run_id,
                story_revision_id=revision["story_revision_id"],
                story_review_id=review_id,
                generation_no=None,
                generation_kind=str(generation_kind_for(accepted)),
                state=str(GenerationState.ADMISSION_PENDING),
                request_idempotency_key_hash=key_hash,
                request_fingerprint_sha256=fingerprint,
                target_script_hash=story_sha256,
                quality_reason_code=quality_reason_code,
                admission_started_at=now,
                generation_revision=1,
                created_at=now,
                updated_at=now,
            )
        )
        self._session.execute(
            insert(_RECEIPTS).values(
                receipt_id=str(uuid4()),
                actor_scope_kind=command_kind,
                actor_scope_ref=scope_ref,
                operation=OPERATION,
                idempotency_scope_kind="STORY_RUN",
                idempotency_scope_ref=run_id,
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="PENDING",
                response_status=None,
                response_resource_version=None,
                # SQL NULL, not JSON null: the receipt shape check requires IS NULL.
                response_body=null(),
                resource_ref=run_id,
                resource_version=new_version,
                state_version=1,
                created_at=now,
                finalized_at=None,
            )
        )
        changed = self._session.execute(
            update(_RUNS)
            .where(_live_run(run_id), _RUNS.c.revision == current_revision)
            .values(
                run_state="VIDEO_ADMISSION_PENDING",
                adult_wait_started_at=None,
                last_meaningful_activity_at=now,
                current_video_generation_id=generation_id,
                revision=new_revision,
                version=new_version,
                updated_at=now,
            )
        )
        if changed.rowcount != 1:  # type: ignore[attr-defined]
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        stored = self._record_row(generation_id)
        return IntentResult(_to_record(stored), False)

    def _record_row(self, generation_id: str) -> RowMapping:
        return (
            self._session.execute(_RECORD_QUERY.where(_VG.c.video_generation_id == generation_id))
            .mappings()
            .one()
        )

    def _require_confirmed_inputs(self, run: RowMapping, revision: RowMapping) -> None:
        """Defensive 422 (D6): the context and the subject were confirmed before this script."""

        run_id = str(run["run_id"])
        current = run["current_input_revision"]
        context_confirmed = False
        if current is not None:
            confirmed_at = self._session.scalar(
                select(story_tables.run_inputs.c.context_confirmed_at).where(
                    story_tables.run_inputs.c.run_id == run_id,
                    story_tables.run_inputs.c.input_revision == current,
                )
            )
            context_confirmed = confirmed_at is not None
        if not context_confirmed:
            raise ParentStoryRunError(422, "PROFILE_CONTEXT_NOT_CONFIRMED")
        decisions = story_tables.review_decisions
        subject = self._session.scalar(
            select(func.count())
            .select_from(decisions)
            .where(
                decisions.c.run_id == run_id,
                decisions.c.stage == "SUBJECT",
                decisions.c.decision == "CONFIRM",
                decisions.c.target_understanding_revision == revision["understanding_revision"],
            )
        )
        if not subject:
            raise ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED")

    # ---------------------------------------------------------------------- reads
    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        with self._unit():
            row = (
                self._session.execute(
                    _RECORD_QUERY.where(_VG.c.video_generation_id == generation_id)
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else _to_record(row)

    def pending_intents(self, limit: int, run_id: str | None = None) -> list[GenerationRecord]:
        predicate = _VG.c.state == str(GenerationState.ADMISSION_PENDING)
        if run_id is not None:
            predicate = predicate & (_VG.c.story_run_id == run_id)
        return self._list(predicate, limit)

    def pending_compute_closures(self, limit: int) -> list[GenerationRecord]:
        return self._list(
            _VG.c.state.not_in([str(state) for state in OPEN_STATES])
            & _VG.c.compute_reservation_ref.is_not(None)
            & _VG.c.compute_released_at.is_(None),
            limit,
        )

    def open_generations(self, run_id: str) -> list[GenerationRecord]:
        return self._list(
            (_VG.c.story_run_id == run_id) & _VG.c.state.in_([str(state) for state in OPEN_STATES]),
            100,
        )

    def runnable_generations(self, limit: int) -> list[GenerationRecord]:
        """Accepted work the video worker may advance, oldest first (FEAT-093)."""

        return self._list(
            _VG.c.state.in_(
                [
                    str(GenerationState.ACCEPTED),
                    str(GenerationState.QUEUED),
                    str(GenerationState.GENERATING),
                    str(GenerationState.TECHNICAL_VALIDATING),
                    str(GenerationState.SAFETY_VALIDATING),
                ]
            ),
            limit,
        )

    def orphaned_in_flight(self, limit: int) -> list[GenerationRecord]:
        """In-flight generations of a run already in a purge state (the cancel hook never ran)."""

        return self._list(
            _VG.c.state.in_([str(state) for state in IN_FLIGHT_STATES])
            & _VG.c.story_run_id.in_(
                select(_RUNS.c.run_id).where(_RUNS.c.run_state.in_(_PURGE_STATE_VALUES))
            ),
            limit,
        )

    def _list(self, predicate: Any, limit: int) -> list[GenerationRecord]:
        with self._unit():
            rows = (
                self._session.execute(
                    _RECORD_QUERY.where(predicate).order_by(_VG.c.admission_started_at).limit(limit)
                )
                .mappings()
                .all()
            )
        return [_to_record(row) for row in rows]

    # ---------------------------------------------------------------------- Tx2
    def finish_admission(
        self, generation_id: str, decision: AdmissionDecision
    ) -> GenerationRecord | None:
        with self._unit():
            run_id = self._session.scalar(
                select(_VG.c.story_run_id).where(_VG.c.video_generation_id == generation_id)
            )
            if run_id is None:
                return None
            run = (
                self._session.execute(
                    select(_RUNS).where(_RUNS.c.run_id == run_id).with_for_update()
                )
                .mappings()
                .one()
            )
            gen = (
                self._session.execute(
                    select(_VG).where(_VG.c.video_generation_id == generation_id).with_for_update()
                )
                .mappings()
                .one()
            )
            if gen["state"] == str(GenerationState.ADMISSION_PENDING):  # compare-and-set
                now = datetime.now(UTC)
                cancelled = run["run_state"] in PURGE_STATES
                if decision.accepted:
                    self._accept(run, gen, decision, now, cancelled=cancelled)
                else:
                    self._reject(run, gen, decision, now, cancelled=cancelled)
            row = self._record_row(generation_id)
        return _to_record(row)

    def _accept(
        self,
        run: RowMapping,
        gen: RowMapping,
        decision: AdmissionDecision,
        now: datetime,
        *,
        cancelled: bool,
    ) -> None:
        run_id = str(run["run_id"])
        number = (
            int(
                self._session.scalar(
                    select(func.count())
                    .select_from(_VG)
                    .where(_VG.c.story_run_id == run_id, _VG.c.generation_no.is_not(None))
                )
                or 0
            )
            + 1
        )
        target = GenerationState.FAILED if cancelled else GenerationState.ACCEPTED
        require_transition(GenerationState.ADMISSION_PENDING, target)
        values: dict[str, Any] = {
            "state": str(target),
            "generation_no": number,
            "accepted_at": now,
            "compute_reservation_ref": decision.reservation_ref,
            "billing_quota_usage_ref": decision.usage_ref,
            "job_ref": "vjob_" + uuid4().hex,
            "generation_revision": int(gen["generation_revision"]) + 1,
            "updated_at": now,
        }
        if cancelled:
            # The unit was admitted before the cancel won: it stays consumed (l.596, FR-C-08).
            values.update(completed_at=now, safe_failure_code=RUN_CANCELLED)
        self._session.execute(
            update(_VG)
            .where(_VG.c.video_generation_id == gen["video_generation_id"])
            .values(**values)
        )
        if not cancelled:
            scenes = (
                self._session.execute(
                    select(story_tables.story_scenes.c.scene_id)
                    .where(
                        story_tables.story_scenes.c.story_revision_id == gen["story_revision_id"]
                    )
                    .order_by(story_tables.story_scenes.c.scene_index)
                )
                .scalars()
                .all()
            )
            for scene_id in scenes:
                self._session.execute(
                    insert(_VGS).values(
                        generation_scene_id=str(uuid4()),
                        video_generation_id=gen["video_generation_id"],
                        story_revision_id=gen["story_revision_id"],
                        story_scene_id=scene_id,
                        state="QUEUED",
                        created_at=now,
                    )
                )
            changed = self._session.execute(
                update(_RUNS)
                .where(_live_run(run_id), _RUNS.c.run_state == "VIDEO_ADMISSION_PENDING")
                .values(
                    run_state=RUN_STATE_FOR_GENERATION[GenerationState.ACCEPTED],
                    job_state=RUN_JOB_STATE_FOR_GENERATION[GenerationState.ACCEPTED],
                    error_code=None,
                    retryable=False,
                    revision=int(run["revision"]) + 1,
                    version=int(run["version"]) + 1,
                    updated_at=now,
                )
            )
            if changed.rowcount != 1:  # type: ignore[attr-defined]
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        self._finalize_receipt(
            run,
            gen,
            status=202,
            body={
                "video_generation_id": str(gen["video_generation_id"]),
                "state": str(target),
                "generation_no": number,
            },
            now=now,
        )

    def _reject(
        self,
        run: RowMapping,
        gen: RowMapping,
        decision: AdmissionDecision,
        now: datetime,
        *,
        cancelled: bool,
    ) -> None:
        code = decision.refusal_code or ""
        status = ADMISSION_REFUSALS[code]
        run_id = str(run["run_id"])
        require_transition(GenerationState.ADMISSION_PENDING, GenerationState.ADMISSION_REJECTED)
        self._session.execute(
            update(_VG)
            .where(_VG.c.video_generation_id == gen["video_generation_id"])
            .values(
                state=str(GenerationState.ADMISSION_REJECTED),
                rejected_at=now,
                safe_failure_code=code,
                compute_reservation_ref=decision.reservation_ref,
                generation_revision=int(gen["generation_revision"]) + 1,
                updated_at=now,
            )
        )
        if not cancelled:
            previous = self._session.scalar(
                select(_VG.c.video_generation_id)
                .where(_VG.c.story_run_id == run_id, _VG.c.generation_no.is_not(None))
                .order_by(_VG.c.generation_no.desc())
                .limit(1)
            )
            changed = self._session.execute(
                update(_RUNS)
                .where(_live_run(run_id), _RUNS.c.run_state == "VIDEO_ADMISSION_PENDING")
                .values(
                    run_state=RUN_STATE_FOR_GENERATION[GenerationState.ADMISSION_REJECTED],
                    adult_wait_started_at=now,
                    current_video_generation_id=previous,
                    revision=int(run["revision"]) + 1,
                    version=int(run["version"]) + 1,
                    updated_at=now,
                )
            )
            if changed.rowcount != 1:  # type: ignore[attr-defined]
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        self._finalize_receipt(run, gen, status=status, body={"code": code}, now=now)

    def _finalize_receipt(
        self,
        run: RowMapping,
        gen: RowMapping,
        *,
        status: int,
        body: dict[str, Any],
        now: datetime,
    ) -> None:
        # The PENDING receipt carries the COMMAND scope of whoever asked: for a Parent run that is
        # the run's own owner pair, for a Teacher run it is ``ORGANIZATION`` plus the digest of the
        # calling Teacher, which is NOT the organization id the run row holds (T-4b3a, T-4b2 hand
        # over F7). The receipt is therefore found by the run's command KIND, the operation, the
        # run and the key hash; the request key is unique per run (``uq_vg_run_key``), so this is
        # the same single row for a Parent as before.
        self._session.execute(
            update(_RECEIPTS)
            .where(
                _RECEIPTS.c.actor_scope_kind == run["actor_scope_kind"],
                _RECEIPTS.c.operation == OPERATION,
                _RECEIPTS.c.idempotency_scope_kind == "STORY_RUN",
                _RECEIPTS.c.idempotency_scope_ref == str(run["run_id"]),
                _RECEIPTS.c.idempotency_key_sha256 == gen["request_idempotency_key_hash"],
                _RECEIPTS.c.state == "PENDING",
            )
            .values(
                state="FINAL",
                response_status=status,
                response_body=body,
                response_resource_version=int(run["version"]) + 1,
                resource_version=int(run["version"]) + 1,
                state_version=_RECEIPTS.c.state_version + 1,
                finalized_at=now,
            )
        )

    def mark_compute_closed(self, generation_id: str) -> None:
        with self._unit():
            self._session.execute(
                update(_VG)
                .where(
                    _VG.c.video_generation_id == generation_id, _VG.c.compute_released_at.is_(None)
                )
                .values(compute_released_at=datetime.now(UTC))
            )

    # ---------------------------------------------------------------------- adult commands (T-1b)
    def mark_unsuitable(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        generation_id: str,
        reason_code: str,
        idempotency_key: str,
    ) -> RunCommandResult:
        """``video-unsuitable`` (SRS l.1671): the ready video is rejected, the run reviews again.

        One transaction under the run lock: owner-scoped lookup (404), replay, run state, run
        revision, current ``READY`` generation (409 ``STALE_REVISION``), then the cap (409
        ``VIDEO_REGENERATION_LIMIT_REACHED``: nothing changes and the video stays). The effect is
        the generation ``REJECTED_BY_ADULT`` and the run ``SCRIPT_REVIEW`` with a new wait; the
        compute reservation was settled at ``READY``, so no port is called.
        """

        command_kind, scope_ref = self._command_scope(principal)
        key_hash = idempotency_key_hash(idempotency_key)
        fingerprint = _command_fingerprint(
            run_id=run_id,
            expected_revision=expected_revision,
            generation_id=generation_id,
            reason_code=reason_code,
        )
        result: RunCommandResult | None = None
        with self._unit():
            run, access = self._owned_run(principal, run_id)
            result = self._command_replay(
                command_kind, scope_ref, run, UNSUITABLE_OPERATION, key_hash, fingerprint
            )
            if result is None:
                self._refuse_read_only_class(access)  # after the replay (SRS l.1697)
                current_revision = self._require_video_ready(run, expected_revision)
                generation = self._current_ready_generation(run, generation_id)
                accepted = self._accepted_count(run_id)
                if accepted >= MAX_ACCEPTED_REQUESTS:
                    raise ParentStoryRunError(409, "VIDEO_REGENERATION_LIMIT_REACHED")
                now = datetime.now(UTC)
                require_transition(GenerationState.READY, GenerationState.REJECTED_BY_ADULT)
                self._session.execute(
                    update(_VG)
                    .where(
                        _VG.c.video_generation_id == generation_id,
                        _VG.c.state == str(GenerationState.READY),
                    )
                    .values(
                        state=str(GenerationState.REJECTED_BY_ADULT),
                        rejection_reason_code=reason_code,
                        generation_revision=int(generation["generation_revision"]) + 1,
                        updated_at=now,
                    )
                )
                self._move_run(
                    run,
                    current_revision,
                    now,
                    run_state=RUN_STATE_FOR_GENERATION[GenerationState.REJECTED_BY_ADULT],
                    adult_wait_started_at=now,
                )
                self._finalize_command(
                    run,
                    command_kind,
                    scope_ref,
                    UNSUITABLE_OPERATION,
                    key_hash,
                    fingerprint,
                    body={
                        "decision": "VIDEO_UNSUITABLE",
                        "generation_id": generation_id,
                        "run_state": "SCRIPT_REVIEW",
                    },
                    now=now,
                )
                result = RunCommandResult(run_id, False)
        assert result is not None
        return result

    def complete_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> RunCommandResult:
        """``complete`` (SRS l.1672): ``VIDEO_READY`` to ``COMPLETED``, the active lock released.

        The generation stays ``READY`` (the run is not a video approval) and the content stays
        until the user deletes the run (FR-C-08).
        """

        command_kind, scope_ref = self._command_scope(principal)
        key_hash = idempotency_key_hash(idempotency_key)
        fingerprint = _command_fingerprint(run_id=run_id, expected_revision=expected_revision)
        result: RunCommandResult | None = None
        with self._unit():
            run, access = self._owned_run(principal, run_id)
            result = self._command_replay(
                command_kind, scope_ref, run, COMPLETE_OPERATION, key_hash, fingerprint
            )
            if result is None:
                self._refuse_read_only_class(access)  # after the replay (SRS l.1697)
                current_revision = self._require_video_ready(run, expected_revision)
                now = datetime.now(UTC)
                self._move_run(
                    run,
                    current_revision,
                    now,
                    run_state="COMPLETED",
                    adult_wait_started_at=None,
                    active_owner_parent_account_id=None,
                    finished_at=now,
                )
                self._finalize_command(
                    run,
                    command_kind,
                    scope_ref,
                    COMPLETE_OPERATION,
                    key_hash,
                    fingerprint,
                    body={"decision": "RUN_COMPLETED", "run_state": "COMPLETED"},
                    now=now,
                )
                result = RunCommandResult(run_id, False)
        assert result is not None
        return result

    def _command_replay(
        self,
        command_kind: str,
        scope_ref: str,
        run: RowMapping,
        operation: str,
        key_hash: str,
        fingerprint: str,
    ) -> RunCommandResult | None:
        """The same key again: the current run (the family's replay), or the purge projection."""

        run_id = str(run["run_id"])
        receipt = self._session.execute(
            select(_RECEIPTS.c.request_fingerprint_sha256).where(
                _RECEIPTS.c.actor_scope_kind == command_kind,
                _RECEIPTS.c.actor_scope_ref == scope_ref,
                _RECEIPTS.c.operation == operation,
                _RECEIPTS.c.idempotency_scope_kind == "STORY_RUN",
                _RECEIPTS.c.idempotency_scope_ref == run_id,
                _RECEIPTS.c.idempotency_key_sha256 == key_hash,
            )
        ).one_or_none()
        if receipt is None:
            return None
        if run["run_state"] in PURGE_STATES:
            # DTR 6.5 (A-3): a purge replaces the fingerprints, so a replay is the projection.
            return RunCommandResult(
                run_id,
                True,
                ParentStoryLifecycleRecord.from_body(
                    lifecycle_projection_body(
                        run_id=run_id,
                        run_state=str(run["run_state"]),
                        revision=int(run["revision"]),
                        version=int(run["version"]),
                    )
                ),
            )
        if not hmac.compare_digest(str(receipt[0]), fingerprint):
            raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
        return RunCommandResult(run_id, True)

    @staticmethod
    def _require_video_ready(run: RowMapping, expected_revision: int) -> int:
        """State first (T-1a order), then the revision; returns the current revision."""

        if run["run_state"] != VIDEO_READY_RUN_STATE:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        current_revision = int(run["revision"])
        if current_revision != expected_revision:
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=current_revision)
        return current_revision

    def _current_ready_generation(self, run: RowMapping, generation_id: str) -> RowMapping:
        """The generation the adult saw: the run's current one, still ``READY`` (else stale)."""

        current = run["current_video_generation_id"]
        stale = ParentStoryRunError(409, "STALE_REVISION", current_version=int(run["revision"]))
        if current is None or str(current) != generation_id:
            raise stale
        generation = (
            self._session.execute(
                select(_VG)
                .where(
                    _VG.c.video_generation_id == generation_id,
                    _VG.c.story_run_id == str(run["run_id"]),
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if generation is None or generation["state"] != str(GenerationState.READY):
            raise stale
        return generation

    def _accepted_count(self, run_id: str) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(_VG)
                .where(_VG.c.story_run_id == run_id, _VG.c.generation_no.is_not(None))
            )
            or 0
        )

    def _move_run(
        self, run: RowMapping, current_revision: int, now: datetime, **values: Any
    ) -> None:
        run_id = str(run["run_id"])
        changed = self._session.execute(
            update(_RUNS)
            .where(
                _live_run(run_id),
                _RUNS.c.revision == current_revision,
                _RUNS.c.run_state == VIDEO_READY_RUN_STATE,
            )
            .values(
                last_meaningful_activity_at=now,
                revision=current_revision + 1,
                version=int(run["version"]) + 1,
                updated_at=now,
                **values,
            )
        )
        if changed.rowcount != 1:  # type: ignore[attr-defined]
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def _finalize_command(
        self,
        run: RowMapping,
        command_kind: str,
        scope_ref: str,
        operation: str,
        key_hash: str,
        fingerprint: str,
        *,
        body: dict[str, Any],
        now: datetime,
    ) -> None:
        """The receipt of a one-step command: final in the same transaction (no pending phase)."""

        new_version = int(run["version"]) + 1
        self._session.execute(
            insert(_RECEIPTS).values(
                receipt_id=str(uuid4()),
                actor_scope_kind=command_kind,
                actor_scope_ref=scope_ref,
                operation=operation,
                idempotency_scope_kind="STORY_RUN",
                idempotency_scope_ref=str(run["run_id"]),
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="FINAL",
                response_status=200,
                response_resource_version=new_version,
                response_body=body,
                resource_ref=str(run["run_id"]),
                resource_version=new_version,
                state_version=1,
                created_at=now,
                finalized_at=now,
            )
        )

    # ---------------------------------------------------------------------- playback (T-1c)
    def resolve_playback(
        self, *, principal: VerifiedPrincipal, run_id: str, generation_id: str | None
    ) -> PlaybackResolution:
        """Owner-scoped, read-only: is the run at ``VIDEO_READY`` or ``COMPLETED`` (V4-A T-1c-fix)
        with its current generation ``READY``, every validation ``PASSED`` and an output (SRS
        l.1676, T-1b hand-over)?

        Run state and generation state are read together in one statement, never the pointer
        alone: after ``video-unsuitable`` the pointer stays on the ``REJECTED_BY_ADULT`` row.
        ``generation_id`` (the token's) must be the current one, else the answer is
        ``NOT_PLAYABLE``. The physical key stays in the returned target and goes nowhere else.

        For a Teacher (T-4b3b D10) the run is a PINNED ``ORGANIZATION`` run and the CURRENT
        occurrence-pin rule must grant the caller (read-only, no lock: a suspended or archived
        class still plays the video, SRS l.364, l.593, l.1425); the target is bound to the digest of
        the calling principal, so the token names one Teacher, not the organization.

        V4-A T-1c-fix: Complete and the idle closeout no longer end playback (owner decisions O-3
        and C1(a)), so every caller passes ``allow_completed``; what still ends it for a Parent is
        a cancel, a delete, a rejected or failed generation and the deletion of the child profile
        (``_parent_profile_revoked``). A Teacher projection confirmed before Complete ends at
        Complete in the Lesson check, not here.
        """

        scope_ref = parent_scope_ref(principal)
        teacher = self._is_teacher
        columns: list[Any] = [
            _RUNS.c.run_state,
            _RUNS.c.current_video_generation_id,
            _VG.c.video_generation_id,
            _VG.c.state.label("generation_state"),
            _VG.c.output_asset_ref,
            _VG.c.technical_validation_state,
            _VG.c.consistency_validation_state,
            _VG.c.safety_validation_state,
        ]
        owner: tuple[Any, ...] = (
            _RUNS.c.actor_scope_kind == _OWNER_SCOPE_KIND,
            _RUNS.c.actor_scope_ref == scope_ref,
        )
        if teacher:
            columns += [_RUNS.c.actor_scope_ref, _RUNS.c.profile_ref, _RUNS.c.occurrence_ref]
            owner = (
                _RUNS.c.actor_scope_kind == _TEACHER_SCOPE_KIND,
                _RUNS.c.occurrence_ref.is_not(None),
            )
        try:
            row = (
                self._session.execute(
                    select(*columns)
                    .select_from(
                        _RUNS.outerjoin(
                            _VG, _VG.c.video_generation_id == _RUNS.c.current_video_generation_id
                        )
                    )
                    .where(_RUNS.c.run_id == run_id, *owner)
                )
                .mappings()
                .one_or_none()
            )
            if row is not None and teacher and not self._teacher_may_read(principal, row):
                row = None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, _STORE_UNAVAILABLE) from None
        if row is None or row["run_state"] in PURGE_STATES:
            return PlaybackResolution(PlaybackStatus.NOT_FOUND)
        if not teacher and self._parent_profile_revoked(run_id):
            return PlaybackResolution(PlaybackStatus.NOT_FOUND)
        current = row["video_generation_id"]
        if not is_playable(
            run_state=str(row["run_state"]),
            generation_state=row["generation_state"],
            technical=row["technical_validation_state"],
            consistency=row["consistency_validation_state"],
            safety=row["safety_validation_state"],
            has_output=row["output_asset_ref"] is not None,
            allow_completed=True,
        ) or (generation_id is not None and str(current) != generation_id):
            return PlaybackResolution(PlaybackStatus.NOT_PLAYABLE)
        return PlaybackResolution(
            PlaybackStatus.PLAYABLE,
            PlaybackTarget(run_id, str(current), scope_ref, str(row["output_asset_ref"])),
        )

    def _parent_profile_revoked(self, run_id: str) -> bool:
        """V4-A T-1c-fix D5 (SRS l.502, l.1736): deleting a child profile ends playback of its runs
        at once, now that Complete no longer does. Two primary-key reads after the owner row was
        found: the run's profile reference, then the profile state. A profile row that is not
        ``ACTIVE`` (or has ``deleted_at``) revokes; no reference, an unparsable one and no profile
        row do not (the check revokes only what profile deletion flipped). Fail-open on a missing
        row: nothing hard-deletes ``parent.child_profiles`` today and ``story_runs.profile_ref``
        has no foreign key, so a future profile purge that removes the row but not the runs must
        also end the runs (note for that task)."""

        try:
            reference = (
                self._session.execute(select(_RUNS.c.profile_ref).where(_RUNS.c.run_id == run_id))
                .mappings()
                .one_or_none()
            )
            raw = None if reference is None else reference["profile_ref"]
            if not isinstance(raw, str):
                return False
            try:
                profile_id = UUID(raw)
            except ValueError:
                return False
            profile = (
                self._session.execute(
                    select(ParentChildProfileModel.state, ParentChildProfileModel.deleted_at).where(
                        ParentChildProfileModel.parent_profile_id == profile_id
                    )
                )
                .mappings()
                .one_or_none()
            )
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, _STORE_UNAVAILABLE) from None
        return profile is not None and (
            profile["state"] != "ACTIVE" or profile["deleted_at"] is not None
        )

    def _teacher_may_read(self, principal: VerifiedPrincipal, run: Mapping[Any, Any]) -> bool:
        """The occurrence-pin rule on the CURRENT assignment, without a lock (a read)."""

        if self._teacher_access is None:
            return False
        access = self._teacher_access.resolve(
            principal=principal,
            organization_id=str(run["actor_scope_ref"]),
            child_id=None if run["profile_ref"] is None else str(run["profile_ref"]),
            lock=False,
            occurrence_ref=None if run["occurrence_ref"] is None else str(run["occurrence_ref"]),
        )
        return access is not None

    # ---------------------------------------------------------------------- progress
    def advance(self, generation_id: str, event: ProgressEvent) -> ProgressResult:
        expected = GenerationState(event.expected_state)
        target = GenerationState(event.target_state)
        require_transition(expected, target)
        if target is GenerationState.READY and (
            event.output_asset_ref is None or event.output_asset_version is None
        ):
            raise ValueError("a READY generation needs its output asset")
        if target is GenerationState.FAILED and not event.safe_failure_code:
            raise ValueError("a FAILED generation needs a safe failure code")
        with self._unit():
            run_id = self._session.scalar(
                select(_VG.c.story_run_id).where(_VG.c.video_generation_id == generation_id)
            )
            if run_id is None:
                return ProgressResult(False, None, "NOT_FOUND")
            run = (
                self._session.execute(
                    select(_RUNS).where(_RUNS.c.run_id == run_id).with_for_update()
                )
                .mappings()
                .one()
            )
            gen = (
                self._session.execute(
                    select(_VG).where(_VG.c.video_generation_id == generation_id).with_for_update()
                )
                .mappings()
                .one()
            )
            if (
                run["run_state"] in PURGE_STATES
                or gen["state"] != str(expected)
                or run["run_state"] != RUN_STATE_FOR_GENERATION[expected]
            ):
                stale = _to_record(self._record_row(generation_id))
                return ProgressResult(False, stale, "STALE")
            if (
                expected in _WORKER_START_STATES
                and target in _WORKER_START_TARGETS
                and self._superseded_plan_no(run) is not None
            ):
                # D8(2): before anything is dispatched, a generation of a superseded plan ends
                # FAILED (the accepted quota receipt is kept, no refund).
                target = GenerationState.FAILED
                event = ProgressEvent(
                    expected_state=str(expected),
                    target_state=str(target),
                    safe_failure_code=PLAN_SUPERSEDED,
                )
            now = datetime.now(UTC)
            self._apply(run, gen, expected, target, event, now)
            record = _to_record(self._record_row(generation_id))
        return ProgressResult(True, record)

    def _apply(
        self,
        run: RowMapping,
        gen: RowMapping,
        expected: GenerationState,
        target: GenerationState,
        event: ProgressEvent,
        now: datetime,
    ) -> None:
        run_id = str(run["run_id"])
        generation_id = gen["video_generation_id"]
        values: dict[str, Any] = {
            "state": str(target),
            "generation_revision": int(gen["generation_revision"]) + 1,
            "updated_at": now,
        }
        for column, value in (
            ("video_profile_ref", event.video_profile_ref),
            ("model_revision", event.model_revision),
            ("config_hash", event.config_hash),
            ("safety_policy_version", event.safety_policy_version),
        ):
            if value is not None:
                values[column] = value
        scene_state: str | None = None
        run_values: dict[str, Any] = {}
        new_run_state = RUN_STATE_FOR_GENERATION[target]
        if target is GenerationState.GENERATING:
            values["started_at"] = now
            scene_state = "GENERATING"
        elif target is GenerationState.TECHNICAL_VALIDATING:
            scene_state = "READY"
        elif target is GenerationState.SAFETY_VALIDATING:
            values["technical_validation_state"] = str(ValidationState.PASSED)
            values["consistency_validation_state"] = str(ValidationState.PASSED)
        elif target is GenerationState.READY:
            values.update(
                safety_validation_state=str(ValidationState.PASSED),
                output_asset_ref=event.output_asset_ref,
                output_asset_version=event.output_asset_version,
                completed_at=now,
            )
            run_values["adult_wait_started_at"] = now
        elif target is GenerationState.SAFETY_BLOCKED:
            # V4-A SAFETY_BLOCKED exit (owner decision C11, SRS l.420, l.2197): the run goes back
            # to the script review (``RUN_STATE_FOR_GENERATION``) with a new adult wait and keeps
            # its owner lock. The blocked request still counts toward the cap, at the cap too (the
            # SRS text, D3); the branch does not read ``return_to_script_review`` (only the
            # deadline sets it). A block event without a code stores the default one, so the
            # public reason is ``VIDEO_SAFETY_BLOCKED`` and never a technical failure.
            block_code = event.safe_failure_code or "SAFETY_BLOCKED"
            values.update(
                safety_validation_state=str(ValidationState.FAILED),
                safety_finding_codes=list(event.safety_finding_codes),
                completed_at=now,
                safe_failure_code=block_code,
            )
            run_values.update(adult_wait_started_at=now, error_code=block_code)
        elif target is GenerationState.FAILED:
            values.update(completed_at=now, safe_failure_code=event.safe_failure_code)
            if expected is GenerationState.TECHNICAL_VALIDATING:
                values["technical_validation_state"] = str(ValidationState.FAILED)
            scene_state = "FAILED"
            if (
                event.return_to_script_review
                and self._accepted_count(run_id) < MAX_ACCEPTED_REQUESTS
            ):
                # The failed request still counts toward the cap (BR-11, l.2120); the run waits
                # for the adult at the script review with a new clock and keeps its owner lock.
                # The way forward is to keep the current story and confirm it again (V4-A
                # T-1b-fix: a new review epoch, so it never needs a free rewrite slot) or a
                # rewrite within the limit; with the cap spent the run ends ``FAILED`` and frees
                # the lock.
                new_run_state = RUN_STATE_FOR_GENERATION[GenerationState.ADMISSION_REJECTED]
                run_values.update(
                    adult_wait_started_at=now,
                    error_code=event.safe_failure_code,
                )
            else:
                run_values.update(
                    active_owner_parent_account_id=None,
                    adult_wait_started_at=None,
                    finished_at=now,
                    error_code=event.safe_failure_code,
                )
        self._session.execute(
            update(_VG).where(_VG.c.video_generation_id == generation_id).values(**values)
        )
        if scene_state is not None:
            scene_values: dict[str, Any] = {"state": scene_state}
            if scene_state == "GENERATING":
                scene_values["started_at"] = now
            else:
                scene_values["completed_at"] = now
            if scene_state == "FAILED":
                scene_values["safe_failure_code"] = event.safe_failure_code
            self._session.execute(
                update(_VGS)
                .where(
                    _VGS.c.video_generation_id == generation_id,
                    _VGS.c.state.in_(["QUEUED", "GENERATING"]),
                )
                .values(**scene_values)
            )
        job_state = RUN_JOB_STATE_FOR_GENERATION.get(target)
        changed = self._session.execute(
            update(_RUNS)
            .where(_live_run(run_id), _RUNS.c.run_state == RUN_STATE_FOR_GENERATION[expected])
            .values(
                run_state=new_run_state,
                **({"job_state": job_state} if job_state is not None else {}),
                retryable=False,
                revision=int(run["revision"]) + 1,
                version=int(run["version"]) + 1,
                updated_at=now,
                **run_values,
            )
        )
        if changed.rowcount != 1:  # type: ignore[attr-defined]
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def fail_for_cancelled_run(self, generation_id: str) -> ProgressResult:
        """An in-flight generation of a cancelled run ends ``FAILED`` (``RUN_CANCELLED``)."""

        with self._unit():
            run_id = self._session.scalar(
                select(_VG.c.story_run_id).where(_VG.c.video_generation_id == generation_id)
            )
            if run_id is None:
                return ProgressResult(False, None, "NOT_FOUND")
            run = (
                self._session.execute(
                    select(_RUNS).where(_RUNS.c.run_id == run_id).with_for_update()
                )
                .mappings()
                .one()
            )
            gen = (
                self._session.execute(
                    select(_VG).where(_VG.c.video_generation_id == generation_id).with_for_update()
                )
                .mappings()
                .one()
            )
            state = GenerationState(gen["state"])
            if run["run_state"] not in PURGE_STATES or state not in IN_FLIGHT_STATES:
                stale = _to_record(self._record_row(generation_id))
                return ProgressResult(False, stale, "STALE")
            now = datetime.now(UTC)
            require_transition(state, GenerationState.FAILED)
            self._session.execute(
                update(_VG)
                .where(_VG.c.video_generation_id == generation_id)
                .values(
                    state=str(GenerationState.FAILED),
                    completed_at=now,
                    safe_failure_code=RUN_CANCELLED,
                    generation_revision=int(gen["generation_revision"]) + 1,
                    updated_at=now,
                )
            )
            self._session.execute(
                update(_VGS)
                .where(
                    _VGS.c.video_generation_id == generation_id,
                    _VGS.c.state.in_(["QUEUED", "GENERATING"]),
                )
                .values(state="FAILED", completed_at=now, safe_failure_code=RUN_CANCELLED)
            )
            record = _to_record(self._record_row(generation_id))
        return ProgressResult(True, record)


def sample_facts(session: Session, run_id: str, *, lock: bool) -> SampleFacts | None:
    """What the class projection (T-5a) needs about one run: the ONE Story read of Lesson code.

    One statement: the run, its current generation and the plan pin of the CURRENT input revision
    (T-4b2 D3 copies the pin forward into every revision). ``lock`` takes the run row ``FOR SHARE``
    (a concurrent cancel, ``video-unsuitable`` or complete takes it ``FOR UPDATE`` and waits or
    loses); it is the last lock of the confirmation, after the occurrence and the class. A run that
    does not exist or is being deleted is ``None``. ``playable`` is the single ``is_playable``
    predicate with ``allow_completed`` (V4-A T-1c-fix, owner decision C1(a)): a ``COMPLETED`` run
    that still holds its READY output is playable, and ``completed_at`` (the run's ``finished_at``)
    is what the Lesson check compares with the confirmation time, so a confirmation given before
    Complete ends at Complete. Nothing is written and no storage key leaves the function.
    """

    inputs = story_tables.run_inputs
    statement = (
        select(
            _RUNS.c.run_id,
            _RUNS.c.occurrence_ref,
            _RUNS.c.run_state,
            _RUNS.c.finished_at.label("run_finished_at"),
            _VG.c.video_generation_id,
            _VG.c.state.label("generation_state"),
            _VG.c.output_asset_ref,
            _VG.c.technical_validation_state,
            _VG.c.consistency_validation_state,
            _VG.c.safety_validation_state,
            _VG.c.completed_at,
            _VG.c.updated_at,
            inputs.c.lesson_pin_snapshot,
        )
        .select_from(
            _RUNS.outerjoin(
                _VG, _VG.c.video_generation_id == _RUNS.c.current_video_generation_id
            ).outerjoin(
                inputs,
                (inputs.c.run_id == _RUNS.c.run_id)
                & (inputs.c.input_revision == _RUNS.c.current_input_revision),
            )
        )
        .where(_RUNS.c.run_id == run_id)
    )
    if lock:
        statement = statement.with_for_update(read=True, of=_RUNS)
    row = session.execute(statement).mappings().one_or_none()
    if row is None or row["run_state"] in PURGE_STATES:
        return None
    pin = row["lesson_pin_snapshot"] if isinstance(row["lesson_pin_snapshot"], dict) else {}
    pin_no = pin.get("plan_revision_no")
    pin_id, pin_hash = pin.get("plan_revision_id"), pin.get("plan_hash")
    generation_state = row["generation_state"]
    return SampleFacts(
        run_id=str(row["run_id"]),
        occurrence_ref=None if row["occurrence_ref"] is None else str(row["occurrence_ref"]),
        run_state=str(row["run_state"]),
        generation_id=(
            None if row["video_generation_id"] is None else str(row["video_generation_id"])
        ),
        ready_at=(row["completed_at"] if row["completed_at"] is not None else row["updated_at"]),
        completed_at=(
            row["run_finished_at"] if row["run_state"] == COMPLETED_RUN_STATE else None
        ),
        playable=is_playable(
            run_state=str(row["run_state"]),
            generation_state=None if generation_state is None else str(generation_state),
            technical=row["technical_validation_state"],
            consistency=row["consistency_validation_state"],
            safety=row["safety_validation_state"],
            has_output=row["output_asset_ref"] is not None,
            allow_completed=True,
        ),
        plan_revision_id=pin_id if isinstance(pin_id, str) else None,
        plan_revision_no=pin_no if type(pin_no) is int else None,
        plan_hash=pin_hash if isinstance(pin_hash, str) else None,
    )


def _field_error(field: str, code: str) -> ParentStoryRunError:
    return ParentStoryRunError(
        400, "INVALID_REQUEST", field_errors=[{"field": field, "code": code}]
    )


def _constraint_name(exc: IntegrityError) -> str | None:
    original = getattr(exc, "orig", None)
    diagnostic = getattr(original, "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None


__all__ = [
    "COMPLETE_OPERATION",
    "OPERATION",
    "UNSUITABLE_OPERATION",
    "SqlStoryVideoRepository",
    "idempotency_key_hash",
    "port_fingerprint",
    "request_fingerprint",
    "sample_facts",
]
