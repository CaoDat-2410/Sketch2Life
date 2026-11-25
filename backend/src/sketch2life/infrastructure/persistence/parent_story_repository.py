"""PostgreSQL adapter for Parent StoryRuns, immutable context, artwork, and reviews."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from io import BytesIO
from typing import Any, cast
from uuid import UUID, uuid4, uuid5

from sqlalchemy import Table, and_, delete, func, insert, null, or_, select, text, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.parent_subject_roles import (
    SubjectRoleError,
    apply_subject_roles,
    approved_subjects,
    present_candidate,
    relabel_main_subject,
)
from sketch2life.contracts.schemas.modal_ai import PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import scanner_identity_sha256
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import (
    MAX_TRANSCRIPT_TEXT,
    DrawingAttachOutcome,
    IdeaOutcome,
    SpeechTranscriptionRequest,
    SubjectConfirmOutcome,
    TranscriptConfirmOutcome,
    TranscriptView,
    VoiceInput,
)
from sketch2life.application.ports.parent_story_profile_lookup import ParentStoryProfileReference
from sketch2life.application.ports.parent_story_runs import (
    ActivityResolver,
    ParentActivityContext,
    ParentActivitySuggestionReservation,
    ParentStoryInputRecord,
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
    ParentStoryRunSummary,
    ParentStoryRunView,
    StoryRewriteOutcome,
    StoryStartedCallback,
    TeacherStoryRunRecord,
)
from sketch2life.application.ports.story_run_actor import (
    TEACHER_COMMAND_SCOPE_KIND,
    RunActor,
    RunAssetOwner,
    TeacherRunAccess,
    TeacherRunAccessPort,
)
from sketch2life.application.ports.story_run_lifecycle import (
    AUDIT_CANCEL_ACCEPTED,
    AUDIT_DELETE_ACCEPTED,
    AUDIT_RESOURCE_TYPE,
    CANCEL_ELIGIBLE_STATES,
    CANCEL_EVENT_TYPE,
    DELETE_ELIGIBLE_STATES,
    DELETE_EVENT_TYPE,
    LIFECYCLE_NS,
    PURGE_STATES,
    is_projection_body,
    lifecycle_audit_id,
    lifecycle_event_id,
    lifecycle_projection_body,
    lifecycle_request_id,
)
from sketch2life.application.ports.story_task_reaper import (
    AUDIT_REWRITE_ATTEMPT_FAILED,
    REWRITE_ATTEMPTS_PER_SLOT,
)
from sketch2life.application.ports.story_video import RunVideoRows
from sketch2life.application.services.story_review_rules import (
    MAX_REVIEW_EPOCH,
    next_review_epoch,
    review_is_spent,
    revision_has_spent_video,
    story_confirmation_required,
)
from sketch2life.application.services.story_run_detail import compose_timeline, compose_video
from sketch2life.application.story_staging import pack_story_content, unpack_sections
from sketch2life.domain.story_teacher import TEACHER_PIN_SCHEMA, teacher_lesson_direction
from sketch2life.domain.story_video.model import (
    MAX_ACCEPTED_REQUESTS,
    REVIEWABLE_RUN_STATES,
    public_failure_code,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.persistence.story_first_start import (
    FirstStoryStarter,
    latest_selection_row,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.detail_read import read_run_video

_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
_PARENT_CONTEXT_SCHEMA = "sketch2life.parent-context.v1"
_PARENT_CONTEXT_MAX_BYTES = 32_768
_PURGE_STATE_VALUES = tuple(sorted(PURGE_STATES))
_AGGREGATES = cast(Table, CoreAggregateRevisionModel.__table__)
_OUTBOX = cast(Table, CoreOutboxEventModel.__table__)
_AUDIT = cast(Table, CoreAuditEntryModel.__table__)
_ASSET_METADATA = cast(Table, CoreAssetMetadataModel.__table__)
_ATTACH_ASSET_OPERATION = "ATTACH_ASSET"
# T-2b: columns of ``story.run_inputs`` that a new drawing revision sets itself; every other
# column is copied from the current input, so a column added later (T-2c voice fields) is carried
# forward instead of silently dropped (R1 B10, T-2c C1).
_DRAWING_INPUT_COLUMNS = frozenset(
    {
        "run_input_id",
        "input_revision",
        "original_asset_ref",
        "original_asset_version",
        "original_sha256",
        "original_media_type",
        "original_size_bytes",
        "derived_asset_ref",
        "derived_asset_version",
        "derived_sha256",
        "derived_media_type",
        "derived_size_bytes",
        "created_at",
    }
)
# A retake is allowed once: the first drawing plus at most one replacement (FR-P-12, l.521).
_MAX_DRAWING_INPUTS = 2
_RETAKE_STATES = frozenset({"SUBJECT_REVIEW", "INPUT_REVIEW"})
# T-2c: the run states in which the adult may still change the input (idea, audio, transcript).
_INPUT_STATES = frozenset({"INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW"})
# T-2d: ``job_state`` values of a drawing analysis that has not reported yet.
_VLM_IN_FLIGHT = frozenset({"QUEUED", "RUNNING", "AWAITING_RECONCILIATION"})
_SUBJECT_DECISIONS = frozenset({"CONFIRMED", "RERUN_REQUESTED"})
# T-2e-a (SRS l.514, l.871): the states in which the subject is not confirmed yet (422) and the one
# state in which the adult chooses the main activity.
_ACTIVITY_PRE_SUBJECT_STATES = frozenset({"INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW"})
_SELECT_ACTIVITY_OPERATION = "SELECT_ACTIVITY"
_POST_VIDEO_STATES = frozenset({"VIDEO_READY", "COMPLETED"})
_ACTIVITY_ITEM_FIELDS = (
    "title",
    "objective",
    "materials_text",
    "preparation_text",
    "instructions_text",
    "observation_notes",
    "safety_notes",
    "activity_kind",
)
_SUBMIT_IDEA_OPERATION = "SUBMIT_IDEA"
_CONFIRM_TRANSCRIPT_OPERATION = "CONFIRM_TRANSCRIPT"


def _live_run(run_id: str) -> Any:
    """DTR Draft 6 §7: every Parent Story writer updates only a run outside the purge states."""

    return and_(
        story_tables.story_runs.c.run_id == run_id,
        story_tables.story_runs.c.run_state.not_in(_PURGE_STATE_VALUES),
    )


def _projection(run: Mapping[str, Any]) -> ParentStoryLifecycleRecord:
    return ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(
            run_id=str(run["run_id"]),
            run_state=str(run["run_state"]),
            revision=int(run["revision"]),
            version=int(run["version"]),
        )
    )


def _lifecycle_reason_code(is_cancel: bool, *, teacher: bool) -> str:
    """The reason code of the outbox payload: who asked for the cancel or the delete."""

    prefix = "TEACHER" if teacher else "PARENT"
    return f"{prefix}_CANCEL_REQUESTED" if is_cancel else f"{prefix}_DELETE_REQUESTED"


def story_task_audit_id(run_id: str, action: str, run_revision: int) -> str:
    """Deterministic audit id of one recovery or reaper action on one run revision (T-2d-fix D4)."""

    return str(uuid5(LIFECYCLE_NS, f"story_task:{run_id}:{action}:{run_revision}"))


def write_story_task_audit(
    session: Session,
    *,
    owner_scope_ref: str,
    actor_ref: str,
    action: str,
    run_id: str,
    decision: str,
    run_revision: int,
    now: datetime,
    owner_scope_kind: str = _OWNER_SCOPE_KIND,
    organization_id: str | None = None,
) -> None:
    """One metadata audit row: actor, action, resource and the safe code (BR-34, l.278).

    Never a story, hint, transcript or error text. The write is idempotent per run revision.
    The defaults give every Parent call the row it always wrote; a Teacher run passes kind
    ``ORGANIZATION`` and its organization id (the scope ref equals it, T-4b3a D13, T-13a H7).
    """

    session.execute(
        pg_insert(_AUDIT)
        .values(
            audit_id=story_task_audit_id(run_id, action, run_revision),
            organization_id=organization_id,
            owner_scope_kind=owner_scope_kind,
            owner_scope_ref=owner_scope_ref,
            actor_ref=actor_ref,
            action=action,
            resource_type=AUDIT_RESOURCE_TYPE,
            resource_id=run_id,
            decision=decision[:64],
            created_at=now,
        )
        .on_conflict_do_nothing(index_elements=["audit_id"])
    )


def story_task_audit_scope(run: Mapping[Any, Any]) -> dict[str, Any]:
    """The audit scope arguments of one run row (T-4b3a D13): the Parent owner scope as ever, or
    for a Teacher run ``ORGANIZATION`` with the organization id as both ``organization_id`` and
    scope ref (the ``OWNER_SCOPE_CHECK`` accepts exactly that)."""

    ref = str(run["actor_scope_ref"])
    if run.get("actor_scope_kind") == TEACHER_COMMAND_SCOPE_KIND:
        return {
            "owner_scope_kind": TEACHER_COMMAND_SCOPE_KIND,
            "owner_scope_ref": ref,
            "organization_id": ref,
        }
    return {"owner_scope_ref": ref}


class SqlParentStoryRunRepository:
    """With no ``actor`` every method is the Parent repository of before T-4a1 (T-4a1-DEC-5).

    With a Teacher ``actor`` only the methods that pass ``teacher_capable=True`` to
    ``_owned_run`` can find a run, and they find it only after ``teacher_access`` confirms the
    CURRENT assignment; every other method answers the uniform 404 for a Teacher. The T-4b3a
    input steps additionally pass ``pinned=True``: a run without an occurrence pin (a T-4a1/T-13a
    fixture row) stays the uniform 404 there.

    ``job_side=True`` (T-4b3a D6) is the repository of a background task of a Teacher run: it
    finds a run by id, ``ORGANIZATION`` kind, an occurrence pin and the organization id the route
    saw, with no live assignment check (FR-T-14, l.553: a valid AI job is not cancelled because an
    assignment changed). Only the methods that pass ``job_side_ok=True`` accept it; every other
    method under ``job_side`` is the uniform 404.
    """

    def __init__(
        self,
        session: Session,
        *,
        actor: RunActor | None = None,
        teacher_access: TeacherRunAccessPort | None = None,
        job_side: bool = False,
        job_side_organization: str | None = None,
    ) -> None:
        self._session = session
        self._actor = actor
        self._teacher_access = teacher_access
        self._job_side = job_side
        self._job_side_organization = job_side_organization

    @property
    def _is_teacher(self) -> bool:
        return self._actor is not None and self._actor.is_teacher

    def _command_scope(self, principal: VerifiedPrincipal) -> tuple[str, str]:
        """Kind and reference of a receipt or a review decision: who gave the command."""

        kind = self._actor.command_scope_kind if self._actor is not None else _OWNER_SCOPE_KIND
        return kind, _principal_scope_ref(principal)

    def _refuse_teacher(self) -> None:
        """A Parent-only method called for a Teacher actor: the uniform 404."""

        if self._is_teacher:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    def create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        profile: ParentStoryProfileReference,
        idempotency_key: str,
        run_id: str,
        topic: str,
        adult_confirmed_idea: str,
        intended_drawing_subject: str | None = None,
        lesson_version_ref: dict[str, str] | None = None,
        lesson_pin_snapshot: dict[str, Any] | None = None,
    ) -> ParentStoryRunView:
        self._refuse_teacher()
        owner_scope_ref = _principal_scope_ref(principal)
        scope_kind = "COLLECTION"
        scope_ref = account_id
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _create_run_fingerprint(
            parent_profile_id=profile.profile_id,
            topic=topic,
            adult_confirmed_idea=adult_confirmed_idea,
            lesson_version_ref=lesson_version_ref,
            intended_drawing_subject=intended_drawing_subject,
        )
        self._lock_idempotency(
            principal=principal,
            operation="CREATE_RUN",
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation="CREATE_RUN",
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            replay_run_id = str(replay["resource_ref"])
            self._session.commit()
            return self.get_run(principal=principal, run_id=replay_run_id)

        existing_run = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                story_tables.story_runs.c.actor_scope_ref == owner_scope_ref,
                story_tables.story_runs.c.active_owner_parent_account_id == account_id,
            )
        )
        if existing_run is not None:
            raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS")

        now = datetime.now(UTC)
        context = {
            "schema_version": _PARENT_CONTEXT_SCHEMA,
            "profile_revision_ref": str(profile.profile_revision_id),
            "age_months": profile.age_months,
            "interests_summary": profile.interests_summary or "",
            "topic": topic,
            "adult_confirmed_idea": adult_confirmed_idea,
        }
        if intended_drawing_subject is not None:
            context["intended_drawing_subject"] = intended_drawing_subject
        context_hash = _sha256_json(context)
        if len(_canonical_json(context).encode("utf-8")) > _PARENT_CONTEXT_MAX_BYTES:
            raise ParentStoryRunError(422, "INVALID_REQUEST")
        lesson_pin = dict(lesson_pin_snapshot) if lesson_pin_snapshot is not None else None
        lesson_pin_hash = _sha256_json(lesson_pin) if lesson_pin is not None else None
        run_input_id = str(uuid4())
        try:
            self._session.execute(
                insert(story_tables.story_runs).values(
                    run_id=run_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_scope_ref,
                    profile_ref=str(profile.profile_id),
                    child_age_months=profile.age_months,
                    run_state="INPUT_PROCESSING",
                    revision=1,
                    version=1,
                    retryable=False,
                    active_owner_parent_account_id=account_id,
                    current_input_revision=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._session.execute(
                insert(story_tables.run_inputs).values(
                    run_input_id=run_input_id,
                    run_id=run_id,
                    input_revision=1,
                    typed_idea=adult_confirmed_idea or None,
                    idea_source="TEXT" if adult_confirmed_idea else None,
                    source_profile_revision_ref=str(profile.profile_revision_id),
                    context_revision=1,
                    context_snapshot=context,
                    context_snapshot_sha256=context_hash,
                    # An explicit None on a JSONB column is bound as JSON null, which the
                    # lesson-pin check refuses; SQL NULL is required.
                    lesson_pin_snapshot=lesson_pin if lesson_pin is not None else null(),
                    lesson_pin_snapshot_sha256=lesson_pin_hash,
                    context_confirmed_by=None,
                    context_confirmed_at=None,
                    created_at=now,
                )
            )
            self._store_idempotency_receipt(
                principal=principal,
                operation="CREATE_RUN",
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=1,
                response_body={"run_id": run_id},
                now=now,
                response_status=201,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if _integrity_constraint_name(exc) == "uq_story_run_active_parent":
                raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS") from None
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            principal=principal,
            run_id=run_id,
        )

    def replay_create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        parent_profile_id: UUID,
        idempotency_key: str,
        topic: str,
        adult_confirmed_idea: str,
        intended_drawing_subject: str | None = None,
        lesson_version_ref: dict[str, str] | None = None,
    ) -> ParentStoryRunView | None:
        self._refuse_teacher()
        scope_kind = "COLLECTION"
        scope_ref = account_id
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _create_run_fingerprint(
            parent_profile_id=parent_profile_id,
            topic=topic,
            adult_confirmed_idea=adult_confirmed_idea,
            lesson_version_ref=lesson_version_ref,
            intended_drawing_subject=intended_drawing_subject,
        )
        try:
            self._lock_idempotency(
                principal=principal,
                operation="CREATE_RUN",
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
            )
            replay = self._find_idempotency_receipt(
                principal=principal,
                operation="CREATE_RUN",
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
                fingerprint=fingerprint,
            )
            if replay is None:
                return None
            replay_run_id = str(replay["resource_ref"])
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(principal=principal, run_id=replay_run_id)

    def get_run(self, *, principal: VerifiedPrincipal, run_id: str) -> ParentStoryRunView:
        return self._read_run_view(principal, run_id, job_side_ok=False)

    def _read_run_view(
        self, principal: VerifiedPrincipal, run_id: str, *, job_side_ok: bool
    ) -> ParentStoryRunView:
        run = self._owned_run(principal, run_id, teacher_capable=True, job_side_ok=job_side_ok)
        if run["run_state"] in PURGE_STATES:
            # DTR Draft 6 §6.5: the projection is returned before any input or profile access.
            return _projection(run)
        if run["profile_ref"] is None:
            # Only the DELETED tombstone may hold a NULL profile ref (D-218 A-4).
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
        input_row = self._current_input(run)
        latest_story = (
            self._session.execute(
                select(story_tables.story_revisions)
                .where(story_tables.story_revisions.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        latest_understanding = self._latest_understanding(run_id)
        candidate = None
        # T-2b: after a retake the earlier understanding belongs to the replaced drawing; it stays
        # as history and is not the candidate of the current input.
        # The key is the drawing, not the input row (T2B-R-2): a later input revision without a
        # drawing change (a text-only idea, T-2c) copies the drawing forward and keeps it.
        if latest_understanding is not None and self._same_drawing(
            latest_understanding["run_input_id"], input_row
        ):
            snapshot = latest_understanding["result_snapshot"]
            result = snapshot.get("result") if isinstance(snapshot, dict) else None
            candidate = dict(result) if isinstance(result, dict) else None
            # The VLM result is immutable. Adult confirmation is stored separately in
            # review_decisions, so project that persisted decision into the client read model
            # instead of leaving the original REVIEW_REQUIRED state visible after confirmation.
            if candidate is not None and run["understanding_revision"] is not None:
                command_scope_kind, command_scope_ref = self._command_scope(principal)
                subject_decision_id = self._session.execute(
                    select(story_tables.review_decisions.c.decision_id)
                    .where(
                        story_tables.review_decisions.c.run_id == run_id,
                        story_tables.review_decisions.c.stage == "SUBJECT",
                        story_tables.review_decisions.c.decision == "CONFIRM",
                        story_tables.review_decisions.c.target_understanding_revision
                        == int(run["understanding_revision"]),
                        story_tables.review_decisions.c.actor_scope_kind == command_scope_kind,
                        story_tables.review_decisions.c.actor_scope_ref == command_scope_ref,
                    )
                    .limit(1)
                ).scalar_one_or_none()
                if subject_decision_id is not None:
                    candidate = _project_confirmed_candidate(candidate, run["subject_label"])
        story_content = None
        if latest_story is not None and latest_story["story_content"] is not None:
            sections = unpack_sections(latest_story["story_content"])
            scenes = (
                self._session.execute(
                    select(story_tables.story_scenes)
                    .where(
                        story_tables.story_scenes.c.story_revision_id
                        == latest_story["story_revision_id"]
                    )
                    .order_by(story_tables.story_scenes.c.scene_index)
                )
                .mappings()
                .all()
            )
            story_content = {
                "schema_version": latest_story["schema_version"],
                "language": latest_story["language"],
                "title": latest_story["title"],
                "story": sections,
                "duration_ms": latest_story["duration_ms"],
                "scenes": [
                    {
                        "scene_index": scene["scene_index"],
                        "title": scene["title"],
                        "action": scene["action"],
                        "narration": scene["narration"],
                        "start_ms": scene["start_ms"],
                        "duration_ms": scene["duration_ms"],
                    }
                    for scene in scenes
                ],
            }
        # T-1c: one bounded Story-owned read (the accepted rows and the pending intent, at most
        # four, and the scenes of the current one); nothing at all while no request exists.
        video_rows = read_run_video(
            self._session, run_id, _text_or_none(run.get("current_video_generation_id"))
        )
        shared: dict[str, Any] = dict(
            run_id=run_id,
            run_state=str(run["run_state"]),
            run_revision=int(run["revision"]),
            context_revision=int(input_row["context_revision"]),
            context_confirmed=(
                input_row["context_confirmed_by"] is not None
                and input_row["context_confirmed_at"] is not None
            ),
            context_snapshot=dict(input_row["context_snapshot"]),
            context_snapshot_sha256=str(input_row["context_snapshot_sha256"]),
            lesson_pin_snapshot=(
                dict(input_row["lesson_pin_snapshot"])
                if input_row["lesson_pin_snapshot"] is not None
                else None
            ),
            current_input_revision=(
                int(run["current_input_revision"])
                if run["current_input_revision"] is not None
                else None
            ),
            understanding_revision=(
                int(run["understanding_revision"])
                if run["understanding_revision"] is not None
                else None
            ),
            subject_label=run["subject_label"],
            candidate=present_candidate(candidate) if candidate is not None else None,
            story_revision_id=(
                str(latest_story["story_revision_id"]) if latest_story is not None else None
            ),
            story_revision_no=(
                int(latest_story["revision_no"]) if latest_story is not None else None
            ),
            story_status=str(latest_story["status"]) if latest_story is not None else None,
            story_sha256=latest_story["story_sha256"] if latest_story is not None else None,
            story_content=story_content,
            story_confirmation_required=self._story_confirmation_required(run, latest_story),
            job_state=run["job_state"],
            retryable=bool(run["retryable"]),
            error_code=_public_run_error_code(run["error_code"], video_rows),
            created_at=run["created_at"],
            updated_at=run["updated_at"],
            video=compose_video(run_id, str(run["run_state"]), video_rows, allow_completed=True),
            timeline=compose_timeline(
                run_state=str(run["run_state"]),
                run_created_at=run["created_at"],
                run_finished_at=run.get("finished_at"),
                rows=video_rows,
            ),
        )
        if self._is_teacher:
            # T-4b2 D10: the Teacher view never calls UUID() on a Managed Profile id (DEC-7 gone).
            plan, activity = _teacher_pin_view(run, input_row)
            return TeacherStoryRunRecord(
                profile_ref=str(run["profile_ref"]),
                profile_revision_ref=str(input_row["source_profile_revision_ref"]),
                occurrence_id=_text_or_none(run.get("occurrence_ref")),
                plan=plan,
                activity=activity,
                **shared,
            )
        profile_id, profile_revision_ref = self._typed_profile_refs(run, input_row)
        main_activity, post_video_activities = self._activity_view(run, input_row)
        return ParentStoryRunRecord(
            parent_profile_id=profile_id,
            profile_revision_ref=profile_revision_ref,
            main_activity=main_activity,
            post_video_activities=post_video_activities,
            **shared,
        )

    def _activity_view(
        self, run: Mapping[str, Any], input_row: Mapping[Any, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
        """``main_activity`` and ``post_video_activities`` of a Parent run (T-2e-a D11).

        Both come from stored data only (the selection snapshot and the run's lesson pin): no
        catalog or lesson access read here. The route withholds the pinned list when the pinned
        lesson is no longer viewable.
        """

        selection = latest_selection_row(
            self._session, str(run["run_id"]), int(run["understanding_revision"] or 0)
        )
        selected: dict[str, Any] | None = None
        main: dict[str, Any] = {"state": "NOT_SELECTED", "selected": None, "selected_at": None}
        if selection is not None:
            snapshot = dict(selection["activity_snapshot"])
            selected_at = snapshot.pop("selected_at", None)
            snapshot.pop("schema", None)
            selected = snapshot
            main = {"state": "SELECTED", "selected": selected, "selected_at": selected_at}
        if run["run_state"] not in _POST_VIDEO_STATES:
            return main, None
        pin = input_row["lesson_pin_snapshot"]
        if pin is None:
            return main, ([{**selected, "is_main": True}] if selected is not None else None)
        main_ref = selected["activity_ref"] if selected is not None else None
        items: list[dict[str, Any]] = []
        for index, raw in enumerate(pin.get("activities") or []):
            reference = {
                "lesson_id": str(pin["lesson_id"]),
                "version_id": str(pin["version_id"]),
                "content_sha256": str(pin["content_sha256"]),
                "activity_index": index,
            }
            items.append(
                {
                    "activity_ref": reference,
                    **{name: raw.get(name, "") for name in _ACTIVITY_ITEM_FIELDS},
                    "source": "PINNED_LESSON",
                    "lesson_title": str(pin["title"]),
                    "lesson_topic": str(pin["topic"]),
                    "is_main": main_ref == reference,
                }
            )
        return main, items

    def list_runs(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID | None,
        limit: int,
        after: tuple[datetime, str] | None,
    ) -> list[ParentStoryRunSummary]:
        """FEAT-081 C3b: owner-scoped history, newest first, ``limit + 1`` rows, no joins."""
        self._refuse_teacher()
        runs = story_tables.story_runs
        query = select(
            runs.c.run_id,
            runs.c.profile_ref,
            runs.c.run_state,
            runs.c.revision,
            runs.c.created_at,
            runs.c.updated_at,
        ).where(
            runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
            runs.c.actor_scope_ref == _principal_scope_ref(principal),
            runs.c.run_state != "DELETED",
        )
        if profile_id is not None:
            # A purge row loses its profile at purge step 4, so a filter lists live runs only.
            query = query.where(
                runs.c.profile_ref == str(profile_id),
                runs.c.run_state.not_in(_PURGE_STATE_VALUES),
            )
        if after is not None:
            created_at, run_id = after
            query = query.where(
                or_(
                    runs.c.created_at < created_at,
                    and_(runs.c.created_at == created_at, runs.c.run_id < run_id),
                )
            )
        query = query.order_by(runs.c.created_at.desc(), runs.c.run_id.desc()).limit(limit + 1)
        try:
            rows = self._session.execute(query).mappings().all()
        except SQLAlchemyError as exc:
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from exc
        return [_run_summary(row) for row in rows]

    def get_active_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunView | None:
        if self._is_teacher:
            return self._get_active_teacher_run(principal=principal, account_id=account_id)
        run_id = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                story_tables.story_runs.c.actor_scope_ref == _principal_scope_ref(principal),
                story_tables.story_runs.c.active_owner_parent_account_id == account_id,
            )
        )
        if run_id is None:
            return None
        return self.get_run(
            principal=principal,
            run_id=str(run_id),
        )

    def _get_active_teacher_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunView | None:
        """The one active run the Teacher holds (T-4b2 D4/D5), for a resume after a reload.

        The lock column finds the run; the run is shown only while the CURRENT occurrence-pin rule
        still grants it, otherwise the answer is the empty one (nothing about the run leaks).
        """

        run_id = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND,
                story_tables.story_runs.c.active_owner_teacher_id == account_id,
            )
        )
        if run_id is None:
            return None
        try:
            return self.get_run(principal=principal, run_id=str(run_id))
        except ParentStoryRunError as error:
            if error.status_code == 404:
                return None
            raise

    def cancel_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> ParentStoryLifecycleRecord:
        """FR-C-08 cancel (Contract Draft 11 §3.1; DTR Draft 6 §6.1)."""

        return self._accept_lifecycle_command(
            principal=principal,
            run_id=run_id,
            operation="CANCEL_RUN",
            idempotency_key=idempotency_key,
            expected_revision=expected_revision,
        )

    def delete_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
    ) -> ParentStoryLifecycleRecord:
        """FR-C-08 delete of a finished run (Contract Draft 11 §3.2; DTR Draft 6 §6.1)."""

        return self._accept_lifecycle_command(
            principal=principal,
            run_id=run_id,
            operation="DELETE_RUN",
            idempotency_key=idempotency_key,
            expected_revision=None,
        )

    def _accept_lifecycle_command(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        operation: str,
        idempotency_key: str,
        expected_revision: int | None,
    ) -> ParentStoryLifecycleRecord:
        """One Story transaction: lock, replay, class state, revision, state, then five writes.

        Error order (Contract §3.1-§3.2, FEAT-066 T-13a-DEC-2): actor (the router), key, the
        owner-scoped lookup with the current Teacher assignment re-checked under the run lock
        (404), replay, the class state of a Teacher (409 ``INVALID_STATE_TRANSITION``), revision
        (cancel only, 409 ``STALE_REVISION`` with ``current_version``), state (409
        ``INVALID_STATE_TRANSITION``). The writes are the run (``DELETE_PENDING``, lock
        released, revision and version +1), the aggregate row, the outbox event, the accepted
        audit row and the receipt whose body is the projection. The aggregate, outbox and audit
        rows carry the run's own owner scope: ``PARENT_ACCOUNT`` without an organization, or
        ``ORGANIZATION`` with the organization for a Teacher run; the receipt carries the command
        scope of the caller (T-4a1-DEC-5).
        """

        is_cancel = operation == "CANCEL_RUN"
        run, access = self._owned_run_access(principal, run_id, lock=True, teacher_capable=True)
        owner_kind = str(run["actor_scope_kind"])
        owner_ref = str(run["actor_scope_ref"])
        owner_organization = owner_ref if owner_kind == TEACHER_COMMAND_SCOPE_KIND else None
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {"run_id": run_id, "expected_revision": expected_revision}
            if is_cancel
            else {"run_id": run_id}
        )
        principal_scope = _principal_scope_ref(principal)
        command_kind, command_ref = self._command_scope(principal)
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="COLLECTION",
            scope_ref=principal_scope,
            key_hash=key_hash,
        )
        try:
            receipt = (
                self._session.execute(
                    select(story_tables.story_command_receipts).where(
                        story_tables.story_command_receipts.c.actor_scope_kind == command_kind,
                        story_tables.story_command_receipts.c.actor_scope_ref == command_ref,
                        story_tables.story_command_receipts.c.operation == operation,
                        story_tables.story_command_receipts.c.idempotency_key_sha256 == key_hash,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if receipt is not None:
                # SRS line 1697: the fingerprint check stays for cancel and delete replays;
                # their fingerprints are never tombstoned (DTR step 4).
                if (
                    receipt["idempotency_scope_kind"] != "STORY_RUN"
                    or receipt["idempotency_scope_ref"] != run_id
                    or not hmac.compare_digest(
                        str(receipt["request_fingerprint_sha256"]), fingerprint
                    )
                ):
                    raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
                body = receipt["response_body"]
                if (
                    receipt["state"] != "FINAL"
                    or receipt["response_status"] != 202
                    or not isinstance(body, dict)
                ):
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                if is_projection_body(body):
                    replayed = ParentStoryLifecycleRecord.from_body(body)
                elif run["run_state"] in PURGE_STATES:
                    # A pre-existing M2 CANCEL_RUN body still holds run content until step 4
                    # rewrites it; until then the replay returns the current projection.
                    replayed = _projection(run)
                else:
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                self._session.commit()
                return replayed

            if access is not None and not access.writable:
                # SRS l.364, l.593, l.1425: a suspended or archived class is read-only and keeps
                # its data; the Teacher's cleanup is refused (OWNER-VISIBLE Q-1). After the replay,
                # so an earlier success is still replayed (l.1697).
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            current_revision = int(run["revision"])
            if is_cancel:
                if current_revision != expected_revision:
                    raise ParentStoryRunError(
                        409, "STALE_REVISION", current_version=current_revision
                    )
                if run["run_state"] not in CANCEL_ELIGIBLE_STATES:
                    raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            elif run["run_state"] not in DELETE_ELIGIBLE_STATES:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

            now = datetime.now(UTC)
            new_revision = current_revision + 1
            new_version = int(run["version"]) + 1
            changed = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_runs)
                    .where(
                        _live_run(run_id),
                        story_tables.story_runs.c.revision == current_revision,
                    )
                    .values(
                        run_state="DELETE_PENDING",
                        active_owner_parent_account_id=None,
                        revision=new_revision,
                        version=new_version,
                        updated_at=now,
                    )
                ),
            )
            if changed.rowcount != 1:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            request_id = lifecycle_request_id(run_id)
            event_type = CANCEL_EVENT_TYPE if is_cancel else DELETE_EVENT_TYPE
            self._upsert_run_aggregate(
                run_id=run_id,
                scope_kind=owner_kind,
                scope_ref=owner_ref,
                revision=new_revision,
                now=now,
            )
            payload = {
                "run_ref": run_id,
                "lifecycle_request_ref": request_id,
                "actor_ref": principal_scope,
                "reason_code": _lifecycle_reason_code(is_cancel, teacher=self._is_teacher),
            }
            if is_cancel:
                payload["expected_revision"] = str(expected_revision)
            self._session.execute(
                pg_insert(_OUTBOX)
                .values(
                    event_id=lifecycle_event_id(request_id, event_type),
                    event_type=event_type,
                    organization_id=owner_organization,
                    owner_scope_kind=owner_kind,
                    owner_scope_ref=owner_ref,
                    aggregate_id=run_id,
                    aggregate_revision=new_revision,
                    payload=payload,
                    status="pending",
                    attempt_count=0,
                    available_at=now,
                    created_at=now,
                )
                .on_conflict_do_nothing(index_elements=["event_id"])
            )
            action = AUDIT_CANCEL_ACCEPTED if is_cancel else AUDIT_DELETE_ACCEPTED
            self._session.execute(
                pg_insert(_AUDIT)
                .values(
                    audit_id=lifecycle_audit_id(request_id, action),
                    organization_id=owner_organization,
                    owner_scope_kind=owner_kind,
                    owner_scope_ref=owner_ref,
                    actor_ref=principal_scope,
                    action=action,
                    resource_type=AUDIT_RESOURCE_TYPE,
                    resource_id=run_id,
                    decision="accepted:" + request_id,
                    created_at=now,
                )
                .on_conflict_do_nothing(index_elements=["audit_id"])
            )
            body = lifecycle_projection_body(
                run_id=run_id,
                run_state="DELETE_PENDING",
                revision=new_revision,
                version=new_version,
            )
            self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body=body,
                now=now,
                response_status=202,
            )
            self._session.commit()
            return ParentStoryLifecycleRecord.from_body(body)
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def _upsert_run_aggregate(
        self, *, run_id: str, scope_kind: str, scope_ref: str, revision: int, now: datetime
    ) -> None:
        """Aggregate row keyed by ``run_id``; ``revision`` = ``story.runs.revision``.

        The scope is the run's OWNER scope: a Parent run (no organization column) or a Teacher
        run (``ORGANIZATION``, ``organization_id`` = the scope ref).
        """

        statement = pg_insert(_AGGREGATES).values(
            aggregate_id=run_id,
            organization_id=scope_ref if scope_kind == TEACHER_COMMAND_SCOPE_KIND else None,
            owner_scope_kind=scope_kind,
            owner_scope_ref=scope_ref,
            revision=revision,
            updated_at=now,
        )
        self._session.execute(
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

    def ensure_accepting_artwork(self, *, principal: VerifiedPrincipal, run_id: str) -> None:
        """Port design §7: re-check the state immediately before the first ``put_object``."""

        # T-4b3a D2: a Teacher needs a pinned run and an active class (the upload route has no
        # replay, so the class check is part of the lookup).
        run = self._owned_run(principal, run_id, teacher_capable=True, pinned=True, write=True)
        if run["run_state"] in PURGE_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        # T-2b: the first drawing, or the one allowed retake (see ``_artwork_slot``).
        self._artwork_slot(run, self._attached_original_refs(run_id))

    def _same_drawing(self, understanding_run_input_id: Any, current: Mapping[Any, Any]) -> bool:
        """True when the understanding was produced for the drawing of the ``current`` input."""
        if str(understanding_run_input_id) == str(current["run_input_id"]):
            return True
        analysed = self._session.execute(
            select(
                story_tables.run_inputs.c.original_asset_ref,
                story_tables.run_inputs.c.derived_sha256,
            ).where(story_tables.run_inputs.c.run_input_id == understanding_run_input_id)
        ).one_or_none()
        if analysed is None:
            return False
        original_ref, derived_sha = analysed
        if original_ref is None and derived_sha is None:
            return False
        return (original_ref, derived_sha) == (
            current["original_asset_ref"],
            current["derived_sha256"],
        )

    def _attached_original_refs(self, run_id: str) -> list[str]:
        """Physical keys of every distinct drawing attached so far, oldest input first.

        A later input revision (an idea or audio, T-2c) copies the drawing forward, so the same
        key can sit in several rows; it counts once (one retake only, FR-P-12).
        """
        refs: list[str] = []
        for value in self._session.scalars(
            select(story_tables.run_inputs.c.original_asset_ref)
            .where(
                story_tables.run_inputs.c.run_id == run_id,
                story_tables.run_inputs.c.original_asset_ref.is_not(None),
            )
            .order_by(story_tables.run_inputs.c.input_revision)
        ):
            if str(value) not in refs:
                refs.append(str(value))
        return refs

    @staticmethod
    def _artwork_slot(
        run: Mapping[str, Any],
        attached: list[str],
        *,
        code: str = "PARENT_STORY_RUN_NOT_ACCEPTING_ARTWORK",
    ) -> str:
        """``FIRST`` or ``RETAKE`` when the run accepts a drawing now, else 409 ``code``.

        First drawing: ``INPUT_PROCESSING`` with no drawing attached. Retake (FR-P-12, l.521;
        one only): exactly one drawing attached and the subject is not yet confirmed
        (``SUBJECT_REVIEW``) or the adult is reviewing the input (``INPUT_REVIEW``: the analysis
        failed recoverably, or a transcript waits for confirmation; T2B-D4/D7, T2C-D6). While a
        transcript is still ``PENDING`` after a recoverable analysis failure the run is in
        ``INPUT_PROCESSING`` with ``job_state = 'FAILED'``; the retake is allowed there too.
        """
        state = run["run_state"]
        can_retake = bool(attached) and len(attached) < _MAX_DRAWING_INPUTS
        if state == "INPUT_PROCESSING":
            if not attached:
                return "FIRST"
            if can_retake and run["job_state"] == "FAILED" and bool(run["retryable"]):
                return "RETAKE"
        elif state in _RETAKE_STATES and can_retake:
            return "RETAKE"
        raise ParentStoryRunError(409, code)

    def _refuse_purged(self, run: Mapping[str, Any]) -> None:
        """DTR Draft 6 §7: DELETE_PENDING and DELETED are refused by every Story writer."""

        if run["run_state"] in PURGE_STATES:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def _first_story_starter(self) -> FirstStoryStarter:
        """The implicit first-story start (T-2e-a D2; a Teacher run since V4-A OPEN-A D1). Only
        the job-side repository of a background task never starts one."""

        return FirstStoryStarter(
            self._session,
            enabled=not self._job_side,
            probe=self._first_story_probe,
            live_run=_live_run,
            sha256_json=_sha256_json,
            teacher=self._is_teacher,
        )

    def _first_story_probe(
        self, principal: VerifiedPrincipal, run: Mapping[str, Any], understanding_revision: int
    ) -> tuple[RowMapping, RowMapping, str, list[str]] | None:
        """``_story_generation_basis`` as a yes or no: an unmet gate (status below 500) is "not
        ready"; a store failure (5xx) propagates and rolls the command back (T-2e-a D3)."""

        try:
            return self._story_generation_basis(
                principal=principal,
                run=run,
                expected_understanding_revision=understanding_revision,
                subject_error=(422, "SUBJECT_NOT_CONFIRMED"),
            )
        except ParentStoryRunError as exc:
            if exc.status_code >= 500:
                raise
            return None

    def confirm_context(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_context_revision: int,
        expected_context_snapshot_sha256: str,
        idempotency_key: str,
        on_story_started: StoryStartedCallback | None = None,
        generator_supports_role: bool = True,
    ) -> ParentStoryRunView:
        operation = "CONFIRM_CONTEXT"
        scope_kind = "STORY_RUN"
        scope_ref = run_id
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_context_revision": expected_context_revision,
                "context_snapshot_sha256": expected_context_snapshot_sha256,
                "confirmed": True,
            }
        )
        run, access = self._owned_run_access(principal, run_id, lock=True, teacher_capable=True)
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            self._session.commit()
            return self.get_run(principal=principal, run_id=run_id)
        self._refuse_read_only_class(access)
        self._refuse_purged(run)

        input_row = self._current_input(run)
        context_revision = int(input_row["context_revision"] or 0)
        context_hash = str(input_row["context_snapshot_sha256"] or "")
        if context_revision != expected_context_revision or not hmac.compare_digest(
            context_hash, expected_context_snapshot_sha256
        ):
            raise ParentStoryRunError(409, "STALE_REVISION")
        if run["run_state"] not in {
            "INPUT_PROCESSING",
            "SUBJECT_REVIEW",
            "PREPARATION_REVIEW",
        }:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

        now = datetime.now(UTC)
        new_version = int(run["version"])
        if input_row["context_confirmed_by"] is None:
            new_version += 1
            self._session.execute(
                update(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_input_id == input_row["run_input_id"])
                .values(
                    context_confirmed_by=_principal_scope_ref(principal),
                    context_confirmed_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
        # T-2e-a D2: the confirmation may be the last gate of the implicit first-story start. The
        # start runs in this transaction after the stamp and before the receipt; a failure in it
        # rolls the whole command back (it raises its own 503).
        reservation = self._first_story_starter().start_if_ready(
            run_id, principal, now, generator_supports_role=generator_supports_role
        )
        try:
            self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={"context_revision": context_revision},
                now=now,
                response_status=200,
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_IDEMPOTENCY_KEY") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        record = self.get_run(principal=principal, run_id=run_id)
        if reservation is not None and on_story_started is not None:
            on_story_started(reservation)
        return record

    def _require_activity_state(self, run: Mapping[str, Any]) -> None:
        """T-2e-a D5/D7: the main activity is chosen in ``PREPARATION_REVIEW``; before the subject
        is confirmed the answer is 422 ``SUBJECT_NOT_CONFIRMED`` (SRS l.871), in any other state
        409."""

        state = str(run["run_state"])
        if state == "PREPARATION_REVIEW":
            return
        if state in _ACTIVITY_PRE_SUBJECT_STATES:
            raise ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED")
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def _activity_context(
        self, principal: VerifiedPrincipal, run: Mapping[str, Any]
    ) -> ParentActivityContext:
        """The stored context the activity list is computed from (no catalog read here)."""

        run_id = str(run["run_id"])
        understanding_revision = int(run["understanding_revision"] or 0)
        understanding = self._latest_understanding(run_id)
        if understanding is None or int(understanding["revision_no"]) != understanding_revision:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        decisions = story_tables.review_decisions
        subject_decision = self._session.scalar(
            select(decisions.c.decision_id).where(
                decisions.c.run_id == run_id,
                decisions.c.stage == "SUBJECT",
                decisions.c.decision == "CONFIRM",
                decisions.c.actor_scope_ref == _principal_scope_ref(principal),
                decisions.c.target_understanding_revision == understanding_revision,
            )
        )
        if subject_decision is None:
            raise ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED")
        input_row = self._current_input(run)
        snapshot = understanding["result_snapshot"]
        candidate = snapshot.get("result") if isinstance(snapshot, dict) else None
        raw_features = candidate.get("visible_features") if isinstance(candidate, dict) else None
        if not isinstance(raw_features, list):
            raw_features = []
        visible_features = [
            str(value).strip()[:160] for value in raw_features[:4] if str(value).strip()
        ]
        if not visible_features:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        pin = input_row["lesson_pin_snapshot"]
        return ParentActivityContext(
            run_id=run_id,
            run_revision=int(run["revision"]),
            understanding_revision=understanding_revision,
            context_snapshot=dict(input_row["context_snapshot"]),
            subject_label=str(run["subject_label"] or "").strip(),
            visible_features=visible_features,
            lesson_pin_snapshot=dict(pin) if pin is not None else None,
        )

    def read_activity_context(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentActivityContext:
        run = self._owned_run(principal, run_id)
        if run["run_state"] in PURGE_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        self._require_activity_state(run)
        return self._activity_context(principal, run)

    def select_activity(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        activity_ref: Mapping[str, Any],
        idempotency_key: str,
        resolve: ActivityResolver,
        on_story_started: StoryStartedCallback | None = None,
    ) -> ParentStoryRunView:
        """Record the adult's main activity (T-2e-a D7, SRS l.514, l.1667).

        Order under the run lock: the idempotency replay (never calls ``resolve``), a purged run,
        the state, the run revision, then ``resolve`` (the application service recomputes the list
        and checks membership), then the receipt, the selection row, the run bump and the implicit
        first-story start, in one commit. A Teacher gets the uniform 404.
        """
        run = self._owned_run(principal, run_id, lock=True)
        key_hash = _idempotency_key_hash(idempotency_key)
        reference = {
            "lesson_id": str(activity_ref["lesson_id"]),
            "version_id": str(activity_ref["version_id"]),
            "content_sha256": str(activity_ref["content_sha256"]),
            "activity_index": int(activity_ref["activity_index"]),
        }
        fingerprint = _sha256_json(
            {"expected_revision": expected_revision, "activity_ref": reference}
        )
        self._lock_idempotency(
            principal=principal,
            operation=_SELECT_ACTIVITY_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=_SELECT_ACTIVITY_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            self._session.commit()
            if run["run_state"] in PURGE_STATES:
                # DTR Draft 6 §6.5: the replay of a purged run returns only the projection.
                return _projection(run)
            return self.get_run(principal=principal, run_id=run_id)
        self._refuse_purged(run)
        self._require_activity_state(run)
        if int(run["revision"]) != expected_revision:
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=int(run["revision"]))
        try:
            pin = resolve(self._activity_context(principal, run))
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        except BaseException:
            self._session.rollback()
            raise
        now = datetime.now(UTC)
        understanding_revision = int(run["understanding_revision"] or 0)
        new_version = int(run["version"]) + 1
        new_revision = int(run["revision"]) + 1
        snapshot = {**pin.snapshot, "selected_at": now.isoformat()}
        selections = story_tables.activity_selections
        try:
            selection_no = (
                int(
                    self._session.scalar(
                        select(func.coalesce(func.max(selections.c.selection_no), 0)).where(
                            selections.c.run_id == run_id
                        )
                    )
                    or 0
                )
                + 1
            )
            command_kind, command_ref = self._command_scope(principal)
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=_SELECT_ACTIVITY_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={
                    "selection_no": selection_no,
                    "activity_ref": reference,
                    "understanding_revision": understanding_revision,
                },
                now=now,
                response_status=200,
            )
            self._session.execute(
                insert(selections).values(
                    selection_id=str(uuid4()),
                    run_id=run_id,
                    selection_no=selection_no,
                    target_understanding_revision=understanding_revision,
                    source_kind="LESSON_ACTIVITY",
                    lesson_id=pin.lesson_id,
                    version_id=pin.version_id,
                    content_sha256=pin.content_sha256,
                    activity_index=pin.activity_index,
                    activity_snapshot=snapshot,
                    activity_snapshot_sha256=_sha256_json(snapshot),
                    command_receipt_id=receipt_id,
                    actor_scope_kind=command_kind,
                    actor_scope_ref=command_ref,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(version=new_version, revision=new_revision, updated_at=now)
            )
        except SQLAlchemyError:
            # The idempotency lock and the run lock make a key or number collision unreachable, and
            # an activity that cannot fit the snapshot bound is never listed (the service), so a
            # database refusal here is a store failure, not a state conflict.
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        reservation = self._first_story_starter().start_if_ready(run_id, principal, now)
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        record = self.get_run(principal=principal, run_id=run_id)
        if reservation is not None and on_story_started is not None:
            on_story_started(reservation)
        return record

    def reserve_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        idempotency_key: str,
    ) -> ParentActivitySuggestionReservation:
        """Reserve one immutable AI suggestion set after the adult confirmed the drawing subject."""
        run = self._owned_run(principal, run_id, lock=True)
        self._require_activity_state(run)
        activity_context = self._activity_context(principal, run)
        if activity_context.understanding_revision != expected_understanding_revision:
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE")
        input_row = self._current_input(run)
        # SRS order: the adult chooses the activity first and confirms the context afterwards, so
        # suggestions must not wait for the context confirmation (the story start still does).
        if input_row["original_sha256"] is None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_REQUIRED")
        context = {
            "understanding_revision": activity_context.understanding_revision,
            "input_revision": int(run["current_input_revision"]),
            "context_revision": int(input_row["context_revision"]),
            "context_snapshot": dict(activity_context.context_snapshot),
            "subject_label": activity_context.subject_label,
            "visible_features": tuple(activity_context.visible_features),
            "lesson_pin_snapshot": activity_context.lesson_pin_snapshot,
        }
        operation = "GENERATE_ACTIVITY_SET"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {"expected_understanding_revision": expected_understanding_revision}
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            if replay["state"] == "PENDING":
                raise ParentStoryRunError(409, "PARENT_ACTIVITY_SUGGESTION_IN_PROGRESS")
            body = replay["response_body"]
            if not isinstance(body, dict):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            error_code = body.get("error_code")
            if isinstance(error_code, str):
                status = replay["response_status"]
                if type(status) is not int or status not in {409, 422, 502, 503, 504}:
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                raise ParentStoryRunError(status, error_code)
            set_id = body.get("suggestion_set_id")
            set_revision = body.get("set_revision")
            if not isinstance(set_id, str) or type(set_revision) is not int:
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
            return ParentActivitySuggestionReservation(
                run_id=run_id,
                suggestion_set_id=set_id,
                set_revision=set_revision,
                **context,
                excluded_candidate_keys=(),
                excluded_activities=(),
                receipt_id=str(replay["receipt_id"]),
                replayed=True,
                replay_body=body,
            )

        sets = story_tables.parent_activity_suggestion_sets
        previous_sets = self._session.execute(
            select(sets)
            .where(
                sets.c.run_id == run_id,
                sets.c.understanding_revision == expected_understanding_revision,
            )
            .order_by(sets.c.set_revision.desc())
        ).mappings().all()
        latest_revision = self._session.scalar(
            select(func.max(sets.c.set_revision)).where(sets.c.run_id == run_id)
        )
        set_revision = int(latest_revision or 0) + 1
        excluded_keys: set[str] = set()
        excluded_activities: list[dict[str, Any]] = []
        for row in previous_sets:
            snapshot = row["activities_snapshot"]
            if not isinstance(snapshot, list):
                continue
            for activity in snapshot:
                if isinstance(activity, dict):
                    excluded_activities.append(dict(activity))
                    key = _parent_activity_candidate_key(activity)
                    if key is not None:
                        excluded_keys.add(key)

        suggestion_set_id = str(uuid4())
        try:
            receipt_id = self._store_pending_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=set_revision,
                now=datetime.now(UTC),
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_IDEMPOTENCY_KEY") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return ParentActivitySuggestionReservation(
            run_id=run_id,
            suggestion_set_id=suggestion_set_id,
            set_revision=set_revision,
            **context,
            excluded_candidate_keys=tuple(sorted(excluded_keys)),
            excluded_activities=tuple(excluded_activities),
            receipt_id=receipt_id,
        )

    def complete_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentActivitySuggestionReservation,
        response: dict[str, Any],
        provider_call_id: str | None,
    ) -> dict[str, Any]:
        if reservation.receipt_id is None or reservation.replayed:
            raise ParentStoryRunError(409, "PARENT_ACTIVITY_SUGGESTION_RESERVATION_INVALID")
        run = self._owned_run(principal, reservation.run_id, lock=True)
        self._require_activity_state(run)
        context = self._activity_context(principal, run)
        input_row = self._current_input(run)
        if (
            context.understanding_revision != reservation.understanding_revision
            or int(run["current_input_revision"]) != reservation.input_revision
            or int(input_row["context_revision"]) != reservation.context_revision
        ):
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE")
        activities = response.get("activities")
        if not isinstance(activities, list) or not activities:
            raise ParentStoryRunError(502, "PARENT_ACTIVITY_RESPONSE_INVALID")
        snapshot_hash = _sha256_json(activities)
        final_response = {
            **response,
            "suggestion_set_id": reservation.suggestion_set_id,
            "set_revision": reservation.set_revision,
            "activities_snapshot_sha256": snapshot_hash,
        }
        now = datetime.now(UTC)
        try:
            self._session.execute(
                insert(story_tables.parent_activity_suggestion_sets).values(
                    suggestion_set_id=reservation.suggestion_set_id,
                    run_id=reservation.run_id,
                    set_revision=reservation.set_revision,
                    understanding_revision=reservation.understanding_revision,
                    input_revision=reservation.input_revision,
                    context_revision=reservation.context_revision,
                    selection_mode=final_response["selection_mode"],
                    catalog_candidate_count=final_response["catalog_candidate_count"],
                    activities_snapshot=activities,
                    activities_snapshot_sha256=snapshot_hash,
                    provider_call_id=provider_call_id,
                    created_at=now,
                )
            )
            updated = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_command_receipts)
                    .where(
                        story_tables.story_command_receipts.c.receipt_id
                        == reservation.receipt_id,
                        story_tables.story_command_receipts.c.state == "PENDING",
                    )
                    .values(
                        state="FINAL",
                        response_status=200,
                        response_resource_version=reservation.set_revision,
                        response_body=final_response,
                        resource_ref=reservation.run_id,
                        resource_version=reservation.set_revision,
                        state_version=story_tables.story_command_receipts.c.state_version + 1,
                        finalized_at=now,
                    )
                ),
            )
            if updated.rowcount != 1:
                self._session.rollback()
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_ACTIVITY_SUGGESTION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return final_response

    def fail_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentActivitySuggestionReservation,
        error_code: str,
        response_status: int,
    ) -> None:
        if reservation.receipt_id is None or reservation.replayed:
            return
        if response_status not in {409, 422, 502, 503, 504}:
            raise ValueError("activity suggestion failure status is not supported")
        try:
            updated = self._session.execute(
                update(story_tables.story_command_receipts)
                .where(
                    story_tables.story_command_receipts.c.receipt_id == reservation.receipt_id,
                    story_tables.story_command_receipts.c.actor_scope_ref
                    == _principal_scope_ref(principal),
                    story_tables.story_command_receipts.c.state == "PENDING",
                )
                .values(
                    state="FINAL",
                    response_status=response_status,
                    response_resource_version=reservation.set_revision,
                    response_body={"error_code": error_code},
                    resource_ref=reservation.run_id,
                    resource_version=reservation.set_revision,
                    state_version=story_tables.story_command_receipts.c.state_version + 1,
                    finalized_at=datetime.now(UTC),
                )
            )
            if updated.rowcount != 1:
                self._session.rollback()
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def select_suggested_activity(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        suggestion_set_id: str,
        expected_understanding_revision: int,
        activity_index: int,
        idempotency_key: str,
        on_story_started: StoryStartedCallback | None = None,
    ) -> ParentStoryRunView:
        """Pin one item from the latest persisted set and pass through the existing story-start gate."""
        run = self._owned_run(principal, run_id, lock=True)
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_revision": expected_revision,
                "suggestion_set_id": suggestion_set_id,
                "expected_understanding_revision": expected_understanding_revision,
                "activity_index": activity_index,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=_SELECT_ACTIVITY_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=_SELECT_ACTIVITY_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            self._session.commit()
            if run["run_state"] in PURGE_STATES:
                return _projection(run)
            return self.get_run(principal=principal, run_id=run_id)

        self._refuse_purged(run)
        self._require_activity_state(run)
        if int(run["revision"]) != expected_revision:
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=int(run["revision"]))
        context = self._activity_context(principal, run)
        if context.understanding_revision != expected_understanding_revision:
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE")
        latest_set = self._session.execute(
            select(story_tables.parent_activity_suggestion_sets)
            .where(
                story_tables.parent_activity_suggestion_sets.c.run_id == run_id,
                story_tables.parent_activity_suggestion_sets.c.understanding_revision
                == expected_understanding_revision,
            )
            .order_by(story_tables.parent_activity_suggestion_sets.c.set_revision.desc())
            .limit(1)
        ).mappings().one_or_none()
        if latest_set is None or str(latest_set["suggestion_set_id"]) != suggestion_set_id:
            raise ParentStoryRunError(409, "PARENT_ACTIVITY_SET_STALE")
        activities = latest_set["activities_snapshot"]
        if (
            not isinstance(activities, list)
            or type(activity_index) is not int
            or not 0 <= activity_index < len(activities)
        ):
            raise ParentStoryRunError(422, "PARENT_ACTIVITY_SELECTION_INVALID")
        suggested = activities[activity_index]
        if not isinstance(suggested, dict):
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
        if not hmac.compare_digest(
            str(latest_set["activities_snapshot_sha256"]), _sha256_json(activities)
        ):
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")

        source = str(suggested.get("source", ""))
        is_ai_draft = source == "AI_GENERATED_DRAFT"
        lesson_id = _text_or_none(suggested.get("source_lesson_id"))
        version_id = _text_or_none(suggested.get("source_lesson_version_id"))
        content_sha256 = _text_or_none(suggested.get("source_content_sha256"))
        source_index = suggested.get("source_activity_index")
        if not is_ai_draft and (
            not lesson_id
            or not version_id
            or not content_sha256
            or type(source_index) is not int
        ):
            raise ParentStoryRunError(422, "PARENT_ACTIVITY_SELECTION_INVALID")
        snapshot = {
            "schema": "sketch2life.parent-activity-pin.v1",
            "activity_ref": (
                {
                    "lesson_id": lesson_id,
                    "version_id": version_id,
                    "content_sha256": content_sha256,
                    "activity_index": source_index,
                }
                if not is_ai_draft
                else None
            ),
            "title": str(suggested["title"]),
            "objective": str(suggested["objective"]),
            "materials_text": str(suggested["materials_text"]),
            "preparation_text": str(suggested["preparation_text"]),
            "instructions_text": str(suggested["instructions_text"]),
            "observation_notes": str(suggested["observation_notes"]),
            "safety_notes": str(suggested["safety_notes"]),
            "activity_kind": str(suggested["activity_kind"]),
            "source": source,
            "lesson_title": suggested.get("source_lesson_title"),
            "lesson_topic": (
                str((context.lesson_pin_snapshot or {}).get("topic", ""))
                if source == "PINNED_LESSON"
                else None
            ),
            "source_lesson_id": lesson_id,
            "source_lesson_version_id": version_id,
            "source_content_sha256": content_sha256,
            "source_activity_index": source_index,
            "match_reason": suggested.get("match_reason"),
            "suggestion_set_id": suggestion_set_id,
            "suggestion_set_revision": int(latest_set["set_revision"]),
            "suggestion_activity_index": activity_index,
        }
        now = datetime.now(UTC)
        snapshot["selected_at"] = now.isoformat()
        snapshot_hash = _sha256_json(snapshot)
        selection_id = str(uuid4())
        selections = story_tables.activity_selections
        legacy_selections = story_tables.parent_activity_selections
        new_version = int(run["version"]) + 1
        new_revision = int(run["revision"]) + 1
        understanding_revision = int(run["understanding_revision"] or 0)
        command_kind, command_ref = self._command_scope(principal)
        try:
            selection_no = int(
                self._session.scalar(
                    select(func.coalesce(func.max(selections.c.selection_no), 0)).where(
                        selections.c.run_id == run_id
                    )
                )
                or 0
            ) + 1
            legacy_revision = int(
                self._session.scalar(
                    select(func.coalesce(func.max(legacy_selections.c.selection_revision), 0)).where(
                        legacy_selections.c.run_id == run_id
                    )
                )
                or 0
            ) + 1
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=_SELECT_ACTIVITY_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={
                    "selection_id": selection_id,
                    "suggestion_set_id": suggestion_set_id,
                    "activity_index": activity_index,
                    "understanding_revision": understanding_revision,
                },
                now=now,
                response_status=200,
            )
            self._session.execute(
                insert(selections).values(
                    selection_id=selection_id,
                    run_id=run_id,
                    selection_no=selection_no,
                    target_understanding_revision=understanding_revision,
                    source_kind="AI_DRAFT" if is_ai_draft else "LESSON_ACTIVITY",
                    lesson_id=None if is_ai_draft else lesson_id,
                    version_id=None if is_ai_draft else version_id,
                    content_sha256=None if is_ai_draft else content_sha256,
                    activity_index=None if is_ai_draft else source_index,
                    activity_snapshot=snapshot,
                    activity_snapshot_sha256=snapshot_hash,
                    command_receipt_id=receipt_id,
                    actor_scope_kind=command_kind,
                    actor_scope_ref=command_ref,
                    created_at=now,
                )
            )
            # Compatibility projection for the existing video-candidate FK; both rows have the
            # same opaque ID and exact immutable snapshot, so story/video cannot refer to different
            # activities during this schema reconciliation.
            self._session.execute(
                insert(legacy_selections).values(
                    activity_selection_id=selection_id,
                    run_id=run_id,
                    selection_revision=legacy_revision,
                    suggestion_set_id=suggestion_set_id,
                    understanding_revision=understanding_revision,
                    activity_index=activity_index,
                    activity_snapshot=snapshot,
                    activity_snapshot_sha256=snapshot_hash,
                    actor_scope_ref=_principal_scope_ref(principal),
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(version=new_version, revision=new_revision, updated_at=now)
            )
            story_reservation = self._first_story_starter().start_if_ready(run_id, principal, now)
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_ACTIVITY_SELECTION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        record = self.get_run(principal=principal, run_id=run_id)
        if story_reservation is not None and on_story_started is not None:
            on_story_started(story_reservation)
        return record

    def attach_artwork(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        original_asset_ref: str,
        original_sha256: str,
        original_media_type: str,
        original_size_bytes: int,
        derived_asset_ref: str,
        derived_sha256: str,
        derived_size_bytes: int,
        scanner_name: str,
        scanner_version: str,
    ) -> ParentStoryInputRecord:
        run = self._owned_run(principal, run_id, lock=True)
        self._refuse_purged(run)
        if run["run_state"] != "INPUT_PROCESSING":
            raise ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_ACCEPTING_ARTWORK")
        previous = self._current_input(run)
        if previous["original_asset_ref"] is not None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_ALREADY_ATTACHED")
        now = datetime.now(UTC)
        new_input_revision = int(previous["input_revision"]) + 1
        lineage = story_tables.asset_lineage
        scanner_hash = hashlib.sha256(
            f"{scanner_name}\0{scanner_version}".encode()
        ).hexdigest()
        try:
            self._session.add_all(
                [
                    CoreAssetMetadataModel(
                        asset_ref=original_asset_ref,
                        asset_version=1,
                        organization_id=None,
                        owner_scope_kind=_OWNER_SCOPE_KIND,
                        owner_scope_ref=_principal_scope_ref(principal),
                        content_sha256=original_sha256,
                        media_type=original_media_type,
                        source_refs=[run_id],
                        derived_from_ref=None,
                    ),
                    CoreAssetMetadataModel(
                        asset_ref=derived_asset_ref,
                        asset_version=1,
                        organization_id=None,
                        owner_scope_kind=_OWNER_SCOPE_KIND,
                        owner_scope_ref=_principal_scope_ref(principal),
                        content_sha256=derived_sha256,
                        media_type="image/png",
                        source_refs=[run_id],
                        derived_from_ref=original_asset_ref,
                    ),
                ]
            )
            # The session factory disables autoflush, so the asset rows must be written
            # before the lineage insert, whose foreign keys are checked immediately.
            self._session.flush()
            self._session.execute(
                insert(lineage).values(
                    lineage_id=str(uuid4()),
                    source_asset_ref=original_asset_ref,
                    source_asset_version=1,
                    derived_asset_ref=derived_asset_ref,
                    derived_asset_version=1,
                    source_sha256=original_sha256,
                    derived_sha256=derived_sha256,
                    source_size_bytes=original_size_bytes,
                    derived_size_bytes=derived_size_bytes,
                    transform_kind="NORMALIZE_DRAWING_IMAGE",
                    transform_version="PILLOW_RGB_PNG_V1",
                    scanner_name=scanner_name,
                    scanner_version=scanner_version,
                    scanner_sha256=scanner_hash,
                    created_at=now,
                )
            )
            input_id = str(uuid4())
            # T-2c C1: every column that is not the drawing is copied forward (voice included).
            self._session.execute(
                insert(story_tables.run_inputs).values(
                    **_next_input_values(
                        previous,
                        run_input_id=input_id,
                        input_revision=new_input_revision,
                        original_asset_ref=original_asset_ref,
                        original_asset_version=1,
                        original_sha256=original_sha256,
                        original_media_type=original_media_type,
                        original_size_bytes=original_size_bytes,
                        derived_asset_ref=derived_asset_ref,
                        derived_asset_version=1,
                        derived_sha256=derived_sha256,
                        derived_media_type="image/png",
                        derived_size_bytes=derived_size_bytes,
                        created_at=now,
                    )
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    current_input_revision=new_input_revision,
                    asset_ref=original_asset_ref,
                    derived_asset_ref=derived_asset_ref,
                    job_state="RUNNING",
                    retryable=False,
                    error_code=None,
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.read_current_input(principal=principal, run_id=run_id)

    def read_current_input(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentStoryInputRecord:
        run = self._owned_run(principal, run_id, job_side_ok=True)
        if run["run_state"] in PURGE_STATES:
            # DTR Draft 6 §6.5: a lifecycle error, not PARENT_STORY_CONTEXT_UNAVAILABLE.
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        row = self._current_input(run)
        return self._input_record(row)

    # ------------------------------------------------------------------ T-2b: uploaded drawing
    def prepare_drawing_attach(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int | None,
    ) -> DrawingAttachOutcome | ParentStoryLifecycleRecord | None:
        """Replay, or the cheap pre-checks that run before any asset byte is read.

        Order: owner-scoped run (404), replay (a purged run answers the lifecycle projection),
        purged run (409), stale revision (409 with ``current_version``), state and retake budget
        (409). The run row is locked while these checks run and released on return, also on
        every error; ``attach_uploaded_drawing`` re-checks under the lock.
        """
        # T2B-R-3: the run row is read FOR UPDATE, so a first attach that is committing is
        # waited for and its receipt is visible below; without the lock a replay racing its own
        # first attach could see the stale run and answer 409 instead of the stored 202. The
        # lock is released by every rollback below, before any asset byte is read.
        run, access = self._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True, pinned=True
        )
        try:
            replay = self._find_idempotency_receipt(
                principal=principal,
                operation=_ATTACH_ASSET_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=_idempotency_key_hash(idempotency_key),
                fingerprint=fingerprint,
            )
            if replay is not None:
                result = self._replayed_attach(run, replay)
                self._session.rollback()
                return result
            self._refuse_read_only_class(access)
            self._refuse_purged(run)
            self._check_expected_run_revision(run, expected_run_revision)
            self._artwork_slot(
                run, self._attached_original_refs(run_id), code="INVALID_STATE_TRANSITION"
            )
        except ParentStoryRunError:
            self._session.rollback()
            raise
        self._session.rollback()
        return None

    @staticmethod
    def _replayed_attach(
        run: Mapping[Any, Any], receipt: Mapping[Any, Any]
    ) -> DrawingAttachOutcome | ParentStoryLifecycleRecord:
        if run["run_state"] in PURGE_STATES:
            # DTR Draft 6 §6.5: a replay of a purged run returns the content-free projection.
            return _projection(run)
        body = receipt["response_body"]
        try:
            return DrawingAttachOutcome(
                input_revision=int(body["input_revision"]),
                run_revision=int(body["run_revision"]),
                run_state=str(body["run_state"]),
                analysis_state=str(body["analysis_state"]),
                replayed=True,
            )
        except (KeyError, TypeError, ValueError):
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def _check_expected_run_revision(
        self, run: Mapping[str, Any], expected_run_revision: int | None
    ) -> None:
        if expected_run_revision is not None and int(run["revision"]) != expected_run_revision:
            current = int(run["revision"])
            self._session.rollback()
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=current)

    def attach_uploaded_drawing(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int | None,
        original_asset_ref: str,
        original_sha256: str,
        original_media_type: str,
        original_size_bytes: int,
        scanner_name: str,
        scanner_version: str,
        derived_png: bytes,
        derived_sha256: str,
        storage: ObjectStoragePort,
    ) -> DrawingAttachOutcome | ParentStoryLifecycleRecord:
        """Attach a completed upload as the run's drawing (first drawing or the one retake).

        One transaction under the run row lock. Every state, revision, retake and "same asset"
        check runs before the derived object is put, so a request that loses a race never touches
        storage and cannot remove the winner's object (R1 B2). The original asset row is the one
        the upload created (T-2a); this writes the derived asset, one lineage row, the new input
        revision, the run update and the receipt, then commits.
        """
        run, access = self._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True, pinned=True
        )
        key_hash = _idempotency_key_hash(idempotency_key)
        self._lock_idempotency(
            principal=principal,
            operation=_ATTACH_ASSET_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=_ATTACH_ASSET_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            result = self._replayed_attach(run, replay)
            self._session.commit()
            return result
        self._refuse_read_only_class(access)
        self._refuse_purged(run)
        self._check_expected_run_revision(run, expected_run_revision)
        attached = self._attached_original_refs(run_id)
        slot = self._artwork_slot(run, attached, code="INVALID_STATE_TRANSITION")
        prefix = f"parent/{run_id}/"
        if not original_asset_ref.startswith(prefix) or original_asset_ref in attached:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        derived_asset_ref = derived_asset_key(original_asset_ref)
        previous = self._current_input(run)
        new_input_revision = int(previous["input_revision"]) + 1
        owner_kind, owner_ref, owner_organization = self._asset_owner(principal, run)
        now = datetime.now(UTC)
        try:
            storage.put_object(
                derived_asset_ref,
                BytesIO(derived_png),
                content_type="image/png",
                content_length=len(derived_png),
                metadata={"sha256": derived_sha256, "source-ref": original_asset_ref},
            )
        except ObjectStorageFailure:
            self._session.rollback()
            self._discard_unreferenced_object(storage, run_id, derived_asset_ref)
            raise ParentStoryRunError(503, "STORAGE_UNAVAILABLE") from None
        try:
            self._session.add(
                CoreAssetMetadataModel(
                    asset_ref=derived_asset_ref,
                    asset_version=1,
                    organization_id=owner_organization,
                    owner_scope_kind=owner_kind,
                    owner_scope_ref=owner_ref,
                    content_sha256=derived_sha256,
                    media_type="image/png",
                    source_refs=[run_id],
                    derived_from_ref=original_asset_ref,
                )
            )
            # The session factory disables autoflush: the metadata row must exist before the
            # lineage insert, whose composite foreign keys are checked immediately.
            self._session.flush()
            self._session.execute(
                insert(story_tables.asset_lineage).values(
                    lineage_id=str(uuid4()),
                    source_asset_ref=original_asset_ref,
                    source_asset_version=1,
                    derived_asset_ref=derived_asset_ref,
                    derived_asset_version=1,
                    source_sha256=original_sha256,
                    derived_sha256=derived_sha256,
                    source_size_bytes=original_size_bytes,
                    derived_size_bytes=len(derived_png),
                    transform_kind="NORMALIZE_DRAWING_IMAGE",
                    transform_version="PILLOW_RGB_PNG_V2",
                    scanner_name=scanner_name,
                    scanner_version=scanner_version,
                    scanner_sha256=scanner_identity_sha256(scanner_name, scanner_version),
                    created_at=now,
                )
            )
            self._session.execute(
                insert(story_tables.run_inputs).values(
                    **_next_input_values(
                        previous,
                        run_input_id=str(uuid4()),
                        input_revision=new_input_revision,
                        original_asset_ref=original_asset_ref,
                        original_asset_version=1,
                        original_sha256=original_sha256,
                        original_media_type=original_media_type,
                        original_size_bytes=original_size_bytes,
                        derived_asset_ref=derived_asset_ref,
                        derived_asset_version=1,
                        derived_sha256=derived_sha256,
                        derived_media_type="image/png",
                        derived_size_bytes=len(derived_png),
                        created_at=now,
                    )
                )
            )
            run_values: dict[str, Any] = {
                "run_state": "INPUT_PROCESSING",
                "current_input_revision": new_input_revision,
                "asset_ref": original_asset_ref,
                "derived_asset_ref": derived_asset_ref,
                "job_state": "QUEUED",
                "retryable": False,
                "error_code": None,
                "version": story_tables.story_runs.c.version + 1,
                "revision": story_tables.story_runs.c.revision + 1,
                "updated_at": now,
            }
            if slot == "RETAKE":
                # The earlier understanding stays as history; the run no longer reports it.
                run_values.update(
                    understanding_revision=None,
                    subject_label=None,
                    confidence=None,
                    result_sha256=None,
                    raw_body_sha256=None,
                )
            run_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_runs).where(_live_run(run_id)).values(**run_values)
                ),
            )
            if run_update.rowcount != 1:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            outcome = DrawingAttachOutcome(
                input_revision=new_input_revision,
                run_revision=int(run["revision"]) + 1,
                run_state="INPUT_PROCESSING",
                analysis_state="QUEUED",
                organization_id=str(run["actor_scope_ref"]) if self._is_teacher else None,
            )
            self._store_idempotency_receipt(
                principal=principal,
                operation=_ATTACH_ASSET_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=int(run["version"]) + 1,
                response_body=outcome.as_body(),
                now=now,
                response_status=202,
            )
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            self._discard_unreferenced_object(storage, run_id, derived_asset_ref)
            raise
        except IntegrityError:
            self._session.rollback()
            self._discard_unreferenced_object(storage, run_id, derived_asset_ref)
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None
        except SQLAlchemyError:
            self._session.rollback()
            self._discard_unreferenced_object(storage, run_id, derived_asset_ref)
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return outcome

    def _asset_owner(
        self, principal: VerifiedPrincipal, run: Mapping[str, Any]
    ) -> tuple[str, str, str | None]:
        """Kind, ref and organization of the Core rows (uploads, assets) of this run (D4, D16).

        Parent: its own typed scope, no organization. Teacher: ``ORGANIZATION`` with the
        organization id as scope ref AND as organization (never NULL: the asset trigger, the
        T-13a seed, the purge plan and the open-session close all match the ref, T-4b3a P2-2).
        """

        if self._is_teacher:
            organization = str(run["actor_scope_ref"])
            return TEACHER_COMMAND_SCOPE_KIND, organization, organization
        return _OWNER_SCOPE_KIND, _principal_scope_ref(principal), None

    def asset_owner(self, *, principal: VerifiedPrincipal, run_id: str) -> RunAssetOwner:
        """The owner triple of the Core rows of the run, for the upload resolution of a service.

        A Parent answers from the principal with no read (the unchanged path); a Teacher needs a
        pinned run on the current assignment (the uniform 404 otherwise)."""

        if not self._is_teacher:
            kind, ref, organization = self._asset_owner(principal, {})
            return RunAssetOwner(kind, ref, organization)
        try:
            run = self._owned_run(principal, run_id, teacher_capable=True, pinned=True)
            kind, ref, organization = self._asset_owner(principal, run)
        finally:
            self._session.rollback()
        return RunAssetOwner(kind, ref, organization)

    def _discard_unreferenced_object(
        self, storage: ObjectStoragePort, run_id: str, key: str
    ) -> None:
        """Delete ``key`` only when no committed asset row references it (R1 B2, T2B-R-1).

        The derived key is deterministic per upload, so after a rollback it may belong to a
        committed winner. The run row is locked first: a competing attach holds that lock from
        its put to its commit, so once this lock is granted the winner's row is either committed
        (referenced, the object stays) or there is no winner in flight. The lock is released by
        the final rollback, after the delete.
        """
        try:
            self._session.execute(
                select(story_tables.story_runs.c.run_id)
                .where(story_tables.story_runs.c.run_id == run_id)
                .with_for_update()
            ).one_or_none()
            referenced = self._session.scalar(
                select(_ASSET_METADATA.c.asset_ref).where(_ASSET_METADATA.c.asset_ref == key)
            )
        except SQLAlchemyError:
            self._session.rollback()
            return
        try:
            if referenced is None:
                try:
                    storage.delete_object(key)
                except ObjectStorageFailure:
                    # The run purge sweep (FR-C-08, prefix ``parent/{run}/``) removes a leftover.
                    return
        finally:
            self._session.rollback()

    def start_drawing_analysis(
        self, *, principal: VerifiedPrincipal, run_id: str, expected_input_revision: int
    ) -> bool:
        """QUEUED -> RUNNING for the current input; ``False`` when the work is stale or gone."""
        run = self._owned_run(principal, run_id, lock=True, job_side_ok=True)
        if (
            run["run_state"] != "INPUT_PROCESSING"
            or run["job_state"] != "QUEUED"
            or not self._drawing_unchanged(run, expected_input_revision)
        ):
            self._session.rollback()
            return False
        try:
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    job_state="RUNNING",
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=datetime.now(UTC),
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return True

    def reconcile_modal_resource_exhausted_rejection(
        self,
        *,
        run_id: str,
        expected_run_revision: int,
        expected_input_revision: int,
        expected_derived_sha256: str,
    ) -> bool:
        """Requeue one operator-verified Modal rejection that created no FunctionCall.

        This is intentionally not exposed as an HTTP operation. A local/test operator may call it
        only after Modal returned the explicit ``ResourceExhaustedError`` from ``Function.spawn``
        with no call ID. Locking, the exact state/error/revision/drawing checks, and the audit row
        make that attested reconciliation a single compare-and-set. Timeouts and transport errors
        must never use this method.
        """
        run = (
            self._session.execute(
                select(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if run is None or run["actor_scope_kind"] != _OWNER_SCOPE_KIND:
            self._session.rollback()
            return False
        if (
            run["run_state"] != "INPUT_PROCESSING"
            or run["job_state"] != "AWAITING_RECONCILIATION"
            or run["error_code"] != "DRAWING_OUTCOME_UNKNOWN"
            or bool(run["retryable"])
            or int(run["revision"]) != expected_run_revision
            or run["current_input_revision"] != expected_input_revision
            or not isinstance(expected_derived_sha256, str)
            or len(expected_derived_sha256) != 64
        ):
            self._session.rollback()
            return False

        current = (
            self._session.execute(
                select(story_tables.run_inputs).where(
                    story_tables.run_inputs.c.run_id == run_id,
                    story_tables.run_inputs.c.input_revision == expected_input_revision,
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            current is None
            or current["original_asset_ref"] is None
            or current["derived_asset_ref"] is None
            or current["derived_sha256"] != expected_derived_sha256
            or not self._drawing_unchanged(run, expected_input_revision)
        ):
            self._session.rollback()
            return False

        now = datetime.now(UTC)
        try:
            updated = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_runs)
                    .where(
                        _live_run(run_id),
                        story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                        story_tables.story_runs.c.run_state == "INPUT_PROCESSING",
                        story_tables.story_runs.c.job_state == "AWAITING_RECONCILIATION",
                        story_tables.story_runs.c.error_code == "DRAWING_OUTCOME_UNKNOWN",
                        story_tables.story_runs.c.retryable.is_(False),
                        story_tables.story_runs.c.revision == expected_run_revision,
                        story_tables.story_runs.c.current_input_revision == expected_input_revision,
                    )
                    .values(
                        job_state="QUEUED",
                        error_code=None,
                        version=story_tables.story_runs.c.version + 1,
                        revision=story_tables.story_runs.c.revision + 1,
                        updated_at=now,
                    )
                ),
            )
            if updated.rowcount != 1:
                self._session.rollback()
                return False
            write_story_task_audit(
                self._session,
                actor_ref="SYSTEM_MODAL_RECONCILER",
                action="DRAWING_DISPATCH_RECONCILED",
                run_id=run_id,
                decision="MODAL_RESOURCE_EXHAUSTED_NO_CALL_ID",
                run_revision=expected_run_revision + 1,
                now=now,
                **story_task_audit_scope(run),
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return True

    def fail_drawing_analysis_recoverable(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        error_code: str,
        expected_input_revision: int,
    ) -> bool:
        """A failure the adult can fix by a retake (T2B-D7): the run moves to ``INPUT_REVIEW``.

        ``job_state`` becomes ``FAILED`` with ``retryable`` true and ``error_code`` set; the
        Parent's active slot is kept (unlike ``fail_drawing_analysis``, whose known failure is
        the terminal ``FAILED`` run). The settle rule (T2C-D6, l.394) puts a run whose drawing
        has no understanding and whose analysis failed into ``INPUT_REVIEW``. ``False`` when the
        work is stale (replaced drawing, other state, purged run, or a job that is no longer in
        flight because the reaper already failed it, T-2d-fix D1).
        """
        run = self._owned_run(principal, run_id, lock=True, job_side_ok=True)
        if (
            run["run_state"] != "INPUT_PROCESSING"
            or run["job_state"] not in _VLM_IN_FLIGHT
            or not self._drawing_unchanged(run, expected_input_revision)
        ):
            self._session.rollback()
            return False
        try:
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    job_state="FAILED",
                    retryable=True,
                    error_code=error_code,
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=datetime.now(UTC),
                )
            )
            self._apply_settle(run_id)
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return True

    def record_understanding(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        result_snapshot: dict[str, Any],
        candidate_subject: str,
        confidence: float,
        expected_input_revision: int | None = None,
    ) -> int:
        run = self._owned_run(principal, run_id, lock=True, job_side_ok=True)
        self._refuse_purged(run)
        if run["run_state"] != "INPUT_PROCESSING":
            raise ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING")
        if expected_input_revision is not None and not self._drawing_unchanged(
            run, expected_input_revision
        ):
            # T-2b: the result is for a drawing that a retake replaced; discard it. A later input
            # revision that only added an idea or audio keeps the drawing (T-2c), so it counts.
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_STORY_INPUT_REPLACED")
        input_row = self._current_input(run)
        if input_row["original_asset_ref"] is None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_REQUIRED")
        self._check_json_bound(result_snapshot)
        latest_revision = self._session.scalar(
            select(story_tables.understanding_revisions.c.revision_no)
            .where(story_tables.understanding_revisions.c.run_id == run_id)
            .order_by(story_tables.understanding_revisions.c.revision_no.desc())
            .limit(1)
        )
        revision_no = int(latest_revision or 0) + 1
        result_hash = _sha256_json(result_snapshot)
        now = datetime.now(UTC)
        try:
            self._session.execute(
                insert(story_tables.understanding_revisions).values(
                    understanding_revision_id=str(uuid4()),
                    run_id=run_id,
                    run_input_id=input_row["run_input_id"],
                    revision_no=revision_no,
                    subject_label=candidate_subject,
                    confidence=confidence,
                    canonical_result_sha256=result_hash,
                    raw_body_sha256=None,
                    result_snapshot=result_snapshot,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    understanding_revision=revision_no,
                    subject_label=candidate_subject,
                    confidence=confidence,
                    result_sha256=result_hash,
                    raw_body_sha256=None,
                    job_state="SUCCEEDED",
                    error_code=None,
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            # T2C-D6: SUBJECT_REVIEW unless a transcript still waits for the adult.
            self._apply_settle(run_id)
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return revision_no

    def confirm_subject(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
        idempotency_key: str,
        subject_roles: list[dict[str, str]] | None = None,
        rerun_on_edit: bool = False,
        on_story_started: StoryStartedCallback | None = None,
        generator_supports_role: bool = True,
    ) -> SubjectConfirmOutcome | ParentStoryLifecycleRecord:
        """Confirm the subject of the latest understanding (SRS l.1666, FR-P-04 l.513, l.394).

        The subject equal to the suggestion is a plain confirmation: decision ``CONFIRMED``, the
        run moves to ``PREPARATION_REVIEW``. An edited subject with ``rerun_on_edit`` asks for a
        new VLM job on the same drawing (T-2d): decision ``RERUN_REQUESTED``, the run returns to
        ``INPUT_PROCESSING`` with ``job_state QUEUED`` and no review decision is written; the
        runner records revision N+1 and the adult confirms it. Without ``rerun_on_edit`` (DEV-1,
        no composed analyzer) the edit is recorded as revision N+1 and confirmed at once.

        V4-A OPEN-A D1: for a Teacher run the confirmation may be the last gate of the implicit
        first-story start. The start runs after the run UPDATE and before the commit; its
        reservation is handed to ``on_story_started`` after the commit. The receipt body (and so
        the 202 and every replay) carries the command's own ``run_revision``, written before the
        start's extra bump. A Parent never starts here (it has no selection yet).
        """
        run, access = self._owned_run_access(principal, run_id, lock=True, teacher_capable=True)
        operation = "CONFIRM_SUBJECT"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint_inputs: dict[str, Any] = {
            "expected_understanding_revision": expected_understanding_revision,
            "confirmed_subject": confirmed_subject,
        }
        if subject_roles is not None:
            fingerprint_inputs["subject_roles"] = subject_roles
        fingerprint = _sha256_json(fingerprint_inputs)
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            if run["run_state"] in PURGE_STATES:
                # DTR Draft 6 §6.5: a replay of a purged run returns the projection.
                self._session.commit()
                return _projection(run)
            body = replay["response_body"]
            self._session.commit()
            if not isinstance(body, dict) or type(body.get("understanding_revision")) is not int:
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            decision = body.get("decision")
            stored_run_revision = body.get("run_revision")
            return SubjectConfirmOutcome(
                understanding_revision=int(body["understanding_revision"]),
                decision=decision if decision in _SUBJECT_DECISIONS else "CONFIRMED",
                # A receipt written before T-2d holds no run revision: the current one is
                # answered (documented); a new receipt answers the revision it created.
                run_revision=(
                    stored_run_revision
                    if type(stored_run_revision) is int
                    else int(run["revision"])
                ),
                replayed=True,
            )
        self._refuse_read_only_class(access)
        self._refuse_purged(run)
        if run["run_state"] != "SUBJECT_REVIEW":
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        latest = self._latest_understanding(run_id)
        if latest is None or int(latest["revision_no"]) != expected_understanding_revision:
            raise ParentStoryRunError(
                409,
                "STALE_REVISION",
                current_version=int(latest["revision_no"]) if latest is not None else None,
            )
        snapshot = latest["result_snapshot"]
        candidate = snapshot.get("result") if isinstance(snapshot, dict) else None
        if not isinstance(candidate, dict):
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_UNAVAILABLE")
        suggested = str(candidate.get("candidate_subject") or "").strip()
        now = datetime.now(UTC)
        new_version = int(run["version"]) + 1
        new_revision = int(run["revision"]) + 1
        edited = confirmed_subject != suggested
        # T-4b3a D7e (closes T4A1-I-05): a Teacher edit of a PINNED run reruns the VLM on the
        # job-side runner like a Parent edit. A fixture row (no occurrence pin) has no job-side
        # lookup, so it keeps the DEV-1 path: the edit is recorded and confirmed at once.
        if (
            edited
            and rerun_on_edit
            and (not self._is_teacher or run.get("occurrence_ref") is not None)
        ):
            return self._request_subject_rerun(
                principal=principal,
                run=run,
                key_hash=key_hash,
                fingerprint=fingerprint,
                understanding_revision=expected_understanding_revision,
                confirmed_subject=confirmed_subject,
                new_version=new_version,
                new_revision=new_revision,
                now=now,
            )
        target_revision = expected_understanding_revision
        if edited or subject_roles is not None:
            if subject_roles is not None:
                try:
                    corrected = apply_subject_roles(candidate, subject_roles)
                except SubjectRoleError as exc:
                    raise ParentStoryRunError(422, exc.code) from None
                if corrected["candidate_subject"] != confirmed_subject:
                    raise ParentStoryRunError(422, "PARENT_SUBJECT_ROLES_INVALID")
            else:
                corrected = relabel_main_subject(candidate, confirmed_subject)
            updated_snapshot = {"result": corrected}
            result_hash = _sha256_json(updated_snapshot)
            target_revision += 1
            try:
                self._session.execute(
                    insert(story_tables.understanding_revisions).values(
                        understanding_revision_id=str(uuid4()),
                        run_id=run_id,
                        run_input_id=latest["run_input_id"],
                        revision_no=target_revision,
                        subject_label=confirmed_subject,
                        confidence=latest["confidence"],
                        canonical_result_sha256=result_hash,
                        raw_body_sha256=latest["raw_body_sha256"],
                        result_snapshot=updated_snapshot,
                        created_at=now,
                    )
                )
            except SQLAlchemyError:
                self._session.rollback()
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        command_kind, command_ref = self._command_scope(principal)
        try:
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={
                    "decision": "CONFIRMED",
                    "understanding_revision": target_revision,
                    "run_revision": new_revision,
                },
                now=now,
                response_status=202,
            )
            self._session.execute(
                insert(story_tables.review_decisions).values(
                    decision_id=str(uuid4()),
                    run_id=run_id,
                    command_receipt_id=receipt_id,
                    stage="SUBJECT",
                    decision="CONFIRM",
                    actor_scope_kind=command_kind,
                    actor_scope_ref=command_ref,
                    target_understanding_revision=target_revision,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    run_state="PREPARATION_REVIEW",
                    understanding_revision=target_revision,
                    subject_label=confirmed_subject,
                    # The confirmed understanding is the successful analysis: a failed rerun that
                    # left job_state FAILED beside this revision is closed here.
                    job_state="SUCCEEDED",
                    retryable=False,
                    error_code=None,
                    version=new_version,
                    revision=new_revision,
                    updated_at=now,
                )
            )
            reservation = (
                self._first_story_starter().start_if_ready(
                    run_id, principal, now, generator_supports_role=generator_supports_role
                )
                if self._is_teacher
                else None
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_SUBJECT_CONFIRMATION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        if reservation is not None and on_story_started is not None:
            on_story_started(reservation)
        return SubjectConfirmOutcome(
            understanding_revision=target_revision,
            decision="CONFIRMED",
            run_revision=new_revision,
        )

    def _request_subject_rerun(
        self,
        *,
        principal: VerifiedPrincipal,
        run: Mapping[str, Any],
        key_hash: str,
        fingerprint: str,
        understanding_revision: int,
        confirmed_subject: str,
        new_version: int,
        new_revision: int,
        now: datetime,
    ) -> SubjectConfirmOutcome:
        """The edit branch of ``confirm_subject`` (SRS l.394, l.1413): queue a VLM rerun.

        No review decision is written and the understanding stays at the revision the adult
        edited; the adult's subject (at most 160 characters) is kept in the receipt body for the
        runner. The run keeps its active slot.
        """
        run_id = str(run["run_id"])
        try:
            self._store_idempotency_receipt(
                principal=principal,
                operation="CONFIRM_SUBJECT",
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={
                    "decision": "RERUN_REQUESTED",
                    "understanding_revision": understanding_revision,
                    "run_revision": new_revision,
                    "subject_hint": confirmed_subject,
                },
                now=now,
                response_status=202,
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    run_state="INPUT_PROCESSING",
                    job_state="QUEUED",
                    retryable=False,
                    error_code=None,
                    version=new_version,
                    revision=new_revision,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_SUBJECT_CONFIRMATION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return SubjectConfirmOutcome(
            understanding_revision=understanding_revision,
            decision="RERUN_REQUESTED",
            run_revision=new_revision,
            input_revision=int(run["current_input_revision"]),
            organization_id=str(run["actor_scope_ref"]) if self._is_teacher else None,
        )

    def read_subject_rerun_hint(self, *, principal: VerifiedPrincipal, run_id: str) -> str | None:
        """The adult's edited subject while its VLM rerun is pending, else ``None`` (T-2d).

        Pending means: the run waits in ``INPUT_PROCESSING`` and the latest ``RERUN_REQUESTED``
        receipt names the latest understanding revision of the current drawing, so no newer
        revision answered it yet and no retake replaced the drawing. Read-only.
        """
        run = self._owned_run(principal, run_id, job_side_ok=True)
        if run["run_state"] != "INPUT_PROCESSING":
            return None
        latest = self._latest_understanding(run_id)
        if latest is None or not self._same_drawing(
            latest["run_input_id"], self._current_input(run)
        ):
            return None
        table = story_tables.story_command_receipts
        body = self._session.scalar(
            select(table.c.response_body)
            .where(
                table.c.resource_ref == run_id,
                table.c.operation == "CONFIRM_SUBJECT",
                table.c.state == "FINAL",
                table.c.response_body["decision"].astext == "RERUN_REQUESTED",
            )
            .order_by(table.c.created_at.desc())
            .limit(1)
        )
        if (
            not isinstance(body, dict)
            or body.get("understanding_revision") != int(latest["revision_no"])
            or not isinstance(body.get("subject_hint"), str)
        ):
            return None
        return str(body["subject_hint"])

    def _story_generation_basis(
        self,
        *,
        principal: VerifiedPrincipal,
        run: Mapping[str, Any],
        expected_understanding_revision: int,
        subject_error: tuple[int, str],
    ) -> tuple[RowMapping, RowMapping, str, list[str]]:
        """The gates both story routes share: understanding, subject, context, idea, features.

        Returns the latest understanding row, the current input row, the idea text for the worker
        (the typed idea plus the adult-confirmed transcript, T2C-D6) and the visible features.
        ``subject_error`` is the status and code of an unconfirmed subject: the legacy route keeps
        its 409 code, ``story-rewrites`` answers 422 ``SUBJECT_NOT_CONFIRMED`` (SRS l.871).
        """
        run_id = str(run["run_id"])
        understanding = self._latest_understanding(run_id)
        if (
            understanding is None
            or int(understanding["revision_no"]) != expected_understanding_revision
            or int(run["understanding_revision"] or 0) != expected_understanding_revision
        ):
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE")
        decisions = story_tables.review_decisions
        # T-4b3a D7c (OPEN-5): for a Teacher run the step actor is "Actor của run" (l.1666,
        # l.1668), not one person: a SUBJECT decision of ANY Teacher command scope of the run
        # counts, so an assignment change cannot strand the run. A Parent still needs its own.
        decider = (
            decisions.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND
            if self._is_teacher
            else decisions.c.actor_scope_ref == _principal_scope_ref(principal)
        )
        subject_decision = self._session.scalar(
            select(decisions.c.decision_id).where(
                decisions.c.run_id == run_id,
                decisions.c.stage == "SUBJECT",
                decisions.c.decision == "CONFIRM",
                decider,
                decisions.c.target_understanding_revision == expected_understanding_revision,
            )
        )
        if subject_decision is None:
            raise ParentStoryRunError(*subject_error)
        input_row = self._current_input(run)
        if input_row["context_confirmed_by"] is None or input_row["context_confirmed_at"] is None:
            raise ParentStoryRunError(422, "PROFILE_CONTEXT_NOT_CONFIRMED")
        if input_row["original_sha256"] is None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_REQUIRED")
        # T2C-D6: a voice idea reaches the worker only as the adult-confirmed transcript text.
        idea_text = self._idea_for_story(run_id, input_row)
        candidate_snapshot = understanding["result_snapshot"]
        candidate = (
            candidate_snapshot.get("result") if isinstance(candidate_snapshot, dict) else None
        )
        raw_features = candidate.get("visible_features") if isinstance(candidate, dict) else None
        if not isinstance(raw_features, list):
            raw_features = []
        visible_features = [
            str(value).strip()[:160] for value in raw_features[:4] if str(value).strip()
        ]
        if not visible_features:
            raise ParentStoryRunError(409, "PARENT_VISIBLE_FEATURES_UNAVAILABLE")
        return understanding, input_row, idea_text, visible_features

    def reserve_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        idempotency_key: str,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
        require_activity_selection: bool = False,
    ) -> ParentStoryRevisionReservation:
        run = self._owned_run(principal, run_id, lock=True)
        operation = "GENERATE_STORY_REVISION"
        scope_kind = "STORY_RUN"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_understanding_revision": expected_understanding_revision,
                "rewrite_instruction": rewrite_instruction,
                "model_id": model_id,
                "model_revision": model_revision,
                "prompt_version": prompt_version,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None and run["run_state"] in PURGE_STATES:
            # DTR Draft 6 §6.5 / S18: the replay branch of a purged run returns only the
            # projection; nothing of the stored story body is rebuilt.
            self._session.commit()
            return ParentStoryRevisionReservation(
                run_id=run_id,
                story_revision_id=str(replay["receipt_id"]),
                revision_no=0,
                understanding_revision=0,
                context_revision=0,
                source_asset_sha256="",
                worker_input={},
                request_sha256=fingerprint,
                receipt_id=str(replay["receipt_id"]),
                replayed=True,
                replay_body=None,
                lifecycle=_projection(run),
            )
        if replay is not None:
            if replay["state"] == "PENDING":
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            replay_body = replay["response_body"]
            if not isinstance(replay_body, dict):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            replay_error = replay_body.get("error_code")
            if isinstance(replay_error, str):
                replay_status = replay["response_status"]
                if type(replay_status) is not int or replay_status not in {502, 504}:
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                raise ParentStoryRunError(replay_status, replay_error)
            try:
                replay_reservation = ParentStoryRevisionReservation(
                    run_id=run_id,
                    story_revision_id=str(replay_body["story_revision_id"]),
                    revision_no=int(replay_body["revision_no"]),
                    understanding_revision=int(replay_body["understanding_revision"]),
                    context_revision=int(replay_body["context_revision"]),
                    source_asset_sha256=str(replay_body["source_asset_sha256"]),
                    worker_input={},
                    request_sha256=fingerprint,
                    receipt_id=str(replay["receipt_id"]),
                    replayed=True,
                    replay_body=replay_body,
                )
            except (KeyError, TypeError, ValueError):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
            self._session.commit()
            return replay_reservation

        self._refuse_purged(run)
        if run["run_state"] not in {"PREPARATION_REVIEW", "SCRIPT_REVIEW"}:
            raise ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT")
        if (
            require_activity_selection
            and run["run_state"] == "PREPARATION_REVIEW"
            and latest_selection_row(self._session, run_id, int(run["understanding_revision"] or 0))
            is None
        ):
            # T-2e-a D9: the legacy first-story route needs the adult's main activity first (only
            # the route asks; repository callers without the flag are unchanged).
            raise ParentStoryRunError(409, "PARENT_ACTIVITY_SELECTION_REQUIRED")
        understanding, input_row, idea_text, visible_features = self._story_generation_basis(
            principal=principal,
            run=run,
            expected_understanding_revision=expected_understanding_revision,
            subject_error=(409, "PARENT_SUBJECT_CONFIRMATION_REQUIRED"),
        )
        context = input_row["context_snapshot"]

        revisions = (
            self._session.execute(
                select(story_tables.story_revisions)
                .where(story_tables.story_revisions.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no.desc())
            )
            .mappings()
            .all()
        )
        latest_story = revisions[0] if revisions else None
        if len(revisions) >= 4:
            raise ParentStoryRunError(409, "STORY_REWRITE_LIMIT_REACHED")
        if latest_story is None and rewrite_instruction is not None:
            raise ParentStoryRunError(409, "PARENT_INITIAL_STORY_CANNOT_BE_REWRITE")
        if latest_story is not None and (
            rewrite_instruction is None or latest_story["status"] not in {"DRAFT", "FAILED"}
        ):
            raise ParentStoryRunError(409, "PARENT_STORY_REWRITE_NOT_ALLOWED")

        # FEAT-092: the Modal story client and worker validate input v3 (topic, lesson notes and the
        # adult's main activity); the v1 object built here made every story fail validation.
        selection_row = latest_selection_row(
            self._session, run_id, int(run["understanding_revision"] or 0)
        )
        if selection_row is None:
            raise ParentStoryRunError(409, "PARENT_ACTIVITY_SELECTION_REQUIRED")
        primary_activity = _story_primary_activity(selection_row["activity_snapshot"])
        primary_activity_hash = _sha256_json(primary_activity)
        topic = context.get("topic", "")
        if not isinstance(topic, str) or len(topic) > 120:
            raise ParentStoryRunError(409, "PARENT_CONTEXT_INVALID")
        lesson_pin = input_row.get("lesson_pin_snapshot")
        lesson_subject_learning_notes: str | None = None
        lesson_direction: str | None = None
        if lesson_pin is not None:
            if not isinstance(lesson_pin, dict):
                raise ParentStoryRunError(409, "PARENT_LESSON_PIN_INVALID")
            notes = lesson_pin.get("subject_learning_notes")
            direction = lesson_pin.get("script_direction")
            follows_script = lesson_pin.get("script_following_allowed")
            if not isinstance(notes, str) or not 1 <= len(notes) <= 5000:
                raise ParentStoryRunError(409, "PARENT_LESSON_PIN_INVALID")
            if direction is not None and (not isinstance(direction, str) or len(direction) > 2000):
                raise ParentStoryRunError(409, "PARENT_LESSON_PIN_INVALID")
            lesson_subject_learning_notes = notes
            if follows_script is True and isinstance(direction, str) and direction.strip():
                lesson_direction = direction
        worker_input = {
            "schema_version": "sketch2life.story-generation-input.v3",
            "role": "PARENT",
            "language": "vi",
            "topic": topic,
            "confirmed_subject": str(run["subject_label"] or "").strip(),
            "understanding_revision": expected_understanding_revision,
            "drawing_sha256": str(input_row["original_sha256"]),
            "visible_features": visible_features,
            "child_age_months": int(context["age_months"]),
            "context_revision": int(input_row["context_revision"]),
            "adult_confirmed_idea": idea_text,
            "rewrite_instruction": rewrite_instruction,
            "lesson_subject_learning_notes": lesson_subject_learning_notes,
            "lesson_direction": lesson_direction,
            "primary_activity": primary_activity,
            "primary_activity_sha256": primary_activity_hash,
        }
        snapshot = understanding["result_snapshot"]
        candidate = snapshot.get("result") if isinstance(snapshot, dict) else None
        _main_subject, approved_secondaries = (
            approved_subjects(candidate) if isinstance(candidate, dict) else ({}, [])
        )
        if approved_secondaries:
            worker_input["secondary_subjects"] = [
                {
                    "entity_id": item["entity_id"],
                    "label": item["label"],
                    "visible_features": list(item.get("visible_features") or []),
                }
                for item in approved_secondaries
            ]
        request_hash = _sha256_json(worker_input)
        revision_no = int(latest_story["revision_no"]) + 1 if latest_story is not None else 1
        now = datetime.now(UTC)
        new_version = int(run["version"]) + 1
        try:
            receipt_id = self._store_pending_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind=scope_kind,
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                now=now,
            )
            if latest_story is not None and latest_story["status"] == "DRAFT":
                self._session.execute(
                    update(story_tables.story_revisions)
                    .where(
                        story_tables.story_revisions.c.story_revision_id
                        == latest_story["story_revision_id"]
                    )
                    .values(status="SUPERSEDED")
                )
            self._session.execute(
                insert(story_tables.story_revisions).values(
                    story_revision_id=story_revision_id,
                    run_id=run_id,
                    revision_no=revision_no,
                    status="GENERATING",
                    source_asset_sha256=str(input_row["original_sha256"]),
                    understanding_revision=expected_understanding_revision,
                    context_revision=int(input_row["context_revision"]),
                    schema_version="sketch2life.story-revision.v1",
                    prompt_version=prompt_version,
                    model_id=model_id,
                    model_revision=model_revision,
                    request_sha256=request_hash,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    run_state="SCRIPT_GENERATING",
                    job_state="RUNNING",
                    retryable=False,
                    error_code=None,
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return ParentStoryRevisionReservation(
            run_id=run_id,
            story_revision_id=story_revision_id,
            revision_no=revision_no,
            understanding_revision=expected_understanding_revision,
            context_revision=int(input_row["context_revision"]),
            source_asset_sha256=str(input_row["original_sha256"]),
            worker_input=worker_input,
            request_sha256=request_hash,
            receipt_id=receipt_id,
        )

    def _has_spent_video(self, run_id: str, story_revision_id: str) -> bool:
        """``True`` when a video generation that gave no playable video sits on any review of this
        revision (the rewrite door, V4-A T-1b-fix D7).

        T-1b: ``REJECTED_BY_ADULT`` (marked unsuitable). T-1d1-fix DEV-3: ``FAILED`` as well (the
        generation deadline closed it and the run returned to the script review, BR-11 l.255,
        l.2120). T-1b-fix: ``SAFETY_BLOCKED`` as well, and the question is per revision, not per
        review: an adult who confirmed the story again (a fresh, unspent review) can still
        rewrite. The run is in ``SCRIPT_REVIEW`` when this is asked, so no video is in flight.
        """

        table = story_tables.video_generations
        by_review: dict[str, list[str]] = {}
        for review_id, state in self._session.execute(
            select(table.c.story_review_id, table.c.state).where(
                table.c.story_run_id == run_id,
                table.c.story_revision_id == story_revision_id,
            )
        ):
            by_review.setdefault(str(review_id), []).append(str(state))
        return revision_has_spent_video(by_review.values())

    def reserve_story_rewrite(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        expected_story_revision: int,
        expected_story_sha256: str | None,
        hint: str | None,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
        instruction_version: str,
        instruction: str,
    ) -> StoryRewriteOutcome:
        """Accept one story rewrite (SRS l.1668, FR-P-07 l.516, l.866, l.1697-1699).

        Order of checks under the run lock: the idempotency replay (also while the run is still
        ``SCRIPT_GENERATING``), a purged run, the run state, the rewrite limit, the stale
        revision or hash, then the gates the first story needs (subject, context, transcript).
        The receipt is final in the reservation transaction (status 202), so a replay never meets
        a pending receipt and completing or failing the generation touches no receipt.
        """
        run, access = self._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True, pinned=True
        )
        operation = "GENERATE_STORY_REVISION"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "kind": "STORY_REWRITE_V1",
                "expected_story_revision": expected_story_revision,
                "expected_story_sha256": expected_story_sha256,
                "hint": hint,
                "instruction_version": instruction_version,
                "model_id": model_id,
                "model_revision": model_revision,
                "prompt_version": prompt_version,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            if run["run_state"] in PURGE_STATES:
                # DTR Draft 6 §6.5: the replay of a purged run returns only the projection.
                self._session.commit()
                return StoryRewriteOutcome(
                    story_revision_no=0,
                    run_revision=int(run["revision"]),
                    run_state=str(run["run_state"]),
                    replayed=True,
                    lifecycle=_projection(run),
                )
            body = replay["response_body"]
            self._session.commit()
            if (
                not isinstance(body, dict)
                or type(body.get("story_revision_no")) is not int
                or type(body.get("run_revision")) is not int
                or not isinstance(body.get("run_state"), str)
            ):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            return StoryRewriteOutcome(
                story_revision_no=int(body["story_revision_no"]),
                run_revision=int(body["run_revision"]),
                run_state=str(body["run_state"]),
                replayed=True,
            )

        self._refuse_read_only_class(access)
        self._refuse_purged(run)
        if run["run_state"] not in REVIEWABLE_RUN_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        revisions = (
            self._session.execute(
                select(story_tables.story_revisions)
                .where(story_tables.story_revisions.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no.desc())
            )
            .mappings()
            .all()
        )
        latest_story = revisions[0] if revisions else None
        if latest_story is None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        # T-1b (SRS l.416, BR-16 l.260): an AI rewrite "including after a video is marked
        # unsuitable" makes a new revision. Then the latest revision is still ``CONFIRMED`` and its
        # review is consumed by a ``REJECTED_BY_ADULT`` generation (T-1d1-fix: or by one the
        # deadline ended ``FAILED``). A confirmed revision without such a generation stays refused
        # (the run is in ``SCRIPT_REVIEW`` here, so no video can be in flight).
        after_spent_video = latest_story["status"] == "CONFIRMED" and self._has_spent_video(
            run_id, str(latest_story["story_revision_id"])
        )
        if latest_story["status"] not in {"DRAFT", "FAILED"} and not after_spent_video:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if len(revisions) >= 4 or (
            # T-2d-fix D2 (OPEN Q1, reading B): a technically failed attempt gives its slot back,
            # up to three attempts per slot; the fourth is refused with the same code (l.866). The
            # client reads ``retryable false`` plus this code as "confirm or cancel" (l.1728).
            self._rewrite_attempts_used(
                run, _principal_scope_ref(principal), int(latest_story["revision_no"]) + 1
            )
            >= REWRITE_ATTEMPTS_PER_SLOT
        ):
            # The first story plus three rewrites (FR-P-07): the client learns the real reason
            # before any stale comparison.
            raise ParentStoryRunError(409, "STORY_REWRITE_LIMIT_REACHED")
        if int(latest_story["revision_no"]) != expected_story_revision or (
            expected_story_sha256 is not None
            and not hmac.compare_digest(
                str(latest_story["story_sha256"] or ""), expected_story_sha256
            )
        ):
            raise ParentStoryRunError(
                409, "STALE_REVISION", current_version=int(latest_story["revision_no"])
            )
        understanding_revision = int(run["understanding_revision"] or 0)
        understanding, input_row, idea_text, visible_features = self._story_generation_basis(
            principal=principal,
            run=run,
            expected_understanding_revision=understanding_revision,
            subject_error=(422, "SUBJECT_NOT_CONFIRMED"),
        )
        context = input_row["context_snapshot"]
        worker_input = {
            "schema_version": "sketch2life.story-rewrite-input.v1",
            "role": "TEACHER" if self._is_teacher else "PARENT",
            "language": "vi",
            "confirmed_subject": str(run["subject_label"] or "").strip(),
            "understanding_revision": understanding_revision,
            "drawing_sha256": str(input_row["original_sha256"]),
            "visible_features": visible_features,
            "child_age_months": int(context["age_months"]),
            "context_revision": int(input_row["context_revision"]),
            "adult_confirmed_idea": idea_text,
            # The instruction is a server constant; the adult's hint is data in its own field.
            "rewrite_instruction": instruction,
            "rewrite_instruction_version": instruction_version,
            "adult_rewrite_hint": hint,
            # T-4b3a D7b: a Teacher run carries a bounded direction taken from its own context
            # snapshot (no name, no media); a Parent run carries none, as ever.
            "lesson_direction": (teacher_lesson_direction(context) if self._is_teacher else None),
        }
        snapshot = understanding["result_snapshot"]
        candidate = snapshot.get("result") if isinstance(snapshot, dict) else None
        _main_subject, approved_secondaries = (
            approved_subjects(candidate) if isinstance(candidate, dict) else ({}, [])
        )
        if approved_secondaries:
            worker_input["secondary_subjects"] = [
                {
                    "entity_id": item["entity_id"],
                    "label": item["label"],
                    "visible_features": list(item.get("visible_features") or []),
                }
                for item in approved_secondaries
            ]
        request_hash = _sha256_json(worker_input)
        revision_no = int(latest_story["revision_no"]) + 1
        now = datetime.now(UTC)
        new_version = int(run["version"]) + 1
        new_revision = int(run["revision"]) + 1
        try:
            self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={
                    "story_revision_no": revision_no,
                    "story_revision_id": story_revision_id,
                    "run_revision": new_revision,
                    "run_state": "SCRIPT_GENERATING",
                },
                now=now,
                response_status=202,
            )
            # T-2d-fix D3: the previous revision is superseded when the new one completes, so a
            # failed attempt only deletes its own row and the story tree stays as it was.
            self._session.execute(
                insert(story_tables.story_revisions).values(
                    story_revision_id=story_revision_id,
                    run_id=run_id,
                    revision_no=revision_no,
                    status="GENERATING",
                    source_asset_sha256=str(input_row["original_sha256"]),
                    understanding_revision=understanding_revision,
                    context_revision=int(input_row["context_revision"]),
                    schema_version="sketch2life.story-revision.v1",
                    prompt_version=prompt_version,
                    model_id=model_id,
                    model_revision=model_revision,
                    request_sha256=request_hash,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    run_state="SCRIPT_GENERATING",
                    job_state="QUEUED",
                    retryable=False,
                    error_code=None,
                    version=new_version,
                    revision=new_revision,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return StoryRewriteOutcome(
            story_revision_no=revision_no,
            run_revision=new_revision,
            run_state="SCRIPT_GENERATING",
            reservation=ParentStoryRevisionReservation(
                run_id=run_id,
                story_revision_id=story_revision_id,
                revision_no=revision_no,
                understanding_revision=understanding_revision,
                context_revision=int(input_row["context_revision"]),
                source_asset_sha256=str(input_row["original_sha256"]),
                worker_input=worker_input,
                request_sha256=request_hash,
                receipt_id=None,
                organization_id=str(run["actor_scope_ref"]) if self._is_teacher else None,
            ),
        )

    def start_story_generation(
        self, *, principal: VerifiedPrincipal, run_id: str, story_revision_id: str
    ) -> bool:
        """QUEUED -> RUNNING for the reserved revision; ``False`` when the work is stale (T-2d)."""
        run = self._owned_run(principal, run_id, lock=True, job_side_ok=True)
        reserved = self._session.scalar(
            select(story_tables.story_revisions.c.story_revision_id).where(
                story_tables.story_revisions.c.story_revision_id == story_revision_id,
                story_tables.story_revisions.c.run_id == run_id,
                story_tables.story_revisions.c.status == "GENERATING",
            )
        )
        if (
            run["run_state"] != "SCRIPT_GENERATING"
            or run["job_state"] != "QUEUED"
            or reserved is None
        ):
            self._session.rollback()
            return False
        try:
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    job_state="RUNNING",
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=datetime.now(UTC),
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return True

    def complete_story_revision(
        self,
        *,
        reservation: ParentStoryRevisionReservation,
        principal: VerifiedPrincipal,
        story: dict[str, Any],
        story_sha256: str,
        provider_call_id: str,
        model_id: str,
        model_revision: str,
        staging: dict[str, Any] | None = None,
        staging_issue: str | None = None,
    ) -> ParentStoryRunView:
        run = self._owned_run(principal, reservation.run_id, lock=True, job_side_ok=True)
        if run["run_state"] in PURGE_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if run["run_state"] != "SCRIPT_GENERATING":
            # T-2d-fix: a late result after the reaper or a new attempt changes nothing.
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        revision_id = self._session.scalar(
            select(story_tables.story_revisions.c.story_revision_id).where(
                story_tables.story_revisions.c.story_revision_id == reservation.story_revision_id,
                story_tables.story_revisions.c.run_id == reservation.run_id,
                story_tables.story_revisions.c.status == "GENERATING",
            )
        )
        if revision_id is None:
            raise ParentStoryRunError(409, "PARENT_STORY_REVISION_NOT_GENERATING")
        now = datetime.now(UTC)
        sections = story["story"]
        new_version = int(run["version"]) + 1
        try:
            self._session.execute(
                update(story_tables.story_revisions)
                .where(
                    story_tables.story_revisions.c.story_revision_id
                    == reservation.story_revision_id
                )
                .values(
                    status="DRAFT",
                    story_sha256=story_sha256,
                    language=story["language"],
                    title=story["title"],
                    duration_ms=story["duration_ms"],
                    story_content=pack_story_content(sections, staging, staging_issue),
                    model_id=model_id,
                    model_revision=model_revision,
                    provider_call_id=provider_call_id,
                )
            )
            if reservation.receipt_id is None and reservation.revision_no >= 2:
                # T-2d-fix D3: the rewrite route supersedes the previous story only now, so a
                # failed attempt leaves it untouched. Compare-and-set: the previous revision must
                # still be the reviewable one (``DRAFT``, or ``CONFIRMED`` after a rejected video).
                superseded = cast(
                    CursorResult[Any],
                    self._session.execute(
                        update(story_tables.story_revisions)
                        .where(
                            story_tables.story_revisions.c.run_id == reservation.run_id,
                            story_tables.story_revisions.c.revision_no
                            == reservation.revision_no - 1,
                            story_tables.story_revisions.c.status.in_(("DRAFT", "CONFIRMED")),
                        )
                        .values(status="SUPERSEDED")
                    ),
                )
                if superseded.rowcount != 1:
                    self._session.rollback()
                    raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            for scene in story["scenes"]:
                self._session.execute(
                    insert(story_tables.story_scenes).values(
                        scene_id=str(uuid4()),
                        story_revision_id=reservation.story_revision_id,
                        scene_index=scene["scene_index"],
                        title=scene["title"],
                        action=scene["action"],
                        visual_prompt=scene["visual_prompt"],
                        narration=scene["narration"],
                        start_ms=scene["start_ms"],
                        duration_ms=scene["duration_ms"],
                        character_anchors=scene["character_anchors"],
                    )
                )
            run_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_runs)
                    .where(_live_run(reservation.run_id))
                    .values(
                        run_state="SCRIPT_REVIEW",
                        job_state="SUCCEEDED",
                        retryable=False,
                        result_sha256=story_sha256,
                        error_code=None,
                        version=new_version,
                        revision=story_tables.story_runs.c.revision + 1,
                        updated_at=now,
                    )
                ),
            )
            if run_update.rowcount != 1:
                self._session.rollback()
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            if reservation.receipt_id is not None:
                # The rewrite route's receipt is final at reservation (T-2d): nothing to update.
                receipt_update = cast(
                    CursorResult[Any],
                    self._session.execute(
                        update(story_tables.story_command_receipts)
                        .where(
                            story_tables.story_command_receipts.c.receipt_id
                            == reservation.receipt_id,
                            story_tables.story_command_receipts.c.state == "PENDING",
                        )
                        .values(
                            state="FINAL",
                            response_status=200,
                            response_resource_version=new_version,
                            response_body={
                                "story_revision_id": reservation.story_revision_id,
                                "revision_no": reservation.revision_no,
                                "understanding_revision": reservation.understanding_revision,
                                "context_revision": reservation.context_revision,
                                "source_asset_sha256": reservation.source_asset_sha256,
                                "story_sha256": story_sha256,
                                "modal_call_id": provider_call_id,
                                "model_id": model_id,
                                "model_revision": model_revision,
                            },
                            resource_ref=reservation.run_id,
                            resource_version=new_version,
                            state_version=story_tables.story_command_receipts.c.state_version + 1,
                            finalized_at=now,
                        )
                    ),
                )
                if receipt_update.rowcount != 1:
                    self._session.rollback()
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
        except ParentStoryRunError:
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        if self._job_side:
            # T-4b3a: the job-side repository cannot call ``get_run`` (it is not a job-side method)
            return self._read_run_view(principal, reservation.run_id, job_side_ok=True)
        return self.get_run(principal=principal, run_id=reservation.run_id)

    def fail_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentStoryRevisionReservation,
        error_code: str,
        outcome_unknown: bool,
    ) -> None:
        """Record a failed generation (SRS l.394, l.1413; T-2d-fix D1).

        A compare-and-set under the run lock: the run must still be ``SCRIPT_GENERATING`` and the
        reserved revision still ``GENERATING``; otherwise (the reaper already settled it, the run
        was cancelled, a new attempt started) nothing changes and the answer is 409
        ``INVALID_STATE_TRANSITION``, which the runner treats as discarded work. A known failure of
        a rewrite returns the run to the previous reviewable story; a known failure of a first
        story (or of the legacy route) ends the run; an unknown outcome waits for reconciliation.
        """

        run = self._owned_run(principal, reservation.run_id, lock=True, job_side_ok=True)
        if run["run_state"] in PURGE_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if run["run_state"] != "SCRIPT_GENERATING":
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        now = datetime.now(UTC)
        is_rewrite = reservation.receipt_id is None and reservation.revision_no >= 2
        try:
            if is_rewrite and not outcome_unknown:
                self.recover_failed_rewrite(
                    run=run,
                    story_revision_id=reservation.story_revision_id,
                    revision_no=reservation.revision_no,
                    error_code=error_code,
                    now=now,
                    actor_ref=_principal_scope_ref(principal),
                )
            else:
                self._fail_generating_revision(
                    run=run,
                    reservation=reservation,
                    error_code=error_code,
                    outcome_unknown=outcome_unknown,
                    now=now,
                )
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def _fail_generating_revision(
        self,
        *,
        run: Mapping[str, Any],
        reservation: ParentStoryRevisionReservation,
        error_code: str,
        outcome_unknown: bool,
        now: datetime,
    ) -> None:
        """The run-ending (or reconciliation) write of ``fail_story_revision``; no commit."""

        revision_state = "AWAITING_RECONCILIATION" if outcome_unknown else "FAILED"
        run_state = "SCRIPT_GENERATION_UNKNOWN" if outcome_unknown else "FAILED"
        job_state = "AWAITING_RECONCILIATION" if outcome_unknown else "FAILED"
        new_version = int(run["version"]) + 1
        # ``story_revisions`` has no ``updated_at`` column: writing it made every failure write
        # raise (the run then stayed in SCRIPT_GENERATING), found by the T-2d failure tests.
        revision_update = cast(
            CursorResult[Any],
            self._session.execute(
                update(story_tables.story_revisions)
                .where(
                    story_tables.story_revisions.c.story_revision_id
                    == reservation.story_revision_id,
                    story_tables.story_revisions.c.run_id == reservation.run_id,
                    story_tables.story_revisions.c.status == "GENERATING",
                )
                .values(status=revision_state)
            ),
        )
        if revision_update.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        terminal: dict[str, Any] = (
            {} if outcome_unknown else {"finished_at": now, "adult_wait_started_at": None}
        )
        run_update = cast(
            CursorResult[Any],
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(reservation.run_id))
                .values(
                    run_state=run_state,
                    job_state=job_state,
                    retryable=False,
                    error_code=error_code,
                    active_owner_parent_account_id=(
                        run["active_owner_parent_account_id"] if outcome_unknown else None
                    ),
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                    **terminal,
                )
            ),
        )
        if run_update.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if reservation.receipt_id is not None:
            # The rewrite route's receipt is final at reservation (T-2d): nothing to update.
            receipt_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_command_receipts)
                    .where(
                        story_tables.story_command_receipts.c.receipt_id == reservation.receipt_id,
                        story_tables.story_command_receipts.c.state == "PENDING",
                    )
                    .values(
                        state="FINAL",
                        response_status=504 if outcome_unknown else 502,
                        response_resource_version=new_version,
                        response_body={"error_code": error_code},
                        resource_ref=reservation.run_id,
                        resource_version=new_version,
                        state_version=story_tables.story_command_receipts.c.state_version + 1,
                        finalized_at=now,
                    )
                ),
            )
            if receipt_update.rowcount != 1:
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")

    def _rewrite_attempts_used(
        self, run: Mapping[Any, Any], parent_scope_ref: str, revision_no: int
    ) -> int:
        """Accepted rewrite requests of one slot (T-2d-fix D2): FINAL 202 receipts of this run.

        A receipt is stored final at reservation (T-2d) and never pruned during a run, so the count
        survives the deletion of a failed attempt's revision row. The legacy route's receipts carry
        no ``story_revision_no`` (and no 202) and never match. A Parent run counts the receipts of
        its owner scope; a Teacher run counts them by kind, whoever gave the command (T-4b3a D7d:
        the slot limit follows the run, not the person, l.516, l.551, l.1413).
        """

        run_id = str(run["run_id"])
        receipts = story_tables.story_command_receipts
        if run.get("actor_scope_kind") == TEACHER_COMMAND_SCOPE_KIND:
            owner: tuple[Any, ...] = (receipts.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND,)
        else:
            owner = (
                receipts.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                receipts.c.actor_scope_ref == parent_scope_ref,
            )
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(receipts)
                .where(
                    *owner,
                    receipts.c.operation == "GENERATE_STORY_REVISION",
                    receipts.c.idempotency_scope_kind == "STORY_RUN",
                    receipts.c.idempotency_scope_ref == run_id,
                    receipts.c.state == "FINAL",
                    receipts.c.response_status == 202,
                    receipts.c.response_body["story_revision_no"].astext == str(revision_no),
                )
            )
            or 0
        )

    def recover_failed_rewrite(
        self,
        *,
        run: Mapping[Any, Any],
        story_revision_id: str,
        revision_no: int,
        error_code: str,
        now: datetime,
        actor_ref: str,
    ) -> None:
        """A rewrite attempt failed technically: back to the previous reviewable story (D1, D3).

        ``run`` is the row read ``FOR UPDATE`` by the caller (the runner path or the reaper); no
        commit here. Every step is a compare-and-set: the failed attempt's own row (``GENERATING``
        or ``AWAITING_RECONCILIATION``, no content, no children) is deleted, the run leaves
        ``SCRIPT_GENERATING``/``SCRIPT_GENERATION_UNKNOWN`` for ``SCRIPT_REVIEW`` with job
        ``FAILED``, a safe code and ``retryable`` while the slot has attempts left, the Parent lock
        is kept and ``updated_at`` starts the adult wait. The previous revision was never touched
        (it is superseded only when a later attempt completes). A missed compare-and-set raises 409
        ``INVALID_STATE_TRANSITION`` and the caller rolls back.
        """

        run_id = str(run["run_id"])
        deleted = cast(
            CursorResult[Any],
            self._session.execute(
                delete(story_tables.story_revisions).where(
                    story_tables.story_revisions.c.story_revision_id == story_revision_id,
                    story_tables.story_revisions.c.run_id == run_id,
                    story_tables.story_revisions.c.status.in_(
                        ("GENERATING", "AWAITING_RECONCILIATION")
                    ),
                )
            ),
        )
        if deleted.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        attempts = self._rewrite_attempts_used(run, str(run["actor_scope_ref"]), revision_no)
        updated = cast(
            CursorResult[Any],
            self._session.execute(
                update(story_tables.story_runs)
                .where(
                    _live_run(run_id),
                    story_tables.story_runs.c.run_state.in_(
                        ("SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN")
                    ),
                    story_tables.story_runs.c.revision == run["revision"],
                )
                .values(
                    run_state="SCRIPT_REVIEW",
                    job_state="FAILED",
                    retryable=attempts < REWRITE_ATTEMPTS_PER_SLOT,
                    error_code=error_code,
                    version=int(run["version"]) + 1,
                    revision=int(run["revision"]) + 1,
                    updated_at=now,
                )
            ),
        )
        if updated.rowcount != 1:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        write_story_task_audit(
            self._session,
            actor_ref=actor_ref,
            action=AUDIT_REWRITE_ATTEMPT_FAILED,
            run_id=run_id,
            decision=error_code,
            run_revision=int(run["revision"]) + 1,
            now=now,
            **story_task_audit_scope(run),
        )

    def settle_run_state(self, run_id: str) -> str:
        """``_apply_settle`` for the reaper store: inside its transaction, under the run lock."""

        return self._apply_settle(run_id)

    def fail_drawing_analysis(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        error_code: str,
        outcome_unknown: bool,
        expected_input_revision: int | None = None,
    ) -> None:
        """Record a failed drawing analysis that ends the run, or an unknown outcome (l.398).

        With ``expected_input_revision`` (the background runner; T-2d-fix D1) the write is a
        compare-and-set: the run must still be ``INPUT_PROCESSING`` with an analysis in flight for
        that drawing, otherwise the reaper or a retake already settled it and the answer is 409
        ``INVALID_STATE_TRANSITION`` (discarded work). Without it (the legacy synchronous route,
        whose caller waits for the answer) the earlier unconditional behaviour is kept.
        """
        run = self._owned_run(principal, run_id, lock=True, job_side_ok=True)
        if run["run_state"] in PURGE_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if expected_input_revision is not None and (
            run["run_state"] != "INPUT_PROCESSING"
            or run["job_state"] not in _VLM_IN_FLIGHT
            or not self._drawing_unchanged(run, expected_input_revision)
        ):
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        now = datetime.now(UTC)
        terminal: dict[str, Any] = (
            {} if outcome_unknown else {"finished_at": now, "adult_wait_started_at": None}
        )
        try:
            run_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_runs)
                    .where(_live_run(run_id))
                    .values(
                        run_state="INPUT_PROCESSING" if outcome_unknown else "FAILED",
                        job_state="AWAITING_RECONCILIATION" if outcome_unknown else "FAILED",
                        retryable=False,
                        error_code=error_code,
                        active_owner_parent_account_id=(
                            run["active_owner_parent_account_id"] if outcome_unknown else None
                        ),
                        version=story_tables.story_runs.c.version + 1,
                        revision=story_tables.story_runs.c.revision + 1,
                        updated_at=now,
                        **terminal,
                    )
                ),
            )
            if run_update.rowcount != 1:
                self._session.rollback()
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def _accepted_video_count(self, run_id: str) -> int:
        """Accepted video requests of the run (a request that got a generation number)."""

        table = story_tables.video_generations
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(table)
                .where(table.c.story_run_id == run_id, table.c.generation_no.is_not(None))
            )
            or 0
        )

    def _latest_review(self, run_id: str, story_revision_id: str) -> RowMapping | None:
        """The review of the revision with the highest epoch (V4-A T-1b-fix D4)."""

        reviews = story_tables.story_revision_reviews
        return (
            self._session.execute(
                select(reviews.c.review_id, reviews.c.review_epoch)
                .where(reviews.c.run_id == run_id, reviews.c.story_revision_id == story_revision_id)
                .order_by(reviews.c.review_epoch.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )

    def _review_states(self, review_id: str) -> list[str]:
        table = story_tables.video_generations
        return [
            str(state)
            for state in self._session.scalars(
                select(table.c.state).where(table.c.story_review_id == review_id)
            )
        ]

    def _story_confirmation_required(
        self, run: RowMapping, latest_story: RowMapping | None
    ) -> bool:
        """``story_confirmation_required`` of the run envelope (V4-A T-1b-fix D8): reads the
        LATEST review of the latest revision only, never the current generation."""

        if latest_story is None or str(run["run_state"]) not in REVIEWABLE_RUN_STATES:
            return False
        if self._accepted_video_count(str(run["run_id"])) >= MAX_ACCEPTED_REQUESTS:
            # V4-A SAFETY_BLOCKED exit D3b: with the request cap spent a confirmation can lead to
            # no video (the confirm and the request both answer VIDEO_REGENERATION_LIMIT_REACHED),
            # so the client is not asked for one; the way on is to stop the run.
            return False
        spent = False
        if latest_story["status"] == "CONFIRMED":
            review = self._latest_review(str(run["run_id"]), str(latest_story["story_revision_id"]))
            spent = review is not None and review_is_spent(
                self._review_states(str(review["review_id"]))
            )
        return story_confirmation_required(
            run_state=str(run["run_state"]),
            story_status=str(latest_story["status"]),
            latest_review_spent=spent,
            reviewable_run_states=REVIEWABLE_RUN_STATES,
        )

    def _confirmable_revision(
        self, run: RowMapping, expected_revision: int, expected_story_sha256: str
    ) -> tuple[RowMapping, int]:
        """The refusal matrix of ``script-confirmation`` (V4-A T-1b-fix D12): the latest story
        revision and the review epoch the confirmation writes (1 for a ``DRAFT``, the next epoch
        for a ``CONFIRMED`` revision whose latest review is spent)."""

        run_id = str(run["run_id"])
        if run["run_state"] not in REVIEWABLE_RUN_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        latest = (
            self._session.execute(
                select(story_tables.story_revisions)
                .where(story_tables.story_revisions.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        if latest is None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        current = int(latest["revision_no"])
        if current != expected_revision or not hmac.compare_digest(
            str(latest["story_sha256"] or ""), expected_story_sha256
        ):
            raise ParentStoryRunError(409, "STALE_REVISION", current_version=current)
        if latest["status"] == "DRAFT":
            return latest, 1
        if latest["status"] != "CONFIRMED":
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        review = self._latest_review(run_id, str(latest["story_revision_id"]))
        if review is None or not review_is_spent(self._review_states(str(review["review_id"]))):
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        epoch = next_review_epoch(int(review["review_epoch"]))
        if self._accepted_video_count(run_id) >= MAX_ACCEPTED_REQUESTS or epoch > MAX_REVIEW_EPOCH:
            raise ParentStoryRunError(409, "VIDEO_REGENERATION_LIMIT_REACHED")
        return latest, epoch

    def confirm_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunView:
        run, access = self._owned_run_access(principal, run_id, lock=True, teacher_capable=True)
        operation = "CONFIRM_STORY_REVISION"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_revision": expected_revision,
                "expected_story_sha256": expected_story_sha256,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            self._session.commit()
            return self.get_run(principal=principal, run_id=run_id)
        self._refuse_read_only_class(access)
        self._refuse_purged(run)
        story_revision, review_epoch = self._confirmable_revision(
            run, expected_revision, expected_story_sha256
        )
        now = datetime.now(UTC)
        new_version = int(run["version"]) + 1
        command_kind, command_ref = self._command_scope(principal)
        try:
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={"decision": "CONFIRMED", "revision": expected_revision},
                now=now,
                response_status=200,
            )
            self._session.execute(
                insert(story_tables.story_revision_reviews).values(
                    review_id=str(uuid4()),
                    run_id=run_id,
                    story_revision_id=story_revision["story_revision_id"],
                    command_receipt_id=receipt_id,
                    actor_scope_kind=command_kind,
                    actor_scope_ref=command_ref,
                    decision="CONFIRM",
                    target_story_sha256=expected_story_sha256,
                    review_epoch=review_epoch,
                    created_at=now,
                )
            )
            if story_revision["status"] != "CONFIRMED":
                # A re-confirmation (epoch 2 or 3) leaves the confirmed revision untouched (BR-14).
                self._session.execute(
                    update(story_tables.story_revisions)
                    .where(
                        story_tables.story_revisions.c.story_revision_id
                        == story_revision["story_revision_id"]
                    )
                    .values(status="CONFIRMED")
                )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    run_state="SCRIPT_REVIEW",
                    job_state="SUCCEEDED",
                    # T-2d-fix D9: a failed attempt's code and retry flag do not outlive the
                    # adult's confirmation.
                    retryable=False,
                    error_code=None,
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            principal=principal,
            run_id=run_id,
        )

    # ------------------------------------------------------------------ T-2c: idea and transcript
    def ensure_accepting_audio(self, *, principal: VerifiedPrincipal, run_id: str) -> None:
        """Port design §7: re-check the state immediately before the first ``put_object``."""

        run = self._owned_run(principal, run_id, teacher_capable=True, pinned=True, write=True)
        if run["run_state"] in PURGE_STATES or run["run_state"] not in _INPUT_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def _drawing_unchanged(self, run: Mapping[str, Any], expected_input_revision: int) -> bool:
        """True when the current input still carries the drawing of ``expected_input_revision``.

        A later input revision that only added an idea or audio copies the drawing forward, so
        work started for the earlier revision is still current (T2C-D1); a retake replaces the
        drawing and makes it stale (T-2b).
        """
        current = self._current_input(run)
        if current["original_asset_ref"] is None:
            return False
        if int(current["input_revision"]) == expected_input_revision:
            return True
        earlier = self._session.execute(
            select(
                story_tables.run_inputs.c.original_asset_ref,
                story_tables.run_inputs.c.derived_sha256,
            ).where(
                story_tables.run_inputs.c.run_id == run["run_id"],
                story_tables.run_inputs.c.input_revision == expected_input_revision,
            )
        ).one_or_none()
        if earlier is None or earlier[0] is None:
            return False
        return (earlier[0], earlier[1]) == (
            current["original_asset_ref"],
            current["derived_sha256"],
        )

    def _latest_transcript(self, run_id: str, voice_asset_ref: str) -> RowMapping | None:
        """The latest non-superseded transcript revision of one voice asset (T2C-D4 d)."""
        table = story_tables.transcript_revisions
        return (
            self._session.execute(
                select(table)
                .where(
                    table.c.run_id == run_id,
                    table.c.source_asset_ref == voice_asset_ref,
                    table.c.state != "SUPERSEDED",
                )
                .order_by(table.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )

    def _next_transcript_revision_no(self, run_id: str) -> int:
        table = story_tables.transcript_revisions
        latest = self._session.scalar(
            select(table.c.revision_no)
            .where(table.c.run_id == run_id)
            .order_by(table.c.revision_no.desc())
            .limit(1)
        )
        return int(latest or 0) + 1

    def _apply_settle(self, run_id: str) -> str:
        """Recompute ``run_state`` from the stored facts after a writer changed them (T2C-D6).

        Called by every writer that can change the drawing, the understanding, the VLM job state
        or the transcript, inside its transaction and under the run row lock. It acts only in the
        three input states; the other states are owned by their own commands.
        """
        run: Any = (
            self._session.execute(
                select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )
        state = str(run["run_state"])
        if state not in _INPUT_STATES:
            return state
        input_row = self._current_input(run)
        has_drawing = input_row["original_asset_ref"] is not None
        understood = False
        if has_drawing:
            latest = self._latest_understanding(run_id)
            understood = latest is not None and self._same_drawing(
                latest["run_input_id"], input_row
            )
            if understood and run["job_state"] in _VLM_IN_FLIGHT:
                # T-2d: a subject edit queued a rerun on the same drawing (SRS l.394); until it
                # reports, the earlier understanding is being replaced and the run keeps waiting.
                understood = False
        transcript_state: str | None = None
        voice_ref = input_row["voice_asset_ref"]
        if voice_ref is not None:
            transcript = self._latest_transcript(run_id, str(voice_ref))
            transcript_state = None if transcript is None else str(transcript["state"])
        settled = settle_input_state(
            has_drawing=has_drawing,
            understood=understood,
            vlm_job_state=run["job_state"],
            transcript_state=transcript_state,
        )
        if settled != state:
            self._session.execute(
                update(story_tables.story_runs).where(_live_run(run_id)).values(run_state=settled)
            )
        return settled

    def _idea_for_story(self, run_id: str, input_row: Mapping[Any, Any]) -> str:
        """The idea text the story worker receives: typed idea plus the confirmed transcript."""
        typed = input_row["typed_idea"]
        voice_ref = input_row["voice_asset_ref"]
        if voice_ref is None:
            return str(typed or "")
        transcript = self._latest_transcript(run_id, str(voice_ref))
        if transcript is None or transcript["state"] != "CONFIRMED":
            raise ParentStoryRunError(422, "TRANSCRIPT_NOT_CONFIRMED")
        combined = _combined_idea(typed, _effective_transcript_text(transcript))
        if len(combined) > MAX_TRANSCRIPT_TEXT:
            raise ParentStoryRunError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "transcript", "code": "TOO_LONG"}],
            )
        return combined

    def prepare_idea(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int,
    ) -> IdeaOutcome | ParentStoryLifecycleRecord | None:
        """Replay, or the cheap pre-checks that run before any audio byte is read.

        Order: owner-scoped run (404), replay (a purged run answers the lifecycle projection),
        purged run (409), stale revision (409 with ``current_version``), input state (409). The
        run row is locked while these checks run and released by the rollback on every exit;
        ``submit_idea`` re-checks under the lock.
        """
        run, access = self._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True, pinned=True
        )
        try:
            replay = self._find_idempotency_receipt(
                principal=principal,
                operation=_SUBMIT_IDEA_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=_idempotency_key_hash(idempotency_key),
                fingerprint=fingerprint,
            )
            if replay is not None:
                result = self._replayed_idea(run, replay)
                self._session.rollback()
                return result
            self._refuse_read_only_class(access)
            self._refuse_purged(run)
            self._check_expected_run_revision(run, expected_run_revision)
            self._require_input_state(run)
        except ParentStoryRunError:
            self._session.rollback()
            raise
        self._session.rollback()
        return None

    @staticmethod
    def _require_input_state(run: Mapping[str, Any]) -> None:
        if run["run_state"] not in _INPUT_STATES:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    @staticmethod
    def _replayed_idea(
        run: Mapping[Any, Any], receipt: Mapping[Any, Any]
    ) -> IdeaOutcome | ParentStoryLifecycleRecord:
        if run["run_state"] in PURGE_STATES:
            # DTR Draft 6 §6.5: a replay of a purged run returns the content-free projection.
            return _projection(run)
        body = receipt["response_body"]
        try:
            revision = body["transcript_revision"]
            state = body["transcript_state"]
            source = body["idea_source"]
            return IdeaOutcome(
                input_revision=int(body["input_revision"]),
                run_revision=int(body["run_revision"]),
                run_state=str(body["run_state"]),
                idea_source=None if source is None else str(source),
                transcript_revision=None if revision is None else int(revision),
                transcript_state=None if state is None else str(state),
                replayed=True,
            )
        except (KeyError, TypeError, ValueError):
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def submit_idea(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int,
        text: str | None = None,
        voice: VoiceInput | None = None,
        correction_base_revision: int | None = None,
        correction_text: str | None = None,
    ) -> IdeaOutcome | ParentStoryLifecycleRecord:
        """One ``/idea`` command in one transaction under the run row lock (T2C-D1, T2C-D4).

        Text and/or audio write input revision N+1 with every other column copied forward (the
        drawing, the Parent context and its confirmation, the voice, the typed idea); a
        correction writes only a transcript revision. The old transcript rows are marked
        ``SUPERSEDED`` before a new row is inserted (the partial unique indexes are checked per
        statement), then the run state is settled and the receipt is stored.
        """
        run, access = self._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True, pinned=True
        )
        key_hash = _idempotency_key_hash(idempotency_key)
        self._lock_idempotency(
            principal=principal,
            operation=_SUBMIT_IDEA_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=_SUBMIT_IDEA_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            result = self._replayed_idea(run, replay)
            self._session.commit()
            return result
        self._refuse_read_only_class(access)
        self._refuse_purged(run)
        self._check_expected_run_revision(run, expected_run_revision)
        try:
            self._require_input_state(run)
        except ParentStoryRunError:
            self._session.rollback()
            raise
        previous = self._current_input(run)
        now = datetime.now(UTC)
        input_revision = int(previous["input_revision"])
        new_transcript_id: str | None = None
        live: RowMapping | None = None
        try:
            if correction_text is not None:
                live = self._write_correction(
                    run, previous, correction_base_revision, correction_text, now
                )
            else:
                input_revision += 1
                live, new_transcript_id = self._write_idea_input(
                    run, previous, input_revision, text, voice, now
                )
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    current_input_revision=input_revision,
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            settled = self._apply_settle(run_id)
            current = self._current_input(
                {"run_id": run_id, "current_input_revision": input_revision}
            )
            outcome = IdeaOutcome(
                input_revision=input_revision,
                run_revision=int(run["revision"]) + 1,
                run_state=settled,
                idea_source=current["idea_source"],
                transcript_revision=None if live is None else int(live["revision_no"]),
                transcript_state=None if live is None else str(live["state"]),
                new_transcript_id=new_transcript_id,
                organization_id=str(run["actor_scope_ref"]) if self._is_teacher else None,
            )
            self._store_idempotency_receipt(
                principal=principal,
                operation=_SUBMIT_IDEA_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=int(run["version"]) + 1,
                response_body=outcome.as_body(),
                now=now,
                response_status=202,
            )
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return outcome

    def _write_idea_input(
        self,
        run: Mapping[str, Any],
        previous: RowMapping,
        new_input_revision: int,
        text: str | None,
        voice: VoiceInput | None,
        now: datetime,
    ) -> tuple[RowMapping | None, str | None]:
        """Insert input revision N+1; returns the live transcript row and a new PENDING row id."""
        run_id = str(run["run_id"])
        typed = text if text is not None else previous["typed_idea"]
        overrides: dict[str, Any] = {
            "run_input_id": str(uuid4()),
            "input_revision": new_input_revision,
            "created_at": now,
            "typed_idea": typed,
        }
        voice_ref = previous["voice_asset_ref"]
        if voice is not None:
            if not voice.asset_key.startswith(f"parent/{run_id}/") or voice.asset_key == voice_ref:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            voice_ref = voice.asset_key
            overrides.update(
                voice_asset_ref=voice.asset_key,
                voice_asset_version=1,
                voice_duration_ms=voice.duration_ms,
            )
        overrides["idea_source"] = idea_source_for(typed, voice_ref)
        live: RowMapping | None = None
        if voice is None and voice_ref is not None:
            live = self._latest_transcript(run_id, str(voice_ref))
            if (
                text is not None
                and live is not None
                and live["state"] == "CONFIRMED"
                and len(_combined_idea(typed, _effective_transcript_text(live)))
                > MAX_TRANSCRIPT_TEXT
            ):
                # The confirmed transcript and the new typed idea must still fit together.
                raise ParentStoryRunError(
                    400,
                    "INVALID_REQUEST",
                    field_errors=[{"field": "text", "code": "TOO_LONG"}],
                )
        self._session.execute(
            insert(story_tables.run_inputs).values(
                **_next_input_values_keeping_drawing(previous, **overrides)
            )
        )
        if voice is None:
            return live, None
        table = story_tables.transcript_revisions
        # Supersede first, insert second: the partial unique indexes are checked per statement.
        self._session.execute(
            update(table)
            .where(table.c.run_id == run_id, table.c.state != "SUPERSEDED")
            .values(state="SUPERSEDED")
        )
        transcript_id = str(uuid4())
        self._session.execute(
            insert(table).values(
                transcript_revision_id=transcript_id,
                run_id=run_id,
                run_input_id=overrides["run_input_id"],
                source_asset_ref=voice.asset_key,
                revision_no=self._next_transcript_revision_no(run_id),
                origin="ASR",
                state="PENDING",
                created_at=now,
            )
        )
        return self._latest_transcript(run_id, voice.asset_key), transcript_id

    def _write_correction(
        self,
        run: Mapping[str, Any],
        previous: RowMapping,
        base_revision: int | None,
        corrected_text: str,
        now: datetime,
    ) -> RowMapping:
        """Supersede the live transcript row and insert the adult's correction (T2C-D4 a, b)."""
        run_id = str(run["run_id"])
        voice_ref = previous["voice_asset_ref"]
        live = None if voice_ref is None else self._latest_transcript(run_id, str(voice_ref))
        if live is None or live["state"] == "PENDING":
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if base_revision != int(live["revision_no"]):
            raise ParentStoryRunError(
                409, "STALE_REVISION", current_version=int(live["revision_no"])
            )
        table = story_tables.transcript_revisions
        self._session.execute(
            update(table)
            .where(
                table.c.run_id == run_id,
                table.c.source_asset_ref == str(voice_ref),
                table.c.state != "SUPERSEDED",
            )
            .values(state="SUPERSEDED")
        )
        self._session.execute(
            insert(table).values(
                transcript_revision_id=str(uuid4()),
                run_id=run_id,
                run_input_id=previous["run_input_id"],
                source_asset_ref=str(voice_ref),
                revision_no=self._next_transcript_revision_no(run_id),
                origin="ADULT_CORRECTION",
                state="NEEDS_CONFIRMATION",
                raw_transcript=live["raw_transcript"],
                adult_corrected_text=corrected_text,
                transcript_sha256=_text_sha256(corrected_text),
                language=live["language"],
                asr_profile_ref=live["asr_profile_ref"],
                model_revision=live["model_revision"],
                config_hash=live["config_hash"],
                created_at=now,
            )
        )
        created = self._latest_transcript(run_id, str(voice_ref))
        if created is None:
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
        return created

    def get_transcript(self, *, principal: VerifiedPrincipal, run_id: str) -> TranscriptView:
        # T-4b3a D2: a read, allowed in a read-only class (l.364, l.593, l.1425)
        run = self._owned_run(principal, run_id, teacher_capable=True, pinned=True)
        if run["run_state"] in PURGE_STATES:
            # A purged run holds no transcript (BR-23, FR-C-08): a lifecycle error, no content.
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        revision = int(run["revision"])
        voice_ref = self._current_input(run)["voice_asset_ref"]
        row = None if voice_ref is None else self._latest_transcript(run_id, str(voice_ref))
        if row is None:
            return TranscriptView(run_revision=revision, state="NONE")
        state = str(row["state"])
        readable = state in {"NEEDS_CONFIRMATION", "CONFIRMED"}
        return TranscriptView(
            run_revision=revision,
            state=state,
            transcript_revision=int(row["revision_no"]),
            origin=str(row["origin"]),
            text=_effective_transcript_text(row) if readable else None,
            transcript_sha256=row["transcript_sha256"] if readable else None,
            language=row["language"],
            error_code=row["error_code"],
        )

    def confirm_transcript(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        expected_transcript_revision: int,
        transcript_sha256: str,
    ) -> TranscriptConfirmOutcome | ParentStoryLifecycleRecord:
        """The adult confirms one exact transcript revision and hash (TD-04, l.1713)."""
        run, access = self._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True, pinned=True
        )
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_transcript_revision": expected_transcript_revision,
                "transcript_sha256": transcript_sha256,
                "confirmed": True,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=_CONFIRM_TRANSCRIPT_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=_CONFIRM_TRANSCRIPT_OPERATION,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            if run["run_state"] in PURGE_STATES:
                self._session.commit()
                return _projection(run)
            body = replay["response_body"]
            self._session.commit()
            try:
                return TranscriptConfirmOutcome(
                    transcript_revision=int(body["transcript_revision"]),
                    run_revision=int(body["run_revision"]),
                    run_state=str(body["run_state"]),
                    replayed=True,
                )
            except (KeyError, TypeError, ValueError):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        self._refuse_read_only_class(access)
        self._refuse_purged(run)
        input_row = self._current_input(run)
        voice_ref = input_row["voice_asset_ref"]
        live = None if voice_ref is None else self._latest_transcript(run_id, str(voice_ref))
        try:
            if live is None:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            current_revision = int(live["revision_no"])
            if expected_transcript_revision != current_revision:
                raise ParentStoryRunError(409, "STALE_REVISION", current_version=current_revision)
            stored_hash = live["transcript_sha256"]
            hash_matches = stored_hash is not None and hmac.compare_digest(
                str(stored_hash), transcript_sha256
            )
            no_op = live["state"] == "CONFIRMED" and hash_matches
            if live["state"] == "CONFIRMED" and not hash_matches:
                # A request that carries another hash than the live row is old, whatever the
                # state is (l.1699: STALE_REVISION with the current version).
                raise ParentStoryRunError(409, "STALE_REVISION", current_version=current_revision)
            if not no_op:
                if live["state"] != "NEEDS_CONFIRMATION" or run["run_state"] not in _INPUT_STATES:
                    raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
                if not hash_matches:
                    raise ParentStoryRunError(
                        409, "STALE_REVISION", current_version=current_revision
                    )
                combined = _combined_idea(input_row["typed_idea"], _effective_transcript_text(live))
                if len(combined) > MAX_TRANSCRIPT_TEXT:
                    # No silent truncation (T2C-D4); the adult shortens the text or the transcript.
                    raise ParentStoryRunError(
                        400,
                        "INVALID_REQUEST",
                        field_errors=[{"field": "transcript", "code": "TOO_LONG"}],
                    )
        except ParentStoryRunError:
            self._session.rollback()
            raise
        now = datetime.now(UTC)
        new_version = int(run["version"])
        run_revision = int(run["revision"])
        run_state = str(run["run_state"])
        try:
            if not no_op:
                table = story_tables.transcript_revisions
                self._session.execute(
                    update(table)
                    .where(
                        table.c.transcript_revision_id == live["transcript_revision_id"],
                        table.c.state == "NEEDS_CONFIRMATION",
                    )
                    .values(
                        state="CONFIRMED",
                        reviewed_by=_principal_scope_ref(principal),
                        reviewed_at=now,
                    )
                )
                new_version += 1
                run_revision += 1
                self._session.execute(
                    update(story_tables.story_runs)
                    .where(_live_run(run_id))
                    .values(
                        version=new_version,
                        revision=story_tables.story_runs.c.revision + 1,
                        updated_at=now,
                    )
                )
                run_state = self._apply_settle(run_id)
            outcome = TranscriptConfirmOutcome(
                transcript_revision=current_revision,
                run_revision=run_revision,
                run_state=run_state,
            )
            self._store_idempotency_receipt(
                principal=principal,
                operation=_CONFIRM_TRANSCRIPT_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body=outcome.as_body(),
                now=now,
                response_status=200,
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return outcome

    def read_pending_transcription(
        self, *, principal: VerifiedPrincipal, run_id: str, transcript_revision_id: str
    ) -> SpeechTranscriptionRequest | None:
        run = self._owned_run(principal, run_id, job_side_ok=True)
        try:
            if run["run_state"] in PURGE_STATES:
                return None
            table = story_tables.transcript_revisions
            row = (
                self._session.execute(
                    select(table).where(
                        table.c.transcript_revision_id == transcript_revision_id,
                        table.c.run_id == run_id,
                        table.c.state == "PENDING",
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            current = self._current_input(run)
            if current["voice_asset_ref"] != row["source_asset_ref"]:
                return None
            metadata = self._session.execute(
                select(_ASSET_METADATA.c.content_sha256, _ASSET_METADATA.c.media_type).where(
                    _ASSET_METADATA.c.asset_ref == row["source_asset_ref"]
                )
            ).one_or_none()
            if metadata is None:
                return None
            return SpeechTranscriptionRequest(
                run_id=run_id,
                transcript_revision_id=transcript_revision_id,
                audio_asset_ref=str(row["source_asset_ref"]),
                audio_sha256=str(metadata[0]),
                media_type=str(metadata[1]),
                duration_ms=int(current["voice_duration_ms"]),
            )
        finally:
            self._session.rollback()

    def complete_transcript(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
        text: str,
        language: str,
        model_revision: str,
        config_hash: str | None,
        asr_profile_ref: str | None,
        segment_timing: list[dict[str, int]] | None,
    ) -> bool:
        """``PENDING`` -> ``NEEDS_CONFIRMATION`` with the ASR text; ``False`` when stale."""
        return self._finish_transcript(
            principal,
            run_id,
            transcript_revision_id,
            {
                "state": "NEEDS_CONFIRMATION",
                "raw_transcript": text,
                "transcript_sha256": _text_sha256(text),
                "language": language[:16],
                "model_revision": model_revision[:128],
                "config_hash": None if config_hash is None else config_hash[:64],
                "asr_profile_ref": None if asr_profile_ref is None else asr_profile_ref[:128],
                "segment_timing": segment_timing if segment_timing else null(),
            },
        )

    def fail_transcript(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
        error_code: str,
    ) -> bool:
        """``PENDING`` -> ``FAILED``; the adult can type the idea as a correction."""
        return self._finish_transcript(
            principal,
            run_id,
            transcript_revision_id,
            {"state": "FAILED", "error_code": error_code[:64]},
        )

    def _finish_transcript(
        self,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
        values: dict[str, Any],
    ) -> bool:
        run = self._owned_run(principal, run_id, lock=True, job_side_ok=True)
        if run["run_state"] in PURGE_STATES:
            self._session.rollback()
            return False
        try:
            table = story_tables.transcript_revisions
            updated = cast(
                CursorResult[Any],
                self._session.execute(
                    update(table)
                    .where(
                        table.c.transcript_revision_id == transcript_revision_id,
                        table.c.run_id == run_id,
                        table.c.state == "PENDING",
                    )
                    .values(**values)
                ),
            )
            if updated.rowcount != 1:
                self._session.rollback()
                return False
            self._session.execute(
                update(story_tables.story_runs)
                .where(_live_run(run_id))
                .values(
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=datetime.now(UTC),
                )
            )
            self._apply_settle(run_id)
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return True

    def _owner_clauses(self, principal: VerifiedPrincipal) -> tuple[Any, ...]:
        """The OWNER predicate of a run row (not the command scope of a receipt).

        Parent: the run belongs to the principal's own scope. Teacher: the run belongs to an
        organization; the row is only a candidate until ``_owned_run`` has confirmed the current
        assignment (T-4a1-DEC-5).
        """

        runs = story_tables.story_runs
        if self._is_teacher:
            return (runs.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND,)
        return (
            runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
            runs.c.actor_scope_ref == _principal_scope_ref(principal),
        )

    def _owned_run(
        self,
        principal: VerifiedPrincipal,
        run_id: str,
        *,
        lock: bool = False,
        teacher_capable: bool = False,
        write: bool = False,
        pinned: bool = False,
        job_side_ok: bool = False,
    ) -> Any:
        """The run row of the actor, or the uniform 404.

        A Teacher actor finds a run only where ``teacher_capable`` is set, and only when the
        CURRENT assignment grants the child's class (FR-T-14, l.553): the same 404 for an
        org-wide, guide or observer row, a former Teacher, another organization and an unknown
        id. ``write`` additionally needs an active class (SRS l.364, l.593, l.1425). ``pinned``
        refuses a run without an occurrence pin for a Teacher; ``job_side_ok`` marks a method a
        job-side repository may run.
        """

        return self._owned_run_access(
            principal,
            run_id,
            lock=lock,
            teacher_capable=teacher_capable,
            write=write,
            pinned=pinned,
            job_side_ok=job_side_ok,
        )[0]

    def _owned_run_access(
        self,
        principal: VerifiedPrincipal,
        run_id: str,
        *,
        lock: bool = False,
        teacher_capable: bool = False,
        write: bool = False,
        pinned: bool = False,
        job_side_ok: bool = False,
    ) -> tuple[Any, TeacherRunAccess | None]:
        """``_owned_run`` and, for a Teacher, what the current assignment granted.

        The lifecycle commands need the class state themselves (T-13a-DEC-2: they check it AFTER
        the replay, so they do not pass ``write``); every other caller goes through ``_owned_run``.
        With ``lock`` the run row is held ``FOR UPDATE`` and the assignment row ``FOR SHARE``.
        """

        if self._job_side:
            return self._job_side_run(run_id, lock=lock, job_side_ok=job_side_ok), None
        if self._is_teacher and not teacher_capable:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        query = select(story_tables.story_runs).where(
            story_tables.story_runs.c.run_id == run_id, *self._owner_clauses(principal)
        )
        if pinned and self._is_teacher:
            query = query.where(story_tables.story_runs.c.occurrence_ref.is_not(None))
        if lock:
            query = query.with_for_update()
        row = self._session.execute(query).mappings().one_or_none()
        if row is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        access: TeacherRunAccess | None = None
        if self._is_teacher:
            access = self._teacher_run_access(principal, row, lock=lock)
            if write and not access.writable:
                self._session.rollback()
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        return row, access

    def _job_side_run(self, run_id: str, *, lock: bool, job_side_ok: bool) -> Any:
        """The run of a background task of a Teacher run (T-4b3a D6): by id, ``ORGANIZATION``
        kind, an occurrence pin and the organization id the route saw. No assignment is read: a
        valid job is not cancelled because the assignment changed (FR-T-14, l.553); the writes
        stay compare-and-set on run state, input and hashes. Anything but a job-side method, a
        missing organization or another organization is the uniform 404."""

        organization = self._job_side_organization
        if not job_side_ok or not self._is_teacher or not organization:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        runs = story_tables.story_runs
        query = select(runs).where(
            runs.c.run_id == run_id,
            runs.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND,
            runs.c.occurrence_ref.is_not(None),
            runs.c.actor_scope_ref == organization,
        )
        if lock:
            query = query.with_for_update()
        row = self._session.execute(query).mappings().one_or_none()
        if row is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        return row

    def _refuse_read_only_class(self, access: TeacherRunAccess | None) -> None:
        """A Teacher write in a suspended or archived class is 409 (SRS l.364, l.593, l.1425).

        Called AFTER the replay lookup so an earlier success is still replayed (SRS l.1697,
        T-13a-DEC-2, T4A1-I-06); the assignment check stays first (404).
        """

        if access is not None and not access.writable:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    def _teacher_run_access(
        self, principal: VerifiedPrincipal, run: Mapping[Any, Any], *, lock: bool
    ) -> TeacherRunAccess:
        access = (
            self._teacher_access.resolve(
                principal=principal,
                organization_id=str(run["actor_scope_ref"]),
                child_id=_text_or_none(run["profile_ref"]),
                lock=lock,
                # T-4b2 D10: a run with an occurrence pin follows the pin, a fixture row the child.
                occurrence_ref=_text_or_none(run.get("occurrence_ref")),
            )
            if self._teacher_access is not None
            else None
        )
        if access is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        return access

    def _typed_profile_refs(
        self, run: Mapping[str, Any], input_row: Mapping[Any, Any]
    ) -> tuple[UUID, UUID]:
        """The typed profile and revision refs of the Parent response (``StoryRunDetailV1``).

        Only the Parent view calls it: the Teacher view keeps the Managed Profile id as a string
        and never calls ``UUID()`` on it (T-4b2 D10 retired T-4a1-DEC-7).
        """

        return (
            UUID(str(run["profile_ref"])),
            UUID(str(input_row["source_profile_revision_ref"])),
        )

    def _lock_idempotency(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
    ) -> None:
        lock_material = _canonical_json(
            {
                "issuer": principal.issuer,
                "subject": principal.subject,
                "operation": operation,
                "scope_kind": scope_kind,
                "scope_ref": scope_ref,
                "key_hash": key_hash,
            }
        ).encode("utf-8")
        lock_key = int.from_bytes(hashlib.sha256(lock_material).digest()[:8], "big", signed=True)
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
        )

    def _find_idempotency_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
    ) -> RowMapping | None:
        command_kind, command_ref = self._command_scope(principal)
        receipt = (
            self._session.execute(
                select(story_tables.story_command_receipts).where(
                    story_tables.story_command_receipts.c.actor_scope_kind == command_kind,
                    story_tables.story_command_receipts.c.actor_scope_ref == command_ref,
                    story_tables.story_command_receipts.c.operation == operation,
                    story_tables.story_command_receipts.c.idempotency_scope_kind == scope_kind,
                    story_tables.story_command_receipts.c.idempotency_scope_ref == scope_ref,
                    story_tables.story_command_receipts.c.idempotency_key_sha256 == key_hash,
                )
            )
            .mappings()
            .one_or_none()
        )
        if receipt is None:
            return None
        if not hmac.compare_digest(str(receipt["request_fingerprint_sha256"]), fingerprint):
            # DTR Draft 6 §6.5 (A-3): a receipt of a run in DELETE_PENDING or DELETED is
            # replayed without the fingerprint check (step 4 replaces those fingerprints).
            if self._receipt_run_purged(principal, receipt):
                return receipt
            raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
        return receipt

    def _receipt_run_purged(self, principal: VerifiedPrincipal, receipt: RowMapping) -> bool:
        run_ref = receipt["resource_ref"]
        if run_ref is None:
            return False
        state = self._session.scalar(
            select(story_tables.story_runs.c.run_state).where(
                story_tables.story_runs.c.run_id == str(run_ref),
                *self._owner_clauses(principal),
            )
        )
        return state in PURGE_STATES

    def _store_idempotency_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
        run_id: str,
        resource_version: int,
        response_body: dict[str, Any],
        now: datetime,
        response_status: int,
    ) -> str:
        receipt_id = str(uuid4())
        command_kind, command_ref = self._command_scope(principal)
        self._session.execute(
            insert(story_tables.story_command_receipts).values(
                receipt_id=receipt_id,
                actor_scope_kind=command_kind,
                actor_scope_ref=command_ref,
                operation=operation,
                idempotency_scope_kind=scope_kind,
                idempotency_scope_ref=scope_ref,
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="FINAL",
                response_status=response_status,
                response_resource_version=resource_version,
                response_body=response_body,
                resource_ref=run_id,
                resource_version=resource_version,
                state_version=1,
                created_at=now,
                finalized_at=now,
            )
        )
        return receipt_id

    def _store_pending_idempotency_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
        run_id: str,
        resource_version: int,
        now: datetime,
    ) -> str:
        receipt_id = str(uuid4())
        command_kind, command_ref = self._command_scope(principal)
        self._session.execute(
            insert(story_tables.story_command_receipts).values(
                receipt_id=receipt_id,
                actor_scope_kind=command_kind,
                actor_scope_ref=command_ref,
                operation=operation,
                idempotency_scope_kind=scope_kind,
                idempotency_scope_ref=scope_ref,
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="PENDING",
                response_status=None,
                response_resource_version=None,
                # SQL NULL, not JSON null: the receipt shape check requires IS NULL.
                response_body=null(),
                resource_ref=run_id,
                resource_version=resource_version,
                state_version=1,
                created_at=now,
                finalized_at=None,
            )
        )
        return receipt_id

    def _current_input(self, run: Mapping[str, Any]) -> RowMapping:
        revision = run["current_input_revision"]
        if revision is None:
            raise ParentStoryRunError(409, "PARENT_STORY_CONTEXT_UNAVAILABLE")
        row = (
            self._session.execute(
                select(story_tables.run_inputs).where(
                    story_tables.run_inputs.c.run_id == run["run_id"],
                    story_tables.run_inputs.c.input_revision == revision,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise ParentStoryRunError(503, "PARENT_STORY_CONTEXT_UNAVAILABLE")
        return row

    def _latest_understanding(self, run_id: str):
        return (
            self._session.execute(
                select(story_tables.understanding_revisions)
                .where(story_tables.understanding_revisions.c.run_id == run_id)
                .order_by(story_tables.understanding_revisions.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _input_record(row) -> ParentStoryInputRecord:
        return ParentStoryInputRecord(
            run_input_id=str(row["run_input_id"]),
            input_revision=int(row["input_revision"]),
            original_asset_ref=row["original_asset_ref"],
            original_sha256=row["original_sha256"],
            original_media_type=row["original_media_type"],
            original_size_bytes=(
                int(row["original_size_bytes"]) if row["original_size_bytes"] is not None else None
            ),
            derived_asset_ref=row["derived_asset_ref"],
            derived_sha256=row["derived_sha256"],
            derived_size_bytes=(
                int(row["derived_size_bytes"]) if row["derived_size_bytes"] is not None else None
            ),
            source_profile_revision_ref=UUID(str(row["source_profile_revision_ref"])),
            context_revision=int(row["context_revision"]),
            context_snapshot=dict(row["context_snapshot"]),
            context_snapshot_sha256=str(row["context_snapshot_sha256"]),
            context_confirmed_by=(
                str(row["context_confirmed_by"])
                if row["context_confirmed_by"] is not None
                else None
            ),
            context_confirmed_at=row["context_confirmed_at"],
        )

    @staticmethod
    def _check_json_bound(value: dict[str, Any]) -> None:
        if len(_canonical_json(value).encode("utf-8")) > 262_144:
            raise ParentStoryRunError(422, "PARENT_UNDERSTANDING_RESULT_TOO_LARGE")


def settle_input_state(
    *,
    has_drawing: bool,
    understood: bool,
    vlm_job_state: str | None,
    transcript_state: str | None,
) -> str:
    """The run state while the adult is still giving input (T2C-D6; SRS l.394).

    ``has_drawing``: the current input carries a drawing. ``understood``: an understanding exists
    for that drawing. ``vlm_job_state``: the run's ``job_state`` (the drawing step; the ASR step
    is read through the transcript). ``transcript_state``: the state of the latest non-superseded
    transcript of the current voice asset, or ``None`` when there is no voice. Rules, in order:

    1. no drawing: ``INPUT_PROCESSING`` (the adult may still add the idea and confirm the text);
    2. the drawing is not understood and its job is queued, running or awaiting reconciliation, or
       the transcript is ``PENDING``: ``INPUT_PROCESSING``;
    3. the drawing is not understood and its job failed recoverably: ``INPUT_REVIEW``;
    4. a transcript that needs confirmation or failed: ``INPUT_REVIEW``;
    5. the drawing is understood: ``SUBJECT_REVIEW`` (also with no voice, or a confirmed one);
    6. otherwise ``INPUT_PROCESSING``.
    """
    if not has_drawing:
        return "INPUT_PROCESSING"
    if not understood and vlm_job_state in {None, "QUEUED", "RUNNING", "AWAITING_RECONCILIATION"}:
        return "INPUT_PROCESSING"
    if transcript_state == "PENDING":
        return "INPUT_PROCESSING"
    if not understood and vlm_job_state == "FAILED":
        return "INPUT_REVIEW"
    if transcript_state in {"NEEDS_CONFIRMATION", "FAILED"}:
        return "INPUT_REVIEW"
    if understood:
        return "SUBJECT_REVIEW"
    return "INPUT_PROCESSING"


def idea_source_for(typed_idea: str | None, voice_asset_ref: str | None) -> str | None:
    """``idea_source`` of an input row (``ck_story_run_input_idea``)."""
    if typed_idea and voice_asset_ref:
        return "TEXT_AND_VOICE"
    if voice_asset_ref:
        return "VOICE"
    if typed_idea:
        return "TEXT"
    return None


def _effective_transcript_text(row: Mapping[Any, Any]) -> str | None:
    """The adult's corrected text, else the raw ASR text (the text the hash covers)."""
    corrected = row["adult_corrected_text"]
    effective = corrected if corrected is not None else row["raw_transcript"]
    return None if effective is None else str(effective)


def _combined_idea(typed_idea: str | None, transcript_text: str | None) -> str:
    """Typed idea and transcript text joined by one space (T2C-D4)."""
    return " ".join(part for part in (typed_idea, transcript_text) if part)


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def derived_asset_key(original_asset_ref: str) -> str:
    """``parent/{run}/{token}/original`` -> ``parent/{run}/{token}/normalized.png`` (T-2b).

    Same token as the original, so the pair is one unit for the FR-C-08 purge closure.
    """
    return original_asset_ref.rsplit("/", 1)[0] + "/normalized.png"


def drawing_attach_fingerprint(asset_ref: str, expected_run_revision: int | None) -> str:
    """Request fingerprint of ``POST /v1/story-runs/{id}/assets`` (T2B-D3)."""
    return _sha256_json({"asset_ref": asset_ref, "expected_run_revision": expected_run_revision})


def idea_fingerprint(
    expected_run_revision: int,
    text: str | None,
    audio_ref: str | None,
    correction: tuple[int, str] | None,
) -> str:
    """Request fingerprint of ``POST /v1/story-runs/{id}/idea`` (T2C-D1)."""
    correction_body = (
        None if correction is None else {"base_revision": correction[0], "text": correction[1]}
    )
    return _sha256_json(
        {
            "expected_run_revision": expected_run_revision,
            "text": text,
            "audio_ref": audio_ref,
            "transcript_correction": correction_body,
        }
    )


def _next_input_values(previous: Mapping[Any, Any], **overrides: Any) -> dict[str, Any]:
    """Every ``run_inputs`` column of the next revision: ``overrides`` set, the rest copied.

    Typed idea, voice, Parent context and its confirmation, lesson pin and any column added later
    move forward from ``previous``. The drawing columns need an explicit value (a new drawing).
    SQL NULL is written for an absent JSONB value.
    """
    return _build_next_input(previous, overrides, copy_drawing=False)


def _next_input_values_keeping_drawing(
    previous: Mapping[Any, Any], **overrides: Any
) -> dict[str, Any]:
    """Like ``_next_input_values`` for an idea or audio revision: the drawing is copied too."""
    return _build_next_input(previous, overrides, copy_drawing=True)


def _build_next_input(
    previous: Mapping[Any, Any], overrides: Mapping[str, Any], *, copy_drawing: bool
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for column in story_tables.run_inputs.columns:
        name = column.name
        if name in overrides:
            values[name] = overrides[name]
        elif name in _DRAWING_INPUT_COLUMNS and not copy_drawing:
            raise RuntimeError(f"run_inputs column {name} needs an explicit value")
        else:
            value = previous[name]
            values[name] = null() if value is None and isinstance(column.type, JSONB) else value
    unknown = set(overrides) - set(values)
    if unknown:
        raise RuntimeError(f"unknown run_inputs columns {sorted(unknown)}")
    return values


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _story_primary_activity(activity: Mapping[str, Any]) -> dict[str, str]:
    """The eight bounded fields of the adult's main activity that the story worker accepts."""

    field_limits = {
        "title": 160,
        "objective": 400,
        "materials_text": 300,
        "preparation_text": PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
        "instructions_text": 700,
        "observation_notes": PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
        "safety_notes": PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
        "activity_kind": 16,
    }
    return {
        key: str(activity.get(key, "")).strip()[:limit]
        for key, limit in field_limits.items()
    }


def _create_run_fingerprint(
    *,
    parent_profile_id: UUID,
    topic: str,
    adult_confirmed_idea: str,
    lesson_version_ref: dict[str, str] | None,
    intended_drawing_subject: str | None = None,
) -> str:
    payload = {
        "parent_profile_id": str(parent_profile_id),
        "topic": topic,
        "adult_confirmed_idea": adult_confirmed_idea,
        "lesson_version": lesson_version_ref,
    }
    # Preserve older idempotency receipts when the optional subject was omitted.
    if intended_drawing_subject is not None:
        payload["intended_drawing_subject"] = intended_drawing_subject
    return _sha256_json(payload)


def _integrity_constraint_name(exc: IntegrityError) -> str | None:
    original = getattr(exc, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    return constraint_name if isinstance(constraint_name, str) else None


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _idempotency_key_hash(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 256:
        raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def run_summary_capabilities(run_state: str) -> tuple[bool, bool, bool]:
    """FEAT-081 C3b: (deleting, can_cancel, can_delete) for a run state (SRS 1518; D-214 item 1)."""
    deleting = run_state in PURGE_STATES
    return (
        deleting,
        not deleting and run_state in CANCEL_ELIGIBLE_STATES,
        not deleting and run_state in DELETE_ELIGIBLE_STATES,
    )


def _run_summary(row: RowMapping) -> ParentStoryRunSummary:
    deleting, can_cancel, can_delete = run_summary_capabilities(str(row["run_state"]))
    profile_id: UUID | None = None
    if not deleting and row["profile_ref"] is not None:
        try:
            profile_id = UUID(str(row["profile_ref"]))
        except ValueError:
            profile_id = None  # A defective row must not fail the whole page.
    return ParentStoryRunSummary(
        run_id=str(row["run_id"]),
        parent_profile_id=profile_id,
        run_state=str(row["run_state"]),
        revision=int(row["revision"]),
        deleting=deleting,
        can_cancel=can_cancel,
        can_delete=can_delete,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _public_run_error_code(stored: Any, video_rows: RunVideoRows | None) -> Any:
    """T-1c (SRS l.875): while the current video failed or was blocked, the run-level code is the
    closed public one, never the stored text (a renderer's code is not a public contract)."""

    if stored is None or video_rows is None:
        return stored
    current = next(
        (g for g in video_rows.generations if g.generation_id == video_rows.current_generation_id),
        None,
    )
    if current is not None and current.state in {"FAILED", "SAFETY_BLOCKED"}:
        return public_failure_code(str(stored))
    return stored


def _text_or_none(value: object) -> str | None:
    return None if value is None else str(value)


def _parent_activity_candidate_key(activity: Any) -> str | None:
    """Stable published-lesson identity used to suppress repeats across suggestion rounds."""
    if not isinstance(activity, Mapping):
        return None
    lesson_id = activity.get("source_lesson_id")
    version_id = activity.get("source_lesson_version_id")
    content_hash = activity.get("source_content_sha256")
    activity_index = activity.get("source_activity_index")
    if (
        not isinstance(lesson_id, str)
        or not lesson_id
        or not isinstance(version_id, str)
        or not version_id
        or not isinstance(content_hash, str)
        or len(content_hash) != 64
        or type(activity_index) is not int
        or activity_index < 0
    ):
        return None
    return f"{lesson_id}:{version_id}:{content_hash}:{activity_index}"


def _project_confirmed_candidate(
    candidate: Mapping[str, Any], confirmed_subject: str | None
) -> dict[str, Any]:
    """Add a persisted adult decision to a copy of the immutable VLM candidate."""

    projected = dict(candidate)
    confirmed = str(confirmed_subject or "").strip()
    if not confirmed:
        return projected
    suggested = str(projected.get("candidate_subject") or "").strip()
    if projected.get("decision") == "CORRECTED_BY_ADULT" or suggested != confirmed:
        projected["candidate_subject"] = confirmed
        projected["decision"] = "CORRECTED_BY_ADULT"
    else:
        projected["decision"] = "CONFIRMED_BY_ADULT"
    return projected


def _teacher_pin_view(
    run: Mapping[str, Any], input_row: Mapping[Any, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The plan and activity pins of a Teacher run as the view shows them (T-4b2 D10); a fixture
    row without an occurrence, or an input without the Teacher pin schema, has none."""

    pin = input_row["lesson_pin_snapshot"]
    if (
        run.get("occurrence_ref") is None
        or not isinstance(pin, dict)
        or pin.get("schema_version") != TEACHER_PIN_SCHEMA
    ):
        return None, None
    activity = pin["activity"]
    return (
        {"revision_no": pin["plan_revision_no"], "plan_hash": pin["plan_hash"]},
        {
            "plan_activity_id": activity["plan_activity_id"],
            "kind": activity["kind"],
            "snapshot_hash": activity.get("snapshot_hash"),
        },
    )


def _principal_scope_ref(principal: VerifiedPrincipal) -> str:
    principal_claims = {"issuer": principal.issuer, "subject": principal.subject}
    return hashlib.sha256(_canonical_json(principal_claims).encode("utf-8")).hexdigest()


def job_side_repository(
    session: Session, actor: RunActor | None, organization_id: str | None
) -> SqlParentStoryRunRepository:
    """The repository of a background task: the unchanged Parent repository for a Parent (or no
    actor), the job-side Teacher repository (T-4b3a D6) for a Teacher actor. The organization id
    is the one the route read from the run row it had just authorized."""

    if actor is not None and actor.is_teacher:
        return SqlParentStoryRunRepository(
            session, actor=actor, job_side=True, job_side_organization=organization_id
        )
    return SqlParentStoryRunRepository(session)


__all__ = [
    "SqlParentStoryRunRepository",
    "derived_asset_key",
    "drawing_attach_fingerprint",
    "idea_fingerprint",
    "idea_source_for",
    "job_side_repository",
    "settle_input_state",
    "story_task_audit_scope",
]
