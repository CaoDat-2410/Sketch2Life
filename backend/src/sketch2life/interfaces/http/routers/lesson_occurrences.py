"""Teacher lesson occurrence routes (FEAT-066 goal v3, T-3a; SRS l.775, l.798, l.1652, l.1699).

Literal paths under ``/v1/lesson-occurrences`` (TD-01, C-D9). Create is keyed (C-D5); reads carry a
strong ``ETag`` (the occurrence revision) and answer 304 after authorisation. Every refusal outside
the caller's scope is the uniform 404 (C-D4, CV-5); only an in-scope role refusal is 403 and a
Teacher without a ``teacher`` assignment for the class is 409 ``TEACHER_ASSIGNMENT_REQUIRED``.
T-3b adds the document routes (attach a completed upload as a 202 extraction job, read the
document and its text revisions); T-3c adds the keyed text edit (a new immutable revision, 201, or
the head unchanged, 200); T-3d adds the plan routes: a keyed draft create (201), a keyed confirm of
the head revision (200) and two reads. Plan routes answer 400 for validation, never 422.
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, NoReturn

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_occurrences import (
    AttachOccurrenceDocumentRequestV1,
    ConfirmPlanRevisionRequestV1,
    CreateLessonOccurrenceRequestV1,
    CreatePlanRevisionRequestV1,
    EditDocumentRevisionRequestV1,
    LessonDocumentRevisionPageV1,
    LessonDocumentRevisionV2,
    LessonOccurrencePageV1,
    LessonOccurrenceV1,
    LessonPlanRevisionPageV1,
    LessonPlanRevisionV1,
    LessonSourceDocumentAcceptedV1,
    LessonSourceDocumentPageV1,
    LessonSourceDocumentV1,
    OccurrenceStateV1,
)
from sketch2life.domain.lesson_occurrences.documents import (
    DocumentRuleError,
    document_etag,
    etag_matches,
    revision_etag,
)
from sketch2life.domain.lesson_occurrences.model import (
    LessonOccurrenceRuleError,
    etag_for_revision,
    if_none_match_matches,
)
from sketch2life.domain.lesson_occurrences.plan import etag_matches as plan_etag_matches
from sketch2life.domain.lesson_occurrences.plan import plan_etag
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    PRODUCTION_REGISTRY,
    ChecklistRegistry,
)
from sketch2life.infrastructure.lesson_occurrences.documents import (
    OccurrenceDocumentService,
    ParseGate,
)
from sketch2life.infrastructure.lesson_occurrences.plans import PlanRevisionService
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.lesson_occurrences.service import LessonOccurrenceService
from sketch2life.interfaces.http.api_conventions import (
    limit_query,
    parse_idempotency_key,
    raise_stale_revision,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/v1/lesson-occurrences", tags=["Lesson Occurrences"])

IdempotencyKeyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]
# A NUL byte can never be part of an id and PostgreSQL text cannot hold it: refuse it as a 400
# before any query instead of a retryable 503 (T-3d review F-02).
_NO_NUL = r"^[^\x00]+$"
OccurrenceId = Annotated[str, Path(min_length=1, max_length=256, pattern=_NO_NUL)]
DocumentId = Annotated[str, Path(min_length=1, max_length=256, pattern=_NO_NUL)]
RevisionNo = Annotated[int, Path(ge=1, le=1_000_000)]
_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}


def get_occurrence_service(db: Session = Depends(get_db)) -> LessonOccurrenceService:
    return LessonOccurrenceService(db)


def get_document_service(
    request: Request, db: Session = Depends(get_db)
) -> OccurrenceDocumentService:
    state = request.app.state
    gate: ParseGate | None = getattr(state, "lesson_document_parse_gate", None)
    return OccurrenceDocumentService(
        db,
        storage=getattr(state, "lesson_library_storage", None),
        parser=getattr(state, "lesson_document_parser", None),
        gate=gate,
    )


def get_checklist_registry() -> ChecklistRegistry:
    """The safety checklist definitions: the shipped registry is empty (T-3d-DEC-3).

    A dependency so a test can inject a definition without any import path that populates the
    production constant.
    """
    return PRODUCTION_REGISTRY


def get_plan_service(
    db: Session = Depends(get_db),
    checklists: ChecklistRegistry = Depends(get_checklist_registry),
) -> PlanRevisionService:
    return PlanRevisionService(db, checklists=checklists)


def _raise(
    exc: LessonOccurrenceError | LessonOccurrenceRuleError | DocumentRuleError,
) -> NoReturn:
    if isinstance(exc, (LessonOccurrenceRuleError, DocumentRuleError)):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": exc.field, "code": exc.code}],
            },
        ) from None
    if exc.code == "STALE_REVISION":
        raise_stale_revision(current_version=exc.current_version, etag=getattr(exc, "etag", None))
    detail: dict[str, Any] = {"code": exc.code}
    if exc.field_errors:
        detail["field_errors"] = exc.field_errors
    retry_after = getattr(exc, "retry_after", None)
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
    raise HTTPException(status_code=exc.status_code, detail=detail, headers=headers) from None


def _call[Result](function: Callable[[], Result]) -> Result:
    try:
        return function()
    except (LessonOccurrenceError, LessonOccurrenceRuleError, DocumentRuleError) as exc:
        _raise(exc)


@router.post(
    "",
    response_model=LessonOccurrenceV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create a lesson occurrence for a class the Teacher is assigned to",
)
def create_lesson_occurrence(
    payload: CreateLessonOccurrenceRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonOccurrenceService = Depends(get_occurrence_service),
) -> dict[str, Any]:
    # The declaration above publishes the header as required; parse_idempotency_key (C-D5, 1-128
    # visible ASCII) is the authority.
    del idempotency_key
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.create(principal=principal, payload=payload, idempotency_key=key)
    )
    body = result.body
    response.headers["Location"] = f"/v1/lesson-occurrences/{body['occurrence_id']}"
    response.headers["ETag"] = etag_for_revision(int(body["revision"]))
    return body


@router.get(
    "/{occurrence_id}",
    response_model=LessonOccurrenceV1,
    summary="Read one lesson occurrence",
    responses={304: {"description": "Not modified (only after the caller was authorised)"}},
)
def get_lesson_occurrence(
    occurrence_id: OccurrenceId,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonOccurrenceService = Depends(get_occurrence_service),
) -> Any:
    body = _call(lambda: service.get(principal=principal, occurrence_id=occurrence_id))
    revision = int(body["revision"])
    etag = etag_for_revision(revision)
    if if_none_match_matches(request.headers.get("If-None-Match"), revision):
        return Response(status_code=304, headers={**_READ_HEADERS, "ETag": etag})
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    response.headers["ETag"] = etag
    return body


@router.get(
    "",
    response_model=LessonOccurrencePageV1,
    summary="List the lesson occurrences of one class, newest first",
)
def list_lesson_occurrences(
    response: Response,
    class_id: str = Query(min_length=1, max_length=128),
    state: OccurrenceStateV1 | None = None,
    limit: int = limit_query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=512),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonOccurrenceService = Depends(get_occurrence_service),
) -> dict[str, Any]:
    page = _call(
        lambda: service.list_page(
            principal=principal, class_id=class_id, state=state, limit=limit, cursor=cursor
        )
    )
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    return page


# ----------------------------------------------------------------------------- source documents
@router.post(
    "/{occurrence_id}/documents",
    response_model=LessonSourceDocumentAcceptedV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Attach a completed upload to an occurrence and start its text extraction job",
)
def attach_occurrence_document(
    occurrence_id: OccurrenceId,
    payload: AttachOccurrenceDocumentRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: OccurrenceDocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    del idempotency_key
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.attach(
            principal=principal,
            occurrence_id=occurrence_id,
            payload=payload,
            idempotency_key=key,
        )
    )
    body = result.body
    response.headers["Location"] = f"/v1/jobs/{body['job']['job_id']}"
    response.headers["Content-Location"] = (
        f"/v1/lesson-occurrences/{occurrence_id}/documents/{body['source_document_id']}"
    )
    return body


@router.get(
    "/{occurrence_id}/documents",
    response_model=LessonSourceDocumentPageV1,
    summary="List the documents attached to an occurrence, newest first",
)
def list_occurrence_documents(
    occurrence_id: OccurrenceId,
    response: Response,
    limit: int = limit_query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=512),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: OccurrenceDocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    page = _call(
        lambda: service.list_documents(
            principal=principal, occurrence_id=occurrence_id, limit=limit, cursor=cursor
        )
    )
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    return page


@router.get(
    "/{occurrence_id}/documents/{document_id}",
    response_model=LessonSourceDocumentV1,
    summary="Read one attached document",
    responses={304: {"description": "Not modified (only after the caller was authorised)"}},
)
def get_occurrence_document(
    occurrence_id: OccurrenceId,
    document_id: DocumentId,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: OccurrenceDocumentService = Depends(get_document_service),
) -> Any:
    body = _call(
        lambda: service.get_document(
            principal=principal, occurrence_id=occurrence_id, document_id=document_id
        )
    )
    etag = document_etag(int(body["head_revision_no"]))
    if etag_matches(request.headers.get("If-None-Match"), etag):
        return Response(status_code=304, headers={**_READ_HEADERS, "ETag": etag})
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    response.headers["ETag"] = etag
    return body


@router.get(
    "/{occurrence_id}/documents/{document_id}/revisions",
    response_model=LessonDocumentRevisionPageV1,
    summary="List the text revisions of a document without their text, newest first",
)
def list_document_revisions(
    occurrence_id: OccurrenceId,
    document_id: DocumentId,
    response: Response,
    limit: int = limit_query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=512),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: OccurrenceDocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    page = _call(
        lambda: service.list_revisions(
            principal=principal,
            occurrence_id=occurrence_id,
            document_id=document_id,
            limit=limit,
            cursor=cursor,
        )
    )
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    return page


@router.post(
    "/{occurrence_id}/documents/{document_id}/revisions",
    response_model=LessonDocumentRevisionV2,
    status_code=status.HTTP_201_CREATED,
    summary="Save the Teacher's edit of the extracted text as a new immutable revision",
    responses={
        200: {
            "description": "The text equals the head: nothing was written",
            "model": LessonDocumentRevisionV2,
        }
    },
)
def edit_document_revision(
    occurrence_id: OccurrenceId,
    document_id: DocumentId,
    payload: EditDocumentRevisionRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: OccurrenceDocumentService = Depends(get_document_service),
) -> dict[str, Any]:
    del idempotency_key
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.edit_revision(
            principal=principal,
            occurrence_id=occurrence_id,
            document_id=document_id,
            payload=payload,
            idempotency_key=key,
        )
    )
    body = result.body
    location = (
        f"/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}"
        f"/revisions/{body['revision_no']}"
    )
    response.status_code = result.status_code
    response.headers["Location" if result.status_code == 201 else "Content-Location"] = location
    response.headers["ETag"] = revision_etag(str(body["text_hash"]), str(body["review_state"]))
    response.headers["Cache-Control"] = "private, no-cache"
    return body


@router.get(
    "/{occurrence_id}/documents/{document_id}/revisions/{revision_no}",
    response_model=LessonDocumentRevisionV2,
    summary="Read one text revision of a document with its extracted text",
    responses={304: {"description": "Not modified (only after the caller was authorised)"}},
)
def get_document_revision(
    occurrence_id: OccurrenceId,
    document_id: DocumentId,
    revision_no: RevisionNo,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: OccurrenceDocumentService = Depends(get_document_service),
) -> Any:
    body = _call(
        lambda: service.get_revision(
            principal=principal,
            occurrence_id=occurrence_id,
            document_id=document_id,
            revision_no=revision_no,
        )
    )
    etag = revision_etag(str(body["text_hash"]), str(body["review_state"]))
    if etag_matches(request.headers.get("If-None-Match"), etag):
        return Response(status_code=304, headers={**_READ_HEADERS, "ETag": etag})
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    response.headers["ETag"] = etag
    return body


# ----------------------------------------------------------------------------- plan revisions
@router.post(
    "/{occurrence_id}/plan-revisions",
    response_model=LessonPlanRevisionV1,
    status_code=status.HTTP_201_CREATED,
    summary="Write a draft plan revision of an occurrence (immutable once written)",
)
def create_plan_revision(
    occurrence_id: OccurrenceId,
    payload: CreatePlanRevisionRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: PlanRevisionService = Depends(get_plan_service),
) -> dict[str, Any]:
    del idempotency_key
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.create_revision(
            principal=principal,
            occurrence_id=occurrence_id,
            payload=payload,
            idempotency_key=key,
        )
    )
    body = result.body
    response.headers["Location"] = (
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{body['revision_no']}"
    )
    response.headers["ETag"] = plan_etag(str(body["content_hash"]), str(body["state"]))
    response.headers["Cache-Control"] = "private, no-cache"
    return body


@router.get(
    "/{occurrence_id}/plan-revisions",
    response_model=LessonPlanRevisionPageV1,
    summary="List the plan revisions of an occurrence, newest first",
)
def list_plan_revisions(
    occurrence_id: OccurrenceId,
    response: Response,
    limit: int = limit_query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=512),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: PlanRevisionService = Depends(get_plan_service),
) -> dict[str, Any]:
    page = _call(
        lambda: service.list_revisions(
            principal=principal, occurrence_id=occurrence_id, limit=limit, cursor=cursor
        )
    )
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    return page


@router.get(
    "/{occurrence_id}/plan-revisions/{revision_no}",
    response_model=LessonPlanRevisionV1,
    summary="Read one plan revision",
    responses={304: {"description": "Not modified (only after the caller was authorised)"}},
)
def get_plan_revision(
    occurrence_id: OccurrenceId,
    revision_no: RevisionNo,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: PlanRevisionService = Depends(get_plan_service),
) -> Any:
    body = _call(
        lambda: service.get_revision(
            principal=principal, occurrence_id=occurrence_id, revision_no=revision_no
        )
    )
    etag = plan_etag(str(body["content_hash"]), str(body["state"]))
    if plan_etag_matches(request.headers.get("If-None-Match"), etag):
        return Response(status_code=304, headers={**_READ_HEADERS, "ETag": etag})
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    response.headers["ETag"] = etag
    return body


@router.post(
    "/{occurrence_id}/plan-revisions/{revision_no}/confirm",
    response_model=LessonPlanRevisionV1,
    summary="Approve the head plan revision with its expected hash and safety checklist",
)
def confirm_plan_revision(
    occurrence_id: OccurrenceId,
    revision_no: RevisionNo,
    payload: ConfirmPlanRevisionRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: PlanRevisionService = Depends(get_plan_service),
) -> dict[str, Any]:
    del idempotency_key
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.confirm_revision(
            principal=principal,
            occurrence_id=occurrence_id,
            revision_no=revision_no,
            payload=payload,
            idempotency_key=key,
        )
    )
    body = result.body
    response.headers["Content-Location"] = (
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{body['revision_no']}"
    )
    response.headers["ETag"] = plan_etag(str(body["content_hash"]), str(body["state"]))
    response.headers["Cache-Control"] = "private, no-cache"
    return body
