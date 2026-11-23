"""Authenticated Parent StoryRun creation, retrieval, and adult confirmation APIs."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import json
import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
    ParentStoryRunView,
    TeacherStoryRunRecord,
)
from sketch2life.application.ports.story_run_actor import RunActor
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.application.services.story_run_detail import detail_etag, etag_matches
from sketch2life.application.services.story_run_video import (
    DEFAULT_PORT_TIMEOUT_SECONDS,
    StoryVideoProgressService,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentActiveStoryRunEnvelopeV1,
    ParentContextConfirmationRequestV1,
    ParentLessonPinSnapshotV1,
    ParentMainActivityV1,
    ParentPostVideoActivityV1,
    ParentStoryCancelErrorEnvelopeV1,
    ParentStoryErrorEnvelopeV1,
    ParentStoryRevisionConfirmationRequestV1,
    ParentStoryRunCancelRequestV1,
    ParentStoryRunCreateRequestV1,
    ParentStoryRunEnvelopeV1,
    ParentStoryRunHistoryPageV1,
    ParentStoryRunLifecycleEnvelopeV1,
    ParentStoryRunResponseV1,
    ParentStoryRunSummaryV1,
    ParentSubjectConfirmationRequestV1,
    ParentSubjectConfirmationResponseV1,
)
from sketch2life.contracts.schemas.story_run_video import (
    ParentStoryRunVideoV1,
    ParentStoryTimelineEventV1,
)
from sketch2life.contracts.schemas.teacher_story_runs import (
    TeacherActiveStoryRunEnvelopeV1,
    TeacherStoryRunEnvelopeV1,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_inputs.runner import ParentInputJobRunner
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from sketch2life.interfaces.http.api_conventions import limit_query, parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.routers.parent_story_inputs import (
    generator_supports_role,
    schedule_first_story,
)
from sketch2life.interfaces.http.routers.story_run_create_dispatch import (
    RoleDispatchedCreateRoute,
    teacher_active_envelope,
    teacher_envelope,
)
from sketch2life.interfaces.http.story_run_actor import require_story_run_actor

router = APIRouter(prefix="/v1/story-runs", tags=["Parent StoryRuns"])
_LOG = logging.getLogger(__name__)
_PARENT_STORY_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The resource was not found, or the caller is not an active Parent.",
    },
    409: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The request conflicts with current state.",
    },
    422: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "Validation uses the standard error envelope.",
    },
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}

# T-4a1: the run read and the three confirmations are open to the current class Teacher as well
# (SRS l.1664-1669, l.1676 "Actor của run"); the 404 row says so, the 409 row names the class state.
_ACTOR_STORY_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    **_PARENT_STORY_ERROR_RESPONSES,
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The resource was not found, or the caller is neither an active Parent nor the "
            "Teacher currently assigned to the child's class."
        ),
    },
}


def _service(db: Session) -> ParentStoryRunService:
    return ParentStoryRunService(
        SqlParentStoryRunRepository(db),
        SqlParentStoryProfileLookup(db),
    )


def _teacher_service(db: Session, actor: RunActor) -> ParentStoryRunService:
    """The service of a Teacher actor: the repository re-reads the CURRENT assignment on every
    step (FR-T-14, l.553). The profile lookup stays the Parent one and is never used for a run."""

    return ParentStoryRunService(
        SqlParentStoryRunRepository(db, actor=actor, teacher_access=SqlTeacherRunAccess(db)),
        SqlParentStoryProfileLookup(db),
    )


def _service_for(db: Session, actor: RunActor) -> ParentStoryRunService:
    return _teacher_service(db, actor) if actor.is_teacher else _service(db)


def _require_parent(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        # CONV-1 (SRS l.864-865, C-D4, OD-18b): not an active Parent means out of scope.
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    return identity


def _meet_video_saga(request: Request, db: Session, run_id: str) -> None:
    """After the cancel commit, outside any transaction: resolve what the video saga still owns.

    Best effort (T-1a, D4): the cancel is already durable. An intent whose admission cannot be read
    stays pending for the reconciler and the purge waits for it; only the error type is logged.
    """

    try:
        state = request.app.state
        StoryVideoProgressService(
            SqlStoryVideoRepository(db),
            getattr(state, "story_video_ports", None),
            call_timeout_seconds=getattr(
                state, "story_video_port_timeout_seconds", DEFAULT_PORT_TIMEOUT_SECONDS
            ),
        ).on_run_cancelled(run_id)
    except Exception as exc:  # the lifecycle consumer retries the purge until it settles
        _LOG.warning("story_video_cancel_hook_failed kind=%s", type(exc).__name__)


def _invoke[ResultT](callable_: Callable[..., ResultT], **kwargs: Any) -> ResultT:
    try:
        return callable_(**kwargs)
    except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
        detail: dict[str, Any] = {"code": exc.code}
        if isinstance(exc, ParentStoryRunError) and exc.current_version is not None:
            detail["current_version"] = exc.current_version
        raise HTTPException(status_code=exc.status_code, detail=detail) from None


def story_run_response(record: ParentStoryRunRecord) -> ParentStoryRunResponseV1:
    """The one builder of ``StoryRunDetailV1`` (SRS l.1811): every route that returns the model
    (this family and the legacy ``/api/parent/v1/ai`` routes) shows the same shape."""

    return ParentStoryRunResponseV1(
        run_id=record.run_id,
        run_revision=record.run_revision,
        run_state=record.run_state,
        parent_profile_id=record.parent_profile_id,
        profile_revision_ref=record.profile_revision_ref,
        context_revision=record.context_revision,
        context_confirmed=record.context_confirmed,
        context_snapshot=record.context_snapshot,
        context_snapshot_sha256=record.context_snapshot_sha256,
        lesson_pin_snapshot=record.lesson_pin_snapshot,
        current_input_revision=record.current_input_revision,
        understanding_revision=record.understanding_revision,
        subject_label=record.subject_label,
        candidate=record.candidate,
        story_revision_id=record.story_revision_id,
        story_revision_no=record.story_revision_no,
        story_status=record.story_status,
        story_sha256=record.story_sha256,
        story=record.story_content,
        job_state=record.job_state,
        retryable=record.retryable,
        error_code=record.error_code,
        created_at=record.created_at,
        updated_at=record.updated_at,
        video=(
            ParentStoryRunVideoV1.model_validate(record.video) if record.video is not None else None
        ),
        timeline=[ParentStoryTimelineEventV1.model_validate(event) for event in record.timeline],
        story_confirmation_required=record.story_confirmation_required,
        main_activity=(
            ParentMainActivityV1.model_validate(record.main_activity)
            if record.main_activity is not None
            else None
        ),
        post_video_activities=(
            [
                ParentPostVideoActivityV1.model_validate(item)
                for item in record.post_video_activities
            ]
            if record.post_video_activities is not None
            else None
        ),
    )


_response = story_run_response


def _guard_post_video_activities[ViewT: ParentStoryRunView | None](
    request: Request, db: Session, principal: VerifiedPrincipal, view: ViewT
) -> ViewT:
    """T-2e-a D11: the activities to try after the video of a run with a lesson pin are listed from
    the stored pin only while the Parent can still view that lesson (one check by lesson id). When
    access is gone, or lesson storage is not composed, the list is withheld and the read goes on."""

    if (
        not isinstance(view, ParentStoryRunRecord)
        or not view.post_video_activities
        or view.lesson_pin_snapshot is None
    ):
        return view
    try:
        get_lesson_library_service(request, db).get_parent_lesson(
            parent_principal_ref=principal.subject,
            lesson_id=str(view.lesson_pin_snapshot["lesson_id"]),
        )
    except (HTTPException, LessonLibraryError):
        return replace(view, post_video_activities=None)
    return view


# FR-C-08 (Contract Draft 11 §3.3-§3.4): from DELETE_PENDING on, a Parent response for the run
# is the content-free lifecycle envelope; before it, the frozen run envelope.
ParentStoryRunResult = ParentStoryRunEnvelopeV1 | ParentStoryRunLifecycleEnvelopeV1


def _lifecycle_envelope(record: ParentStoryLifecycleRecord) -> ParentStoryRunLifecycleEnvelopeV1:
    return ParentStoryRunLifecycleEnvelopeV1.model_validate(
        {"request_id": uuid4(), "lifecycle": record.as_body()}
    )


# T-4b2 D10: the run read and the confirmations answer a Teacher with the Teacher view (a string
# profile ref, the occurrence, plan and activity pins); a Parent still gets the Parent result.
StoryRunResult = ParentStoryRunResult | TeacherStoryRunEnvelopeV1


def _envelope(view: ParentStoryRunView) -> StoryRunResult:
    if isinstance(view, ParentStoryLifecycleRecord):
        return _lifecycle_envelope(view)
    if isinstance(view, TeacherStoryRunRecord):
        return teacher_envelope(view)
    return ParentStoryRunEnvelopeV1(request_id=uuid4(), story_run=_response(view))


def create_parent_story_run(
    payload: ParentStoryRunCreateRequestV1,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> StoryRunResult:
    # The registration below publishes the header as required; parse_idempotency_key (C-D5, 1-128
    # visible ASCII) is the authority and runs after the role check, as for cancel/delete.
    del idempotency_key
    identity = _require_parent(db, principal)
    key = parse_idempotency_key(request)
    service = _service(db)
    lesson_version_ref = (
        payload.lesson_version.model_dump(mode="json")
        if payload.lesson_version is not None
        else None
    )
    replay = _invoke(
        service.replay_create_run,
        principal=principal,
        account_id=identity.account_id,
        parent_profile_id=payload.parent_profile_id,
        idempotency_key=key,
        topic=payload.topic,
        adult_confirmed_idea=payload.adult_confirmed_idea,
        lesson_version_ref=lesson_version_ref,
    )
    if replay is not None:
        return _envelope(replay)

    lesson_pin_snapshot = None
    if payload.lesson_version is not None:
        lesson_service = get_lesson_library_service(request, db)
        try:
            lesson = lesson_service.get_parent_lesson(
                parent_principal_ref=principal.subject,
                lesson_id=payload.lesson_version.lesson_id,
            )
        except LessonLibraryError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"code": exc.code, "message": exc.message},
            ) from None
        if (
            lesson.get("version_id") != payload.lesson_version.version_id
            or lesson.get("content_sha256") != payload.lesson_version.content_sha256
        ):
            raise HTTPException(status_code=409, detail={"code": "STALE_REVISION"})
        lesson_pin_snapshot = ParentLessonPinSnapshotV1.model_validate(
            {
                "schema_version": "sketch2life.parent-lesson-pin.v1",
                "lesson_id": lesson["lesson_id"],
                "version_id": lesson["version_id"],
                "version_no": lesson["version_no"],
                "content_sha256": lesson["content_sha256"],
                "target_age_band_ref": lesson["target_age_band_ref"],
                "target_age_band_version": lesson["target_age_band_version"],
                "title": lesson["title"],
                "topic": lesson["topic"],
                "drawing_subject": lesson["drawing_subject"],
                "subject_learning_notes": lesson["subject_learning_notes"],
                "script_direction": lesson["script_direction"],
                "script_following_allowed": lesson["script_following_allowed"],
                "activities": lesson["activities"],
            }
        ).model_dump(mode="json")
    record = _invoke(
        service.create_run,
        principal=principal,
        account_id=identity.account_id,
        parent_profile_id=payload.parent_profile_id,
        idempotency_key=key,
        topic=payload.topic,
        adult_confirmed_idea=payload.adult_confirmed_idea,
        lesson_version_ref=lesson_version_ref,
        lesson_pin_snapshot=lesson_pin_snapshot,
    )
    return _envelope(record)


# T-4b2 D1: one route, two bodies. The Parent function above is registered exactly as before; the
# route class sends a Teacher-shaped body from an active Teacher to the Teacher endpoint and answers
# every other request with this handler, byte for byte as before.
router.add_api_route(
    "",
    create_parent_story_run,
    methods=["POST"],
    response_model=ParentStoryRunResult,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Parent StoryRun with a pinned profile and context proposal",
    responses=_PARENT_STORY_ERROR_RESPONSES,
    route_class_override=RoleDispatchedCreateRoute,
)


_HISTORY_RESPONSES: dict[int | str, dict[str, Any]] = {
    status_code: _PARENT_STORY_ERROR_RESPONSES[status_code]
    for status_code in (400, 401, 404, 422, 500, 503)
}


def _encode_history_cursor(created_at: datetime, run_id: str) -> str:
    payload = json.dumps(
        {"created_at": created_at.isoformat(), "run_id": run_id, "v": 1},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_history_cursor(cursor: str) -> tuple[datetime, str]:
    """A malformed cursor is 400 INVALID_REQUEST in this family's envelope (C3B-2)."""
    try:
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != {"created_at", "run_id", "v"}:
            raise ValueError
        if type(decoded["v"]) is not int or decoded["v"] != 1:
            raise ValueError
        if not isinstance(decoded["created_at"], str) or not isinstance(decoded["run_id"], str):
            raise ValueError
        created_at = datetime.fromisoformat(decoded["created_at"])
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError
        return created_at, str(UUID(decoded["run_id"]))
    except (binascii.Error, json.JSONDecodeError, UnicodeEncodeError, ValueError):
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST"}) from None


@router.get(
    "",
    response_model=ParentStoryRunHistoryPageV1,
    summary="[PROPOSAL] List the authenticated Parent's StoryRuns, newest first",
    responses=_HISTORY_RESPONSES,
)
def list_parent_story_runs(
    limit: int = limit_query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=512),
    parent_profile_id: UUID | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunHistoryPageV1:
    """FEAT-081 C3b: summary history (SRS §21.5 line 1707; §21.2 has no list route)."""
    _require_parent(db, principal)
    after = _decode_history_cursor(cursor) if cursor is not None else None
    rows = _invoke(
        _service(db).list_runs,
        principal=principal,
        profile_id=parent_profile_id,
        limit=limit,
        after=after,
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    return ParentStoryRunHistoryPageV1(
        request_id=uuid4(),
        items=[
            ParentStoryRunSummaryV1(
                run_id=UUID(row.run_id),
                parent_profile_id=row.parent_profile_id,
                run_state=row.run_state,
                revision=row.revision,
                deleting=row.deleting,
                can_cancel=row.can_cancel,
                can_delete=row.can_delete,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
        next_cursor=(
            _encode_history_cursor(rows[-1].created_at, rows[-1].run_id)
            if has_more and rows
            else None
        ),
    )


@router.get(
    "/active/current",
    response_model=ParentActiveStoryRunEnvelopeV1 | TeacherActiveStoryRunEnvelopeV1,
    summary="[PROPOSAL] Resume the authenticated Parent's active StoryRun, if one exists",
    responses=_ACTOR_STORY_ERROR_RESPONSES,
)
def get_active_parent_story_run(
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActiveStoryRunEnvelopeV1 | TeacherActiveStoryRunEnvelopeV1:
    # T-4b2: the Parent's active run, or the one active run a Teacher holds through the Teacher lock
    # (resume after a reload); the same empty answer when there is none.
    actor = require_story_run_actor(db, principal)
    service = _service_for(db, actor)
    record = _invoke(
        service.get_active_run,
        principal=principal,
        account_id=actor.account_id,
    )
    record = _guard_post_video_activities(request, db, principal, record)
    if actor.is_teacher:
        return teacher_active_envelope(
            record if isinstance(record, TeacherStoryRunRecord) else None
        )
    return ParentActiveStoryRunEnvelopeV1(
        request_id=uuid4(),
        story_run=_response(record) if isinstance(record, ParentStoryRunRecord) else None,
    )


_DETAIL_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}


@router.get(
    "/{run_id}",
    response_model=StoryRunResult,
    summary="Read the authenticated Parent's saved StoryRun and review state",
    responses={
        **_ACTOR_STORY_ERROR_RESPONSES,
        304: {"description": "Not modified (only after the caller was authorised)"},
    },
)
def get_parent_story_run(
    run_id: UUID,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    """``StoryRunDetailV1`` (SRS l.1811): the strong ``ETag`` is a content hash of the body; the
    304 comes only after authorisation and a recomputation from the database (no cache)."""

    actor = require_story_run_actor(db, principal)
    service = _service_for(db, actor)
    record = _invoke(
        service.get_run,
        principal=principal,
        run_id=str(run_id),
    )
    record = _guard_post_video_activities(request, db, principal, record)
    result = _envelope(record)
    if isinstance(result, ParentStoryRunEnvelopeV1 | TeacherStoryRunEnvelopeV1):
        etag = detail_etag(result.story_run.model_dump(mode="json"))
        if etag_matches(request.headers.get("If-None-Match"), etag):
            return Response(status_code=304, headers={**_DETAIL_READ_HEADERS, "ETag": etag})
        for name, value in _DETAIL_READ_HEADERS.items():
            response.headers[name] = value
        response.headers["ETag"] = etag
    return result


@router.post(
    "/{run_id}/cancel",
    response_model=ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel the StoryRun of the authenticated actor and request its deletion",
    responses={
        **_ACTOR_STORY_ERROR_RESPONSES,
        409: {
            "model": ParentStoryCancelErrorEnvelopeV1,
            "description": "The request conflicts with the current StoryRun revision or state.",
        },
    },
)
def cancel_parent_story_run(
    run_id: UUID,
    payload: ParentStoryRunCancelRequestV1,
    request: Request,
    # Contract Draft 11 §3.1: optional, no length constraint; parse_idempotency_key (1-128
    # visible ASCII) decides, so a missing or invalid key is 400 INVALID_REQUEST.
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunLifecycleEnvelopeV1:
    del idempotency_key
    # T-13a: the owning Parent or the Teacher currently assigned to the child's class (SRS l.1673,
    # UC-07 l.1467, UC-11 l.1515); everyone else gets the one 404.
    actor = require_story_run_actor(db, principal)
    # Key errors (400) come after the role check and before the owner-scoped lookup (404);
    # the 400 does not depend on the run, so it reveals nothing about its existence.
    key = parse_idempotency_key(request)
    record = _invoke(
        _service_for(db, actor).cancel_run,
        principal=principal,
        run_id=str(run_id),
        expected_revision=payload.expected_revision,
        idempotency_key=key,
    )
    # T-4b3b (T-13a hand-off H6): a Teacher run can own a video generation too, so the cancel of
    # either actor meets the saga (the saga reads its scope from the generation, not the actor).
    _meet_video_saga(request, db, str(run_id))
    return _lifecycle_envelope(record)


@router.delete(
    "/{run_id}",
    response_model=ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Delete the finished StoryRun of the authenticated actor",
    responses=_ACTOR_STORY_ERROR_RESPONSES,
)
def delete_parent_story_run(
    run_id: UUID,
    request: Request,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunLifecycleEnvelopeV1:
    """Contract Draft 11 §3.2: COMPLETED, FAILED or ABANDONED; no body, no revision."""
    del idempotency_key
    actor = require_story_run_actor(db, principal)  # Parent owner or current class Teacher
    key = parse_idempotency_key(request)  # after the role check, before the lookup
    record = _invoke(
        _service_for(db, actor).delete_run,
        principal=principal,
        run_id=str(run_id),
        idempotency_key=key,
    )
    return _lifecycle_envelope(record)


@router.post(
    "/{run_id}/context-confirmation",
    response_model=StoryRunResult,
    summary="[PROPOSAL] Confirm the immutable Parent context snapshot before story generation",
    responses=_ACTOR_STORY_ERROR_RESPONSES,
)
def confirm_parent_story_context(
    run_id: UUID,
    payload: ParentContextConfirmationRequestV1,
    request: Request,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> StoryRunResult:
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    # T-2e-a D3: the confirmation may start the first story (when the adult chose the activity
    # first); the reservation arrives after the commit and the story is generated after the
    # response.
    started: list[ParentStoryRevisionReservation] = []
    record = _invoke(
        _service_for(db, actor).confirm_context,
        principal=principal,
        run_id=str(run_id),
        expected_context_revision=payload.expected_context_revision,
        expected_context_snapshot_sha256=payload.context_snapshot_sha256,
        idempotency_key=key,
        on_story_started=started.append,
        generator_supports_role=generator_supports_role(request, actor),
    )
    schedule_first_story(request, background_tasks, principal, actor, started)
    return _envelope(record)


@router.post(
    "/{run_id}/subject-confirmation",
    response_model=ParentSubjectConfirmationResponseV1 | ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="[PROPOSAL] Persist adult confirmation of an interpreted drawing subject",
    responses=_ACTOR_STORY_ERROR_RESPONSES,
)
def confirm_parent_story_subject(
    run_id: UUID,
    payload: ParentSubjectConfirmationRequestV1,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentSubjectConfirmationResponseV1 | ParentStoryRunLifecycleEnvelopeV1:
    """SRS l.1666: 202. A plain confirmation settles at once; an edited subject reruns the VLM.

    The rerun (SRS l.394, l.1413) needs an analyzer to answer it: with none composed, or with
    ``app.state.subject_edit_reruns_vlm`` switched off, the edit is recorded and confirmed in one
    step (the recorded deviation DEV-1), so no client waits for a worker that does not exist.
    """
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    state = request.app.state
    analyzer = getattr(state, "drawing_analyzer", None)
    runtime = getattr(state, "be1_runtime", None)
    # T-4b3a D7e: a Teacher edit of a pinned run reruns the VLM like a Parent edit (the job runs
    # on the job-side repository); the repository keeps the DEV-1 path for a fixture row.
    rerun = bool(getattr(state, "subject_edit_reruns_vlm", True)) and analyzer is not None
    # V4-A OPEN-A D1: a Teacher confirmation may be the last gate of the first-story start.
    started: list[ParentStoryRevisionReservation] = []
    outcome = _invoke(
        _service_for(db, actor).confirm_subject,
        principal=principal,
        run_id=str(run_id),
        expected_understanding_revision=payload.expected_understanding_revision,
        confirmed_subject=payload.confirmed_subject,
        idempotency_key=key,
        rerun_on_edit=rerun,
        on_story_started=started.append,
        generator_supports_role=generator_supports_role(request, actor),
    )
    response.headers["Content-Location"] = f"/v1/story-runs/{run_id}"
    if isinstance(outcome, ParentStoryLifecycleRecord):
        return _lifecycle_envelope(outcome)
    schedule_first_story(request, background_tasks, principal, actor, started)
    if (
        outcome.decision == "RERUN_REQUESTED"
        and not outcome.replayed
        and outcome.input_revision is not None
        and analyzer is not None
        and runtime is not None
        and runtime.session_factory is not None
    ):
        runner = ParentInputJobRunner(runtime.session_factory, analyzer)
        job_arguments: tuple[Any, ...] = (
            (actor, outcome.organization_id) if actor.is_teacher else ()
        )
        background_tasks.add_task(
            runner.run, principal, str(run_id), outcome.input_revision, *job_arguments
        )
    return ParentSubjectConfirmationResponseV1.model_validate(
        {
            "request_id": uuid4(),
            "story_run_id": run_id,
            "understanding_revision": outcome.understanding_revision,
            "decision": outcome.decision,
            "run_revision": outcome.run_revision,
        }
    )


@router.post(
    "/{run_id}/script-confirmation",
    response_model=StoryRunResult,
    summary="[PROPOSAL] Persist adult confirmation of a generated story revision",
    responses=_ACTOR_STORY_ERROR_RESPONSES,
)
def confirm_parent_story_revision(
    run_id: UUID,
    payload: ParentStoryRevisionConfirmationRequestV1,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> StoryRunResult:
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    service = _service_for(db, actor)
    record = _invoke(
        service.confirm_story_revision,
        principal=principal,
        run_id=str(run_id),
        expected_revision=payload.expected_revision,
        expected_story_sha256=payload.story_sha256,
        idempotency_key=key,
    )
    return _envelope(record)


__all__ = ["router"]
