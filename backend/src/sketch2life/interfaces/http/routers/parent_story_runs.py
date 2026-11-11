"""Authenticated Parent StoryRun creation, retrieval, and adult confirmation APIs."""

# ruff: noqa: B008

from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentActiveStoryRunEnvelopeV1,
    ParentContextConfirmationRequestV1,
    ParentLessonPinSnapshotV1,
    ParentStoryErrorEnvelopeV1,
    ParentStoryRevisionConfirmationRequestV1,
    ParentStoryRunCreateRequestV1,
    ParentStoryRunEnvelopeV1,
    ParentStoryRunResponseV1,
    ParentSubjectConfirmationRequestV1,
    ParentSubjectConfirmationResponseV1,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service

router = APIRouter(prefix="/v1/story-runs", tags=["Parent StoryRuns"])
_PARENT_STORY_ERROR_RESPONSES = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    403: {"model": ParentStoryErrorEnvelopeV1, "description": "The action is not allowed."},
    404: {"model": ParentStoryErrorEnvelopeV1, "description": "The resource was not found."},
    409: {"model": ParentStoryErrorEnvelopeV1, "description": "The request conflicts with current state."},
    422: {"model": ParentStoryErrorEnvelopeV1, "description": "Validation uses the standard error envelope."},
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}


def _service(db: Session) -> ParentStoryRunService:
    return ParentStoryRunService(
        SqlParentStoryRunRepository(db),
        SqlParentStoryProfileLookup(db),
    )


def _require_parent(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "ACTION_NOT_ALLOWED"})
    return identity


def _invoke(callable_, **kwargs):
    try:
        return callable_(**kwargs)
    except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None


def _response(record) -> ParentStoryRunResponseV1:
    return ParentStoryRunResponseV1(
        run_id=record.run_id,
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
    )


@router.post(
    "",
    response_model=ParentStoryRunEnvelopeV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Parent StoryRun with a pinned profile and context proposal",
    responses=_PARENT_STORY_ERROR_RESPONSES,
)
def create_parent_story_run(
    payload: ParentStoryRunCreateRequestV1,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=256)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunEnvelopeV1:
    identity = _require_parent(db, principal)
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
        idempotency_key=idempotency_key,
        topic=payload.topic,
        adult_confirmed_idea=payload.adult_confirmed_idea,
        lesson_version_ref=lesson_version_ref,
    )
    if replay is not None:
        return ParentStoryRunEnvelopeV1(request_id=uuid4(), story_run=_response(replay))

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
        idempotency_key=idempotency_key,
        topic=payload.topic,
        adult_confirmed_idea=payload.adult_confirmed_idea,
        lesson_version_ref=lesson_version_ref,
        lesson_pin_snapshot=lesson_pin_snapshot,
    )
    return ParentStoryRunEnvelopeV1(request_id=uuid4(), story_run=_response(record))


@router.get(
    "/active/current",
    response_model=ParentActiveStoryRunEnvelopeV1,
    summary="[PROPOSAL] Resume the authenticated Parent's active StoryRun, if one exists",
    responses=_PARENT_STORY_ERROR_RESPONSES,
)
def get_active_parent_story_run(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActiveStoryRunEnvelopeV1:
    identity = _require_parent(db, principal)
    service = _service(db)
    record = _invoke(
        service.get_active_run,
        principal=principal,
        account_id=identity.account_id,
    )
    return ParentActiveStoryRunEnvelopeV1(
        request_id=uuid4(), story_run=_response(record) if record is not None else None
    )


@router.get(
    "/{run_id}",
    response_model=ParentStoryRunEnvelopeV1,
    summary="Read the authenticated Parent's saved StoryRun and review state",
    responses=_PARENT_STORY_ERROR_RESPONSES,
)
def get_parent_story_run(
    run_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunEnvelopeV1:
    _require_parent(db, principal)
    service = _service(db)
    record = _invoke(
        service.get_run,
        principal=principal,
        run_id=str(run_id),
    )
    return ParentStoryRunEnvelopeV1(request_id=uuid4(), story_run=_response(record))


@router.post(
    "/{run_id}/context-confirmation",
    response_model=ParentStoryRunEnvelopeV1,
    summary="[PROPOSAL] Confirm the immutable Parent context snapshot before story generation",
    responses=_PARENT_STORY_ERROR_RESPONSES,
)
def confirm_parent_story_context(
    run_id: UUID,
    payload: ParentContextConfirmationRequestV1,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=256)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunEnvelopeV1:
    _require_parent(db, principal)
    record = _invoke(
        _service(db).confirm_context,
        principal=principal,
        run_id=str(run_id),
        expected_context_revision=payload.expected_context_revision,
        expected_context_snapshot_sha256=payload.context_snapshot_sha256,
        idempotency_key=idempotency_key,
    )
    return ParentStoryRunEnvelopeV1(request_id=uuid4(), story_run=_response(record))


@router.post(
    "/{run_id}/subject-confirmation",
    response_model=ParentSubjectConfirmationResponseV1,
    summary="[PROPOSAL] Persist adult confirmation of an interpreted drawing subject",
    responses=_PARENT_STORY_ERROR_RESPONSES,
)
def confirm_parent_story_subject(
    run_id: UUID,
    payload: ParentSubjectConfirmationRequestV1,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=256)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentSubjectConfirmationResponseV1:
    _require_parent(db, principal)
    service = _service(db)
    revision = _invoke(
        service.confirm_subject,
        principal=principal,
        run_id=str(run_id),
        expected_understanding_revision=payload.expected_understanding_revision,
        confirmed_subject=payload.confirmed_subject,
        idempotency_key=idempotency_key,
    )
    return ParentSubjectConfirmationResponseV1(
        request_id=uuid4(),
        story_run_id=run_id,
        understanding_revision=revision,
        decision="CONFIRMED",
    )


@router.post(
    "/{run_id}/script-confirmation",
    response_model=ParentStoryRunEnvelopeV1,
    summary="[PROPOSAL] Persist adult confirmation of a generated story revision",
    responses=_PARENT_STORY_ERROR_RESPONSES,
)
def confirm_parent_story_revision(
    run_id: UUID,
    payload: ParentStoryRevisionConfirmationRequestV1,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=256)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunEnvelopeV1:
    _require_parent(db, principal)
    service = _service(db)
    record = _invoke(
        service.confirm_story_revision,
        principal=principal,
        run_id=str(run_id),
        expected_revision=payload.expected_revision,
        expected_story_sha256=payload.story_sha256,
        idempotency_key=idempotency_key,
    )
    return ParentStoryRunEnvelopeV1(request_id=uuid4(), story_run=_response(record))


__all__ = ["router"]
