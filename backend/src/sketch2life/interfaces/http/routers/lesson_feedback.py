"""Lesson feedback access for Parent and assigned school staff."""

# ruff: noqa: B008
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_feedback import (
    LessonFeedbackPageV1,
    LessonFeedbackThreadV1,
    ParentLessonFeedbackInputV1,
    ParentLessonFeedbackReplyPageV1,
    ParentLessonFeedbackStateV1,
    ParentLessonFeedbackV1,
)
from sketch2life.contracts.schemas.platform_admin import FeedbackInput
from sketch2life.infrastructure.lesson_library.feedback import (
    LessonFeedbackService,
    ParentLessonFeedbackService,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.platform_admin.service import PlatformAdminService
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import (
    IdempotencyKeyHeader,
    _call,
    _limit_cursor,
    _parent_actor,
    get_lesson_library_service,
)
from sketch2life.interfaces.http.routers.platform_admin import Key, revision, run, service

router = APIRouter(prefix="/api/lesson-library/v1", tags=["Lesson feedback"])


def feedback_service(
    request: Request,
    admin: PlatformAdminService = Depends(service),
    lesson: LessonLibraryService = Depends(get_lesson_library_service),
) -> LessonFeedbackService:
    return LessonFeedbackService(
        admin,
        parent_lesson=lambda ref: _call(
            lambda: lesson.get_parent_lesson(
                parent_principal_ref=admin.principal.subject, lesson_id=ref
            )
        ),
        identity_provisioner=getattr(
            request.app.state, "identity_account_provisioner", None
        ),
    )


def parent_feedback_actor(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> VerifiedPrincipal:
    _parent_actor(db, principal)
    return principal


def parent_feedback_service(
    principal: VerifiedPrincipal = Depends(parent_feedback_actor),
    admin: PlatformAdminService = Depends(service),
    lesson: LessonLibraryService = Depends(get_lesson_library_service),
) -> ParentLessonFeedbackService:
    return ParentLessonFeedbackService(
        admin,
        parent_lesson=lambda ref: _call(
            lambda: lesson.get_parent_lesson(
                parent_principal_ref=principal.subject,
                lesson_id=ref,
            )
        ),
    )


@router.post("/organizations/{organization_id}/lessons/{lesson_id}/feedback", status_code=201)
def create_feedback(
    organization_id: str,
    lesson_id: str,
    payload: FeedbackInput,
    key: Key,
    svc=Depends(feedback_service),
):
    return run(lambda: svc.create(organization_id, lesson_id, payload.body, key))


@router.get(
    "/organizations/{organization_id}/feedback",
    response_model=LessonFeedbackPageV1,
)
def list_feedback(
    organization_id: str,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(feedback_service),
):
    return run(lambda: svc.list(organization_id, limit, cursor))


@router.get(
    "/organizations/{organization_id}/feedback/{thread_id}",
    response_model=LessonFeedbackThreadV1,
)
def read_feedback(
    organization_id: str,
    thread_id: str,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(feedback_service),
):
    return run(lambda: svc.detail(organization_id, thread_id, limit, cursor))


@router.post("/organizations/{organization_id}/feedback/{thread_id}/replies")
def reply_feedback(
    organization_id: str,
    thread_id: str,
    payload: FeedbackInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(feedback_service),
):
    return run(lambda: svc.reply(organization_id, thread_id, payload.body, expected, key))


@router.post(
    "/me/lessons/{lesson_id}/feedback",
    status_code=201,
    response_model=ParentLessonFeedbackV1,
)
def submit_parent_feedback(
    lesson_id: str,
    payload: ParentLessonFeedbackInputV1,
    response: Response,
    key: IdempotencyKeyHeader,
    svc: ParentLessonFeedbackService = Depends(parent_feedback_service),
) -> dict[str, object]:
    result = _call(
        lambda: svc.submit(
            lesson_id=lesson_id,
            feedback_text=payload.feedback_text,
            idempotency_key=key,
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/me/lessons/{lesson_id}/feedback",
    response_model=ParentLessonFeedbackStateV1,
)
def get_parent_feedback(
    lesson_id: str,
    response: Response,
    svc: ParentLessonFeedbackService = Depends(parent_feedback_service),
) -> dict[str, object]:
    result = _call(lambda: svc.state(lesson_id))
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/me/lessons/{lesson_id}/feedback/replies",
    response_model=ParentLessonFeedbackReplyPageV1,
)
def get_parent_feedback_replies(
    lesson_id: str,
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=768),
    svc: ParentLessonFeedbackService = Depends(parent_feedback_service),
) -> dict[str, object]:
    limit, cursor = _limit_cursor(limit, cursor)
    result = _call(lambda: svc.replies(lesson_id, limit=limit, cursor=cursor))
    response.headers["Cache-Control"] = "private, no-store"
    return result
