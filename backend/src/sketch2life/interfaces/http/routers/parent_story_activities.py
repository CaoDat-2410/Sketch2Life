"""Parent main-activity routes (goal v4 T-2e-a; SRS l.514, l.527, l.1412, l.1667).

``GET /v1/activities?story_run_id=`` is the bounded list of age-fit lesson activities the adult may
choose from (at most 12, no cursor: a recommendation list, not a collection; DEV-4).
``POST /v1/story-runs/{run_id}/activity-selection`` records the choice; the same transaction may
start the first story (``context-confirmation`` does the same when it is the last gate). Both are
Parent only: any other caller gets the uniform 404. The story router is mounted and unmounted
together with ``parent_story_runs`` (the StoryRun-lite demo owns ``/v1/story-runs*``).
"""

# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentActivityListV1,
    ParentActivitySelectionRequestV1,
    ParentStoryErrorEnvelopeV1,
)
from sketch2life.infrastructure.lesson_library.parent_activity_catalog import (
    LessonLibraryParentActivityCatalogAdapter,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.routers.parent_story_inputs import schedule_first_story
from sketch2life.interfaces.http.routers.parent_story_runs import (
    StoryRunResult,
    _envelope,
    _require_parent,
)

router = APIRouter(prefix="/v1/story-runs", tags=["Parent StoryRuns"])
activities_router = APIRouter(prefix="/v1/activities", tags=["Parent StoryRuns"])

_ACTIVITY_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The run or the activity was not found, or the caller is not an active Parent owner."
        ),
    },
    409: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The run state or revision does not allow choosing an activity now.",
    },
    422: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The subject of the drawing is not confirmed yet (SUBJECT_NOT_CONFIRMED).",
    },
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}


class _LessonLibraryCatalog(ParentActivityCatalogPort):
    """The Lesson Library catalog, built on first use: a replay of a selection never recomputes the
    list, so it needs no lesson storage. When storage is not composed the first read answers the
    503 ``DEPENDENCY_UNAVAILABLE`` of ``get_lesson_library_service``."""

    def __init__(self, request: Request, db: Session) -> None:
        self._request = request
        self._db = db

    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        adapter = LessonLibraryParentActivityCatalogAdapter(
            get_lesson_library_service(self._request, self._db)
        )
        return adapter.list_accessible_lessons(parent_principal_ref=parent_principal_ref)


def _selection_service(request: Request, db: Session) -> ParentActivitySelectionService:
    """The repository of the Parent and the catalog over the Lesson Library, both on the request's
    one ``Session`` (the catalog is read inside the Story transaction, read-only)."""

    return ParentActivitySelectionService(
        SqlParentStoryRunRepository(db), _LessonLibraryCatalog(request, db)
    )


def _http_error(exc: ParentStoryRunError) -> HTTPException:
    detail: dict[str, Any] = {"code": exc.code}
    if exc.current_version is not None:
        detail["current_version"] = exc.current_version
    return HTTPException(status_code=exc.status_code, detail=detail)


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})


@activities_router.get(
    "",
    response_model=ParentActivityListV1,
    summary="[PROPOSAL] List the age-fit lesson activities a Parent may choose for a StoryRun",
    responses={
        status: _ACTIVITY_ERROR_RESPONSES[status] for status in (400, 401, 404, 409, 422, 503, 500)
    },
)
def list_parent_activities(
    request: Request,
    story_run_id: UUID = Query(),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActivityListV1:
    """At most 12 activities in a deterministic order, with the basis they were chosen on."""

    _require_parent(db, principal)
    service = _selection_service(request, db)
    try:
        listing = service.list_activities(principal=principal, run_id=str(story_run_id))
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    except LessonLibraryError:
        raise _not_found() from None
    return ParentActivityListV1.model_validate({"request_id": uuid4(), **listing})


@router.post(
    "/{run_id}/activity-selection",
    response_model=StoryRunResult,
    summary="[PROPOSAL] Choose the main activity of the Parent StoryRun",
    responses=_ACTIVITY_ERROR_RESPONSES,
)
def select_parent_story_activity(
    run_id: UUID,
    payload: ParentActivitySelectionRequestV1,
    request: Request,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> StoryRunResult:
    """200 with the run envelope. A replay returns the run as it is now and never recomputes the
    list; a first execution accepts only an activity that is in the list recomputed now."""

    del idempotency_key
    _require_parent(db, principal)
    key = parse_idempotency_key(request)
    service = _selection_service(request, db)
    started: list[ParentStoryRevisionReservation] = []
    try:
        if payload.activity is not None:
            record = service.select_activity(
                principal=principal,
                run_id=str(run_id),
                expected_revision=payload.expected_revision,
                activity_ref=payload.activity.model_dump(),
                idempotency_key=key,
                on_story_started=started.append,
            )
        else:
            if (
                payload.suggestion_set_id is None
                or payload.expected_understanding_revision is None
                or payload.activity_index is None
            ):
                raise ParentStoryRunError(422, "PARENT_ACTIVITY_SELECTION_INVALID")
            record = SqlParentStoryRunRepository(db).select_suggested_activity(
                principal=principal,
                run_id=str(run_id),
                expected_revision=payload.expected_revision,
                suggestion_set_id=str(payload.suggestion_set_id),
                expected_understanding_revision=payload.expected_understanding_revision,
                activity_index=payload.activity_index,
                idempotency_key=key,
                on_story_started=started.append,
            )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    except LessonLibraryError:
        raise _not_found() from None
    schedule_first_story(request, background_tasks, principal, None, started)
    return _envelope(record)


__all__ = ["activities_router", "router"]
