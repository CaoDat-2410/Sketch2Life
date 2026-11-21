"""Lesson feedback access for Parent and assigned school staff."""

# ruff: noqa: B008
from fastapi import APIRouter, Depends, Query

from sketch2life.contracts.schemas.platform_admin import FeedbackInput
from sketch2life.infrastructure.lesson_library.feedback import LessonFeedbackService
from sketch2life.interfaces.http.routers.lesson_library import _call, get_lesson_library_service
from sketch2life.interfaces.http.routers.platform_admin import Key, revision, run, service

router = APIRouter(prefix="/api/lesson-library/v1", tags=["Lesson feedback"])


def feedback_service(admin=Depends(service), lesson=Depends(get_lesson_library_service)):
    return LessonFeedbackService(
        admin,
        parent_lesson=lambda ref: _call(
            lambda: lesson.get_parent_lesson(
                parent_principal_ref=admin.principal.subject, lesson_id=ref
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


@router.get("/organizations/{organization_id}/feedback")
def list_feedback(
    organization_id: str,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(feedback_service),
):
    return run(lambda: svc.list(organization_id, limit, cursor))


@router.get("/organizations/{organization_id}/feedback/{thread_id}")
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
